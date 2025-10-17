#Feed Indexer tests [316-000000-043]

#Author: P.P.A. Kotze, H. Niehaus, T. Glaubach
#Date: 1/9/2020
#Version: 
#0.1 Initial
#0.2 Update after feedback and correction from HN email dated 1/8/2020
#0.3 Rework scu_get and scu_put to simplify
#0.4 attempt more generic scu_put with either jason payload or simple params, remove payload from feedback function
#0.5 create scu_lib
#0.6 1/10/2020 added load track tables and start table tracking also as debug added 'field' command for old scu
#HN: 13/05/2021 Changed the way file name is defined by defining a start time 
# 1.0 2022-05-26 added stowing / unstowing / taking /releasing command authorithy / (de)activating axis
#                added logging
#                changed the session saving function

#Import of Python available libraries

import os, inspect, sys
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
if __name__ == '__main__':
    sys.path.insert(0, parent_dir)

import ctypes
import sys
import threading
import warnings
from io import StringIO
import datetime
import time
import requests
import re
import json
import traceback
import urllib


import warnings
from functools import wraps

import numpy as np
import pandas as pd


from astropy.time import Time
import astropy.units as u
from astropy.coordinates import EarthLocation, get_sun, AltAz, get_body


def get_moon(*args, **kwargs):
    return get_body("moon", *args, **kwargs)

import logging, websockets, asyncio, socket

from websockets.sync.client import connect as ws_sync_connect

import mke_sculib.chan_list_acu as chans
from mke_sculib.helpers import make_zulustr, match_zulutime, get_utcnow, parse_zulutime, parse_timedelta, colors, colors_dc, print_color, is_notebook, get_ntp_time_with_socket, anytime2datetime
from mke_sculib import dish_checker

    

def send_mattermost(url, whoami, subject, emoji='', t=''):

    try:
        if not url:
            print_color('send_mattermost not sending text, since no URL given', color=colors.WARNING)
        if not whoami:
            whoami = send_mattermost.hostname
        if not t:
            t = 'no_time_given'
        s = f'{emoji}```[{t}]: {subject}```'
        
        username = f'sculib "{whoami}" sending from :"{send_mattermost.ip}"'
        headers = {'Content-Type': 'application/json'}
        dc = { "text": s, "username": username}

        response = requests.post(url, headers=headers, json=dc) 

        if response.status_code != 200:
            print_color(f'send_mattermost failed with status_code: {response.status_code} | text: {response.text}', color=colors.WARNING)
    except Exception as err:
        print_color(f'send_mattermost failed with exception: {err.__repr__()}', color=colors.WARNING)
    
send_mattermost.hostname = socket.gethostname()
send_mattermost.ip = socket.gethostbyname(socket.gethostname())

log_mattermost = None
def activate_logging_mattermost(whoami, url_qry = 'http://10.98.76.45:8990/logurl'):
    log('DEPRECATED!: logging should in future be handled by the actual acu objects, NOT globally!', color=colors.WARNING)
    mattermost_url = requests.get(f'{url_qry}').json().get('url')
    if issubclass(type(whoami), scu):
        whoami = whoami.antenna_id if whoami.antenna_id else whoami.ip
    global log_mattermost
    log_mattermost = lambda x: send_mattermost(mattermost_url, whoami, x)
    return True

def deactivate_logging_mattermost():
    log('DEPRECATED!: logging should in future be handled by the actual acu objects, NOT globally!', color=colors.WARNING)
    global log_mattermost
    log_mattermost = None


def _cb_log_send_mattermost(name, msg, color, t, *args, mattermost_url = None, **kwargs):

    if not mattermost_url is None:
        emoji = ''
        if color == colors.WARNING:
            emoji =':warning: '
        elif color == colors.FAIL:
            emoji = ':x: '
        elif color == colors.OKGREEN:
            emoji = ':white_check_mark: '
        else:
            emoji = ':information_source: '
            
        # log_mattermost(emoji + msg)
        threading.Thread(target = send_mattermost, args=(mattermost_url, name, msg, emoji, t)).start()


def logfun(msg, color=colors.BLACK, name='noname', t=None, callbacks_logging=None, do_print=True):
    if callbacks_logging is None:
        callbacks_logging  = {}

    if t is None:
        t = datetime.datetime.now(datetime.timezone.utc)

    if isinstance(t, datetime.datetime):
        t = t.isoformat().replace('T', ' ').split('.')[0] + 'Zl'
    elif isinstance(t, Time):
        t = t.iso
    elif isinstance(t, (float, int)) and t > 1700000000:
        t = Time(t, format='unix').iso
    elif isinstance(t, (float, int)):
        t = Time(t, format='mjd').iso
    elif isinstance(t, (str, bytes)):
        pass # is OK
    else:
        raise TypeError(f'time input {t=} is of unknown type  {type(t)=}')
    
    for key, fun in callbacks_logging.items():
        try:
            fun(name, msg, color=color, t=t)
        except Exception as err:
            pass
        
    if do_print:
        print(f'{color}[{t} - {name}] {msg}{colors.BLACK}')

def getLogger(name):
    def printlog(msg, color=colors.BLACK, t=None): 
        return logfun(msg, color, name=name, t=t)
    return printlog


log = getLogger('sculib')


configs_dc = {
    'full': chans.channels_detailed,
    'normal': chans.channels_normal,
    'reduced': chans.channels_reduced,
    'small': chans.channels_small,
    'hn_fi': chans.channels_hn_feed_indexer_sensors,
    'hn_tilt': chans.channels_hn_tilt_sensors,
}

command_auth_dc = {
    -1: 'UNKNOWN',
    0: 'FREE',
    1: 'LMC',
    2: 'ENG_UI',
    3: 'WEB_UI',
    4: 'HHP'
}

state_dc = {
    -1: "UNKNOWN",
    0: "Undefined",
    1: "Standby",
    2: "Parked",
    3: "Locked",
    4: "E-Stop",
    6: "Stowed",
    9: "Locked and Stowed (3+9)",
    10: "Activating",
    19: "Deactivating",
    110: "SIP",
    120: "Stop",
    130: "Slew",
    220: "Jog",
    300: "Track",
}

bands_dc_inv = {
    0: "Not in Pos.",
    1: "Band 1",
    2: "Band 2",
    3: "Band 3",
    4: "Band 4",
    5: "Band 5a",
    6: "Band 5b",
    7: "Band 5c",
    8: "Maint. Pos. 1",
    9: "Maint. Pos. 2",    
}
bands_dc = {v:k for k, v in bands_dc_inv.items()}

# bands_dc = {'Band 1': 1, 'Band 2': 2, 'Band 3': 3, 'Band 4': 4, 'Band 5a': 5, 'Band 5b': 6, 'Band 5c': 7}
# bands_dc_inv = {v:k for k, v in bands_dc.items()}

state_dc_all = {k:v.upper() for k, v in state_dc.items()}
state_dc_all.update({str(k):v.upper() for k, v in state_dc.items()})
state_dc_all.update({v.upper():v.upper() for k, v in state_dc.items()})
state_dc_all.update({v.lower():v.upper() for k, v in state_dc.items()})

state_dc = {k:v.upper() for k, v in state_dc.items()}
state_dc_inv = {v:k for k, v in state_dc.items()}

state_dc_inv['DEPLOYING'] = 4
state_dc_inv['DEPLOYED'] = 3
state_dc_inv['RETRACTING'] = 2
state_dc_inv['RETRACTED'] = 1





def link_stellarium(antenna_id='', stellarium_address = 'http://localhost:8090', debug=False, url_qry = 'http://10.98.76.45:8990/antennas', **kwargs):

    if not 'use_socket' in kwargs:
        kwargs['use_socket'] = False
    if not 'wait_done_by_uuid' in kwargs:
        kwargs['wait_done_by_uuid'] = False
    if not 'start_streams_on_construct':
        kwargs['start_streams_on_construct'] = False

    dish = load(antenna_id=antenna_id, debug=debug, url_qry=url_qry, **kwargs)
    dish.link_stellarium(stellarium_address)

def _resolve_antenna_ip(ip, url_qry = 'http://10.98.76.45:8990/antennas', **kwargs):

    antennas = requests.get(f'{url_qry}', **kwargs).json()
    antenna_id = next((d['id'] for d in antennas if d['address'] == ip), "")
    if not antenna_id:
        antenna_id = next((d['id'] for d in antennas if ip in d['address'] or d['address'] in ip), "")
    return antenna_id


def load(antenna_id='', readonly=False, use_socket=True, debug=False, url_qry = 'http://10.98.76.45:8990/antennas', **kwargs):

    was_int = False
    if not isinstance(antenna_id, str):
        antenna_id = str(antenna_id)
        was_int = True

    antennas = requests.get(f'{url_qry}').json()

    if not antenna_id:
        prompt = '\n   '.join([f'{i: 3.0f}: Dish "{dc.get("id")}" @{dc.get("address")}' for i, dc in enumerate(antennas)])
        prompt = f'Found the following dishes to choose from:\n   {prompt}\n\n Please select one (0...{len(antennas)-1}): '
        isel = None
        allowed = [str(i) for i in range(len(antennas))]

        while not isel in allowed:
            if not isel is None:
                print(f'INPUT: "{isel}" incorrect please try again')
            isel = input(prompt)

        dc = antennas[int(isel)]
        antenna_id = dc.get('id')

    else:
        ids = [a.get('id') for a in antennas]
        dcs = [a for a in antennas if a.get('id') == antenna_id]

        if not dcs:
            
            dcs = [a for a in antennas if antenna_id in a.get('id')]

            if dcs and not was_int:
                log(f'requested {antenna_id=} not found in available {ids=}, resolved to "{next(iter(dcs))}"', colors.WARNING)
        assert dcs, f'could not find any antenna which matches the requested {antenna_id=} in available {ids=}'
        dc = next(iter(dcs))
    
    # dc = requests.get(f'{url_qry}/{antenna_id}').json()
    
    assert antenna_id, 'need to give an antenna id'

    try:
        params = json.loads(dc.get('params_json', '{}'))
        if not params:
            params = dc.get('params', {})
    except Exception as err:
        log(f'could not load "params_json" from server', colors.WARNING)
        params = {}

    kwargs['readonly'] = readonly
    kwargs['use_socket'] = use_socket
    kwargs['wait_done_by_uuid'] = kwargs.get('wait_done_by_uuid', True if use_socket else False)
    kwargs['start_streams_on_construct'] = kwargs.pop('start_streams_on_construct', True if use_socket else False)
    kwargs['antenna_dc'] = dc
    kwargs['antenna_id'] = antenna_id    
    kwargs['debug'] = debug
    
    address = dc['address']

    fun = lambda x: f'{type(x).__name__} of len {len(x)}' if isinstance(x, (dict, list)) else x
    log('constructing dish with: address = "{}" and kwargs={}'.format(address, {k:fun(v) for k, v in kwargs.items()}), color=colors.OKBLUE)

    dish = scu(dc['address'], **kwargs)
    
    for k, v in params.items():
        if hasattr(dish, k):
            setattr(dish, k, v)

    try:
        assert dish.ping(), 'ping failed!'
        dish.determine_dish_type()

    except Exception as err:
        log(f'Error when trying to initialize connection to dish {dish}', colors.FAIL)
        
    log(f'loaded dish: {dish}', colors.OKBLUE)
    return dish
        



"""
███████ ████████ ██████  ███████  █████  ███    ███     ███████ ██    ██ ███████ ███    ██ ████████ 
██         ██    ██   ██ ██      ██   ██ ████  ████     ██      ██    ██ ██      ████   ██    ██    
███████    ██    ██████  █████   ███████ ██ ████ ██     █████   ██    ██ █████   ██ ██  ██    ██    
     ██    ██    ██   ██ ██      ██   ██ ██  ██  ██     ██       ██  ██  ██      ██  ██ ██    ██    
███████    ██    ██   ██ ███████ ██   ██ ██      ██     ███████   ████   ███████ ██   ████    ██    
"""


class ScuEvent():
    @staticmethod
    def get_uuid(dc):
        return '' if not dc else dc.get('parameters', {}).get('uuid', '')
    
    def __init__(self, dc) -> None:
        self.history = [dc]
        self._uuid = ScuEvent.get_uuid(dc)

        self.is_done = False if not dc else dc.get('parameters', {}).get('resultMessage', False)


    def update(self, dc):
        if dc:
            assert ScuEvent.get_uuid(dc) == self.uuid, 'wrong event uuid!'
            if not self.is_done:
                self.is_done = dc.get('parameters', {}).get('resultMessage', False)
            self.history.append(dc)

    @property
    def dc(self):
        return next(iter(self.history), {})

    
    @property
    def level(self):
        return '' if not self.dc else self.dc.get('level', None)
        
    @property
    def state(self):
        return '' if not self.dc else self.dc.get('parameters', {}).get('currentState', None)

    @property
    def path(self):
        return '' if not self.dc else self.dc.get('parameters', {}).get('path', None)

    @property
    def timestamp(self):
        return '' if not self.dc else self.dc.get('parameters', {}).get('timestamp', None)

    @property
    def id(self):
        """synonym for self.uuid"""
        return self.uuid
    
    @property
    def uuid(self):
        return self._uuid if self._uuid else id(self)
    
    def to_str(self):
        return f'Event {self.uuid}: @{self.timestamp} | State: {self.state} | path: {self.path}'
    
    def pprint(self, seperate_time=False):
        dc = getattr(self, 'dc', self)
        flatdict = {**{k:v for k, v in dc.items() if k != 'parameters'}, **dc.get('parameters')}

        for needed in 'timestamp level codeName path currentState resultCode resultMessage'.split():
            if not needed in flatdict:
                flatdict[needed] = ''

        if seperate_time:
            t = flatdict.pop('timestamp')
            path = flatdict.pop('path')
            # if len(path) > 20: 
            #     path = '...' + path[-20:]
            
            return 'event {level} {codeName}: {path} {currentState}=>{resultCode} ({resultMessage})'.format(path=path, **flatdict), t
        else:
            return '[{timestamp}] event {level} | {codeName}: {path} {currentState} => {resultCode} ({resultMessage})'.format(**flatdict)

"""
███████ ████████ ██████  ███████  █████  ███    ███     ██████   █████  ████████  █████  
██         ██    ██   ██ ██      ██   ██ ████  ████     ██   ██ ██   ██    ██    ██   ██ 
███████    ██    ██████  █████   ███████ ██ ████ ██     ██   ██ ███████    ██    ███████ 
     ██    ██    ██   ██ ██      ██   ██ ██  ██  ██     ██   ██ ██   ██    ██    ██   ██ 
███████    ██    ██   ██ ███████ ██   ██ ██      ██     ██████  ██   ██    ██    ██   ██ 
"""


class EventStreamHandler():

    def __init__(self, parent, dict_size = 200, verb=True, on_new_cbs=None, log_errors=True, log_warnings=True)  -> None:
        assert not parent is None, 'parent can not be None'
        self.parent = parent

        self.events = {}
        self.uids_cmd = {}

        self.thread = None
        self.thread_id = None
        self.tickcount = 0
        self.dict_size = dict_size

        self.do_test_on_call = True
        self.do_start_on_call = True

        self.callbacks_on_new = [] if on_new_cbs is None else on_new_cbs

        self.log_errors = log_errors
        self.log_warnings = log_warnings

        self.verb=verb

    # def wait_for_start(self, timeout=10.):
    #     if self.verb: log('waiting for data stream to start...', color=colors.HEADER)
    #     t = time.time()
    #     while (time.time() - t) < timeout and not self.tickcount:
    #         time.sleep(0.1)
    #     if self.verb: log('--> stream started OK', color=colors.OKGREEN)

    def log(self, *args, **kwargs):
        if hasattr(self.parent, 'log'):
            return self.parent.log(*args, **kwargs)
        else:
            return log(*args, **kwargs)

    def test_is_done(self, key):
        return key in self.events and self.events[key].is_done

    def __getitem__(self, key):
        return self.events[key]
    
    def __contains__(self, key):
        return key in self.events
    
    def is_alive(self):
        return False if self.thread is None else self.thread.is_alive()

    def start(self) -> None:
        if self.verb: 
            self.log(f'{self.parent.ip} starting event stream in new thread...', color=colors.HEADER)

        assert not self.parent is None, 'parent can not be None'
        
        def eventupdate():
            with ws_sync_connect(f'ws://{self.parent.ip}:{self.parent.port}/wsevents') as ws:
                while True:
                    event_dc = json.loads(ws.recv())

                    event = ScuEvent(event_dc)
                    self.events[event.id] = event

                    if self.log_errors and event.level in ['ERR', 'ERROR', 'ALARM']:
                        msg, t = event.pprint(seperate_time=True)
                        self.log(msg, t=t, color=colors.FAIL )

                    if self.log_warnings and event.level in ['WARN', 'WARNING']:
                        msg, t = event.pprint(seperate_time=True)
                        a, b = t.replace('T', ' ').split('.') 
                        t = a + '.' + b[:2] + 'Zr'
                        self.log(msg, t=t, color=colors.WARNING )

                    for callback in self.callbacks_on_new:
                        callback(event)

                    if len(self.events) > self.dict_size:
                        k0 = next(iter(self.events.keys()))
                        self.events.pop(k0) 

                    # self.t_last_local = Time.now()
                    # self.tickcount += 1
                    # self.data = {k:v[0] for k, v in data['fields'].items()}
                    # # data['timestamp'] is the local NTP timestamp of the windows system, not the actual PTP time
                    # tptp = self.data.get('acu.time.external_ptp', None)
                    # self.t_last_remote = Time(tptp, format='mjd') if tptp else Time(data['timestamp'])


        self.thread = threading.Thread(target=eventupdate)
        self.thread.daemon = True
        self.thread.start()
        self.thread_id = self.thread.native_id
        if self.verb: 
            self.log(f'{self.parent.ip} --> eventstream started...', color=colors.OKGREEN)

        return self.thread
    

    def stop_by_exception(self):
        if self.thread and self.thread.is_alive():
            if self.thread_id is None:
                thread_id = next((id_ for id_, thread in threading._active.items() if thread is self.thread))
            else:
                thread_id = self.thread_id
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                raise Exception('Exception raise failure')


class DataStreamHandler():

    def __init__(self, parent, channels=None, limit_too_old_s = 1.0, verb=True, on_new_cbs=None) -> None:
        assert not parent is None, 'parent can not be None'
        self.parent = parent
        self.t_last_remote = None
        self.t_last_local = None

        self.data = {}
        self.channels = channels
        self.thread = None
        self.thread_id = None
        self.limit_too_old_s = limit_too_old_s
        self.dt_local_remote = None

        self.tickcount = 0

        self.do_test_on_call = True
        self.do_start_on_call = True

        self.callbacks_on_new = [] if on_new_cbs is None else on_new_cbs
        self.verb=verb

        name = str(self.parent.antenna_id) if self.parent.antenna_id else self.parent.address
        self._logger = getLogger(f"{name}.data_stream")

    def log(self, *args, **kwargs):
        if hasattr(self.parent, 'log'):
            t = kwargs.pop('t', None)
            if t is None:                    
                t = datetime.datetime.now(datetime.timezone.utc).isoformat()[:-4].replace('T', ' ') + 'Zl'
            return self.parent.log(*args, t=t, **kwargs)
        else:
            return self._logger(*args, **kwargs)
        
    def wait_for_start(self, timeout=10.):
        if self.verb: 
            self.log(f'{self.parent.ip} waiting for data stream to provide first data...', color=colors.HEADER)
        t = time.time()
        while (time.time() - t) < timeout and not self.tickcount:
            time.sleep(0.1)
        if self.verb: 
            self.log(f'{self.parent.ip} --> stream started OK', color=colors.OKGREEN)

    def __test(self):
        if not self.do_test_on_call:
            return
        
        if self.tickcount == 0 and self.do_start_on_call:
            self.start()
            self.wait_for_start()
        
        if self.dt_local_remote is None:
            self.dt_local_remote = (self.t_last_remote - self.t_last_local).to(u.s).value
            if abs(self.dt_local_remote) > 2:
                self.log(f'WARNING! local and remote clocks differ by more than 2 second! BE CAREFUL! remote={self.t_last_remote.iso} local={self.t_last_local.iso} --> dt={self.dt_local_remote:.2f}s', color=colors.WARNING)
            else:
                self.log(f'INFO: local and remote clocks difference is remote={self.t_last_remote.iso} local={self.t_last_local.iso} --> dt={self.dt_local_remote:.2f}s', color=colors.OKBLUE)

        assert self.thread and self.thread.is_alive(), 'no update thread running!'
        assert not self.t_last_local is None, 'not started or no data received yet (timestamp None)'


        dt = (Time.now() - self.t_last_local).to(u.s).value
        assert dt < self.limit_too_old_s, f'the data stored in the stream object is too old ({dt=} >= {self.limit_too_old_s})'
        assert self.data, 'not started or no data received yet (data empty)'

    def get_all(self, as_dict=False):
        return self.get_many(channels=None, as_dict=as_dict)
    
    def get_many(self, channels=None, as_dict=False):
        self.__test()
        keys = self.channels if channels is None else channels

        if as_dict:
            return {k:self.data[k] for k in keys}
        else:
            return [self.data[k] for k in keys]
        
    def getc(self, channels=None, as_dict=False):
        if isinstance(channels, str):
            return {channels: self[channels]} if as_dict else self[channels]
        else:
            return self.get_many(channels=channels, as_dict=as_dict)

    def __getitem__(self, key):
        self.__test()
        return self.data[key]
    
    def __contains__(self, key):
        self.__test()
        return key in self.data
    
    def is_alive(self):
        return False if self.thread is None else self.thread.is_alive()

    def start(self) -> None:
        if self.verb: 
            self.log(f'{self.parent.ip} starting data stream in new thread...', color=colors.HEADER)

        assert not self.parent is None, 'parent can not be None'
        if self.channels is None:
            self.channels = self.parent.get_channel_list()
        assert self.channels, 'channels must be iterable and not empty!'
        
        def statusupdate():
            
            with ws_sync_connect(f'ws://{self.parent.ip}:{self.parent.port}/wsstatus') as ws:
                ws.send(json.dumps(self.channels))
                while True:
                    data = json.loads(ws.recv())
                    self.t_last_local = Time.now()
                    self.tickcount += 1
                    self.data = {k:v[0] for k, v in data['fields'].items()}
                    # data['timestamp'] is the local NTP timestamp of the windows system, not the actual PTP time
                    tptp = self.data.get('acu.time.external_ptp', None)
                    self.t_last_remote = Time(tptp, format='mjd') if tptp else Time(data['timestamp'])
                    for callback in self.callbacks_on_new:
                        callback(self.t_last_remote, self.data)

        self.thread = threading.Thread(target=statusupdate)
        self.thread.daemon = True
        self.thread.start()
        self.thread_id = self.thread.native_id

        if self.verb: 
            self.log(f'{self.parent.ip} --> datastream started...', color=colors.OKGREEN)
        return self.thread
    

    def wait_next_data(self, dt_sleep = 0.05, timeout = 2):
        t_start_wait = time.time()
        old_id = id(self.data)

        while id(self.data) == old_id:
            self.parent.wait(dt_sleep, no_stout=True)
            t = time.time()
            dt = t - t_start_wait
            assert dt < timeout, f'timeput while waiting for new data. {id(self.data)=}, {self.t_last_remote=}, {self.t_last_local=}'
        return self.data


    def stop_by_exception(self):
        if self.thread and self.thread.is_alive():
            if self.thread_id is None:
                thread_id = next((id_ for id_, thread in threading._active.items() if thread is self.thread))
            else:
                thread_id = self.thread_id
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                raise Exception('Exception raise failure')



