#Feed Indexer tests [316-000000-043]

#Author: P.P.A. Kotze
#Date: 1/9/2020
#Version: 
#0.1 Initial
#0.2 Update after feedback and correction from HN email dated 1/8/2020
#0.3 Rework scu_get and scu_put to simplify
#0.4 attempt more generic scu_put with either jason payload or simple params, remove payload from feedback function
#0.5 create scu_lib
#0.6 1/10/2020 added load track tables and start table tracking also as debug added 'field' command for old scu


#Import of Python available libraries
import uuid
import numpy as np
import json
import pandas as pd

from astropy.time import Time
import datetime, pytz

#scu_ip = '10.96.64.10'
# port = '8080'


bands = {'Band 1': 1, 'Band 2': 2, 'Band 3': 3, 'Band 4': 4, 'Band 5a': 5, 'Band 5b': 6, 'Band 5c': 7}      

lims_az = (-270, +270)
lims_el = (15, 90)
lims_fi = (-103.5, +100)

lims = dict(azimuth=lims_az, elevation=lims_el, feed_indexer=lims_fi)


dc_band_positions = {
    1: 99.85156,
    2: -103.4874,
    3: -47.6828,
    4: 10.4436,
    5: -6.3976,
    6: -30.84201,
    7: -22.35018,
}

categories = {'Deactivate': -1,
        'Deactivating': -1,
        'Activate': 1,
        'Activating': 1,
        'Standby': 2,
        'SIP': 3,
        'Slew': 4,
        'Track': 5,
        'Parked': 6,
        'Stowed': 7,
        'Locked': 8,
        'Locked and Stowed': 9,
        'Undefined': 0,
}




# mocks the SCU api to a degree as needed for developing

import json


import time
import astropy

import datetime

import os, inspect, sys
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
if __name__ == '__main__':
    sys.path.insert(0, parent_dir)

from mke_sculib.mock_telescope import Telescope
import mke_sculib.scu as scu
from mke_sculib.scu import log





def get_routes(telescope: Telescope) -> dict:
    dc_routes_get = {
        '/datalogging/currentState': lambda args: telescope.datalogging_currentState(*args),
        '/devices/statusValue': lambda args: telescope.devices_statusValue(args),
        '/devices/getAllDeviceStatusValues': lambda args: telescope.devices_getAllDeviceStatusValues(args),
        '/devices/statusPaths': lambda args: telescope.devices_statusPaths(args),

        '/datalogging/lastSession': lambda args: telescope.datalogging_lastSession(*args),
        '/datalogging/exportSession': lambda args: telescope.datalogging_exportSession(args),
        '/datalogging/sessions': lambda args: telescope.datalogging_sessions(*args),
    }
    dc_routes_put = {
        '/devices/command': lambda payload, params, data: telescope.devices_command(payload),
        '/datalogging/start': lambda payload, params, data: telescope.datalogging_start(*params),
        '/datalogging/stop': lambda payload, params, data: telescope.datalogging_stop(*params),
        '/acuska/programTrack': lambda payload, params, data: telescope.program_track(data),
        '/acuska/stopLoadingTable': lambda payload, params, data: telescope.stop_loading_track(),
    }
    return dict(GET=dc_routes_get, PUT=dc_routes_put)


class MockRequest():
    def __init__(self, method, url, body) -> None:
        self.url = url
        self.body = body
        self.method = method

class MockResponseObject():
    def __init__(self, method, url, status_code:int, content, with_uuid = False) -> None:
        self.status_code = status_code
        self._content = content
        self.reason = 'I am a teapod!'
        self.request = MockRequest(method, url, content)
        self.uuid = str(uuid.uuid4()) if with_uuid else ''

    def json(self):
        if isinstance(self._content, dict) and self.uuid:
            res = {'uuid': self.uuid}.update(self._content)
            return res 
        if not isinstance(self._content, str):
            return self._content
        else:
            res = json.loads(self._content)
            if self.uuid and isinstance(res, dict):
                res.update({'uuid': self.uuid})
            return res

    @property
    def text(self):
        return str(self._content)