"""
████████ ██████   █████   ██████ ██   ██ 
   ██    ██   ██ ██   ██ ██      ██  ██  
   ██    ██████  ███████ ██      █████   
   ██    ██   ██ ██   ██ ██      ██  ██  
   ██    ██   ██ ██   ██  ██████ ██   ██ 
"""

class TrackHandler(object):
    
    @staticmethod
    def run_in_background(*args, **kwargs):
        def runner(*args, **kwargs):
            with TrackHandler(*args, **kwargs) as track:
                track.log('Started running a track table in background...', color=colors.OKBLUE)
            track.log('Finished running a track table in background...', color=colors.OKGREEN)

        thread = threading.Thread(target=runner, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
    
    def __init__(self, scu, t, az, el, activate_logging, config_name, wait_start=True, verb=False, wait_for_end_pos=True, wait_after_stopping_logger_sec=0):
        
        # if its a astropy time object get the mjd format from it to pass to the SCU
        if isinstance(t, Time): 
            t = t.mjd

        self.scu = scu
        self.args = (t, az, el, activate_logging, config_name)
        self.t_end = Time(t[-1], format='mjd')
        self.verb=verb
        self.wait_start = wait_start
        self.wait_for_end_pos = wait_for_end_pos
        self.wait_after_stopping_logger_sec = wait_after_stopping_logger_sec
        self.logging_active = False
        self.session_id = None
        self._last_session_old = None
        self.t_start_act = None
        self.t_end_act = None

    def log(self, *args, **kwargs):
        if hasattr(self.scu, 'log'):
            return self.scu.log(*args, **kwargs)
        else:
            return log(*args, **kwargs)
        
    def get_t_remaining(self):
        """estimate of remaining time in tracking table (in seconds)"""
        return (self.t_end - self.scu.t_internal).to(u.s).value
    
    @property
    def session(self):
        return self.get_session_df()
    
    def get_session_as_df(self, interval_ms=100, do_sanity_test=True):
        return self.get_session_df(interval_ms=interval_ms, do_sanity_test=do_sanity_test)
    
    def get_session_df(self, interval_ms=100, do_sanity_test=True):
        scu = self.scu
        assert self.logging_active, 'can not get data, since no logging was active!'
        assert not self.session_id is None, 'no session ID marked for this track!'
        df = scu.get_session_as_df(interval_ms=interval_ms, session=self.session_id)

        if do_sanity_test:
            def _index_dt(dt):
                try:
                    return dt.to_pydatetime()
                except Exception as err:
                    if "has no attribute 'to_pydatetime'" in str(err):
                        return dt.to_datetime()
                    else:
                        raise

            t_start_df = _index_dt(df.index.min())
            t_end_df = _index_dt(df.index.max())
            dt_start = abs((t_start_df - self.t_start_act).total_seconds())
            dt_end = abs((t_end_df - self.t_end_act).total_seconds())

            tol_s = 2 # seconds
            if dt_start > 2:
                warnings.warn(f'start time of acu logging table and actual start time differ by more than {tol_s} seconds (t_start_session={make_zulustr(t_start_df)} vs t_start_act={make_zulustr(self.t_start_act)} |=> dt={dt_start:.2f}sec)')
            if dt_end > 2:
                warnings.warn(f'end time of acu logging table and actual end time differ by more than {tol_s} seconds (t_end_session={make_zulustr(t_end_df)} vs t_end_act={make_zulustr(self.t_end_act)} |=> dt={dt_end:.2f}sec)')

        return df

    def start(self):

        scu = self.scu
        self.log('Entering a tracking table t_internal = {} AZEL_now: {:5.3f}°, {:5.3f}° ...'.format(scu.t_internal.iso, *scu.azel), color=colors.OKBLUE)

        t, az, el, activate_logging, config_name = self.args

        scu.stop_program_track(not self.verb)
        if self.wait_after_stopping_logger_sec > 0:
            scu.wait_duration(5)

        t_start, t_end = Time(t[0], format='mjd'), Time(t[-1], format='mjd')
        if activate_logging and scu.logger_state() != 'STOPPED':
            self.log('WARNING, logger already recording - attempting to stop and start a fresh logger...', color=colors.WARNING)
            scu.stop_logger()  
            if self.wait_after_stopping_logger_sec > 0:
                scu.wait_duration(2, not self.verb)
        
        self.log(f'Uploading tracking table...', color=colors.OKBLUE)
        dt_wait = scu.upload_track_table(t, az, el, wait_for_start=False)
        t_now = scu.t_internal
        if self.wait_start and (t_start - 3*u.s) > t_now:
            self.log(f'Waiting for track start time. dt={(t_start - t_now).to(u.s) - 3*u.s}', color=colors.OKBLUE)
            scu.wait_until(t_start - 3*u.s, not self.verb)
        
        self.t_start_act = get_utcnow()

        if activate_logging:
            self._last_session_old = scu.last_session()
            self.logging_active = True
            # start logging for my testrun
            scu.start_logger(config_name=config_name, stop_if_need=False)
        
        if self.wait_start and (t_start - 3*u.s) > scu.t_internal:
            scu.wait_until(t_start, not self.verb)
        self.log(f'Waiting for state to be either TRACK or SLEW...', color=colors.OKBLUE)
        scu.wait_state('acu.general_management_and_controller.state', ['TRACK', "SLEW"], timeout=20, query_delay=.25, operator = 'IN')
        self.log(f'Entering a tracking table..DONE', color=colors.OKGREEN)
        return self


    def finish(self):
        self.log(f'Exiting a tracking table..', color=colors.OKBLUE)
        scu = self.scu
        t, az, el, activate_logging, config_name = self.args
        t_start, t_end = Time(t[0], format='mjd'), Time(t[-1], format='mjd')
        scu.wait_until(t_end, not self.verb)
        if self.wait_for_end_pos:
            scu.wait_for_pos('az', az[-1], tolerance=0.05, timeout=20)
            scu.wait_for_pos('el', el[-1], tolerance=0.05, timeout=20)
        self.t_end_act = get_utcnow()

        if scu.logger_state() != 'STOPPED':
            scu.stop_logger()
        scu.stop_program_track()
        scu.wait_duration(5, not self.verb)
        if self.logging_active:
            self.session_id = scu.last_session()
            assert self.session_id != self._last_session_old, f'The logger session id did not increment after this tracking table! It seems the log is not ready or logging did not work! {self.session_id=} {self._last_session_old=}' 
        self.log(f'Exiting a tracking table..DONE', color=colors.OKGREEN)

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.log(f'Exiting a tracking table..', color=colors.OKBLUE)
        self.finish()
        self.log(f'Exiting a tracking table..DONE', color=colors.OKGREEN)

###################################################################################################
###################################################################################################
###################################################################################################

# ██████  ███████  ██████  ██████  ██████   █████  ████████  ██████  ██████  ███████ 
# ██   ██ ██      ██      ██    ██ ██   ██ ██   ██    ██    ██    ██ ██   ██ ██      
# ██   ██ █████   ██      ██    ██ ██████  ███████    ██    ██    ██ ██████  ███████ 
# ██   ██ ██      ██      ██    ██ ██   ██ ██   ██    ██    ██    ██ ██   ██      ██ 
# ██████  ███████  ██████  ██████  ██   ██ ██   ██    ██     ██████  ██   ██ ███████ 
                                                                                   
                                                                                   




def event_start_before(f):
    def wrapper(self, *args, **kwargs):

        if self.wait_done_by_uuid and (self.event_streamer is None or not self.event_streamer.is_alive()):
            self.log(f'Starting event stream because method with name "{f.__name__}"  requested it', colors.HEADER)
            self.start_event_stream()

        return f(self, *args, **kwargs)
    return wrapper

def event_start_before_wait_done_after(f):
    def wrapper(self, *args, **kwargs):

        if self.wait_done_by_uuid and (self.event_streamer is None or not self.event_streamer.is_alive()):
            self.log(f'Starting event stream because method with name "{f.__name__}"  requested it', color=colors.HEADER)
            self.start_event_stream()

        uuid = f(self, *args, **kwargs)
        valid_uuid = isinstance(uuid, str) and uuid
        if self.wait_done_by_uuid and valid_uuid:
            self.wait_uuid_done(uuid, f.__name__)
        elif self.wait_done_by_uuid and not valid_uuid:
            self.log(f"wait by UUID requested for {f.__name__}, but API call did not return a valid uuid! {type(uuid)=} | {uuid=}", color=colors.WARNING)

        return uuid
    return wrapper


def event_wait_done_after(f):
    def wrapper(self, *args, **kwargs):

        uuid = f(self, *args, **kwargs)
        valid_uuid = isinstance(uuid, str) and uuid
        if self.wait_done_by_uuid and valid_uuid:
            self.wait_uuid_done(uuid, f.__name__)
        elif self.wait_done_by_uuid and not valid_uuid:
            self.log(f"wait by UUID requested for {f.__name__}, but API call did not return a valid uuid! {type(uuid)=} | {uuid=}", color=colors.WARNING)

        return uuid
    return wrapper
    
def aliased(klass):
    '''
    Decorator to be used in combination with `@alias` decorator.
    Classes decorated with @aliased will have their aliased methods
    (via @alias) actually aliased.
    '''
    methods = klass.__dict__.copy()
    for name, method in methods.items():
        if hasattr(method, '_aliases'):
            # add aliases but don't override attributes of 'klass'
            try:
                for alias in method._aliases - set(methods):
                    setattr(klass, alias, method)
            except TypeError: pass
    return klass


class alias(object):
    '''
    Decorator for aliasing method names.
    Only works within classes decorated with '@aliased'
    ''' 
    def __init__(self, *aliases):
        self.aliases = set(aliases)
    
    def __call__(self, f):
        f._aliases = self.aliases
        return f



def deprecated(reason):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated: {reason}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

"""
 ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄         ▄ 
▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░▌       ▐░▌
▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀▀▀ ▐░▌       ▐░▌
▐░▌          ▐░▌          ▐░▌       ▐░▌
▐░█▄▄▄▄▄▄▄▄▄ ▐░▌          ▐░▌       ▐░▌
▐░░░░░░░░░░░▌▐░▌          ▐░▌       ▐░▌
 ▀▀▀▀▀▀▀▀▀█░▌▐░▌          ▐░▌       ▐░▌
          ▐░▌▐░▌          ▐░▌       ▐░▌
 ▄▄▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄▄▄ ▐░█▄▄▄▄▄▄▄█░▌
▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌
 ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀ 
"""

@aliased
class scu():
    """SCU Interface Object

    This class provides an interface to the MeerKAT Extension Telescopes' dish structure controllers
    It does so by connecting to the Antenna Control Unit (ACU) via the HTTP REST API and websockets 
    of the Science Computation Unit (SCU) both developed by OHB Digital Connect GmbH. 
    It's designed for use with the SKA-MPI Demonstrator Radio Telescope in South Africa and the MeerKAT
    Extension Radio Telescopes.
    """
    
    def __init__(self, address='', ip='', port='8080', antenna_id='', 
                 debug=False, lims_az=(-270.0, 270, 3.0), lims_el=(15, 90, 1.35), 
                 dish_type='mke', post_put_delay=0.2, use_socket=True, 
                 influx_token='', kwargs_requests = None, 
                 wait_done_by_uuid=True, start_streams_on_construct=False, 
                 timeout_wait_uuid=900, 
                 antenna_dc=None, readonly=False, **kwargs):
        """Initializes an SCU interface object for communication with an Antenna Control Unit (ACU).

        Args:
            address (str, optional): Combined IP address and port of the ACU (e.g., "localhost:8080"). Defaults to ''.
            ip (str, optional): IP address of the ACU. Defaults to 'localhost'. This argument takes precedence over `address`.
            port (str, optional): Port number of the ACU. Defaults to '8080'.
            antenna_id (str, optional): Any ID/name you want to give to this dish object. Defaults to '')
            debug (bool, optional): Enables debug logging. Defaults to False.
            lims_az (tuple, optional): Limits for the azimuth axis (angle_min, angle_max, speed_max). Defaults to (-270.0, 270.0, 3.0).
            lims_el (tuple, optional): Limits for the elevation axis (angle_min, angle_max, speed_max). Defaults to (15.0, 90.0, 1.35).
            dish_type (str): Type of the dish antenna (e.g., "mke"). Lowercased automatically.
            post_put_delay (float, optional): Delay (in seconds) after any POST or PUT commands. Defaults to 0.2.
            use_socket (bool, optional): Enables asynchronous streaming of events and data in the background using websockets. Defaults to True.
            influx_token (str, optional): Token for accessing an InfluxDB instance. Defaults to ''.
            kwargs_requests (dict, optional): Keyword arguments to be passed to requests library calls. Defaults to an empty dictionary.
            wait_done_by_uuid (bool, optional): Enables waiting for command completion by waiting for an event marking the command as completed. Defaults to True.
            start_streams_on_construct (bool, optional): Starts the data and event streams on creation (requires websockets). Defaults to False.
            antenna_dc (dict, optional): stores any dict for this dish/antenna (typically queried from an API) holding its information
            readonly (bool, optional): Set to true to disallow this object to send any commands which could change something on server. Defaults to False.            
            **kwargs (optional): Additional keyword arguments passed through to the object.

        Raises:
            AssertionError: If invalid arguments are provided (e.g., setting both `address` and `ip`).

        Notes:
            Use `address` for a combined IP and port specification.
            `ip` takes precedence over `address` if both are provided.
            Refer to the class documentation for detailed information on functionalities.
        """
        
        if ip and not address:
            address = ip
            ip = ''
            
        if address:
            if isinstance(ip, int) or ip.isdigit():
                port, ip = ip, ''

            assert not ip, 'can not set address and ip simultanious'

            if 'localhost' in address:
                matches = re.findall(r'(localhost):?([0-9]+)?', address)
            else:
                matches = re.findall(r'([0-9\.]+):?([0-9]+)?', address)

            assert len(matches) > 0, 'given antenna addess does not match any known IP or address pattern'
            matches = matches[0]
            if len(matches) == 1:
                ip, port = matches[0], port
            elif len(matches) == 2:
                ip = matches[0]
                port = matches[1] if matches[1] else port

        self.influx_token = influx_token
        self.ip = ip
        self.port = str(port)
        self.debug = debug

        self.call_log = {}

        self.t_start = Time.now()
        if dish_type.lower() == 'skampi' and lims_el[0] < 17:
            lims_el = (17, lims_el[1], lims_el[2])

        self.lims_az = lims_az
        self.lims_el = lims_el
        
        self.bands_possible = {k:v for k, v in bands_dc.items() if k.lower().startswith('band')}
        self.post_put_delay = post_put_delay
        self.kwargs_requests = kwargs_requests if kwargs_requests else {}

        self.wait_done_by_uuid = wait_done_by_uuid
        self.timeout_wait_uuid = timeout_wait_uuid
        self.wait_history = []

        self.dish_type = dish_type.lower()
        self.dish_type_is_verified = False
        self.antenna_id = antenna_id
        self.antenna_dc = antenna_dc

        self.is_readonly = readonly

        self.use_socket = use_socket
        self.data_streamer = DataStreamHandler(self)
        self.event_streamer = None

        self.callback_on_logging = {}   # callbacks to call when the logging function is called

        self._setup(start_streams_on_construct)


    def _setup(self, start_streams_on_construct):
        
        if not self.use_socket:
            assert not self.wait_done_by_uuid, 'can not wait by UUID if no websocket is requested!'

        if start_streams_on_construct and self.use_socket and not self.dish_type_is_verified:
            self.determine_dish_type()
            
        
        if (self.wait_done_by_uuid and self.use_socket) and start_streams_on_construct:
            self.start_event_stream()

        if self.use_socket and start_streams_on_construct:
            self.data_streamer.start()


    def __str__(self):
        antenna_id = f'"{self.antenna_id}"' if self.antenna_id else ''        
        return f'scu_{self.dish_type} {antenna_id} @{self.address}'

    def __repr__(self):
        antenna_id = f' with antenna_id: "{self.antenna_id}"' if self.antenna_id else ''        
        is_verified = '(verified)' if self.dish_type_is_verified else '(unverified)'
        is_readonly = ' (readonly)' if self.is_readonly else ''
        return f'scu object{antenna_id} @{self.address}, dish_type: "{self.dish_type}" {is_verified} {is_readonly}'
    
    def __getitem__(self, key):
        return self.getc(key)
    

###################################################################################################
###################################################################################################
###################################################################################################
 
# ██████  ██████   ██████  ██████  ███████ 
# ██   ██ ██   ██ ██    ██ ██   ██ ██      
# ██████  ██████  ██    ██ ██████  ███████ 
# ██      ██   ██ ██    ██ ██           ██ 
# ██      ██   ██  ██████  ██      ███████ 

    @property
    def callbacks_on_new_events(self):
        """the list of callbacks to be called on receiving a new event. The callback signature is
        def my_callback(event_i):
            pass
        """
        if self.event_streamer is None:
            self.event_streamer = EventStreamHandler(self)
            warnings.warn('Event stream is not running, but you accessed "callbacks_on_new_events" need to call start_event_stream() to actually start the event stream.')
        return self.event_streamer.callbacks_on_new
    
    @property
    def callbacks_on_new_data(self):
        """the list of callbacks to be called on receiving a data update. The callback signature is
        def my_callback(timestamp_astropy, channel_data_as_dict):
            pass
        """
        return self.data_streamer.callbacks_on_new
    
    @property
    def address(self):
        """address of the dish as: http://IP:PORT"""
        return f'http://{self.ip}:{self.port}'
    
    @property
    def version_acu(self):
        if self.dish_type == 'mke':
            chans = ['acu.general_management_and_controller.ds_software_version_major', 
                    'acu.general_management_and_controller.ds_software_version_minor',
                    'acu.general_management_and_controller.ds_software_version_fix']
            return '.'.join([str(s) for s in self.getc(chans)])
        else:
            return str(self.getc('acu.general_management_and_controller.ds_software_version'))

    @property
    def is_simulator(self):
        """indicates, whether or not this object is a simulator a real antenna

        Returns:
            True if it is a simulator
        """
        return hasattr(self, 'telescope')

    @property
    def t_internal(self):
        """internal telescope time as astropy Time object based on MJD format

        Returns:
            astropy.time.Time: the ACU internal time now
        """
        value = self.getc(f'acu.time.internal_time')
        return Time(value, format='mjd')
        # return Time.now()

    @property
    def spem_keys(self):
        
        if self.dish_type == 'skampi':
            return ["p1_encoder_offset_azimuth", "p2_collimation",
                "p3_non_orthog_nasmyth", "p4_e_w_azimuth_tilt",
                "p5_n_s_azimuth_tilt", "p6_declination_error",
                "p7_encoder_offset_elevation", "p8_cos_terx_gray_nasmyth",
                "p9_sin_term_gray_nasmyth"]

        elif self.dish_type == 'mke':
            return [
                "p1_azimuth_encoder_offset",
                "p3_non_orthog_az_el",
                "p4_collimination_az",
                "p5_n_s_azimuth_tilt",
                "p6_e_w_azimuth_tilt",
                "p7_elevation_encoder_offset",
                "p8_grav_vertical_shift_el_az",
                "p9_linear_scale_factor_el",
                "p11_grav_horizontal_shift_el_az",
                "p12_linear_scale_factor_az",
                "p13_az_frequency_cos_part",
                "p14_az_frequency_sin_part",
                "p15_twice_el_frequency_cos_part",
                "p16_twice_az_frequency_sin_part",
                "p17_twice_az_frequency_cos_part",
                "p18_twice_az_frequency_sin_part",
                ]
        else:
            raise ValueError(f'{self.dish_type} is an unknon dish type for SPEM models, only skampi and mke are allowed')
    
    @property
    def spem_param_name_map(self):
        param_name_map = [re.match(r"^[Pp][0-9]+", k) for k in self.spem_keys]
        param_name_map = {m.group().upper():k for m, k in zip(param_name_map, self.spem_keys)}
        return param_name_map
    
    @property
    def stow_pos(self):
        az = 0.0 if self.dish_type == 'mke' else -90.0
        el = 89.75
        return az, el

    @property
    def band_in_focus(self):
        return self.get_band_in_focus(False)

    def get_band_in_focus(self, as_name=False):
        bint_str = self.getc('acu.general_management_and_controller.feed_indexer_pos')
        return bands_dc_inv.get(int(bint_str), f'UNKNOWN ("{bint_str}")') if as_name else bint_str
    
    @property
    def command_auth(self):
        """shorthand for get_act_authority_value(as_str=True)"""
        return self.get_act_authority_value(as_str=True)

    @property
    def azel(self):
        return self.get_azel()
    
    @property
    def state(self):
        return self.get_state()
    
    @property
    def azel_setp(self):
        return tuple(self.getc(['acu.azimuth.p_set', 'acu.elevation.p_set']))
    
    @property
    def azel_shape(self):
        return tuple(self.getc(['acu.azimuth.p_shape', 'acu.elevation.p_shape']))

    @property
    def acu_eventlog(self):
        return self.get_events(as_pandas=True)
    
    @property
    def events(self):
        return self.get_events(as_pandas=True)

    @property
    def readonly(self):
        """shorthand for is_readonly"""
        return self.is_readonly
    
    def getc(self, key=None, as_dict=False, allow_concurrent=False):
        """get one or many channel values. key(s) must be string or list of strings

        Args:
            key (string or iterable[str]): the channel names to get
            allow_concurrent (bool): set to True to allow concurrent calling via aiohttp. Default=False

        Returns:
            dict, list or immuteable: type depending on the input.
        """
        try:
            if self.use_socket:
                return self.data_streamer.getc(key, as_dict=as_dict)
        except Exception as err:
            self.log(f'error while getting data from socket stream... falling back to HTTP api. {err=}', color=colors.WARNING)

        if key is None and self.dish_type == 'skampi':
            keys = self.get_channel_list()
            return dict(keys, self._get_device_status_value(keys, allow_concurrent))
        elif key is None:
            return dict(self.get_channel_list(with_values=True, with_timestamps=False))
        elif not isinstance(key, str) and hasattr(key, '__len__') and self.dish_type != 'skampi':
            allchans = dict(self.get_channel_list(with_values=True, with_timestamps=False))
            if as_dict:
                return {k:allchans[k] for k in key}
            else:
                return [allchans[k] for k in key]
        else:
            res = self._get_device_status_value(key, allow_concurrent)
            if as_dict and isinstance(key, list):
                return dict(zip(key, res))
            elif as_dict:
                return {key: res}
            else:
                return res
            
###################################################################################################
###################################################################################################
###################################################################################################
    
# ██ ███    ██ ████████ ███████ ██████  ███    ██  █████  ██          ███████ ██    ██ ███    ██ ███████ 
# ██ ████   ██    ██    ██      ██   ██ ████   ██ ██   ██ ██          ██      ██    ██ ████   ██ ██      
# ██ ██ ██  ██    ██    █████   ██████  ██ ██  ██ ███████ ██          █████   ██    ██ ██ ██  ██ ███████ 
# ██ ██  ██ ██    ██    ██      ██   ██ ██  ██ ██ ██   ██ ██          ██      ██    ██ ██  ██ ██      ██ 
# ██ ██   ████    ██    ███████ ██   ██ ██   ████ ██   ██ ███████     ██       ██████  ██   ████ ███████ 
                                                                                                       
    def log(self, msg, *args, t = None, name=None, color=colors.BLACK, **kwargs):
        if name is None:
            name = self.antenna_id if self.antenna_id else self.address

        # if t is None and self.use_socket and self.data_streamer and self.data_streamer.is_alive(): # not costly to get current time!
        #     t = self.t_internal.iso[:-1] + 'Zr'

        return logfun(msg, *args, t=t, color=color, name=name, callbacks_logging=self.callback_on_logging, **kwargs)

    def start_event_stream(self):
        self.event_streamer = EventStreamHandler(self)
        self.event_streamer.start()
        #self.event_streamer.wait_for_start()

    def keys(self):
        """get all channel names as list of strings"""
        if self.use_socket:
            return self.data_streamer.data.keys()
        else:
            return self.get_channel_list(with_values=False, with_timestamps=False)
        
    def clear_all_callbacks(self):
        self.callbacks_on_new_events.clear()
        self.callbacks_on_new_data.clear()
        self.callback_on_logging.clear()

        
    def activate_logging_mattermost(self, url_qry = 'http://10.98.76.45:8990/logurl', key='mattermost'):
        
        mattermost_url = requests.get(f'{url_qry}').json().get('url')
        def log_mattermost(name, msg, color=colors.BLACK, t=''):
            return _cb_log_send_mattermost(name, msg, color, t=t, mattermost_url=mattermost_url)

        self.callback_on_logging[key] = log_mattermost
        return True
        
    def deactivate_logging_mattermost(self, key='mattermost'):
        return self.callback_on_logging.pop(key, None)


    def _limit_motion(self, az_pos, el_pos, az_speed=None, el_speed=None):
        def limit(name, x, xmin, xmax):
            if x is None:
                return x
            vlim = max(min(x, xmax), xmin)
            if vlim != x:
                txt = f"WARNING: variable {name} exceeds its allowed limit and was set to {vlim} from {x}"
                self.log(txt)
                warnings.warn(txt)
            return float(vlim)
        
        angle_min, angle_max, speed_max = self.lims_az
        az_pos = limit('az_pos', az_pos, angle_min, angle_max)
        az_speed = limit('az_speed', az_speed, 1e-10, speed_max)

        angle_min, angle_max, speed_max = self.lims_el
        el_pos = limit('el_pos', el_pos, angle_min, angle_max)
        el_speed = limit('el_speed', el_speed, 1e-10, speed_max)
        return az_pos, el_pos, az_speed, el_speed

###################################################################################################
###################################################################################################
###################################################################################################

# ██   ██ ████████ ████████ ██████       ██████  ███████ ████████     ██████  ██    ██ ████████ 
# ██   ██    ██       ██    ██   ██     ██       ██         ██        ██   ██ ██    ██    ██    
# ███████    ██       ██    ██████      ██   ███ █████      ██        ██████  ██    ██    ██    
# ██   ██    ██       ██    ██          ██    ██ ██         ██        ██      ██    ██    ██    
# ██   ██    ██       ██    ██           ██████  ███████    ██        ██       ██████     ██    
                                                                                              
                                                                                              


    #Direct SCU webapi functions based on urllib PUT/GET
    def _feedback(self, r, get_uuid=True):
        if self.debug == True:
            self.log('***Feedback:' +  str(r.request.url) + ' ' + str(r.request.body))
            self.log(f'{r.status_code}: {r.reason}')
            self.log("***Text returned:")
            self.log(r.text)
        elif r.status_code != 200:
            self.log('***Feedback:' +  str(r.request.url) + ' ' + str(r.request.body), color=colors.WARNING)
            self.log(f'{r.status_code}: {r.reason}', color=colors.WARNING)
            self.log("***Text returned:", color=colors.WARNING)
            self.log(r.text, color=colors.WARNING)
            #self.log(r.reason, r.status_code)
            #self.log()

        uuid = ''
        if get_uuid:
            try:
                if (not (r.status_code != 200)) and r.request.method == 'PUT':
                    dc = r.json()
                    if isinstance(dc, dict):
                        uuid = dc.get('uuid', None)
                    self.uuid_last = uuid

            except Exception as err:
                uuid = ''
                self.log(f'ERROR in getting UUID: {r} | {r.request.url} | {err}', color=colors.FAIL)
                if self.debug:
                    print(r.text)
                    traceback.print_exception(err)

            return uuid
        else:
            return r
    
    def wait_uuid_done(self, uuid:str=None, funname='unknown_command', timeout = None, dt_poll=0.1):

        timeout = self.timeout_wait_uuid if not timeout else timeout

        if uuid is None:
            uuid = self.uuid_last

        if not self.event_streamer or not self.event_streamer.is_alive():
            self.start_event_stream()
        
        if self.debug:
            self.log(f'wait_uuid_done | waiting for {uuid=}')

        t_start_wait = time.time()
        while not self.event_streamer.test_is_done(uuid):
            dt = (time.time() - t_start_wait)
            if dt > self.timeout_wait_uuid:
                raise TimeoutError(f'waiting for command "{funname}" with {uuid=} to complete timed out after {dt:.1f} sec. (limit: {self.timeout_wait_uuid:.1f} sec)')
            self.wait_duration(dt_poll, no_stout=True )
        
        dt = (time.time() - t_start_wait)
        if len(self.wait_history) > 100:
            self.wait_history.pop()
        self.wait_history.append((funname, uuid, time.time(), dt))
        
    #	def scu_get(device, params = {}, r_ip = self.ip, r_port = port):
    def scu_get(self, device, params = {}):
        '''This is a generic GET command into http: scu port + folder 
        with params=payload'''
        URL = 'http://' + self.ip + ':' + self.port + device
        if device != '/devices/statusValue':
            self.call_log[datetime.datetime.now(datetime.timezone.utc)] = 'GET | ' + device

        if self.debug == True:
            self.log(f'request.get(**{dict(url = URL, params = params)}):')

        r = requests.get(url = URL, params = params, **self.kwargs_requests)
        uuid = self._feedback(r)
        r.raise_for_status()
        if r.status_code != 200:
            self.log(f'Statuscode != 200. Returnded: {r.status_code}: {r.reason}', color=colors.WARNING)

        return r

    async def scu_get_async(self, devices, params):
        '''This is a generic GET command into http: scu port + folder 
        with params=payload fur multiple devices and params at the same time'''
        url = self.address
        try:
            aiohttp.__version__
        except Exception as err:
            try:
                import aiohttp
                has_aio = True
            except ModuleNotFoundError as err:
                warnings.warn(f'aiohttp was not found. Falling back to synchronous api calling. error details: {err=}')
                has_aio = False
            
        if has_aio:
            async with aiohttp.ClientSession() as session:                
                async def get(device, params):
                    async with session.get(url + device, params=params) as r:
                        txt = await r.text()
                        r.raise_for_status()
                        return json.loads(txt)
                        
                return await asyncio.gather(*(get(d, p) for d, p in zip(devices, params)))
        else:
            return [self.scu_get(d, p).json() for d, p in zip(devices, params)]


    def scu_get_concurrent(self, devices, params):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.scu_get_async(devices, params))
            
        
    def scu_put(self, device, payload = {}, params = {}, data='', get_uuid=True):
        '''This is a generic PUT command into http: scu port + folder 
        with json=payload'''
        URL = 'http://' + self.ip + ':' + self.port + device

        assert not self.is_readonly, f'FORBIDDEN: stopped a PUT command to "{URL}" because this object is readonly!'
            
        self.call_log[datetime.datetime.now(datetime.timezone.utc)] = 'PUT | ' + device
        if self.debug == True:
            self.log(f'request.put(**{dict(url = URL, json = payload, params = params, data = data)}):')

        r = requests.put(url = URL, json = payload, params = params, data = data, **self.kwargs_requests)
        uuid = self._feedback(r, get_uuid=get_uuid)
        r.raise_for_status()
        if r.status_code != 200:
            self.log(f'Statuscode != 200. Returnded: {r.status_code}: {r.reason}', color=colors.WARNING)

        if self.post_put_delay > 0:
            self.wait_duration(self.post_put_delay, no_stout=True)

        return uuid

    def scu_delete(self, device, payload = {}, params = {}):
        '''This is a generic DELETE command into http: scu port + folder 
        with params=payload'''
        URL = 'http://' + self.ip + ':' + self.port + device
        
        assert not self.is_readonly, f'FORBIDDEN: stopped a DELETE command to "{URL}" because this object is readonly!'

        self.call_log[datetime.datetime.now(datetime.timezone.utc)] = 'DEL | ' + device
        if self.debug == True:
            self.log(f'request.delete(**{dict(url = URL, json = payload, params = params)}):')

        r = requests.delete(url = URL, json = payload, params = params, **self.kwargs_requests)
        uuid = self._feedback(r)
        r.raise_for_status()

        if r.status_code != 200:
            self.log(f'Statuscode != 200. Returnded: {r.status_code}: {r.reason}', color=colors.WARNING)
        
        if self.post_put_delay > 0:
            self.wait_duration(self.post_put_delay, no_stout=True)

        return uuid

###################################################################################################
###################################################################################################
###################################################################################################
    
#  ██████  ███████ ████████ ████████ ███████ ██████      ███████ ██    ██ ███    ██ ███████ 
# ██       ██         ██       ██    ██      ██   ██     ██      ██    ██ ████   ██ ██      
# ██   ███ █████      ██       ██    █████   ██████      █████   ██    ██ ██ ██  ██ ███████ 
# ██    ██ ██         ██       ██    ██      ██   ██     ██      ██    ██ ██  ██ ██      ██ 
#  ██████  ███████    ██       ██    ███████ ██   ██     ██       ██████  ██   ████ ███████ 
                                                                                          
                                                                                          


    def ping(self, timeout=10):
        URL = 'http://' + self.ip + ':' + self.port + '/devices/'
        kwargs = {**self.kwargs_requests, **dict(timeout=timeout)}
        r = requests.get(url = URL, **kwargs)
        return r.status_code == 200
    

    def determine_dish_type(self):
        """will set and return the dish type by checking a status value 

        Returns:
            string: either 'skampi' or 'mke'
        """
        chans = self.scu_get("/devices/statusPaths").json()
        if 'acu.general_management_and_controller.ds_software_version' in chans:
            self.dish_type = 'skampi'
            if self.lims_el[0] < 17:
                self.lims_el = (17, self.lims_el[1], self.lims_el[2])
        else:
            self.dish_type == 'mke'
        
        self.dish_type_is_verified = True
        return self.dish_type
            

    def get_warnings(self):

        fun = lambda k: ('warn' in k.lower()) and 'not_used' not in k and 'limit' not in k and 'stowpins' not in k
        chans = [k for k in self.keys() if fun(k)]

        return {k:v for k, v in zip(chans, self.getc(chans, as_dict=False)) if v}
    
    def get_errors(self, warnings=True):
        if warnings:
            fun = lambda k: ('warn' in k.lower() or 'err' in k.lower()) and 'not_used' not in k and 'limit' not in k and 'stowpins' not in k
            chans = [k for k in self.keys() if fun(k)]
        else:
            chans =  [k for k in self.keys() if 'err' in k.lower()]

        return {k:v for k, v in zip(chans, self.getc(chans, as_dict=False)) if v}

        # if warnings:
        #     fun = lambda k, v: ('warn' in k.lower() or 'err' in k.lower()) and v and 'not_used' not in k and 'limit' not in k and 'stowpins' not in k and v
        #     return {k:v for k, v in self.getc(as_dict=True).items() if fun(k, v)}

        # return {k:v for k, v in self.getc(as_dict=True).items() if 'err' in k.lower() and v}
    
    def get_all_channels(self):
        return self.get_channel_list(with_values=True, with_timestamps=True)
    
    
    def get_events(self, nlast=1000, as_pandas=True):
        records = self.scu_get('/events/lastn', params=dict(n=nlast)).json()
        if as_pandas:
            df = pd.DataFrame(records)
            df['time'] = pd.to_datetime(df['timestamp'], utc=True)
            df.set_index('time', inplace=True, drop=True)
            return df
        else:
            return records

    
    def get_events_range(self, t_start, t_end, as_pandas=True):
        """
        Retrieves dish events within a specified time range from the SCU.

        Args:
            t_start (str): Start time in Zulu format (e.g., "2024-10-24T15:00:00.000Z").
            t_end (str): End time in Zulu format (e.g., "2024-10-24T15:00:00.000Z").
            as_pandas (bool, optional): Whether to return the events as a Pandas DataFrame. Defaults to True.

        Returns:
            list or pandas.DataFrame:
                If `as_pandas` is False, returns a list of event records.
                If `as_pandas` is True and there are events, returns a Pandas DataFrame with the events, indexed by timestamp.
                If `as_pandas` is True and there are no events, returns an empty Pandas DataFrame.

        Raises:
            AssertionError: If `t_start` or `t_end` is not a valid Zulu time string or if `t_start` is greater than `t_end`.

        Warnings:
            Warns if the number of retrieved events is exactly 1000, indicating potential truncation of data.
        """

        assert isinstance(t_start, str) and parse_zulutime(t_start), f'ERROR in t_start. Expected zulu string like "2024-10-24T15:00:00.000Z" but got {type(t_start)=} {t_start=}'
        assert isinstance(t_end, str) and parse_zulutime(t_end), f'ERROR in t_end. Expected zulu string like "2024-10-24T15:00:00.000Z" but got {type(t_end)=} {t_end=}'

        assert t_end > t_start, f'ERROR: t_start must be smaller than t_end, but got: {t_start=}, {t_end=}'

        records = self.scu_get('/events/events', params=dict(startTime=t_start, endTime=t_end)).json()
        if len(records) == 1000:
            warnings.warn('length of records is exactly 1000 this is the limit for queries in a given range. It is very likely, that your data is truncated. Either reduce the range or perform multiple calls with sub ranges.')

        if as_pandas and records:
            df = pd.DataFrame(records)
            df['time'] = pd.to_datetime(df['timestamp'], utc=True)
            df.set_index('time', inplace=True, drop=True)
            return df
        elif as_pandas and not records:
            return pd.DataFrame([])
        else:
            return records
    
    @alias('show_events')
    def events_show(self, t_start=None, t_end=None, nlast=1000, ret_df=False):
            
        assert t_start and t_end or (not t_start and not t_end), f'If t_start is given t_end must be given as well and vice versa, but given was {t_start=} {t_end=}'

        if t_start:
            events_dc = self.get_events_range(t_start, t_end, as_pandas=False)
        else:
            events_dc = self.get_events(nlast=nlast, as_pandas=False)

        def mapper(row):
            dc = dict(
                id = row.get('id'), 
                uuid = row.get('parameters', {}).get('uuid'),
                path = row.get('parameters', {}).get('path'),
                msg = row.get('parameters', {}).get('resultMessage'),
                state = row.get('parameters', {}).get('currentState'),
                code = row.get('parameters', {}).get('resultCode'),
                time = row.get('timestamp'),
                params = row.get('parameters', {}).get('params')
            )
            dc = {k:(v if k in {'id', "params"} else ("" if v is None else v)) for k, v in dc.items()}
            p = dc.get('params', {})
            if not p:
                name =   row.get('source') + '-' + row.get('codeName')
                dc['state'] = str(row.get('level'))
            else:
                p = p[:15] + "..." if len(p) > 15 else p
                name = f"{dc['uuid'][-4:]}-{dc['path'].split('.')[-1]}"
                if p != '{}':
                    name += '-' + p

            dc['name'] = name
            return dc
        
        all_events = [mapper(row) for row in events_dc]

        df = pd.DataFrame.from_records(all_events)
        df = df.sort_values('id', ascending=True).set_index('id')
        df['time'] = [s.split('.')[0] + '.' + s.split('.')[-1][1] for s in df['time']]
        df['dt_sec'] = pd.to_datetime(df['time']).apply(lambda x: x.timestamp())
        df['dt_sec'] -= df['dt_sec'].min()
        df = df[(df['state'] != 'TRANSFERRED') & (df['state'] != 'ACTIVATED')]
        df = df['name state code msg dt_sec time'.split()]
        
        if ret_df:
            return df

        try:
            get_ipython().__class__.__name__
            from IPython.display import display
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors

            names = df['name'].unique()
            cmap = plt.get_cmap('tab20', len(names))
            colors = {n: mcolors.rgb2hex(cmap(i)) for i, n in enumerate(names)}

            def style_row(row):
                bgc = f'background-color: {colors.get(row["name"], "")}'
                if row['code'] == 'ERROR':
                    fgc = 'color: red'
                elif row['code'] == 'OK':
                    fgc = 'color: green'
                elif row['state'] == 'PENDING':
                    fgc = 'color: blue'
                else:
                    fgc = ''
                return [bgc] + [fgc] * (df.shape[-1] - 1)
                

            styled_df = df.style.apply(style_row, axis=1)
            styled_df = styled_df.format({col: '{:.1f}' for col in df.select_dtypes(include='float')})
            styled_df

            return display(styled_df)
        except NameError as err:
            print(df.to_markdown())
        
        
    def get_temperatures(self, shorten_names = True):

        chans =  {
            'acu.general_management_and_controller.temp_azimuth_i_o_unit': 'temp_az_i_o_unit',
            'acu.general_management_and_controller.temp_elevation_i_o_unit': 'temp_el_i_o_unit',
            'acu.general_management_and_controller.temp_feedindexer_i_o_unit': 'temp_fi_i_o_unit',
            'acu.general_management_and_controller.temp_emisc': 'temp_emisc',
            'acu.general_management_and_controller.temp_drive_cab': 'temp_drive_cab',
            'acu.general_management_and_controller.temp_air_inlet_psc': 'temp_air_inlet_psc',
            'acu.general_management_and_controller.temp_air_outlet_psc': 'temp_air_outlet_psc',
            'acu.azimuth.motor_1.motor_temperature': 'temp_az_motor_1',
            'acu.azimuth.motor_2.motor_temperature': 'temp_az_motor_2',
            'acu.elevation.motor_1.motor_temperature': 'temp_el_motor_1',
            'acu.elevation.motor_2.motor_temperature': 'temp_el_motor_2',
            'acu.feed_indexer.motor_1.motor_temperature': 'temp_fi_motor_1',
            'acu.feed_indexer.motor_2.motor_temperature': 'temp_fi_motor_2',
            'acu.pointing.act_amb_temp_1': 'temp_tower_amb_S',
            'acu.pointing.act_amb_temp_2': 'temp_tower_amb_E',
            'acu.pointing.act_amb_temp_3': 'temp_tower_amb_W',
        }

        vals = self.getc(list(chans.keys()), as_dict=True)
        if shorten_names:
            return {chans[k]:v for k, v in vals.items()}
        else:
            return vals

    
    def get_act_authority_value(self, as_str=True):
        """gets the currently active command authority either as int value or string depending on the arg as_str"""
        act_com_int = int(self.getc('acu.command_arbiter.act_authority'))
        
        if as_str:
            return command_auth_dc.get(act_com_int, f'UNKNOWN (i={act_com_int})')
        else:
            return act_com_int
        

    def get_azel(self, concurrent=False):
        """gets the current az and el values in degree and returns them as tuple
        """
        if concurrent:
            az_dc, el_dc = self.get_device_status_value_async(['acu.azimuth.p_act', 'acu.elevation.p_act'])
            return az_dc['value'], el_dc['value']
        else:
            return tuple(self.getc(['acu.azimuth.p_act', 'acu.elevation.p_act']))
    

    def get_state(self, path='acu.general_management_and_controller.state'):
        alias_dc = {    
            'gmc': 'acu.general_management_and_controller.state',
            'az': 'acu.azimuth.state',
            'el': 'acu.elevation.state',
            'fi': 'acu.feed_indexer.state',
        }
        
        if path in alias_dc:
            path = alias_dc[path]

        return self.status_finalValue(path)
    
    def get_device_status_value_async(self, pathes):
        params = [{"path": path} for path in pathes]
        devices = ["/devices/statusValue"] * len(params)
        return self.scu_get_concurrent(devices, params)


    def _get_device_status_value(self, path, concurrent = False):
        """
        Gets one or many device status values (status now)

        Args:
            path:       path of the SCU device status as string, or a list of strings for many
        returns:
            either the value directly or a list of values in case of a list of pathes
        """

        if not isinstance(path, str):
            if concurrent:
                devices = ["/devices/statusValue"] * len(path)
                params = [{"path": p} for p in path]
                data = self.scu_get_concurrent(devices, params)
                return [d['value'] for d in data]
            else:
                if len(path) > 10:
                    warnings.warn(f'{traceback.format_stack(limit=5)}\n\n\ngetting N={len(path)} channels from {self}. This will result in N={len(path)} calls to the REST api which can potentially take very long...')
                fun = lambda p: self.scu_get("/devices/statusValue", {"path": p}).json()['value']
                return [fun(p) for p in path]
        else:
            return self.scu_get("/devices/statusValue", {"path": path}).json()['value']
            
    def get_device_status_message(self, path, value_only=False):
        """
        Gets one or many device status fields (which is the value and additional information)

        Args:
            path:       path of the SCU device status as string, or a list of strings for many
        returns:
            either the status message dict directly or a list of dicts in case of a list of pathes
        """
        if not isinstance(path, str):
            if value_only:
                fun = lambda p: self.scu_get("/devices/statusMessageField", {"path": p}).json()['lastFinalValue']
            else:
                fun = lambda p: self.scu_get("/devices/statusMessageField", {"path": p}).json()
            return [fun(p) for p in path]
        else:
            if value_only:
                return self.scu_get("/devices/statusMessageField", {"path": path}).json()['lastFinalValue']
            else:
                return self.scu_get("/devices/statusMessageField", {"path": path}).json()
        
    def get_channel_list(self, with_values=False, with_timestamps=False):
        if self.dish_type == 'mke':
            lst = self.scu_get("/devices/getAllDeviceStatusValues", {"device":"acu"}).json()
            
            if with_values and with_timestamps:
                fun = lambda v: ('acu.' + v['path'], v['values'][0]['timestamp'], v['values'][0]['lastValue'])
            elif not with_values and with_timestamps:
                fun = lambda v: ('acu.' + v['path'], v['values'][0]['timestamp'])
            elif with_values and not with_timestamps:
                fun = lambda v: ('acu.' + v['path'], v['values'][0]['lastValue'])
            else:
                fun = lambda v: 'acu.' + v['path']
            
            return [fun(v) for v in lst if v]
        else:
            if with_values or with_timestamps:
                raise ValueError('skampi type dish can not be queried for values, only for channel names')
            return self.scu_get("/devices/statusPaths").json()



    #status get functions goes here
    
    def status_Value(self, sensor):
        """Low Level function to get the 'value' field from the 
        status message fields a of given device.

        Args:
            sensor (str): path to the sensor to get
        """

        r = self.scu_get('/devices/statusValue', 
            {'path': sensor})
        data = r.json()['value']
        #self.log('value: ', data)
        return(data)

    def status_finalValue(self, sensor):
        """Low Level function to get the 'finalValue' field from the 
        status message fields a of given device.

        Args:
            sensor (str): path to the sensor to get
        """
        #self.log('get status finalValue: ', sensor)
        r = self.scu_get('/devices/statusValue', 
            {'path': sensor})
        data = r.json()['finalValue']
        #self.log('finalValue: ', data)
        return(data)



    def commandMessageFields(self, commandPath):
        """Low Level function to get complete list of all commands message 
        fields from a device given by device name or a single command by given path.

        Use the responses .json() method to access the returned data as a dictionary.

        Args:
            commandPath (str): The path of the command to get

        Returns:
            request.model.Response: response object from this call.
        """
        r = self.scu_get('/devices/commandMessageFields', 
            {'path': commandPath})
        return r

    def statusMessageField(self, statusPath):
        """Low Level function to get a complete list of all 
        status message fields (including the last known value) of given device.

        Use the responses .json() method to access the returned data as a dictionary.

        Args:
            statusPath (str): The path of the status to get

        Returns:
            request.model.Response: response object from this call.
        """
        r = self.scu_get('/devices/statusMessageFields', 
            {'deviceName': statusPath})
        return r
    
    #ppak added 1/10/2020 as debug for onsite SCU version
    #but only info about sensor, value itself is murky?
    def field(self, sensor):
        """Low Level function to get a specific status field.

        Args:
            sensor (str): path to the sensor to get
        """
        #old field method still used on site
        r = self.scu_get('/devices/field', 
            {'path': sensor})
        #data = r.json()['value']
        data = r.json()
        return(data)
    