@scu.aliased
class scu_sim(scu.scu):
    """A SCU SIMULATOR object, which SIMULATES a connection to a real SCU controller by OHB 
    Digital Connect GmbH for the SKA-MPI Demonstrator Radio Telescope in the Karroo Desert 
    in South Africa as well as the MeerKAT Extension Radio telescopes. 
    
    This class can be used to simulate the motion of a real Antenna in simulation time 
    (ahead of time) in order to debug test scripts etc.

    This simulators motion control capabilities as well as functional interface is reduced 
    compared to a real antenna.

    (This class inherits from a real SCU interface object and overwrites the communication channels)
    """
    def __init__(self, address='', ip='', port='8080', use_realtime=False, debug=True, speedup_factor=1, t_start = astropy.time.Time.now(), UPDATE_INTERVAL = .1, lims_az=(-270.0, 270, 3.0), lims_el=(15, 90, 1.35), dish_type='mke', post_put_delay=0.0, antenna_dc=None, **kwargs):
        """create an antenna scu/acu simulator object, which can be used to simulate the motion of
        a real Antenna in simulation time (ahead of time) in order to debug test scripts etc.

        This simulators motion control capeabilities as well as functional interface is reduced 
        compared to a real antenna.

        Args:
            ip (str, optional): NOT USED FOR SIMULATOR: ip address of the antenna to connect to. Defaults to 'localhost'.
            port (str, optional): NOT USED FOR SIMULATOR: port of the antenna to connect to. Defaults to '8080'.
            debug (bool, optional): Set to True, to receive additional information in stdout, when using commands. Defaults to True.
            lims_az (tuple, optional): limits on AZ axis, angle_min, angle_max, speed_max. Defaults to (-270.0, 270, 3.0).
            lims_el (tuple, optional): limits on EL axis, angle_min, angle_max, speed_max. Defaults to (15, 90, 1.35).
        """

        self.dc = {}

        self.t_start = t_start.datetime
        self.history = {}
        
        self.t_elapsed = 0

        self.telescope = Telescope( speedup_factor = speedup_factor, 
                                    t_start = t_start, 
                                    use_realtime = use_realtime, 
                                    UPDATE_INTERVAL = UPDATE_INTERVAL, 
                                    do_write_history=True)        

        self.routes = get_routes(self.telescope)


        scu.scu.__init__(self, debug=debug, lims_az=lims_az, lims_el=lims_el, dish_type=dish_type, post_put_delay=post_put_delay, use_socket=False, wait_done_by_uuid=False, antenna_dc=antenna_dc, **kwargs)
    
    def __str__(self):
        antenna_id = f' with antenna_id: "{self.antenna_id}"' if self.antenna_id else ''        
        use_realtime = 'YES' if self.telescope.use_realtime else 'NO'
        return f'scu_sim object{antenna_id} @SIMULATOR, dish_type: "{self.dish_type}" realtime?:{use_realtime}'

    def __repr__(self):
        return str(self)
    
    @property
    def address(self):
        """address of the dish as: http://IP:PORT"""
        return f'SIMULATOR'
    
    @property
    def version_acu(self):
        rt = '_rt' if self.telescope.use_realtime else ''
        return 'sim' + rt

    @property
    def event_streamer(self):
        return None

    @event_streamer.setter
    def event_streamer(self, value):
        pass

    @property
    def data_streamer(self):
        return None

    @data_streamer.setter
    def data_streamer(self, value):
        pass

    @property
    def wait_done_by_uuid(self):
        return None
    
    @wait_done_by_uuid.setter
    def wait_done_by_uuid(self, value):
        pass

    @property
    def use_socket(self):
        return None
    
    @use_socket.setter
    def use_socket(self, value):
        pass

    @property
    def data(self):
        return self.telescope.data

    def getc(self, key=None, as_dict=False):
        """get one or many channel values. key(s) must be string or list of strings

        Args:
            key (string or iterable[str]): the channel names to get

        Returns:
            dict, list or immuteable: type depending on the input.
        """
        try:
            if self.use_socket:
                if isinstance(key, str):
                    return {key: self[key]} if as_dict else self[key]
                else:
                    return self.get_many(channels=key, as_dict=as_dict)
        except Exception as err:
            log(f'error while getting data from socket stream... falling back to HTTP api. {err=}', color=scu.colors.WARNING)

        if key is None:
            return dict(self.get_channel_list(with_values=True, with_timestamps=False))
        elif not isinstance(key, str) and hasattr(key, '__len__'):
            allchans = {**{k:None for k in key}, **self.data}
            if as_dict:
                return {k:allchans[k] for k in key}
            else:
                return [allchans[k] for k in key]
        else:
            return self._get_device_status_value(key)

    def __getitem__(self, key):
        if not isinstance(key, str) and hasattr(key, '__len__'):
            return [self.data[k] for k in key]
        else:
            return self.data[key]
    
    def __contains__(self, key):
        if not isinstance(key, str) and hasattr(key, '__len__'):
            return True if [k for k in key if k in self.data] else False
        else:
            return key in self.data

    @property
    def t_internal(self):
        """internal telescope time as astropy Time object based on MJD format

        Returns:
            astropy.time.Time: the ACU internal time now
        """
        return self.telescope.t_internal


    #	def scu_get(device, params = {}, r_ip = self.ip, r_port = port):
    def scu_get(self, device, params = {}):
        '''This is a generic GET command into http: scu port + folder 
        with params=payload (OVERWRITTEN FOR SIMULATION!)'''
        URL = 'http://' + self.ip + ':' + self.port + device
        if device != '/devices/statusValue':
            self.call_log[self.telescope.t_internal.datetime] = 'GET | ' + device

        if device not in self.routes['GET']:
            r = MockResponseObject('GET', URL, 404, {})
        else:
            fun = self.routes['GET'][device]
            res = fun(params)
            r = MockResponseObject('GET', URL, res['status'], res['body'])

        self._feedback(r)

        return(r)

    def scu_put(self, device, payload = {}, params = {}, data='', get_uuid=True):
        '''This is a generic PUT command into http: scu port + folder 
        with json=payload (OVERWRITTEN FOR SIMULATION!)'''
        URL = 'http://' + self.ip + ':' + self.port + device
        self.call_log[self.telescope.t_internal.datetime] = 'PUT | ' + device
        if device not in self.routes['PUT']:
            r = MockResponseObject('PUT', URL, 404, {}, with_uuid=get_uuid)
        else:
            fun = self.routes['PUT'][device]
            res = fun(payload, params, data)
            r = MockResponseObject('PUT', URL, res['status'], res['body'], with_uuid=get_uuid)
        self._feedback(r, get_uuid=False)
        
        if self.post_put_delay > 0:
            self.wait_duration(self.post_put_delay, no_stout=True)
        
        return r.uuid
    
    def ping(self, *args, **kwargs):
        return f'I AM A SIMULATOR! {self}'
    
    def scu_delete(self, device, payload = {}, params = {}):
        '''This is a generic DELETE command into http: scu port + folder 
        with params=payload (OVERWRITTEN FOR SIMULATION!)'''
        raise NotImplementedError('Not Implemented for a simulator')
        
    #SIMPLE PUTS
    def print_scu(self, *args, **kwargs):
        """print a text with "t = XXXs SCU_SIM: " in front of it to stdout
        """
        print('t = {:10.1f}s SCU_SIM: '.format(self.t_elapsed), end='')
        print(*args, **kwargs)

    #wait seconds, wait value, wait finalValue
    @scu.alias('sleep', 'wait')
    def wait_duration(self, seconds, no_stout=False):
        """have the simulator wait for a given amount of seconds (but script will continue)

        Args:
            seconds (int): number of seconds to wait for
            no_stout (bool, optional): whether or not to give feedback in stdout. Defaults to False.
        """

        if not no_stout:
            self.print_scu('wait for {:.1f}s'.format(seconds))
        self.t_elapsed += seconds

        # move until n seconds reached
        ti = 0
        while ti < seconds:
            stepsize = min(seconds - ti, self.telescope.UPDATE_INTERVAL)
            # print(ti)
            ti += stepsize
            self.telescope.update(stepsize)
        if not no_stout:
            self.print_scu(' done *')


    # def wait_track_end(self, timeout=600, query_delay=1.):
    #     # This is to allow logging to continue until the track is completed
    #     log('Waiting for track to finish...')

    #     self.wait_duration(10.0, no_stout=True)  
    #     key = "acu.general_management_and_controller.state"
    #     self.wait_state(key, 'TRACK', timeout, query_delay, operator = '!=')
    #     log('   -> done')


    def wait_settle(self, axis='all', timeout=600, query_delay=.25, tolerance=0.01, wait_by_pos=False, initial_delay=1.0):
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

        if axis == 'all':          
            self.wait_settle('az', initial_delay=0.0, wait_by_pos=True)
            self.wait_settle('el', initial_delay=0.0, wait_by_pos=True)
            self.wait_settle('fi', initial_delay=0.0)
            return
        else:
            super().wait_settle(axis=axis, timeout=timeout, query_delay=query_delay, tolerance=tolerance, wait_by_pos=wait_by_pos, initial_delay=0.0)

    def get_history_df(self, interval_ms = None):
        """get this simulators internal motion history as DataFrame

        Args:
            interval_ms (int, optional): Sampling time in ms. None will leave sampling time as used internally in simulator. Defaults to None.

        Returns:
            pandas.DataFrame: the motion data as dataframe with the timestamps as UTC datetime index
        """
        df = self.telescope.get_log('history', interval_ms)
        if 'Unnamed: 0' in df:
            df = df.set_index('Unnamed: 0')

        df.index = pd.to_datetime(df.index, errors='coerce')
        return df

    def get_band_in_focus(self, as_name=False):
        band_str = self.getc('acu.general_management_and_controller.feed_indexer_pos')
        return band_str if as_name else scu.bands_dc.get(band_str, -1)

    def start(self, az_start=None, el_start=None, band_start=None, az_speed=3, el_speed=1, send_default_configs=True):
        """getting command authority, unstow, activate and start the antenna for usage

        Args:
            az_start (-270 <= az_start <= 270, optional): start position for AZ axis in degree. Defaults to None.
            el_start (15 <= el_start <= 90, optional): start position for EL axis in degree. Defaults to None.
            band_start (str or int, optional): start position ('Band 1'... 'Band 5c' or 1...7) for the Feed Indexer Axis to move to. Defaults to None.
            az_speed (0 < az_speed <= 3.0, optional): azimuth speed to use for movement to inital position. Defaults to 3.
            el_speed (0 < el_speed <= 1.0, optional): elevation speed to use for movement to inital position. Defaults to 1.
            send_default_configs (bool, optional): Whether or not to generate the default logging configs on the SCU on startup. Defaults to True.
        """

        log('=== INITIATING STARTUP ROUTINE ===')
        self.get_command_authority()
        # self.reset_dmc()
        self.wait_duration(3)
        self.unstow(nowait=True)

        self.wait_duration(5)
        # self.activate_dmc()
        self.wait_duration(5)
        # self.activate_axes()
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
        log('=== STARTUP ROUTINE COMPLETED ===')

    def shutdown(self):
        """Stow, deactivate, and release command authority for antenna in order to finish before handing back the antenna
        """
        log('=== INITIATING SHUTDOWN ROUTINE ===')
        self.stow(nowait=True)
        self.wait_duration(5)
        # self.deactivate_axes()
        self.wait_duration(5)
        # self.deactivate_dmc()
        self.wait_duration(5)
        self.release_command_authority()
        self.wait_duration(5)

        log('=== SHUTDOWN ROUTINE COMPLETED ===')