###################################################################################################
###################################################################################################
###################################################################################################
    
#  ██████ ███    ███ ██████      ██████  ██ ███████ ██   ██ 
# ██      ████  ████ ██   ██     ██   ██ ██ ██      ██   ██ 
# ██      ██ ████ ██ ██   ██     ██   ██ ██ ███████ ███████ 
# ██      ██  ██  ██ ██   ██     ██   ██ ██      ██ ██   ██ 
#  ██████ ██      ██ ██████      ██████  ██ ███████ ██   ██ 
                                                          
                                                          


                                                                                                        


    #SIMPLE PUTS

    #commands to DMC state - dish management controller
    
    @event_start_before_wait_done_after
    def interlock_acknowledge_dmc(self):
        """Send an interlock acknowledge command to the digital motion controller in case
        of trying to acknowledge errors etc.
        """
        self.log('Acknowledge interlock...')

        uuid = self.scu_put('/devices/command',
            {'path': 'acu.dish_management_controller.interlock_acknowledge'})
        return uuid
    
    @event_start_before_wait_done_after
    def reset_dmc(self):
        """reset the digital motion controller in case of errors"""
        self.log('reset dmc...')

        uuid = self.scu_put('/devices/command', 
            {'path': 'acu.dish_management_controller.reset'})
        
        return uuid
    
    @event_start_before_wait_done_after
    def activate_dmc(self):
        """activate the digital motion controller"""
        self.log('activate dmc...')

        uuid = self.scu_put('/devices/command',
            {'path': 'acu.dish_management_controller.activate'})
        return uuid
    
    @event_start_before_wait_done_after
    def deactivate_dmc(self):
        """deactivate the digital motion controller"""
        self.log('deactivate dmc')
        
        uuid = self.scu_put('/devices/command', 
            {'path': 'acu.dish_management_controller.deactivate'})

        return uuid
    
    @event_start_before_wait_done_after
    def move_to_band(self, position):
        """move the feed indexer to a predefined band position
        options str: "Band 1", "Band 2", "Band 3", "Band 5a", "Band 5b"
        "Band 5c"
        Args:
            position (str or int): Either "Band 1"..."Band 5c" or 1...7
        """

        self.log('move to band:' + str(position))
        
        if not(isinstance(position, str)):
            uuid = self.scu_put('/devices/command',
            {'path': 'acu.dish_management_controller.move_to_band',
            'params': {'action': position}})
        else:
            uuid = self.scu_put('/devices/command',
            {'path': 'acu.dish_management_controller.move_to_band',
            'params': {'action': bands_dc[position]}})

        return uuid
    
    def move(self, az=None, el=None, band=None, wait_settle=False):
        """synonym for abs_azel. Moves to an absolute az el position and/or
        Args:
            az_angle (-270 <= az_angle <= 270): abs AZ angle in degree.
            el_angle (15 <= el_angle <= 90): abs EL angle in degree.
            band (str or int): Either "Band 1", "Band 2", "Band 3", "Band 5a", "Band 5b", "Band 5c" or 1...7
        """
        assert not (az is None and el is None and band is None), 'need to give ANY input! either, az, el, or band'

        if not az is None or not el is None:
            az_angle = self.getc('acu.azimuth.p_act') if az is None else az
            el_angle = self.getc('acu.elevation.p_act') if el is None else el
            self.move_to_azel(az_angle, el_angle, wait_settle=wait_settle)

        if not band is None:
            self.move_to_band(band)


    @event_start_before
    def move_to_azel(self, az_angle, el_angle, az_vel=None, el_vel=None, wait_settle=False):
        """synonym for abs_azel. Moves to an absolute az el position
        with a preset slew rate
        Args:
            az_angle (-270 <= az_angle <= 270): abs AZ angle in degree.
            el_angle (15 <= el_angle <= 90): abs EL angle in degree.
            az_vel (0 < az_vel <= 3.0): AZ angular slew rate in degree/s. None for as fast as possible.
            el_vel (0 < el_vel <= 1.35): EL angular slew rate in degree/s. None for as fast as possible.
        """
        if az_vel is None and el_vel is None: 
            self.abs_azel(az_angle, el_angle)
        else:

            assert all([v is not None for v in [az_angle, el_angle, az_vel, el_vel]]), 'inputs can not be None'
            self.log('move to az: {:.4f} el: {:.4f} (vels: ({:.4f}, {:.4f})'.format(az_angle, el_angle, az_vel, el_vel))
            assert (az_vel is None) == (el_vel is None), 'either both velocities must be None, or neither'

            az_angle, el_angle, az_vel, el_vel = self._limit_motion(az_angle, el_angle, az_vel, el_vel)

            uuid1 = self.scu_put('/devices/command',
                {'path': 'acu.azimuth.slew_to_abs_pos',
                'params': {'new_axis_absolute_position_set_point': az_angle,
                'new_axis_speed_set_point_for_this_move': az_vel}})    

            uuid2 = self.scu_put('/devices/command',
                {'path': 'acu.elevation.slew_to_abs_pos',
                'params': {'new_axis_absolute_position_set_point': el_angle,
                'new_axis_speed_set_point_for_this_move': el_vel}}) 

            if wait_settle and self.wait_done_by_uuid:
                self.wait_uuid_done(uuid1, 'slew_abs_az')
                self.wait_uuid_done(uuid2, 'slew_abs_el')

    @event_start_before_wait_done_after
    def abs_azel(self, az_angle, el_angle, wait_settle=False):
        """move to a given absolut position on both axes

        Args:
            az_angle (-270 <= az_angle <= 270): abs AZ angle in degree.
            el_angle (15 <= el_angle <= 90): abs EL angle in degree.
        """
        

        self.log('move to az: {:.4f} el: {:.4f}'.format(az_angle, el_angle))
        
        az_angle, el_angle, _, _ = self._limit_motion(az_angle, el_angle)

        uuid = self.scu_put('/devices/command',
            {'path': 'acu.dish_management_controller.slew_to_abs_pos',
            'params': {'new_azimuth_absolute_position_set_point': az_angle,
                'new_elevation_absolute_position_set_point': el_angle}})

        return uuid
    
    #commands to ACU
        
    @event_start_before_wait_done_after
    def deactivate_lowpowermode(self):
        uuid = self.scu_put("/devices/command", {"path":"acu.dish_management_controller.set_power_mode","params":{"action":"0"}})
        return uuid
    
    @event_start_before_wait_done_after
    def activate_lowpowermode(self):
        uuid = self.scu_put("/devices/command", {"path":"acu.dish_management_controller.set_power_mode","params":{"action":"1"}})
        return uuid
    
    def stow(self, pre_move=True, nowait=False):
        """stow the antenna on pos 1 (both axes) and wait for stowing to be completed
        """
        self.log('Stowing...')
        uuid = '<N/A>'
        
        if not nowait:
            if self.wait_done_by_uuid and (self.event_streamer is None or not self.event_streamer.is_alive()):
                self.start_event_stream()

        if self.get_state().upper() != 'STOWED':

            if pre_move:
                 # offset by one degree, since it was suspected (by ODC), that moving to close to stow position before stowing can lead to errors
                az, el = self.stow_pos
                az += 1.
                el -= 1.
                self.abs_azel(az, el, wait_settle=True)
                self.wait_duration(0.5)
                self.wait_settle()
                self.wait_duration(1.0)

            if self.dish_type == 'mke':
                uuid = self.scu_put("/devices/command", {"path": "acu.dish_management_controller.stow", "params": {"az_stow": "1", "el_stow": "1"}})
            else:
                uuid = self.scu_put("/devices/command", {"path": "acu.dish_management_controller.stow", "params": {"action": "1"}})
        
        if not nowait:
            if self.wait_done_by_uuid:
                self.wait_uuid_done(uuid, 'stow', 1200) # give a bit longer for the stow  
            
            self.wait_state("acu.stow_pin_controller.azimuth_status", "DEPLOYED", operator='==')
            self.wait_state("acu.stow_pin_controller.elevation_status", "DEPLOYED", operator='==')
            self.wait_duration(1, no_stout=True)          

        return uuid
    

        
    def unstow(self, nowait=False):
        """
        Unstow both axes
        """
        self.log('Unstowing...')
        if not nowait:
            if self.wait_done_by_uuid and (self.event_streamer is None or not self.event_streamer.is_alive()):
                self.start_event_stream()

        uuid = self.scu_put("/devices/command", {"path": "acu.dish_management_controller.unstow"})


        if not nowait:
            if self.wait_done_by_uuid:
                self.wait_uuid_done(uuid, 'unstow')        
            else:
                self.wait_duration(3, no_stout=True)      
                self.wait_state("acu.stow_pin_controller.azimuth_status", "RETRACTED", operator='==')
                self.wait_state("acu.stow_pin_controller.elevation_status", "RETRACTED", operator='==')
                self.wait_duration(1, no_stout=True)  
        return uuid
    
    @event_start_before
    def activate_axes(self):
        """
        Activate axes
        """
        
        self.log('Activating axes...')

        uuid1 = self.scu_put("/devices/command", {"path": "acu.azimuth.activate"})
        uuid2 = self.scu_put("/devices/command", {"path": "acu.elevation.activate"})


        if self.wait_done_by_uuid:
            self.wait_uuid_done(uuid1, 'activate_az')
            self.wait_uuid_done(uuid2, 'activate_el')
        else:
            self.wait_duration(1, no_stout=True)
            self.waitForStatusValue("acu.azimuth.axis_bit_status.abs_active", True, timeout=15)
            self.waitForStatusValue("acu.elevation.axis_bit_status.abs_active", True, timeout=15)
        return uuid1, uuid2
    
    
    @event_start_before_wait_done_after
    def activate_fi(self):
        """activate the the feed indexer axis"""
        self.log('activate fi...')

        uuid = self.scu_put('/devices/command',
            {'path': 'acu.feed_indexer.activate'})
        return uuid
    
    @event_start_before_wait_done_after
    def deactivate_fi(self):
        """Deactivate the feed indexer axis"""
        self.log('activate fi...')

        uuid = self.scu_put('/devices/command',
            {'path': 'acu.feed_indexer.deactivate'})
        return uuid
    

    @event_start_before
    def deactivate_axes(self):
        """
        Deactivate axes
        """

        uuid1 = self.scu_put("/devices/command", {"path": "acu.azimuth.deactivate"})
        uuid2 = self.scu_put("/devices/command", {"path": "acu.elevation.deactivate"})


        if self.wait_done_by_uuid:
            self.wait_uuid_done(uuid1, 'deactivate_az')
            self.wait_uuid_done(uuid2, 'deactivate_el')
        else:
            self.wait_duration(1, no_stout=True)        
            self.waitForStatusValue("acu.azimuth.axis_bit_status.abs_active", False, timeout=15)
            self.waitForStatusValue("acu.elevation.axis_bit_status.abs_active", False, timeout=15)
        return uuid1, uuid2
    

    def release_command_authority(self):
        """
        Release command authority.
        """
        self.log('Releasing Command Authority...')
        self._command_authority('Release')
        if not self.wait_done_by_uuid:
            self.wait_duration(5)
    
    def get_command_authority(self):
        """
        get command authority.
        """
        self.log('Getting Command Authority...')


        self._command_authority('Get')
        # # ICD Version 2.4 says 4, but actual behavior of 21.07.2021 is value 3 == SCU
        # self.wait_for_status("acu.command_arbiter.act_authority", "3", timeout=10)
        if not self.wait_done_by_uuid:
            self.wait_duration(5)
        
    #command authority
    
    @event_start_before_wait_done_after
    def _command_authority(self, action):
        #1 get #2 release
        

        authority={'Get': 1, 'Release': 2}
        uuid = self.scu_put('/devices/command', 
            {'path': 'acu.command_arbiter.authority',
            'params': {'action': authority[action]}})

        return uuid
    
    @event_start_before_wait_done_after
    def activate_az(self):
        """activate azimuth axis (controller)"""
        self.log('activate azimuth')
        
        uuid = self.scu_put('/devices/command', 
            {'path': 'acu.elevation.activate'})

        return uuid
    
    @event_start_before_wait_done_after
    def activate_el(self):
        """activate elevation axis (controller)"""
        self.log('activate elevation')

        uuid = self.scu_put('/devices/command', 
            {'path': 'acu.elevation.activate'})

        return uuid
    
    @event_start_before_wait_done_after
    def deactivate_el(self):
        """deactivate elevation axis (controller)"""
        self.log('deactivate elevation')

        uuid = self.scu_put('/devices/command', 
            {'path': 'acu.elevation.deactivate'})

        return uuid
    
    @event_start_before_wait_done_after
    def abs_fi(self, fi_angle, fi_vel=11.0):
        """Moves to an absolute FI position
        with a preset slew rate
        Args:
            az_angle (-104 <= az_angle <= 105): abs FI angle in degree.
            az_vel (0 <= az_vel <= 11.0): FI angular slew rate in degree/s.
        """
        
        self.log('abs fi: {:.4f} vel: {:.4f}'.format(fi_angle, fi_vel))

        fi_vel = self.lims_az[-1] if fi_vel is None else fi_vel
        fi_angle = max(min(fi_angle, 104), -104)
        fi_vel =  max(min(fi_vel, 11.0), 0.000001)
        uuid = self.scu_put('/devices/command',
            {'path': 'acu.feed_indexer.slew_to_abs_pos',
            'params': {'new_axis_absolute_position_set_point': fi_angle,
            'new_axis_speed_set_point_for_this_move': fi_vel}})    

        return uuid
    

    @event_start_before_wait_done_after
    def abs_azimuth(self, az_angle, az_vel):
        """Moves to an absolute az position
        with a preset slew rate
        Args:
            az_angle (-270 <= az_angle <= 270): abs AZ angle in degree.
            az_vel (0 <= az_vel <= 3.0): AZ angular slew rate in degree/s.
        """
        
        self.log('abs az: {:.4f} vel: {:.4f}'.format(az_angle, az_vel))

        az_vel = self.lims_az[-1] if az_vel is None else az_vel
        az_angle, _, az_vel, _ = self._limit_motion(az_angle, None, az_vel, None)
        uuid = self.scu_put('/devices/command',
            {'path': 'acu.azimuth.slew_to_abs_pos',
            'params': {'new_axis_absolute_position_set_point': az_angle,
            'new_axis_speed_set_point_for_this_move': az_vel}})    

        return uuid
    
    @event_start_before_wait_done_after
    def abs_elevation(self, el_angle, el_vel):
        """Moves to an absolute el position
        with a preset slew rate
        Args:
            az_vel (0 <= az_vel <= 3.0): AZ angular slew rate in degree/s.
            el_vel (0 <= el_vel <= 3.0): EL angular slew rate in degree/s.
        """

        self.log('abs el: {:.4f} vel: {:.4f}'.format(el_angle, el_vel))
        
        el_vel = self.lims_el[-1] if el_vel is None else el_vel
        _, el_angle, _, el_vel = self._limit_motion(None, el_angle, None, el_vel)

        uuid = self.scu_put('/devices/command',
            {'path': 'acu.elevation.slew_to_abs_pos',
            'params': {'new_axis_absolute_position_set_point': el_angle,
            'new_axis_speed_set_point_for_this_move': el_vel}}) 

        return uuid
    
    @event_start_before_wait_done_after
    def load_static_offset(self, az_offset, el_offset):
        """loads a static offset to the tracking controller

        Args:
            az_offset (float): the AZ offset to load. Unit Unclear!
            el_offset (float): the EL offset to load. Unit Unclear!
        """
        self.log('offset az: {:.4f} el: {:.4f}'.format(az_offset, el_offset))
        
        uuid = self.scu_put('/devices/command',
            {'path': 'acu.tracking_controller.load_static_tracking_offsets.',
            'params': {'azimuth_tracking_offset': float(az_offset),
                        'elevation_tracking_offset': float(el_offset)}})     #Track table commands

        return uuid
    

    @event_start_before_wait_done_after
    def load_program_track(self, load_type, entries, t=[0]*50, az=[0]*50, el=[0]*50):
        """WARNING DEPRECATED! please use upload_track_table instead
        load a program track table to the ACU of exactly 50 entries

        Args:
            load_type (str): either 'LOAD_NEW', 'LOAD_ADD', or 'LOAD_RESET'
            entries (int): number of entries in track table
            t (list of float, optional): time values to upload. Defaults to [0]*50.
            az (list of float, optional): az values to upload. Defaults to [0]*50.
            el (list of float, optional): el values to upload. Defaults to [0]*50.
        """

        warnings.warn(
            "Legacy Function: This is not maintained and might not work as intended\nWARNING DEPRECATED! please use upload_track_table instead",
            DeprecationWarning
        )

        self.log(load_type)    
        LOAD_TYPES = {
            'LOAD_NEW' : 1, 
            'LOAD_ADD' : 2, 
            'LOAD_RESET' : 3}
        
        #table selector - to tidy for future use
        ptrackA = 11
        
        TABLE_SELECTOR =  {
            'pTrackA' : 11,
            'pTrackB' : 12,
            'oTrackA' : 21,
            'oTrackB' : 22}
        
        #funny thing is SCU wants 50 entries, even for LOAD RESET! or if you send less then you have to pad the table
    
        if entries != 50:
            padding = 50 - entries
            t  += [0] * padding
            az += [0] * padding
            el += [0] * padding
        

        uuid = self.scu_put('/devices/command',
                    {'path': 'acu.dish_management_controller.load_program_track',
                    'params': {'table_selector': ptrackA,
                                'load_mode': LOAD_TYPES[load_type],
                                'number_of_transmitted_program_track_table_entries': entries,
                                'time_0': t[0], 'time_1': t[1], 'time_2': t[2], 'time_3': t[3], 'time_4': t[4], 'time_5': t[5], 'time_6': t[6], 'time_7': t[7], 'time_8': t[8], 'time_9': t[9], 'time_10': t[10], 'time_11': t[11], 'time_12': t[12], 'time_13': t[13], 'time_14': t[14], 'time_15': t[15], 'time_16': t[16], 'time_17': t[17], 'time_18': t[18], 'time_19': t[19], 'time_20': t[20], 'time_21': t[21], 'time_22': t[22], 'time_23': t[23], 'time_24': t[24], 'time_25': t[25], 'time_26': t[26], 'time_27': t[27], 'time_28': t[28], 'time_29': t[29], 'time_30': t[30], 'time_31': t[31], 'time_32': t[32], 'time_33': t[33], 'time_34': t[34], 'time_35': t[35], 'time_36': t[36], 'time_37': t[37], 'time_38': t[38], 'time_39': t[39], 'time_40': t[40], 'time_41': t[41], 'time_42': t[42], 'time_43': t[43], 'time_44': t[44], 'time_45': t[45], 'time_46': t[46], 'time_47': t[47], 'time_48': t[48], 'time_49': t[49],
                                'azimuth_position_0': az[0], 'azimuth_position_1': az[1], 'azimuth_position_2': az[2], 'azimuth_position_3': az[3], 'azimuth_position_4': az[4], 'azimuth_position_5': az[5], 'azimuth_position_6': az[6], 'azimuth_position_7': az[7], 'azimuth_position_8': az[8], 'azimuth_position_9': az[9], 'azimuth_position_10': az[10], 'azimuth_position_11': az[11], 'azimuth_position_12': az[12], 'azimuth_position_13': az[13], 'azimuth_position_14': az[14], 'azimuth_position_15': az[15], 'azimuth_position_16': az[16], 'azimuth_position_17': az[17], 'azimuth_position_18': az[18], 'azimuth_position_19': az[19], 'azimuth_position_20': az[20], 'azimuth_position_21': az[21], 'azimuth_position_22': az[22], 'azimuth_position_23': az[23], 'azimuth_position_24': az[24], 'azimuth_position_25': az[25], 'azimuth_position_26': az[26], 'azimuth_position_27': az[27], 'azimuth_position_28': az[28], 'azimuth_position_29': az[29], 'azimuth_position_30': az[30], 'azimuth_position_31': az[31], 'azimuth_position_32': az[32], 'azimuth_position_33': az[33], 'azimuth_position_34': az[34], 'azimuth_position_35': az[35], 'azimuth_position_36': az[36], 'azimuth_position_37': az[37], 'azimuth_position_38': az[38], 'azimuth_position_39': az[39], 'azimuth_position_40': az[40], 'azimuth_position_41': az[41], 'azimuth_position_42': az[42], 'azimuth_position_43': az[43], 'azimuth_position_44': az[44], 'azimuth_position_45': az[45], 'azimuth_position_46': az[46], 'azimuth_position_47': az[47], 'azimuth_position_48': az[48], 'azimuth_position_49': az[49],
                                'elevation_position_0': el[0], 'elevation_position_1': el[1], 'elevation_position_2': el[2], 'elevation_position_3': el[3], 'elevation_position_4': el[4], 'elevation_position_5': el[5], 'elevation_position_6': el[6], 'elevation_position_7': el[7], 'elevation_position_8': el[8], 'elevation_position_9': el[9], 'elevation_position_10': el[10], 'elevation_position_11': el[11], 'elevation_position_12': el[12], 'elevation_position_13': el[13], 'elevation_position_14': el[14], 'elevation_position_15': el[15], 'elevation_position_16': el[16], 'elevation_position_17': el[17], 'elevation_position_18': el[18], 'elevation_position_19': el[19], 'elevation_position_20': el[20], 'elevation_position_21': el[21], 'elevation_position_22': el[22], 'elevation_position_23': el[23], 'elevation_position_24': el[24], 'elevation_position_25': el[25], 'elevation_position_26': el[26], 'elevation_position_27': el[27], 'elevation_position_28': el[28], 'elevation_position_29': el[29], 'elevation_position_30': el[30], 'elevation_position_31': el[31], 'elevation_position_32': el[32], 'elevation_position_33': el[33], 'elevation_position_34': el[34], 'elevation_position_35': el[35], 'elevation_position_36': el[36], 'elevation_position_37': el[37], 'elevation_position_38': el[38], 'elevation_position_39': el[39], 'elevation_position_40': el[40], 'elevation_position_41': el[41], 'elevation_position_42': el[42], 'elevation_position_43': el[43], 'elevation_position_44': el[44], 'elevation_position_45': el[45], 'elevation_position_46': el[46], 'elevation_position_47': el[47], 'elevation_position_48': el[48], 'elevation_position_49': el[49]}})


        return uuid
    

    # def start_program_track(self, start_time):
    #     """Start a previously loaded tracking table (Table A) using SPLINE interpolation and AZ EL tracking Mode

    #     Args:
    #         start_time (float): start time as MJD
    #     """
    #     ptrackA = 11
    #     #interpol_modes
    #     NEWTON = 0
    #     SPLINE = 1
    #     #start_track_modes
    #     AZ_EL = 1
    #     RA_DEC = 2
    #     RA_DEC_SC = 3  #shortcut
    #     self.scu_put('/devices/command',
    #                 {'path': 'acu.dish_management_controller.start_program_track',
    #                 'params' : {'table_selector': ptrackA,
    #                             'start_time_mjd': start_time,
    #                             'interpol_mode': SPLINE,
    #                             'track_mode': AZ_EL }})

    def run_tt_bg(self, t=None, az=None, el=None, df=None, columns=['time', 'az', 'el'], activate_logging=True, config_name='full_configuration'):
        """run a tracking tabel in the background as a seperate thread see method "with_tt" for details: 

        Args:
            t (numpy array Nx1, optional): time vector for tracking table in mjd. Defaults to None.
            az (numpy array Nx1, optional): azimuth values for tracking table. Defaults to None.
            el (numpy array N x1, optional): elevation values for tracking table. Defaults to None.
            df (pd.DataFrame, optional): optional instead of az, el, t to pass a dataframe and use the columns defined in colums. Defaults to None.
            columns (list, optional): columns to use in the dataframe for t, az, el. Defaults to ['time', 'az', 'el'].
            activate_logging (bool, optional): whether or not to activate logging during running of this table. Defaults to True.
            config_name (str, optional): the logging configuration to use. Defaults to 'full_configuration'.
        returns:
            threading thread: the thread where the tracking table is running under
        """

        assert not (isinstance(t, pd.DataFrame) and az is None and el is None), 'Must pass a dataframe with the keyword argument df=...'
        if t is None and az is None and el is None and df is not None and columns is not None:
            t, az, el = [df[c].values for c in columns]
        
        return TrackHandler.run_in_background(self, t, az, el, activate_logging, config_name, wait_start=False, wait_for_end_pos=False)

        
    def with_tt(self, t=None, az=None, el=None, df=None, columns=['time', 'az', 'el'], activate_logging=True, config_name='full_configuration', wait_start=True, wait_for_end_pos=True):
        """run a tracking tabel using a context manager like this: 

        with scu.with_tt(**tt) as track:
            print(f'{track.get_t_remaining()=} {scu.azel=}')

        carries out the steps:
            stop_program_track()
            start_logger() only if needed
            upload_trac_table()
            t0 = time.time()
            wait_duration(2)
            while dt_i < dt:
                dt_i = time.time() - t0
                yield dt_i
            wait_for_pos(az[-1])
            wait_for_pos(el[-1])
            stop_logger() only if needed
            stop_program_track()
            wait_duration(5)
         

        Args:
            t (numpy array Nx1, optional): time vector for tracking table in mjd. Defaults to None.
            az (numpy array Nx1, optional): azimuth values for tracking table. Defaults to None.
            el (numpy array N x1, optional): elevation values for tracking table. Defaults to None.
            df (pd.DataFrame, optional): optional instead of az, el, t to pass a dataframe and use the columns defined in colums. Defaults to None.
            columns (list, optional): columns to use in the dataframe for t, az, el. Defaults to ['time', 'az', 'el'].
            activate_logging (bool, optional): whether or not to activate logging during running of this table. Defaults to True.
            config_name (str, optional): the logging configuration to use. Defaults to 'full_configuration'.
        """


        assert not (isinstance(t, pd.DataFrame) and az is None and el is None), 'Must pass a dataframe with the keyword argument df=...'
        if t is None and az is None and el is None and df is not None and columns is not None:
            t, az, el = [df[c].values for c in columns]
        
        return TrackHandler(self, t, az, el, activate_logging, config_name, wait_start=wait_start, wait_for_end_pos=wait_for_end_pos)

    def run_track_table(self, t=None, az=None, el=None, df=None, columns=['time', 'az', 'el'], activate_logging=True, config_name='full_configuration', wait_start=True, verb=False):
        """run a tracking tabel and block until complete
        stop_program_track()
        start_logger() only if needed
        upload_trac_table()
        wait_duration(dt)
        wait_for_pos(az[-1])
        wait_for_pos(el[-1])
        stop_logger() only if needed
        stop_program_track()
        wait_duration(5)
        return 

        Args:
            t (numpy array Nx1, optional): time vector for tracking table in mjd. Defaults to None.
            az (numpy array Nx1, optional): azimuth values for tracking table. Defaults to None.
            el (numpy array N x1, optional): elevation values for tracking table. Defaults to None.
            df (pd.DataFrame, optional): optional instead of az, el, t to pass a dataframe and use the columns defined in colums. Defaults to None.
            columns (list, optional): columns to use in the dataframe for t, az, el. Defaults to ['time', 'az', 'el'].
            activate_logging (bool, optional): whether or not to activate logging during running of this table. Defaults to True.
            config_name (str, optional): the logging configuration to use. Defaults to 'full_configuration'.
        """
        assert not (isinstance(t, pd.DataFrame) and az is None and el is None), 'Must pass a dataframe with the keyword argument df=...'
        if t is None and az is None and el is None and df is not None and columns is not None:
            t, az, el = [df[c].values for c in columns]
        
        with TrackHandler(self, t, az, el, activate_logging, config_name, wait_start, verb) as track:
            self.log('Tracking...', color=colors.OKGREEN)

        return track
    
    def _tt_test_and_clean(self, t, az, el, verb=True):
        
        is_mon_increasing = np.all(np.diff(t) > 0)
        if not is_mon_increasing:
            raise Exception('Time vector in tracking table is not monotonically increasing!')
        
        t_astro = Time(np.round(t, 12), format='mjd')
        t_end = t_astro[-1]
        dt = np.min(np.diff(t_astro.unix))
        assert len(t) == len(az) == len(el), f"ERROR: length of time, az, el all need to be equal, but got {len(t)=}, {len(az)=}, {len(el)=}"
        assert dt >= 0.2, "ERROR, The ACU will only accept tracking tables with dt > 0.2s, but given was: dt_min={}".format(dt)

        if verb:
            t0, t1 = Time(t[0], format='mjd'), Time(t[-1], format='mjd')

            self.log('Running Table ({}, {:5.3f}, {:5.3f}) --> ({}, {:5.3f}, {:5.3f}) T={:.2f} N={}, dt_min={:.12f}'.format(t0.iso, az[0], el[0], t1.iso, az[-1], el[-1],  np.ptp(t_astro.unix), len(az), dt), color=colors.BOLD)
            self.log('t_internal = {} az_now={:5.3f}°, el_now={:5.3f}°'.format(self.t_internal.iso, *self.azel))
            dt_start = (t0 - self.t_internal).to(u.s).value
            dt_end = (t1 - self.t_internal).to(u.s).value
            self.log('timedelta for table to now is dt_start={:+4.1f}s dt_end={:+4.1f}s (negative means in the past!)'.format(dt_start, dt_end))

        # hack: Workaround. The SCU ignores tracking tables with <= 50 entries
        if len(t) <= 50:
            self.log(f'WARNING!: The given tracking table has only {len(t)} entries.', color=colors.WARNING)
            self.log(f'The SCU has a bug where tracking tables with <=50 samples are silently ignored.', color=colors.WARNING)
            self.log(f'appending until the tracking table has at least 51 entries', color=colors.WARNING)
            
            t, az, el = list(t), list(az), list(el)
            dte = t[-1] - t[-2]
            while len(t) <= 50:
                t.append(t[-1]+dte)
                az.append(az[-1])
                el.append(el[-1])

        t, az, el = np.array(t), np.array(az), np.array(el)

        return t, az, el, t_end

    def upload_track_table(self, t=None, az=None, el=None, df=None, columns=['time', 'az', 'el'], wait_for_start=False):
        """convenience funtion to wrap 
                scu.acu_ska_track(scu.format_body(t, az, el))
            in one call
        Args:
            Either:
                t (iterable of float): time as mjd
                az (iterable of float): azimuth in degree
                el (iterable of float): elevation (alt) in degree
            Or:
                df (pandas.DataFrame): with at least three columns giving time [mjd], az [deg], el[el]
                a (iterable of str): the columns to use in the dataframe. Default: ['time', 'az', 'el']
            wait_for_start (bool, optional): Whether or not to wait for the tracking table to start after upload. Defaults to False.
        """
        assert not (isinstance(t, pd.DataFrame) and az is None and el is None), 'Must pass a dataframe with the keyword argument df=...'
        if t is None and az is None and el is None and df is not None and columns is not None:
            t, az, el = [df[c].values for c in columns]
        
        t, az, el, t_end = self._tt_test_and_clean(t, az, el)

        rows_table = ["{:6.12f} {:3.8f} {:3.8f}".format(ti, azi, eli) for ti, azi, eli in zip(t, az, el)]
        self.acu_ska_track("\n".join(rows_table))
        if wait_for_start:
            self.wait_track_start(timeout=30)

        return t_end.unix - self.t_internal.unix

    @event_start_before_wait_done_after
    def stop_program_track(self, no_stdout=False):
        """
        Stop loading program track table - presumably, stops a programmed track
        """

        self.log("Requesting stop program track")
        self.acu_ska_track_stoploadingtable()
        # stopLoadingTable has no uuid return value
        self.wait_duration(0.5, no_stdout)
    
        # See E-Mail from Arne, 2021/11/05
        uuid = self.scu_put("/devices/command", payload={"path": "acu.tracking_controller.reset_program_track",
                    "params": {"table_selector": "11", "load_mode": "3", "number_of_transmitted_program_track_table_entries": "0"}})
        if not self.wait_done_by_uuid:
            self.wait_duration(1, no_stdout)

        return uuid
    
        

    # @event_start_before_wait_done_after
    def acu_ska_track(self, BODY):
        """Low level function. Use 'upload_track_table()' instead to upload a tracking table.
            This function uploads a programTrack (tracking table) in the internal SCU specific format, which is
                "{:6.12f} {:3.8f} {:3.8f}\n" for time[mjd] az[deg] el[deg]
            per row.
        

        Args:
            BODY (str): the string holing the tracking table in the internal SCU specific format.

        Returns:
            request.model.Response: response object from this call (useless for anything but ID and returncode checking)
        """
        self.log(f'uploading acu-ska-track with {len(BODY)} char size...')
        # for some reason no uuid here
        uuid = self.scu_put('/acuska/programTrack', data = BODY, get_uuid=False)
        return uuid
    
    def acu_ska_track_stoploadingtable(self):
        """Low level function. Use 'stop_program_track()' instead 

        Returns:
            request.model.Response: response object from this call (useless for anything but ID and returncode checking)
        """
        self.log('acuska stopLoadingTable...')
        # for some reason stopLoadingTable does not give a uuid feedback
        r = self.scu_put('/acuska/stopLoadingTable', get_uuid=False)
        self.log('acuska stopLoadingTable...done')
        return r
    
    def format_tt_line(self, t, az,  el, capture_flag = 1, parallactic_angle = 0.0):
        """Low Level Function to format a single line within a tracking table in SCU native format.
        assumption is capture flag and parallactic angle will not be used.

        Args:
            t (float): time in MJD
            az (-270 <= float <= 270): azimuth position in deg
            el (15 <= float <= 90): elevation position in deg
            capture_flag (int, optional): ???. Defaults to 1.
            parallactic_angle (float, optional): ???. Defaults to 0.0.
        """
        f_str = '{:.12f} {:.6f} {:.6f} {:.0f} {:.6f}\n'.format(float(t), float(az), float(el), capture_flag, float(parallactic_angle))
        return(f_str)

    def format_body(self, t, az, el):
        """Low Level function to format a list of tracking table entries in SCU native format.

        Args:
            t (list of float): time in MJD
            az (list of float, -270 <= float <= 270): azimuth position in deg
            el (lost of float, 15 <= float <= 90): elevation position in deg
        Returns:
            str: The tracking table in SCU native format.
        """

        body = ''
        for i in range(len(t)):
            body += self.format_tt_line(t[i], az[i], el[i])
        return(body)        



    @event_start_before_wait_done_after
    def set_time_source(self, select='2'):
        """
        Selects the time source for the device.

        Args:
            select (str): The time source to select. Must be one of:
                - "0": Internal PC Time
                - "1": PTP clock module
                - "2": Absolute time by CMD

        Raises:
            AssertionError: If the `select` parameter is not a valid string.
        """

        if not isinstance(select, str):
            select = str(select)

        dc_map = {
              "0": "Internal PC Time",
              "1": "PTP clock module",
              "2": "Absolute time by CMD"
        }
        dc_map_inv = {v:k for k, v in dc_map.items()}
    
        select = dc_map_inv.get(select, select)
        assert select in '0 1 2'.split(), f'select must be in 0, 1, or 2, but was {select=}'

        # "acu.time_controller.time_source.choose_time_source"
        self.scu_put("/devices/command", payload={"path": "time_controller.time_source",
                    "params": {"time_controller.time_source.choose_time_source": str(select)}})
        


    def antenna_config_get(self, antenna_id='',  numeric=True, filename="Customer_Config.json", url_qry = 'http://10.98.76.45:8990/antenna_config/get', **kwargs):
        """Get antenna configuration.

        Args:
            antenna_id (str): The ID of the antenna. If not provided, the instance's antenna_id is used.
            numeric (bool): Whether to return numeric values. Defaults to True.
            filename (str): The name of the configuration file. Defaults to "Customer_Config.json".
            url_qry (str): The base URL for the query. Defaults to 'http://10.98.76.45:8990/antenna_config/get'.
            **kwargs: Additional keyword arguments to pass to the requests.get method.

        Returns:
            dict: The JSON response from the server.

        Raises:
            AssertionError: If no valid antenna_id is provided.
            HTTPError: If the server returns a non-200 status code.
        """
        if not antenna_id and self.antenna_id:
            antenna_id = self.antenna_id
        elif not antenna_id and not self.antenna_id:
            parsed_url = urllib.urlparse(url_qry)
            antenna_id = _resolve_antenna_ip(self.address, url_qry=f"{parsed_url.scheme}://{parsed_url.netloc}/antennas")
        assert antenna_id, f"must give a valid antenna_id, but given was {antenna_id=}"
        qry = f'?numeric={urllib.parse.quote(str("1" if numeric else "0"))}&filename={urllib.parse.quote(filename)}'
        r = requests.get(f'{url_qry}/{antenna_id}{qry}', **kwargs)
        if not str(r.status_code).startswith('2'):
            logfun(f"HTTP ERROR ({r.status_code}): {r.text}", colors.FAIL, name=antenna_id)
            r.raise_for_status()
        return r.json()


###################################################################################################
###################################################################################################
###################################################################################################
        
# ██████  ██ ███████ ██   ██     ███████ ████████  █████  ██████  ████████         ██     ███████ ████████  ██████  ██████  
# ██   ██ ██ ██      ██   ██     ██         ██    ██   ██ ██   ██    ██           ██      ██         ██    ██    ██ ██   ██ 
# ██   ██ ██ ███████ ███████     ███████    ██    ███████ ██████     ██          ██       ███████    ██    ██    ██ ██████  
# ██   ██ ██      ██ ██   ██          ██    ██    ██   ██ ██   ██    ██         ██             ██    ██    ██    ██ ██      
# ██████  ██ ███████ ██   ██     ███████    ██    ██   ██ ██   ██    ██        ██         ███████    ██     ██████  ██      
                                                                                                                          
                                                                                                                          



    def start(self, az_start=None, el_start=None, band_start=None, az_speed=None, el_speed=None, send_default_configs=True, interlock_acknowledge_on_start=True, **kwargs):
        """getting command authority, unstow, activate and start the antenna for usage

        Args:
            az_start (-270 <= az_start <= 270, optional): start position for AZ axis in degree. Defaults to None.
            el_start (15 <= el_start <= 90, optional): start position for EL axis in degree. Defaults to None.
            band_start (str or int, optional): start position ('Band 1'... 'Band 5c' or 1...7) for the Feed Indexer Axis to move to. Defaults to None.
            az_speed (0 < az_speed <= 3.0, optional): azimuth speed to use for movement to inital position. None means as fast as possible. Defaults to None.
            el_speed (0 < el_speed <= 1.0, optional): elevation speed to use for movement to inital position None means as fast as possible. Defaults to None.
            send_default_configs (bool, optional): Whether or not to generate the default logging configs on the SCU on startup. Defaults to True.
            interlock_acknowledge_on_start (bool, optional): Whether or not to send an interlock acknowledged command to the scu after startup. Defaults to True.
        """
        self.log('=== INITIATING STARTUP ROUTINE ===', color=colors.BOLD)
        self.t_start = Time.now()
        self.determine_dish_type()
        self.get_command_authority()
        
        self.wait_duration(0.1)
        if self.dish_type == 'mke':
            self.deactivate_lowpowermode()
            self.wait_duration(0.1)

        self.reset_dmc()
        if not self.wait_done_by_uuid:
            self.wait_duration(3)

        if self.use_socket and not self.data_streamer.is_alive():
            self.data_streamer.start()


        if interlock_acknowledge_on_start:
            try:
                self.interlock_acknowledge_dmc()    
            except Exception as err:
                self.log(f'WARNING: Interlock acknowledged failed with error: {err} --> skipping', color=colors.WARNING)


        if self.get_state().upper() == 'STOWED':
            self.unstow()
            self.wait_duration(5) # Workaround for a bug in the ACU, where the stow command is followed by an deactivate command, which overwrites the "activate" which would follow after the stow

        if send_default_configs:
            self.create_configs_minimal()
            
        if not self.wait_done_by_uuid:
            self.wait_duration(5)

        self.log('Getting configs from SCU')
        configs_scu_dc = self.logger_configs()
        configs_scu = [c['name'] for c in configs_scu_dc]
        
        if not 'all' in configs_scu:
            self.log('WARNING: logger config "all" is missing in SCU logger configurations', color=colors.WARNING)
        if not 'full_configuration' in configs_scu:
            self.log('WARNING: logger config "full_configuration" is missing in SCO logger configurations', color=colors.WARNING)

        self.activate_dmc()

        self.waitForStatusValue("acu.azimuth.axis_bit_status.abs_active", True, timeout=40)
        self.waitForStatusValue("acu.elevation.axis_bit_status.abs_active", True, timeout=40)
        
        if not self.wait_done_by_uuid:
            self.wait_duration(5)

        if band_start is not None:
            self.move_to_band(band_start)

        if az_start is not None:
            self.abs_azimuth(az_start, az_speed)
        if el_start is not None:
            self.abs_elevation(el_start, el_speed)

        if az_start is not None or el_start is not None or band_start is not None:
            self.wait_settle()
            self.wait_duration(3)
        self.log('=== STARTUP ROUTINE COMPLETED ===', color=colors.BOLD)

    def shutdown(self):
        """Stow, deactivate, and release command authority for antenna in order to finish before handing back the antenna
        """
        self.log('=== INITIATING SHUTDOWN ROUTINE ===', color=colors.BOLD)
        if self.get_state().upper() != 'STOWED':
            self.stow()
        if not self.wait_done_by_uuid:
            self.wait_duration(10)
        self.release_command_authority()
        if not self.wait_done_by_uuid:
            self.wait_duration(5)

        self.log('=== SHUTDOWN ROUTINE COMPLETED ===', color=colors.BOLD)


###################################################################################################
###################################################################################################
###################################################################################################