def plot_motion_pyplot(df, xkey='index', figsize=(12, 10), df_tt=None, event_log_in=None):
    """plot the motion of a telescope using pyplot if its given in a dataframe

        The DataFrame(s) should contain the columns 
        - 'azimuth'
        - 'elevation' 
        and optional:
        - 'feed_indexer'
        - 'acu.general_management_and_controller.state'
        - 'datalogging.currentstate'

    Args:
        df (pandas.DataFrame): the dataframe where the motion data is stored in. For column information read function description.
        xkey (str, optional): The column in the dataframe to use for the x-Axis in the plot (time), if 'index' is given the dataframes .index attribute is used. Defaults to 'index'.
        figsize (tuple, optional): pyplot figsize tuple. Defaults to (12, 10).
        df_tt (pandas.DataFrame, optional): an optional DataFrame holding the requested tracking Table to overlay with the actual motion data. Defaults to None.
        event_log_in (dict, optional): A simulator objects event log in order to use for annotating the plot. Defaults to None.
    
    Returns:
        array of matplotlib.axes: the axes of the plot generated
    """
    import matplotlib.pyplot as plt

    if df_tt is not None:
        x_tt = Time(df_tt['time'].values, format='mjd').datetime
        df_tt['azimuth'] = df_tt['az']
        df_tt['elevation'] = df_tt['el']

    fx, fy = figsize
    n_axes = 4
    constrained_layout = False

    # if event_log:
    #     n_axes += 1
    #     constrained_layout = True


    f, axs = plt.subplots(n_axes, 1, sharex=True, figsize=(fx, fy), constrained_layout=constrained_layout)   


    telescope_axes = 'azimuth elevation feed_indexer'.split()

    if xkey == 'index':
        x = df.index

    if 'acu.general_management_and_controller.state' in df:
        ser = df['acu.general_management_and_controller.state']
        # cats = list(categories.keys())

        # raw_cat = pd.Categorical(ser, categories=cats, ordered=False)
        # s = pd.Series(raw_cat)

        ax = axs[0]
        ax.plot(x, ser, '-k')
        ax.grid()

    # cats_dc = {i:c for i, c in enumerate(cats)}
    
    # ax.set_ylim(-.05, len(cats) + .05)
    # ax.set_yticks(cats)
    # ax.invert_yaxis()

    xlims = None
    colors = 'bgr'
    for ax, s, c in zip(axs[1:], telescope_axes, colors):
        setp, actp = f'acu.{s}.p_set', f'acu.{s}.p_act'

        ax.plot(x, df[setp], '-k')
        ax.plot(x, df[actp], '-' + c)

        if df_tt is not None and s in df_tt:
            ax.plot(x_tt, df_tt[s], ':k', label=f'tracking table: {s}')

        if xlims is None:
            xlims = ax.get_xlim()

        act_lim_l, act_lim_h  = ax.get_ylim()
        lim_l, lim_h = lims[s]

        if act_lim_l < lim_l:
            ax.fill_between(xlims, act_lim_l, lim_l, color='gray', alpha=0.3)

        if act_lim_h > lim_h:
            ax.fill_between(xlims, act_lim_h, lim_h, color='gray', alpha=0.3)

        if s == 'feed_indexer':
            for v, k in bands.items():
                pos = dc_band_positions[k]
                if act_lim_l < pos < act_lim_h:
                    ax.axhline(y=pos, color='gray', linestyle='--')
                    ax.annotate(v, xy=(1,pos), xytext=(6,0), color='k', 
                    xycoords = ax.get_yaxis_transform(), textcoords="offset points",
                    size=14, va="center")

        else:
            if 'datalogging.currentstate' in df:
                record = df['datalogging.currentstate'].replace({'STOPPED':0, 'RECORDING':1})
                lim_l, lim_u = ax.get_ylim()
                ax.fill_between(record.index,lim_l*1.1, lim_u*1.1, where=record.values == 1, color='b', alpha=0.2, label='logging_state')
                ax.set_ylim((lim_l, lim_u))

        ax.set_ylim((act_lim_l, act_lim_h))
        ax.set_ylabel(s + '\n[deg]')
        ax.legend([setp, actp])
        ax.grid()



    ax.set_xlim(xlims)
    ax.set_xlabel('time')

    if event_log_in:
        f, ax = plt.subplots(1,1, figsize=(fx, 6), constrained_layout=True)
        lg = {k:v for k, v in event_log_in.items() if k !=  '/devices/statusValue'}

        dates = list(lg.keys())
        log = list([v.split('|')[-1] for v in lg.values()])
        print(len(log), np.max(dates), np.min(dates))
        print(len(df), df.index.max(), df.index.min())

        # ax = axs[-1]

        # print(dates)

        # Choose some nice levels
        # levels = np.tile([1, 2],
        #                 int(np.ceil(len(dates)/n_level)))[:len(dates)]

        # levels = np.ones_like(dates)

        # ax.set(title="REST-API call event log")

        # ax.vlines(dates, 0, levels, color="tab:red")  # The vertical stems.
        ax.plot(dates, np.zeros_like(dates), "-o",
                color="k", markerfacecolor="w")  # Baseline and markers on it.

        # ax.annotate("Test", xy=(0.5, 0.5), xycoords="axes fraction")

        # annotate lines
        for d, dfract, r in zip(dates, np.linspace(0, 1, len(dates)), log):
            ax.annotate(r, xy=(d, 0),
                        xytext=(dfract, 0.8), textcoords="axes fraction",
                        horizontalalignment="center", verticalalignment="bottom",
                        rotation = 90, arrowprops=dict(arrowstyle="->",
                                    connectionstyle="angle3"),)

        # remove y axis and spines
        ax.yaxis.set_visible(False)
        ax.spines[["left", "top", "right"]].set_visible(False)

        ax.margins(y=0.1)
        ax.grid()

    return axs




if __name__ == '__main__':
    print("main")
    dish = scu_sim()
    print(dish.ping())
    print(dish.sleep(10))