# ██     ██  █████  ██ ████████     ███████ ██    ██ ███    ██ ███████ 
# ██     ██ ██   ██ ██    ██        ██      ██    ██ ████   ██ ██      
# ██  █  ██ ███████ ██    ██        █████   ██    ██ ██ ██  ██ ███████ 
# ██ ███ ██ ██   ██ ██    ██        ██      ██    ██ ██  ██ ██      ██ 
#  ███ ███  ██   ██ ██    ██        ██       ██████  ██   ████ ███████ 
                                                                     

    def wait_track_start(self, timeout=600, query_delay=.25):
        """wait for a tracing table to start by waiting for the two axis to change 
        to state 'TRACK'

        Args:
            timeout (int, optional): timeout time in seconds. Defaults to 600.
            query_delay (float, optional): period between two checks if status has changed in seconds. Defaults to .25.
        """
        self.wait_state("acu.azimuth.state", "TRACK", timeout, query_delay)
        self.wait_state("acu.elevation.state", "TRACK", timeout, query_delay)

    # def wait_track_end(self, timeout=600, query_delay=1.):
    #     # This is to allow logging to continue until the track is completed
    #     self.log('Waiting for track to finish...')

    #     self.wait_duration(10.0, no_stout=True)  

    #     def tester():
    #         a = self.status_Value("acu.tracking.act_pt_end_index_a")
    #         b = self.status_Value("acu.tracking.act_pt_act_index_a")
    #         return (int(a) - int(b)) > 0
        

    #     self.wait_by_testfun(tester, timeout, query_delay)
    #     self.log('   -> done')

    def wait_settle(self, axis='all', timeout=600, query_delay=.25, tolerance=0.01, wait_by_pos=True, initial_delay=2.0):
        """
        alias for waitForStatusValue but mapping 'AZ', 'EL', 'FI' to 'acu.azimuth.p_act'
        'acu.elevation.p_act' and 'acu.feed_indexer.p_act'

        Periodically queries a device status 'path' until a specific value is reached.

        Args:
            path:       path of the SCU device status
            Value:      value to be reached
            timeout:    Raise TimeoutError after this duration
            query_delay: Period in seconds to wait between two queries.
        """
        
        if initial_delay > 0:
            # assures setpoint has actually been send to acu!
            self.wait_duration(initial_delay, no_stout=True)  

        dc1 = {
            'az': 'azimuth', 'el': 'elevation', 'fi': 'feed_indexer', 
            'azimuth':'azimuth', 'elevation': 'elevation', 'feed_indexer': 'feed_indexer' }
        
        if axis == 'all':
                    
            self.wait_settle('az', initial_delay=0.0)
            self.wait_settle('el', initial_delay=0.0)
            self.wait_settle('fi', initial_delay=0.0)
            self.wait_duration(0.5)

            return

        key = dc1[axis.lower()]


        if key == 'feed_indexer':
            path = 'acu.feed_indexer.state'
            self.wait_state(path, "SIP", timeout, query_delay, operator = '<=')
        else:
            
            if timeout is None:
                p_set = self.getc(f'acu.{key}.p_set')
                p_act = self.getc(f'acu.{key}.p_act')
                # print(p_set, p_act)
                p_diff = float(p_act) - float(p_set)

                if key == 'azimuth':
                    # these numbers are from a stepping test done on the MKE Simulator mid August 2023
                    p = [0.3335957 , 8.95694938] # s/° + s
                elif key == 'elevation':
                    # these numbers are from a stepping test done on the MKE Simulator mid August 2023
                    p = [0.7274147 , 5.90958871] # s/° + s

                dt = p_diff * p[0] + p[1]
                timeout = dt + 10
        
        
            if wait_by_pos:
                value = self.getc(f'acu.{key}.p_set')
                self.wait_for_pos(key, value, timeout, query_delay, tolerance)
            else:
                path = f'acu.{key}.state'
                self.wait_state(path, ['Standby', "Parked", "SIP", "TRACK"], timeout, query_delay, operator = 'IN')


    def wait_for_pos(self, axis, value, timeout=600, query_delay=.25, tolerance=None):
        """
        alias for waitForStatusValue but mapping 'AZ', 'EL', 'FI' to 'acu.azimuth.p_act'
        'acu.elevation.p_act' and 'acu.feed_indexer.p_act'

        Periodically queries a device status 'path' until a specific value is reached.

        Args:
            path:       path of the SCU device status
            Value:      value to be reached
            timeout:    Raise TimeoutError after this duration
            query_delay: Period in seconds to wait between two queries.
        """
        dc1 = {
            'az': 'azimuth', 'el': 'elevation', 'fi': 'feed_indexer', 
            'azimuth':'azimuth', 'elevation': 'elevation', 'feed_indexer': 'feed_indexer' }
        
        key = dc1[axis.lower()]
    
        if tolerance is not None:
            path = f'acu.{key}.p_shape'
            tester = lambda v: abs(v - value) < abs(tolerance)
        else:
            path = f'acu.{key}.p_shape'
            tester = lambda v: v == value

        self.wait_for_status(path, value, tester, timeout, query_delay, tolerance)


    def wait_state(self, path, value=None, timeout=600, query_delay=.5, operator = '=='):    
        """Wait for a given status at a given path using a given operator

        Args:
            path (str): the device path. Example
            value (str or int): the value to wait for
            timeout (int, optional): time in seconds after which to raise an timeout. Defaults to 600.
            query_delay (float, optional): re-query period for checking status change. Defaults to .25.
            operator (str, optional): optional operator to give '==', '!=', '<', '>' '>=', '<='. Defaults to '=='.
        """
        if value is None and path.upper() in state_dc_inv:
            value = path.upper()
            path = 'acu.general_management_and_controller.state'

        if isinstance(value, (int, str)):
            val = state_dc_inv.get(value, value)
        elif hasattr(value, '__len__'):
            val = [state_dc_inv.get(v.upper() if isinstance(v, str) else v, v) for v in value]
            errs = [v for v in val if not isinstance(v, int)]
            assert not any(errs), f'wait_state got unrecognized state: {errs}'
        else:
            val = value

        def tester(v):
            if  isinstance(v, int) or v.isnumeric():
                vv = int(v)    
            else:
                vv = state_dc_inv[v.upper()]

            if operator == '==':   return vv == val
            elif operator == '!=': return vv != val
            elif operator == '<':  return vv <  val
            elif operator == '<=': return vv <= val
            elif operator == '>':  return vv >  val
            elif operator == '>=': return vv >= val
            elif operator == 'IN': return vv in val
            else: raise Exception(str(operator) + ' is not recognized as a valid operator. Allowed are only ==, !=, <=, >=, <, >')

        self.wait_for_status(path, val, tester, timeout, query_delay)


    def waitForStatusValue(self, path, value, timeout=600, query_delay=.25, tolerance=None):
        """
        alias for wait_for_status
        queries a device status 'path' until a specific value is reached.

        Args:
            path:       path of the SCU device status
            Value:      value to be reached
            timeout:    Raise TimeoutError after this duration
            query_delay: Period in seconds to wait between two queries.
        """
        self.wait_for_status(path, value, None, timeout=timeout, query_delay=query_delay, tolerance=tolerance)


    def wait_by_testfun(self, tester, timeout=600, query_delay=1.0, no_stout=False):
        """
        Periodically queries a device status 'path' until a specific value is reached.

        Args:
            path:       path of the SCU device status
            tester:     any test function that returns true, when reached
            timeout:    Raise TimeoutError after this duration
            query_delay: Period in seconds to wait between two queries.
        """
        starttime = time.time()

        self.wait_duration(0.5, no_stout=True)    

        is_first = True
        while time.time() - starttime < timeout:            
            if tester():
                if not no_stout and not is_first:
                    self.log('  -> done', color=colors.OKBLUE)
                return True
            
            if not no_stout and is_first:
                self.log('waiting for tester to return true...', color=colors.OKBLUE)
                is_first = False
            self.wait_duration(query_delay, no_stout=True)  

        err = "Sensor: tester() not true after {}s".format(timeout)
        self.log(err, color=colors.FAIL)
        raise TimeoutError(err)


    def wait_for_status(self, path, value, tester = None, timeout=600, query_delay=.25, tolerance=None, no_stout=False):
        """
        Periodically queries a device status 'path' until a specific value is reached.

        Args:
            path:       path of the SCU device status
            Value:      value to be reached
            timeout:    Raise TimeoutError after this duration
            query_delay: Period in seconds to wait between two queries.
        """
        starttime = time.time()

        self.wait_duration(0.5, no_stout=True)    

        is_first = True
        v = 'UNKNOWN'
        
        while time.time() - starttime < timeout:
            v = self.getc(path)
            
            if tester is not None and tester(v):
                if not no_stout and not is_first:
                    self.log('  -> done', color=colors.OKBLUE)
                return True
            elif tester is None and tolerance is not None and abs(v - value) < abs(tolerance): 
                if not no_stout and not is_first:
                    self.log('  -> done', color=colors.OKBLUE)
                return True
            elif tester is None and v == value:
                if not no_stout and not is_first:
                    self.log('  -> done', color=colors.OKBLUE)
                return True

            if not no_stout and is_first:
                if isinstance(value, float):
                    self.log('wait for {}: {:.3f} (currently at: {:.3f})'.format(path, value, v), color=colors.OKBLUE)
                elif 'state' in path:
                    if not isinstance(value, str) and hasattr(value, '__len__'):
                        vv = [state_dc_all.get(vvv, vvv) for vvv in value]
                    else:
                        vv = state_dc_all.get(value, value)
                    self.log('wait for {}: {} (currently at: {})'.format(path, vv, state_dc_all.get(v, v)), color=colors.OKBLUE)
                else:
                    self.log('wait for {}: {} (currently at: {})'.format(path, value, v), color=colors.OKBLUE)

                is_first = False

            self.wait_duration(query_delay, no_stout=True)

        if 'state' in path:
            v = self.getc(path)
            v = (state_dc_all.get(v, v), v)
            if not isinstance(value, str) and hasattr(value, '__len__'):
                vv = [(state_dc_all.get(vvv, vvv), vvv) for vvv in value]
            else:
                vv = (state_dc_all.get(value, value), value)
            err = "Sensor: {} not equal to {} after {}s. Current value: {}".format(path, vv, timeout, v)
        else:
            err = "Sensor: {} not equal to {} after {}s. Current value: {}".format(path, value, timeout, v)

        self.log(err, color=colors.FAIL)
        raise TimeoutError(err)


    #wait seconds, wait value, wait finalValue
    def wait_until(self, T, no_stout=False):
        """wait until a certain time has been reached

        Args:
            T (astropy.time.Time object): timestamp until which to wait
            no_stout (bool, optional): whether or not to give feedback in stdout. Defaults to False.
        """
        tnow = self.t_internal
        
        if T < tnow:
            self.log('T={} is {} in the past! returning without waiting!'.format(T.iso, (T-tnow).to(u.s).value), color=colors.WARNING)

        else:
            # fun = lambda : self.t_internal >= T
            dt_wait = (T - tnow).to(u.s).value                
            return self.wait_duration(dt_wait, no_stout=no_stout)
        
            
    @alias('sleep', 'wait')
    def wait_duration(self, seconds, no_stout=False):
        """wait for a given amount of seconds

        Args:
            seconds (int): number of seconds to wait for
            no_stout (bool, optional): whether or not to give feedback in stdout. Defaults to False.
        """
        #wait seconds, wait value, wait finalValue
        if not no_stout:
            self.log('wait for {:.1f}s'.format(seconds), color=colors.OKBLUE)
        time.sleep(seconds)
        # if not no_stout:
        #     self.log('  -> done', color=colors.OKBLUE)



###################################################################################################
###################################################################################################
###################################################################################################
    
# ███████  ██████ ██    ██     ██       ██████   ██████   ██████  ███████ ██████       █████  ██████  ██ 
# ██      ██      ██    ██     ██      ██    ██ ██       ██       ██      ██   ██     ██   ██ ██   ██ ██ 
# ███████ ██      ██    ██     ██      ██    ██ ██   ███ ██   ███ █████   ██████      ███████ ██████  ██ 
#      ██ ██      ██    ██     ██      ██    ██ ██    ██ ██    ██ ██      ██   ██     ██   ██ ██      ██ 
# ███████  ██████  ██████      ███████  ██████   ██████   ██████  ███████ ██   ██     ██   ██ ██      ██ 
                                                                                                       
                                                                                                       
    @alias('create_configs_minimal')
    def configs_create_minimal(self):
        """
        Create the minimal set of logger configurations for SCU.
        """
        
        chans = list(set(self.get_channel_list()))
        configs_scu_dc = {d['name']: list(set(d['paths'])) for d in self.logger_configs()}

        if 'all' in configs_scu_dc:
            a = tuple(sorted(configs_scu_dc['all']))
            b = tuple(sorted(chans))
            assert a == b, f'config "all" differs from all available channels! N_scu = {len(a)} vs N_all = {len(b)}'
        else:
            self.create_logger('all', chans)

        if 'full_configuration' in configs_scu_dc:
            a = tuple(sorted(configs_scu_dc['full_configuration']))
            b = tuple(sorted(chans))
            assert a == b, f'config "full_configuration" differs from all available channels! N_scu = {len(a)} vs N_all = {len(b)}'
        else:
            self.create_logger('full_configuration', chans)

    def test_configs(self):
        configs_scu_dc = {d['name']: set(d['paths']) for d in self.logger_configs()}
        assert "all" in  configs_scu_dc, 'config "all" is missing'
        assert "full_configuration" in  configs_scu_dc, 'config "full_configuration" is missing'



    #logger functions goes here
    @alias('create_logger')
    @event_start_before_wait_done_after
    def logger_create(self, config_name, sensor_list):
        '''
        PUT create a config for logging
        Usage:
        create_logger('HN_INDEX_TEST', hn_feed_indexer_sensors)
        or 
        create_logger('HN_TILT_TEST', hn_tilt_sensors)
        '''
        self.log('create logger')
        uuid = self.scu_put('/datalogging/config', 
            {'name': config_name,
            'paths': sensor_list})

        return uuid
    
    alias('delete_logger')
    def logger_delete(self, config_name):
        '''
        DELETE a config for logging
        
        '''
        self.log(f'logger_delete logger {config_name=}')
        loggers = self.logger_configs()
        matching_logger_uuids = [logger.get('uuid') for logger in loggers if logger.get('name') == config_name]

        uuid = ''
        for logger_uuid in matching_logger_uuids:
            self.log(f'deleting logger with uuid={logger_uuid}')
            uuid = self.scu_delete(f'/datalogging/config?id={logger_uuid}')
            self.wait_duration(0.1)

        return uuid
    
    

    '''unusual does not take json but params'''
    # @event_start_before_wait_done_after
    @alias('start_logger')
    def logger_start(self, config_name='full_configuration', stop_if_need=True):
        """start logging with a given logging config.
        The logging config must have been registered prior. (see self.start() method)

        Args:
            config_name (str, optional): Config to use for logging. Defaults to 'normal'.
            stop_if_need (bool, optional): _description_. Defaults to True.
        """
        
            # Start data recording
        if stop_if_need and self.logger_state() != 'STOPPED':
            self.log('WARNING, logger already recording - attempting to stop and start a fresh logger...', color=colors.WARNING)
            self.stop_logger()  
            self.wait_duration(5)

        if self.logger_state() == 'STOPPED':
            self.log('Starting logger with config: {} ...'.format(config_name))
            # for some reason no uuid here
            uuid = self.scu_put('/datalogging/start', params='configName=' + config_name, get_uuid=False)
        else:
            raise Exception(f'Can not start logging, since logging state != "STOPPED" (actual state: "{self.logger_state()}"')

        return uuid
    
    # @event_start_before_wait_done_after
    @alias('stop_logger')
    def logger_stop(self, verb=True):
        """stop logging, will raise HTTPError: 412 if logging is not running

        Returns:
            request.model.Response: response object from this call (useless for anything but ID and returncode checking)
        """
        self.log('logger stop')
        # for some reason no uuid here
        uuid = self.scu_put('/datalogging/stop')
        
        if verb:
            r = self.session_last()
            uuid = r.get('uuid')
            self.log(f'logger stop...success (last_session={r})')

        return uuid
    

    def logger_state(self):
        """get current logger state

        Returns:
            str: "RUNNING" or "STOPPED"
        """
#        self.log('logger state ')
        r = self.scu_get('/datalogging/currentState')
        #self.log(r.json()['state'])
        return(r.json()['state'])

    def logger_configs(self):
        """GET all config names
        """
        self.log('logger configs ')
        r = self.scu_get('/datalogging/configs')
        return(r.json())


    def logger_sessions(self):
        '''
        GET all sessions
        '''
        warnings.warn(
            "Legacy Function: This is not maintained and might not work as intended",
            DeprecationWarning
        )
        self.log('logger sessions ')
        r = self.scu_get('/datalogging/sessions')
        return r.json()
    
###################################################################################################
###################################################################################################
###################################################################################################

# ███████ ███████ ███████ ███████ ██  ██████  ███    ██      █████  ██████  ██ 
# ██      ██      ██      ██      ██ ██    ██ ████   ██     ██   ██ ██   ██ ██ 
# ███████ █████   ███████ ███████ ██ ██    ██ ██ ██  ██     ███████ ██████  ██ 
#      ██ ██           ██      ██ ██ ██    ██ ██  ██ ██     ██   ██ ██      ██ 
# ███████ ███████ ███████ ███████ ██  ██████  ██   ████     ██   ██ ██      ██ 
                                                                             

    @alias('last_session')
    def session_last_id(self, no_log = False):
        '''
        GET last session id as integer
        '''
        return int(self.session_last(no_log=no_log)['uuid'])
    

    def session_last(self, no_log = False):
        '''
        GET last session as dict
        '''
        if not no_log:
            self.log('Last sessions ')
        r = self.scu_get('/datalogging/lastSession')
        if r.status_code == 404 and 'no datalog sessions found' in r.text.lower():
            return -1
        
        return r.json()
    
    def session_query(self, id):
        '''
        GET specific session only - specified by id number
        Usage:
        session_query('16')
        '''
        warnings.warn(
            "Legacy Function: This is not maintained and might not work as intended",
            DeprecationWarning
        )

        self.log(f'logger session query id "{id}"')
        r = self.scu_get('/datalogging/session',
            {'id': id})
        return r.json()


    @alias('export_session')
    @deprecated("LEGACY function: Do not use! Use self.session_last() or self.session_query(session_id) instead!")
    def session_export(self, id = 'last', interval_ms=100):
        '''
        LEGACY function: Do not use!

        EXPORT specific session - by id and with interval
        output r.text could be directed to be saved to file 
        Usage: 
        export_session('16',1000)
        or export_session('16',1000).text 
        '''
        self.log('export session ')
        if interval_ms is None and not hasattr(self, 'telescope'):
            interval_ms = 100

        if id == 'last':
            id = self.last_session()

        r = self.scu_get('/datalogging/exportSession',
            params = {'id': id, 
                'interval_ms' : interval_ms})
        return r

    #sorted_sessions not working yet

    def sorted_sessions(self, isDescending = 'True', startValue = '1', endValue = '25', sortBy = 'startTime', filterType='indexSpan'):
        self.log(f'getting sortedSessions with {startValue=}, {endValue=}, {filterType=}')

        r = self.scu_get('/datalogging/sortedSessions',
            {'isDescending': isDescending,
            'startValue': startValue,
            'endValue': endValue,
            'filterType': filterType, #STRING - indexSpan|timeSpan,
            'sortBy': sortBy})
        return r
    
    def _session_make_index_table(self, startValue, endValue, descending, sortBy, filterType, as_df, map_types):

        isDescending = 'True' if descending else 'False'
        r = self.sorted_sessions(isDescending=isDescending, startValue=str(startValue), endValue=str(endValue), sortBy=sortBy, filterType=filterType)
        rows = self._feedback(r, get_uuid=False).json()

        if map_types:
            for r in rows:
                r['uuid'] = int(r['uuid'])
                r['startTime'] = parse_zulutime(r['startTime'])
                r['stopTime'] = parse_zulutime(r['stopTime'])
                r['duration'] = parse_timedelta(r['duration'])
                r['configId'] = int(r['configId'])
                
        return pd.DataFrame(rows) if as_df else rows

    # http://10.96.65.10:8080/datalogging/filteredSessions?filterType=timeSpan&startValue=2024-11-20&endValue=2024-11-22
    def session_get_table_time(self, t0 = None, t1 = None, descending=False, sort_by = 'startTime', as_df=True, map_types=True):
        """
        Retrieves a list of session information between two dates.

        Args:
            t0: start time (best in iso string format).
            t1: end time (best in iso string format).
            descending: Whether to sort the results in descending order.
            sort_by: The field to sort the results by.
            as_df: Whether to return the results as a Pandas DataFrame.
            map_types: Whether to convert the string types to python types such as int timedelta and datetime.

        Returns:
            A list of dictionaries, each representing a session, or a Pandas DataFrame if `as_df` is True.
        """

        if t1 is None:
            t1 = get_utcnow()
        t1 = anytime2datetime(t1)

        if t0 is None:
            t0 = t1 - datetime.timedelta(days=1)
        t0 = anytime2datetime(t0)
        
        t0, t1 = min(t0, t1), max(t0, t1)
        t0 = make_zulustr(t0) # .split('T')[0]
        t1 = make_zulustr(t1) # .split('T')[0]

        return self._session_make_index_table(t0, t1, descending, sort_by, filterType='timeSpan', as_df=as_df, map_types=map_types)
    



    def session_get_table_index(self, i_start = None, i_end = None, descending=False, sort_by = 'startTime', as_df=True, map_types=True):
        """
        Retrieves a paginated list of session information.

        Args:
            i_start: first session uuid to include.
            i_end: last session uuid to include.
            descending: Whether to sort the results in descending order.
            sort_by: The field to sort the results by.
            as_df: Whether to return the results as a Pandas DataFrame.
            map_types: Whether to convert the string types to python types such as int timedelta and datetime.

        Returns:
            A list of dictionaries, each representing a session, or a Pandas DataFrame if `as_df` is True.
        """
        if i_end is None:
            i_end = self.session_last_id(no_log=True)
        
        if i_start is None:
            i_start = max(1, int(i_end) - 100)

        return self._session_make_index_table(i_start, i_end, descending, sort_by, filterType='indexSpan', as_df=as_df, map_types=map_types)

    def get_session_as_text(self, interval_ms=100, session = 'last'):
        """Download and return a session log in original text form

        Args:
            interval_ms (int, optional): sampling interval in milliseconds. Defaults to 1000.
            session (str, optional): session id to save either string with number or 'last'. Defaults to 'last'.

        Returns:
            str: the raw text as downloaded from the SCU
        """

        self.log('Attempt export of session: "{}" at rate {} ms'.format(session, interval_ms))
        if session == 'last':
            #get all logger sessions, may be many
            # r = self.logger_sessions()
            #[-1] for end of list, and ['uuid'] to get id of last session in list
            session = self.last_session()
        self.log('Session id: {} '.format(session))

        file_txt = self.export_session(session, interval_ms).text
        return file_txt

    def get_session_as_df(self, session = 'last', interval_ms=100):
        """Download and return a session log as pandas dataframe

        Args:
            session (str, optional): session id to save either string with number or 'last'. Defaults to 'last'.
            interval_ms (int, optional): sampling interval in milliseconds. Defaults to 1000.
        Raises:
            Exception: on unknown format returned by the SCU for the log file it will raise an generic exception

        Returns:
            pandas.DataFrame: a dataframe with the time column (datetime UTC) as index.
        """

        file_txt = self.get_session_as_text(interval_ms=interval_ms, session = session)

        self.log(f'Received a session text file with {len(file_txt)} chars. Will load as dataframe now...', color=colors.OKBLUE)
        buf = StringIO(file_txt)
        columns = None

        for i in range(100):
            linestart = buf.tell()
            s = buf.readline()
            if s.strip().startswith(';acu.') or s.strip().startswith('Date/Time;acu.'):
                columns = s
                buf.seek(linestart)
                break

        if columns is None: 
            raise Exception("The return format of the acu was not recognized. Here is the first 1000 chars:" + file_txt[:1000]) 

        df = pd.read_csv(buf, sep=';', index_col=0)


        if 'Unnamed: 0' in df:
            df = df.set_index('Unnamed: 0')

        t_ptp = pd.to_datetime(Time(df['acu.time.external_ptp'], format='mjd').to_datetime(timezone=datetime.timezone.utc))

        df.index = pd.to_datetime(df.index, errors='coerce')
        t_offset_max = (pd.Series(df.index) - t_ptp).abs().max().total_seconds()

        if t_offset_max > 1:
            warnings.warn(f'Loaded session data timestamps deviate from PTP time by {t_offset_max=} seconds. This has no impact on analysis, since ptp time will be used as index')

        df = df.set_index(t_ptp, drop=False)
        self.log(f'Sucessfully loaded {session=} as DataFrame with {df.shape=}', color=colors.OKBLUE)
        return df

                        
    # def save_session(self, path_to_save, interval_ms=1000, session = 'last'):
    #     """Download and save a session to the filesystem

    #     Args:
    #         path_to_save (str): path on local filesys to save the session to
    #         interval_ms (int, optional): sampling interval in milliseconds. Defaults to 1000.
    #         session (str, optional): session id to save either string with number or 'last'. Defaults to 'last'.
    #     """
        
        
    #     file_txt = self.get_session_as_text(interval_ms, session)

    #     folder = os.path.dirname(path_to_save)
    #     if os.path.exists(folder) == 0:
    #         self.log(folder + " does not exist. making new dir", color=colors.WARNING)
    #         os.mkdir(folder)
            
    #     self.log(f'Saving Session as log file to: "{path_to_save}"', color=colors.BOLD)    
    #     with open(path_to_save, 'a+') as f:
    #         f.write(file_txt)
        
        
    #Simplified one line commands particular to test section being peformed 

    
    

###################################################################################################
###################################################################################################
###################################################################################################

# ██████   ██████  ██ ███    ██ ████████ ██ ███    ██  ██████       █████  ██████  ██ 
# ██   ██ ██    ██ ██ ████   ██    ██    ██ ████   ██ ██           ██   ██ ██   ██ ██ 
# ██████  ██    ██ ██ ██ ██  ██    ██    ██ ██ ██  ██ ██   ███     ███████ ██████  ██ 
# ██      ██    ██ ██ ██  ██ ██    ██    ██ ██  ██ ██ ██    ██     ██   ██ ██      ██ 
# ██       ██████  ██ ██   ████    ██    ██ ██   ████  ██████      ██   ██ ██      ██ 
                                                                                    
                                                                                    

    @event_start_before_wait_done_after
    def __point_toggle(self, action, select):

        uuid = self.scu_put("/devices/command", payload={"path": "acu.pointing_controller.pointing_correction_toggle",
                    "params": {"action": str(action), "select": str(select)}})
        return uuid
        
    def point_all_ON(self):
        self.__point_toggle(1, '1')

    def point_all_OFF(self):
        self.__point_toggle(0, '1')
    
    def point_tilt_ON(self):
        self.__point_toggle(1, '10')

    def point_tilt_OFF(self):
        self.__point_toggle(0, '10')

    def point_AT_ON(self):
        self.__point_toggle(1, '11')
    
    def point_AT_OFF(self):
        self.__point_toggle(0, '11')
    
    def point_refr_ON(self):
        self.__point_toggle(1, '12')
    
    def point_refr_OFF(self):
        self.__point_toggle(0, '12')
    
    def point_spem_ON(self):
        self.__point_toggle(1, '20')
    
    def point_spem_OFF(self):
        self.__point_toggle(0, '20')
    

    def point_spem_set(self, params:dict, band = 'all', activate = True, set_rest_zero=True, wait_for_set=False, no_stdout=False):
        """set new pointing model parameters to a specific band in ArcSec

        Args:
            params (list): list of parameters (must be of length 9 only contain numbers and in ArcSeconds)
            band (int, optional): the band to set these values to (1...7). Defaults to 1.
            activate (bool, optional): whether or not ton directly activate after setting (there seems to be an error currently). Defaults to False.
        """

        n_timouts = 0
        ready = False
        while not ready:
            try:
                fi_pos = self.get_state('acu.general_management_and_controller.feed_indexer_pos')
                params_old = self.point_spem_get()

                if band == 'all':
                    bands = bands_dc.values()
                else:
                    bands = [band]

                for i, b in enumerate(bands):
                    is_last = i+1 == len(bands)

                    if isinstance(b, str):
                        assert b in bands_dc, f'ERROR: Band "{b}" not in allowed bands: ' + str(bands_dc)
                        bandi = bands_dc[b]
                    else:
                        assert b in bands_dc_inv, f'ERROR: Band {b} not in allowed bands: ' + str(bands_dc_inv)
                        bandi = b

                    assert isinstance(params, dict), 'this version of the SCU lib does only accept dict parameters'
                    assert np.all([isinstance(k, str) for k in params.keys()]), 'dict keys must be strings in the form "P1"..."P9", but given was: ' + ', '.join(params.keys())
                    
                    params = {k.upper():v for k, v in params.items()}
                    param_name_map = self.spem_param_name_map
                    unknown_params = [p for p in params if not p in param_name_map]

                    # remove senseless params
                    senseless_params = [p for p in unknown_params if not params.get(p)]
                    unknown_params = [p for p in unknown_params if not p in senseless_params]

                    if senseless_params:
                        self.log(f'found unknown parameters which evaluated to zero --> Will remove them now. The parameters in question are: {senseless_params}', color=colors.WARNING)
                    
                    assert not unknown_params, f'Found unknown parameters only {" ".join([k for k in param_name_map])} is allowed, but given was: ' + ', '.join(unknown_params.keys())

                    d = {param_name_map[k]:v for k, v in params.items()}
                    if set_rest_zero:
                        d = {**{k:0 for k in self.spem_keys}, **d}
                    else:
                        if band != 'all' and bands_dc_inv[bandi] != str(fi_pos) and len(d) != 18:
                            raise ValueError("can not set a partial pointing model for a feed indexer position which is currently not in focus! Need to position the Feed indexer first and then set the Pointing model or provide a full model!")
                        elif len(d) != 18:
                            params = {**params_old, **params}
                            dold = {param_name_map[k]:v for k, v in params_old.items()}
                            d = {**dold, **d}

                    
                        
                    d['band_information'] = str(bandi)

                    path = 'acu.pointing_controller.set_static_pointing_model_parameters'
                    payload = {'path': path, "params": d}
                    if self.debug:
                        self.log('setting pointing model with payload: ' + json.dumps(payload))

                    if is_last and not no_stdout:
                        self.log('setting pointing model to band "{}". Params: {}'.format(band, params), color=colors.OKBLUE)

                    uuid = self.scu_put('/devices/command', payload=payload)
                    if self.wait_done_by_uuid:
                        self.wait_uuid_done(uuid, f'set_spem_{bandi}')
                    else:
                        self.wait_duration(0.5)
                if wait_for_set:
                    if band != 'all' and bands_dc_inv[bandi] != str(fi_pos):
                        self.log('Can not wait for pointing model parameters to be set, because the feed indexer is in the wrong position. Will return without waiting! band_is = {} vs band_set = {}'.format(fi_pos, bandi), color=colors.WARNING)
                    else:                        
                        for k, v in params.items():
                            delay = wait_for_set if not isinstance(wait_for_set, bool) and wait_for_set > 0 else 0.5
                            self.wait_for_status('acu.pointing.' + k.lower(), v, query_delay=delay, timeout=5, no_stout=no_stdout)
                        if not no_stdout:
                            self.log(f'Pointing model {params} has been set successfully!', color=colors.OKGREEN)

                if activate:
                    self.point_spem_ON()

                ready = True
            except TimeoutError as terr:
                n_timouts += 1
                if n_timouts > 3:
                    self.log('ERROR: ' + str(terr), colors.FAIL)
                    raise
            

    def point_spem_get(self):
        """get channels for the pointing model parameters"""
        param_keys = list(self.spem_param_name_map.keys())
        pathes = {k:f'acu.pointing.' + k.lower() for k in param_keys}
        # return dict(zip(pathes.keys(), self.getc(list(pathes.values()))))
        dc = self.getc(list(pathes.values()), as_dict=True)
        return {k:dc[p] for k, p in pathes.items()}
        
    @event_start_before
    def point_AT_set(self, p_at_azel, band = 'all', activate=False, wait_for_set=True):
        """Set new values to the ambient temperature correction values in arcseconds for a specific band

        Args:
            p_at_azel (ambient_temperature_factor_az, ambient_temperature_factor_el) (float): factors for temp correction in ArcSec/deg-C
            band (int|str, optional): the band to set these values to (1...7). Defaults to 0.
            activate (bool, optional): whether or not ton directly activate after setting (there seems to be an error currently). Defaults to False.
        """
        # TG 2023-09-07 seems to work with MKE
        # self.log('WARNING! setting an ambient temp correction model currently has errors in SCU and may not work as intended!', color=colors.WARNING)
        
        if band == 'all':
            bands = self.bands_possible.values()
        else:
            bands = [band]

        bd = {k:v for k, v in bands_dc.items() if k.lower().strip().startswith('band')}
        bd_inv = {v:k for k, v in bd.items()}

        for bandi in bands:
            if isinstance(bandi, str):
                assert bandi in bd and bandi.lower().strip().startswith('band'), f'ERROR: Band "{bandi}" not in allowed bands: ' + str(bd)
                bandi = bd[bandi]
            else:
                assert bandi in bd_inv, f'ERROR: Band {bandi} not in allowed bands: ' + str(bd_inv)
                assert bd_inv[bandi].lower().strip().startswith('band'), f'ERROR: Band "{bd_inv[bandi]}" not in allowed bands: ' + str(bd)
                bandi = bandi

            assert int(bandi) in bd_inv, "The given band was not pound in the possible bands for this scu. See scu.bands_possible for further info"

            d = {   'ambient_temperature_factor_az': p_at_azel[0],
                    'ambient_temperature_factor_el': p_at_azel[1],
                    'band_information': str(bandi)}
            
            path = 'acu.pointing_controller.ambient_temperature_correction_setup_values'
            uuid = self.scu_put('/devices/command', payload={'path': path, "params": d})
            
            if wait_for_set:
                if self.wait_done_by_uuid:
                    self.wait_uuid_done(uuid, 'point_AT_set')
                else:
                    fun = lambda: self.point_AT_get(band=bandi) == tuple(p_at_azel)
                    delay = wait_for_set if not isinstance(wait_for_set, bool) and wait_for_set > 0 else 0.5
                    self.wait_by_testfun(fun, query_delay=delay, timeout=10)
            
        if wait_for_set:
            self.log(f'AT correction model {p_at_azel} for band {band} has been set successfully!', color=colors.OKGREEN)

        if activate:
            self.point_AT_ON()

        return uuid
        
    def point_AT_get(self, band = 'current'):
        """get the ambient temperature correction coefficients for the band in question

        Args:
            band (str, optional): either 'all' or current, or a specific band name, sich as 'Band 5c'. Defaults to 'current'.

        Returns:
            if band == 'all' a dictionary of all coefficients, else a tuple with the two coefficients for az and el
        """

        channels = [
            'acu.ambient_temp_correction_config.ambient_factor_az_band_1',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_2',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_3',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_4',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_5a',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_5b',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_5c',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_8',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_9',
            'acu.ambient_temp_correction_config.ambient_factor_az_band_10',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_1',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_2',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_3',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_4',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_5a',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_5b',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_5c',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_8',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_9',
            'acu.ambient_temp_correction_config.ambient_factor_el_band_10'
            # 'acu.pointing.amb_temp_corr_val_az',
            # 'acu.pointing.amb_temp_corr_val_el',
            # 'acu.pointing.amb_temp_corr_filter_constant'
        ]

        vals = self.getc(channels, as_dict=True)
        if band == 'all':
            return vals
        elif band == 'current':
            b = self.get_band_in_focus(as_name=True)
            assert b, 'Current Band is None or empty. This should not be for getting AT with the current band!'
            b = b.lower().replace(' ', '_')
            v = tuple([v for p, v in vals.items() if p.endswith(b)])
            return v[0], v[1]
        else:
            b = bands_dc_inv[band] if band in bands_dc_inv else band
            b = b.lower().replace(' ', '_')
            v = tuple([v for p, v in vals.items() if p.endswith(b)])
            assert len(v) >= 2, f'input band "{b}" is not a valid input for an AT model'
            return v[0], v[1]
            
###################################################################################################
###################################################################################################
###################################################################################################
        
#  ██████  ███████ ████████     ██ ███    ██ ███████ ██      ██    ██ ██   ██ 
# ██       ██         ██        ██ ████   ██ ██      ██      ██    ██  ██ ██  
# ██   ███ █████      ██        ██ ██ ██  ██ █████   ██      ██    ██   ███   
# ██    ██ ██         ██        ██ ██  ██ ██ ██      ██      ██    ██  ██ ██  
#  ██████  ███████    ██        ██ ██   ████ ██      ███████  ██████  ██   ██ 
                                                                            
                                                                            

    def get_from_scu_influx_dt(self, dt_seconds, token=None, org = 'OHBDC', timeout=360_000, channels = None, sample_rate=None, verb = 0):
        """
        Fetches data from SCU InfluxDB for a specified duration before the current time.

        Args:
            dt_seconds (int): The duration in seconds before the current time for which data is to be fetched.
            token (str, optional): The authentication token for InfluxDB. Defaults to None.
            org (str, optional): The organization name in InfluxDB. Defaults to 'OHBDC'.
            timeout (int, optional): The timeout duration for the InfluxDB query. Defaults to 360_000.
            channels (list, optional): The list of channels for which data is to be fetched. Defaults to None.
            sample_rate (float, optional): The desired sample rate for the data. Defaults to None.
            verb (int, optional): The verbosity level for logging. Defaults to 0.

        Returns:
            pandas.DataFrame: A DataFrame containing the fetched data.
        """
        tend = Time.now()
        tstart = tend - dt_seconds * u.s
        return self.get_from_scu_influx(tstart, tend, token=token, org = org, timeout=timeout, channels = channels, sample_rate=sample_rate, verb = verb)


    def get_from_scu_influx(self, tstart, tend, token=None, org = 'OHBDC', timeout=360_000, channels = None, sample_rate=None, verb = 0):
        """
        Fetches data from SCU InfluxDB within a specified time range.

        Parameters:
            tstart (Time or datetime.datetime): The start of the time range.
            tend (Time or datetime.datetime): The end of the time range.
            token (str, optional): The InfluxDB authentication token. If not provided, it will be fetched from self.influx_token.
            org (str, optional): The InfluxDB organization. Default is 'OHBDC'.
            timeout (int, optional): The timeout for the InfluxDB client. Default is 360_000.
            channels (list, optional): The list of channels to fetch data from. If not provided, it will be fetched from self.get_channel_list.
            sample_rate (int, optional): The sample rate for the data. If not provided or less than or equal to 0, it will be set to 1.
            verb (int, optional): The verbosity level. If greater than 0, it will print the query. Default is 0.

        Returns:
            pandas.DataFrame: A DataFrame containing the fetched data.
        """

        if 'InfluxDBClient' not in locals():
            from influxdb_client import InfluxDBClient
        
        if token is None and hasattr(self, 'influx_token') and self.influx_token:
            token = self.influx_token
        
        if not channels:
            channels = self.get_channel_list()

        sample_rate = 1 if sample_rate is None or sample_rate <= 0 else sample_rate
        chans_s = ', '.join([f'"{s}"' for s in channels])
        temp = "{}"
        base_query= f"""
        from(bucket: "SCU")
        |> range(start: {temp}, stop: {temp})
        |> filter(fn: (r) => r["_measurement"] == "device_status")
        |> filter(fn: (r) => r["device"] == "acu")
        |> sample(n: {sample_rate}, pos: 0)
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", {chans_s}])
        """
        
            

        if isinstance(tstart, Time):
            tstart = make_zulustr(tstart.datetime, remove_ms=False)
        elif isinstance(tstart, datetime.datetime):
            tstart = make_zulustr(tstart, remove_ms=False)

        if isinstance(tend, Time):
            tend = make_zulustr(tend.datetime, remove_ms=False)
        elif isinstance(tstart, datetime.datetime):
            tend = make_zulustr(tend, remove_ms=False)

        url = f'http://{self.ip}:8086'
        client = InfluxDBClient(url, token, org=org, debug = False, timeout=timeout)

        query = base_query.format(tstart, tend)

        if verb:
            self.log(query)

        df = client.query_api().query_data_frame(query)
        df = df.drop(columns=['result', 'table'])
        df = df.rename(columns={'_time':'time'})
        df = df.set_index('time')

        return df
    
    
    def get_from_scu_influx_dt_batched(self, dt_seconds, token=None, org = 'OHBDC', timeout=360_000, channels = None, sample_rate=None, verb = 0):
        """
        Fetches data from SCU Influx over a specified time duration.

        Args:
            dt_seconds (int): The duration in seconds for which to fetch data.
            token (str, optional): The authentication token. Defaults to None.
            org (str, optional): The organization name. Defaults to 'OHBDC'.
            timeout (int, optional): The timeout duration in milliseconds. Defaults to 360_000.
            channels (list, optional): The list of channels to fetch data from. Defaults to None.
            sample_rate (float, optional): The sample rate. Defaults to None.
            verb (int, optional): The verbosity level. Defaults to 0.

        Yields:
            generator: A generator that yields data fetched from SCU Influx in batches.
        """
        tend = Time.now()
        tstart = tend - dt_seconds * u.s
        for tmp in self.get_from_scu_influx_batched(tstart, tend, token=token, org = org, timeout=timeout, channels = channels, sample_rate=sample_rate, verb = verb):
            yield tmp



    def get_from_scu_influx_batched(self, tstart, tend, token=None, org = 'OHBDC', timeout=360_000, channels = None, batch_size=1000, sample_rate=None, verb=0):
        """
        Fetches data from SCU InfluxDB in batches.

        Args:
            tstart (Time or datetime.datetime): The start time of the data range.
            tend (Time or datetime.datetime): The end time of the data range.
            token (str, optional): The InfluxDB authentication token. If not provided, it will be fetched from self.influx_token.
            org (str, optional): The InfluxDB organization. Defaults to 'OHBDC'.
            timeout (int, optional): The timeout for the InfluxDB client. Defaults to 360_000.
            channels (list, optional): The list of channels to fetch data from. If not provided, it will be fetched from self.get_channel_list.
            batch_size (int, optional): The number of data points to fetch in each batch. Defaults to 1000.
            sample_rate (int, optional): The sample rate for the data. If not provided or less than or equal to 0, it will be set to 1.
            verb (int, optional): The verbosity level. If set to a truthy value, it will print the query. Defaults to 0.

        Yields:
            pandas.DataFrame: A DataFrame containing a batch of data.
        """
        
        if 'InfluxDBClient' not in locals():
            from influxdb_client import InfluxDBClient

        if token is None and hasattr(self, 'influx_token') and self.influx_token:
            token = self.influx_token

        if not channels:
            channels = self.get_channel_list()

        sample_rate = 1 if sample_rate is None or sample_rate <= 0 else sample_rate
        chans_s = ', '.join([f'"{s}"' for s in channels])
        temp = "{}"
        base_query= f"""
        from(bucket: "SCU")
        |> range(start: {temp}, stop: {temp})
        |> filter(fn: (r) => r["_measurement"] == "device_status")
        |> filter(fn: (r) => r["device"] == "acu")
        |> sample(n: {sample_rate}, pos: 0)
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", {chans_s}])
        |> limit(n: {batch_size}, offset: {temp})
        """

        if isinstance(tstart, Time):
            tstart = make_zulustr(tstart.datetime, remove_ms=False)
        elif isinstance(tstart, datetime.datetime):
            tstart = make_zulustr(tstart, remove_ms=False)

        if isinstance(tend, Time):
            tend = make_zulustr(tend.datetime, remove_ms=False)
        elif isinstance(tend, datetime.datetime):
            tend = make_zulustr(tend, remove_ms=False)

        url = f'http://{self.ip}:8086'
        client = InfluxDBClient(url, token, org=org, debug = False, timeout=timeout)

        offset = 0
        while True:
            query = base_query.format(tstart, tend, offset)
                
            if verb:
                self.log(query)
                
            df = client.query_api().query_data_frame(query)
            if df.empty:
                break
            df = df.drop(columns=['result', 'table'])
            df = df.rename(columns={'_time':'time'})
            df = df.set_index('time')
            yield df
            offset += batch_size
    
###################################################################################################
###################################################################################################
###################################################################################################

# ██     ██ ███████ ██████      ███████  ██████   ██████ ██   ██ ███████ ████████ 
# ██     ██ ██      ██   ██     ██      ██    ██ ██      ██  ██  ██         ██    
# ██  █  ██ █████   ██████      ███████ ██    ██ ██      █████   █████      ██    
# ██ ███ ██ ██      ██   ██          ██ ██    ██ ██      ██  ██  ██         ██    
#  ███ ███  ███████ ██████      ███████  ██████   ██████ ██   ██ ███████    ██    
                                                                                
                                                                                


    def sock_stream(self, channels=None):
        """connect to the websocket of the acu, request some measurement channels and stream them continiously. 
        use with for loop. 

        for t, fields in obj.sock_stream():
           print(t.iso, fields)

        Args:
            channels (list of strings or None): None for all channels available, else list of channel names to request

        Yields:
            tuple: Time, dict[channel_name, val]
        """
        

        _log = logging.getLogger('sock_stream')
        host, port = self.ip, self.port

        url = f'ws://{host}:{port}/wsstatus'

        if not channels:
            channels = self.get_channel_list()
            _log.debug('Creating new connection...')

        with ws_sync_connect(url) as ws:

            out = json.dumps(channels)
            _log.info(f"{self} | requesting n={len(channels)} channels from ACU")
            _log.debug(f"{self} | requesting {out}")
            ws.send(out)
                
            is_first = True
            while True:
            # listener loop

                if is_first:
                    _log.info('Staring data stream...')

                reply = ws.recv()

                if is_first:
                    is_first = False
                    _log.info('Stream data OK. Continuing to stream data...')

                data = json.loads(reply)
                ts = Time(data['timestamp'])

                fields = {k:v[0] for k, v in data['fields'].items()}
                yield ts, fields


    async def sock_stream_async(self, channels=None):
        """connect to the websocket of the acu, request some measurement channels and stream the data. 
        use with an async for loop. 

        async for t, fields in obj.sock_stream_async():
           print(t.iso, fields)

        Args:
            channels (list of strings or None): None for all channels available, else list of channel names to request

        Yields:
            tuple: Time, dict[channel_name, val]
        """
        

        _log = logging.getLogger('sock_stream_async')
        host, port = self.ip, self.port

        url = f'ws://{host}:{port}/wsstatus'

        if not channels:
            channels = self.get_channel_list()

        _log.debug('Creating new connection...')

        async with websockets.connect(url) as ws:

            out = json.dumps(channels)
            _log.info(f"{self} | requesting n={len(channels)} channels from ACU")
            _log.debug(f"{self} | requesting {out}")
            await ws.send(out)
                
            is_first = True
            while True:
            # listener loop
                if is_first:
                    _log.info('Staring data stream...')

                reply = await ws.recv()

                if is_first:
                    is_first = False
                    _log.info('Stream data OK. Continuing to stream data...')

                data = json.loads(reply)

                ts = Time(data['timestamp'])

                fields = {k:v[0] for k, v in data['fields'].items()}
                yield ts, fields




    def sock_listen_forever(self, channels=None, ping_timeout=10, sleep_time=30):
        gen = self.sock_listen_forever_async(channels, ping_timeout=ping_timeout, sleep_time=sleep_time)

        loop = asyncio.get_event_loop()
        while 1:
            yield loop.run_until_complete(gen.__anext__())


    async def sock_listen_forever_async(self, channels=None, ping_timeout=10, sleep_time=30):
        """connect to the websocket of the acu, request some measurement channels and listen forver on it. 
        use with an async for loop. 

        async for t, fields in obj.sock_listen_forever():
           print(t.iso, fields)

        Args:
            channels (list of strings or None): None for all channels available, else list of channel names to request
            ping_timeout (int, optional): timeout for the ping to keep a connection alive. Defaults to 10.
            sleep_time (int, optional): timeout between reconnection attempts. Defaults to 30.

        Yields:
            tuple: Time, dict[channel_name, val]
        """
        

        _log = logging.getLogger('listen_forever')
        host, port = self.ip, self.port

        url = f'ws://{host}:{port}/wsstatus'

        if not channels:
            channels = self.get_channel_list()


        while True:
        # outer loop restarted every time the connection fails
            has_err = False
            _log.debug('Creating new connection...')
            try:
                async with websockets.connect(url) as ws:

                    out = json.dumps(channels)
                    _log.info(f"{self} | requesting n={len(channels)} channels from ACU")
                    _log.debug(f"{self} | requesting {out}")
                    await ws.send(out)
                        
                    is_first = True
                    while True:
                    # listener loop
                        try:
                            if is_first:
                                _log.info('Staring data stream...')

                            reply = await ws.recv()

                            if is_first:
                                is_first = False
                                _log.info('Stream data OK. Continuing to stream data...')

                            if has_err:
                                has_err = False
                                _log.info('Stream data OK, keeping connection alive...')

                        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                            try:
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=ping_timeout)
                                _log.info('Ping OK, keeping connection alive...')
                                continue
                            except:
                                _log.warn(
                                    'Ping error - retrying connection in {} sec (Ctrl-C to quit)'.format(sleep_time))
                                await asyncio.sleep(sleep_time)
                                has_err = True
                                break

                        data = json.loads(reply)

                        ts = Time(data['timestamp'])

                        fields = {k:v[0] for k, v in data['fields'].items()}
                        yield ts, fields

            except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                _log.warn(
                    'TimeoutError error - retrying connection in {} sec (Ctrl-C to quit)'.format(sleep_time))
                await asyncio.sleep(sleep_time)
                has_err = True
                continue
            except socket.gaierror:
                _log.warn(
                    'Socket error - retrying connection in {} sec (Ctrl-C to quit)'.format(sleep_time))
                await asyncio.sleep(sleep_time)
                has_err = True
                continue
            except ConnectionRefusedError:
                _log.warn('Nobody seems to listen to this endpoint. Please check the URL.')
                _log.warn('Retrying connection in {} sec (Ctrl-C to quit)'.format(sleep_time))
                await asyncio.sleep(sleep_time)
                continue

###################################################################################################
###################################################################################################
###################################################################################################            

#  ██████  ██████  ███    ██ ██    ██ ███████ ███    ██ ██ ███████ ███    ██  ██████ ███████ 
# ██      ██    ██ ████   ██ ██    ██ ██      ████   ██ ██ ██      ████   ██ ██      ██      
# ██      ██    ██ ██ ██  ██ ██    ██ █████   ██ ██  ██ ██ █████   ██ ██  ██ ██      █████   
# ██      ██    ██ ██  ██ ██  ██  ██  ██      ██  ██ ██ ██ ██      ██  ██ ██ ██      ██      
#  ██████  ██████  ██   ████   ████   ███████ ██   ████ ██ ███████ ██   ████  ██████ ███████ 
                                                                                           
                                                                                           

    def time_test_dt(self, reference='local', verb=1):
        """
        Measures the time difference between the reference and the dish as t_ref - t_dish
            negative: dish ahead of reference
            positive: dish behind of reference

        Args:
            reference (str, optional): The reference time source. Can be 'ntp1', 'ntp2', or 'local'.
                'ntp1' first NTP server in the KDRA with IP 10.97.64.1
                'ntp2' second NTP server in the KDRA with IP 10.97.64.2
                'local' local UTC time as queryied through astropy.time.Time.now()
                Defaults to 'local'.
            verb (int, optional): Verbosity level. If greater than 0, prints the time difference.
                Defaults to 1.

        Returns:
            float: The time difference in seconds between the reference and the dish.

        Raises:
            ValueError: If an invalid reference time source is provided.
        """
        if reference == 'ntp1':
            t_ref = get_ntp_time_with_socket('10.97.64.1')
            t_ref = Time(parse_zulutime(t_ref), format='datetime')
        elif reference == 'ntp2':
            t_ref = get_ntp_time_with_socket('10.97.64.2')
            t_ref = Time(parse_zulutime(t_ref), format='datetime')
        else:
            raise ValueError(f'Can only select "ntp1", "ntp2", or "local", but given was {reference=}')
        
        t_dish = Time(self['acu.time.external_ptp'], format='mjd')
        dt_sec = (t_ref - t_dish).to(u.s).value
        
        if verb:
            if abs(dt_sec) > 1.0:
                col = colors.FAIL
            elif abs(dt_sec) > 0.5:
                col = colors.WARNING
            elif abs(dt_sec) > 0.1:
                col = colors.OKBLUE
            else:
                col = colors.OKGREEN        
            self.log(f'Time difference {reference} to dish is: ref={t_ref.isot} vs. dish={t_dish.isot} --> dt={dt_sec:.2f}s', color=col)

        return dt_sec


    def time_test(self, timeout=5, test_worldtime=False):
        tworld = 'Not Tested!'
        if test_worldtime:
            try:
                tworld = requests.get('http://worldtimeapi.org/api/timezone/utc', timeout=timeout).json()['utc_datetime']
            except Exception as err:
                tworld = 'Error while fetching: ' + str(err)
            
        try:
            ntp_1 = get_ntp_time_with_socket('10.97.64.1')
            ntp_1 = Time(parse_zulutime(ntp_1), format='datetime').isot if parse_zulutime(ntp_1) else ntp_1

        except Exception as err:
            ntp_1 = 'Error while fetching: ' + str(err)

        try:
            ntp_2 = get_ntp_time_with_socket('10.97.64.2')
            ntp_2 = Time(parse_zulutime(ntp_2), format='datetime').isot if parse_zulutime(ntp_2) else ntp_2
        except Exception as err:
            ntp_2 = 'Error while fetching: ' + str(err)

        dct = {'local_machine.system_time': Time.now().isot, 
            'remote.worldtimeapi': tworld,
            'dish.ptp_direct' : Time(self['acu.time.external_ptp'], format='mjd').isot,
            'dish.t_internal': self.t_internal.isot, 
            'kdra.ntp_server1': ntp_1,
            'kdra.ntp_server2': ntp_2,
        }
        return dct
    

    def link_stellarium_bg(self, 
                    stellarium_address = 'http://localhost:8090',
                    name = 'meerkat_site',
                    country = 'South Africa', 
                    verb: bool = True):
        """
        Links to a Stellarium instance by updating in the background.

        This function establishes a connection to a Stellarium instance running on the specified address. 
        It sets the observer's location and name, and defines a callback function to update the telescope's 
        pointing direction in Stellarium.

        Args:
            stellarium_address (str, optional): The address of the Stellarium instance. Defaults to 'http://localhost:8090'.
            name (str, optional): The name of the observer's location. Defaults to 'meerkat_site'.
            country (str, optional): The country of the observer's location. Defaults to 'South Africa'.
            verb (bool, optional): Whether to print verbose output. Defaults to True.
    
        Returns:
            mke_sculib.stellarium_api.StellariumAPI: The Stellarium API object for further interaction with the Stellarium instance.

        Raises:
            AssertionError: If `use_socket` is not set to True.
        """
        assert self.use_socket, 'linking stellarium in the background only works with use_socket=True'
        lon, lat, height = self.get_earth_location(as_tuple=True)
        from mke_sculib.stellarium_api import stellarium_api
        api = stellarium_api(stellarium_address, lat, lon, height, name, country=country)

        api.loc_name += '-' + self.address
        
        self.log(f'setting stellarium to: {name=} | {lat=} | {lon=} | {height=}')
        api._run_init(self, verb)
        def cb_newdata(time_astropy, data_dict):
            az, el = [data_dict.get(c, -90) for c in api.channels]

            if verb:
                dt = abs((time_astropy - cb_newdata.t_last).to(u.s).value)
                fps = 0. if dt <= 0 else 1/dt
                print(' {} | {: 10.4f}    | {: 10.4f}      | {: 4.2f}'.format(time_astropy.iso, az % 360, el, fps), end='\r')
            
            api.set_boresight(az, el)
            cb_newdata.t_last = time_astropy
        
        cb_newdata.t_last = dish.t_internal

        self.log(f'linking to stellarium @ {stellarium_address} by attaching callback', color=colors.OKBLUE)
        self.callbacks_on_new_data.append(cb_newdata)

        return api

    def link_stellarium(self, 
                    stellarium_address = 'http://localhost:8090',
                    antenna_id=None,
                    lat = -30.717972,
                    lon = 21.413028,
                    altitude = 1086,
                    name = 'meerkat_site',
                    country = 'South Africa', 
                    use_async: bool = True, 
                    verb: bool = True, 
                    use_socket: bool = True):
        """
            Links an instance of Stellarium to this dish objects AZ-El position by updating
            the Stellarium boresight position continiously based on the dish Az-EL readings
            until it is interrupted. 

            This function retrieves dish information (name, latitude, longitude, altitude)
            from the MeerTest server for the specified antenna ID (if provided) or falls 
            back to the object's antenna ID and default values.

            It then connects to a Stellarium instance at the given address and continually 
            sets the boresight position based on the retrieved or default information.

            It will run until interrupted or an error has occured. 

            Args:
                stellarium_address (str, optional): The URL of the Stellarium Web instance.
                    Defaults to 'http://localhost:8090'.
                antenna_id (str, optional): The ID of the antenna to retrieve information from.
                    If not provided, will use the object's antenna ID (if available) or None.
                lat (float, optional): The latitude of the dish. Defaults to -30.717972.
                    Will be overridden by the value retrieved from the MeerTest server
                    if an antenna ID is provided.
                lon (float, optional): The longitude of the dish. Defaults to 21.413028.
                    Will be overridden by the value retrieved from the MeerTest server
                    if an antenna ID is provided.
                altitude (float, optional): The altitude of the dish in meters. Defaults to 1086.
                    Will be overridden by the value retrieved from the MeerTest server
                    if an antenna ID is provided.
                name (str, optional): The name of the dish to use in Stellarium. Defaults to
                    'meerkat_site'. Will be updated with the retrieved antenna ID (if any)
                    appended with the object's address.
                country (str, optional): The country where the dish is located. Defaults to
                    'South Africa'.
                use_async (bool, optional): Whether to use asynchronous communication with
                    Stellarium Web. Defaults to True.
                verb (bool, optional): Whether to print verbose messages during execution.
                    Defaults to True.
                use_socket (bool, optional): Whether to use socket communication
                    with Stellarium Web (experimental). Defaults to True.

            """
        
        if not antenna_id and self.antenna_id:
            antenna_id = self.antenna_id
            if verb:
                print(f'getting dish info from this object {antenna_id=}')

        if antenna_id:
            try:
                dc = self.get_antenna_dc(antenna_id)
                name = dc.get('id', name) + '-' + self.address
                lat = dc.get('lat', lat)
                lon = dc.get('lon', lon)
                altitude = dc.get('altitude', altitude)

            except Exception as err:
                log.error('error while fetching dish info from MeerTest Server.')
                log.error(err)
                self.log('Falling back to default values for dish position and name...',color=colors.WARNING)


        if verb:
            print(f'setting stellarium to: {name=} | {lat=} | {lon=} | {altitude=}')

        from mke_sculib.stellarium_api import stellarium_api
        api = stellarium_api(stellarium_address, lat, lon, altitude, name, country=country)
        #self.use_socket = False
        
        if self.data_streamer and self.data_streamer.is_alive():
            self.log('stopping running data stream before connecting to stellarium!', color=colors.WARNING)
            self.data_streamer.stop_by_exception()
        if self.event_streamer and self.event_streamer.is_alive():
            self.log('stopping running data stream before connecting to stellarium!', color=colors.WARNING)
            self.event_streamer.stop_by_exception()
            # self.data_streamer = None
        
        api.run(self, use_async=use_async, verb=verb, use_socket=use_socket)

    def get_earth_location(self, antenna_id=None, as_tuple = False):     
        """
        Retrieves the EarthLocation object for a given antenna.

        Args:
            antenna_id (str, optional): The ID of the antenna. If not provided, the default antenna will be used.
            as_tuple (bool, optional): if True, returns a (lon, lat, height) tuple instead


        Returns:
            astropy.coordinates.EarthLocation: The EarthLocation object for the antenna.

        Raises:
            ValueError: If the antenna ID is invalid or the antenna data is missing.
        """
        
        dc = self.get_antenna_dc(antenna_id)
        args = (dc['lon'], dc['lat'], dc['altitude'])
        if as_tuple:
            return args
        else:
            return EarthLocation.from_geodetic(*args)

    def get_antenna_dc(self, antenna_id = None, url_db = f'http://10.98.76.45:8990/antennas'):
        """
        Retrieves the antenna configuration data from the specified URL.

        Args:
            antenna_id (str, optional): The ID of the antenna. If not provided,
                the default antenna ID of the object will be used.
            url_db (str, optional): The URL of the database containing antenna configurations.

        Returns:
            dict: The antenna configuration data, including longitude, latitude, and altitude.

        Raises:
            AssertionError: If no antenna ID is provided and the object's default antenna ID is not set.
            requests.exceptions.RequestException: If there is an error fetching the data from the URL.
        """

        if not antenna_id:
            antenna_id = self.antenna_id
        if antenna_id == self.antenna_id and self.antenna_dc:
            return self.antenna_dc
        
        assert antenna_id, f'need to give an antenna id or set the antenna_id for this dish object'
        url = url_db.rstrip('/') + '/' + str(antenna_id).strip('/')
        return requests.get(url).json()    


    def show_liveplot(self, channels:list=None, width=600, height=100):
        try:
            get_ipython().__class__.__name__
        except NameError as err:
            raise EnvironmentError('Not running in Ipython!') 
        from IPython.display import display, HTML
        from mke_sculib.js_helpers import make_livepos_page, make_liveplot_page
        if not channels:
            return HTML(make_livepos_page(self.ip, port = self.port, style=f"width:{width}px;height:{height}px;"))
        else:
            return HTML(make_liveplot_page(self.ip, channels, port = self.port, style=f"width:{width}px;height:{height}px;"))

    @alias('showc')
    def show_channels(self, channels:list=None, n_digits=3, regex=''):

        def get_style(df):
            return df.style.applymap(
                lambda v: "color:green;" if v == True else ("color:red;" if v == False else None)
            ).format(lambda x: ("{:." + str(n_digits) + "f}").format(x) if isinstance(x, float) else x)
            
        chans_dc = self.getc(channels, as_dict=True)

        if regex:
            regex = re.compile(regex) 
            chans_dc = {k: v for k, v in chans_dc.items() if regex.search(k)}
    
        try:
            get_ipython().__class__.__name__
            from IPython.display import display, HTML
            
            return display(get_style(pd.DataFrame(chans_dc, index=['value']).T))
        except NameError as err:
            print(json.dumps(chans_dc, indent=2))
        
        
        

    def test_all_clear(self, do_print_info=False, as_log=False):
        s, is_ok = dish_checker.show_dish_state_text(self, None, short=False, return_is_ok=True)
        if do_print_info:
            if as_log:
                self.log('\n' + s)
            else:
                print(s)
        
        return is_ok
    
    def print_info(self, short=False, as_log=False):
        s = self.get_info(short=short)
        
        if as_log:
            self.log('\n' + s)
        else:
            print(s)
    
    def get_info(self, short=False, as_html=False):
        f = dish_checker.show_dish_state_html if as_html else dish_checker.show_dish_state_text
        return f(self, self.antenna_id, short=short, return_is_ok=False)

    def show(self, as_log=False):
        if not as_log and is_notebook():
            from IPython.display import display, HTML
            html_string = self.get_info(as_html=True)
            return HTML(html_string)
        else:
            self.print_info(as_log=as_log)

    def info(self, short=False, as_log=False):
        self.print_info(short=short, as_log=as_log)

    def status(self, as_log=True, oneliner=True):
        s = self.get_info(short=3 if oneliner else 2)
        if as_log:
            color = colors.FAIL if oneliner and 'FAIL' in s else colors.OKGREEN
            if not oneliner:
                s = '\n' + s
            self.log(s, color=color)
        else:
            print(s)




def plot_tt(t, az, el, tint=None, do_show=True, is_simulation=False):
    if not 'plt' in locals():
        import matplotlib.pyplot as plt

    t_local = Time.now()
    f, (ax1, ax2) = plt.subplots(2,1, figsize=(12,6), sharex=True)
    ti = Time(t, format='mjd').datetime
    # print(t)
    # print(ti)
    
    ax1.plot(ti, az, 'b', label='AZ tracking curve')
    ax2.plot(ti, el, 'g', label='EL tracking curve')

    if not tint is None:
        ax1.axvline(tint.datetime, label=f'Creation Time: {tint.datetime}', color='k')
        ax2.axvline(tint.datetime, label=f'Creation Time: {tint.datetime}', color='k')

    if not is_simulation:
        ax1.axvline(t_local.datetime, label=f'Local Time: {t_local.datetime}', color='r')
        ax2.axvline(t_local.datetime, label=f'Local Time: {t_local.datetime}', color='r')

    ax1.set_ylabel('AZ [deg]')
    ax2.set_ylabel('EL [deg]')
    ax2.set_xlabel('time')
    # ax1.set_title('Tracking Table')
    ax1.legend()
    ax2.legend()
    ax1.grid()
    ax2.grid()

    if do_show:
        plt.show()

    return f, (ax1, ax2)
        
        
if __name__ == '__main__':

    # link_stellarium(121)

    

    dish = load("020H", readonly=True, use_socket=False)
    dish.events_show()
    #dish.events_show("2025-09-04T13:00:00.000Z", "2025-09-04T13:10:00.000Z")
    #print(json.dumps(dish.antenna_config_get(), indent=2))
    # dish = load(117, use_socket=False)
    # dish.configs_create_minimal()
    

    # # dish.activate_logging_mattermost()
    # dish.status()
    # # for k, color in colors_dc.items():
    # #     dish.log(f'TEST MESSAGE with color=({k}, {color}', color=color)


    # tester_dc = {'OFF': dish.point_spem_OFF, 'ON': dish.point_spem_ON}

    # dish.get_command_authority()

    # #dish.point_spem_set({'P1': -366.94, 'P7': 21.68})
    # print(dish.point_spem_get())

    # dish.start()


    # dish.point_spem_OFF()
    # # dish.point_spem_set({'P1': -366.94, 'P7': 21.68})

    # dish.point_spem_ON()
    # dish.status()

    # dish.showc(regex=r'.*enab.*')

    # dish.stop_program_track()
    # dish.log('creating tracking table now!')
    # tmjd = (dish.t_internal + np.arange(50)*0.3 * u.s).mjd
    # az, el = dish.azel
    # tt = tmjd, [az]*len(tmjd), [el]*len(tmjd)
    # with dish.with_tt(*tt) as track:
    #     print('tracking dummy table for 10s')
    # plot_tt(*tt)

    # dish.link_stellarium_bg()
    # dish.wait_duration(10)

    # dish.start()
    # dish.move(85, 0)
    # dish.shutdown()
# 

    # activate_logging_mattermost('https://mattermost.mpifr-bonn.mpg.de/hooks/nju3mqf4bjdczr6c7rm6c986ya', 'tester')

    # log("main")
    # dish = scu('http://10.96.64.10:8080/', use_socket=True, wait_done_by_uuid=True)
    # dish.status()

    # for band in dish.bands_possible:
    #     print(band)
    #     p_at_azel_in = tuple(np.random.rand(2))
    #     dish.point_AT_set(p_at_azel_in, band, activate = True)
    #     p_at_azel_out = dish.point_AT_get(band)
    #     s = 'TESTcase band {} AZ | SET: {} vs GET: {}'.format(band, p_at_azel_in, p_at_azel_out)
    #     if not (p_at_azel_in == p_at_azel_out):
    #         print('The ambient temperature correction value AZ for band "{}" was incorrect. SET: {} vs GET: {}'.format(band, p_at_azel_in, p_at_azel_out))


    # dish.show()
    
    # dish.start()


    # dish.link_stellarium()


    # d119.determine_dish_type()
    # d119.get_command_authority()
    # d119.move_to_azel(0, 89.5)

    # strm = EventStreamHandler(d119)

    # strm.start()

    # while not strm.events:
    #     d119.move_to_azel(5, 89.5)
    #     time.sleep(5)

    # print('waithere')
#     # print(websockets.__version__)
#     # with websockets.sync.client.connect(f'ws://{"10.96.66.10"}:{8080}/wsstatus') as ws:
#     #     print('success!')

#     # from astropy.time import Time
#     # from astropy import units as u

#     d119 = scu('http://10.96.66.10:8080/', debug=False, use_socket=True)

#     d119.set_time_source()

#     d119.wait_duration(10)
    
#     print({k:v for k, v in d119.get_channel_list(with_values=True) if 'time' in k})

#     # stream = DataStreamHandler(d119)
#     # stream.start()
#     # while 1:
#     #     print(f'{stream.t_last_local=} | {stream.t_last_remote=}')
#     # try:



#     el = 80

#     az, el = 0, 15

#     d119.move_to_azel(az, el)
#     d119.wait_settle()
#     print(d119.azel)
#     d119.reset_dmc()

#     #t0 = datetime.datetime.now(tz=datetime.timezone.utc)
#     t0 = d119.t_internal.datetime
#     t0p = t0.replace(second=0, microsecond=0)



#     t0, t0p
#     if t0.second > 30:
#         t00 = Time(t0p) + 2*u.minute
#     else:
#         t00 = Time(t0p) + 1*u.minute

    
#     t = np.arange(0, 60, 0.5)
#     azs = np.linspace(az, az+10, len(t))
#     els = np.ones_like(t) * el
#     tmjd = (t00 + t * u.s).mjd

#     d119.run_track_table(tmjd, azs, els, wait_start=False, verb=True)

    # finally:
    #     d119.shutdown()
    # D119A.reset_dmc()
    # D119A.stow()

    # D119A.move_to_azel(45, 80)
    # D119A.wait_settle()
    # print(D119A.azel)
    # D119A.reset_dmc()
    # D119A.move_to_azel(40, 75)
    # print(D119A.azel)
    # D119A.shutdown()

    # channels = ['acu.azimuth.p_act', 'acu.elevation.p_act']
    
    # while 1:
    #     print(api.get_device_status_value_async(channels))

    # gen = api.sock_listen_forever(channels)
    # while 1:
    #     t, fields = next(gen)
    # # for t, fields in api.sock_listen_forever(channels):
    #     print(time.time(), t, list(fields.values()))

    # import asyncio

    # async def run():
        
    #     gen = api.sock_listen_forever_async(channels)

    #     while 1:
    #         t, fields = await gen.__anext__()
    #         print(time.time(), t, list(fields.values()))

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(run())
    # loop.close()

    # api = scu('10.96.64.10', wait_done_by_uuid=False, use_socket=False)
    # api.determine_dish_type()
    # print('errors', api.get_errors(warnings=False))

    # print('warnings', api.get_warnings())

    pass
    