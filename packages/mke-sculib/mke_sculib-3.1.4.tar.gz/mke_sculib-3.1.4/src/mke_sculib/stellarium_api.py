import requests
import numpy as np
import datetime
import asyncio
import time

class stellarium_api():
    
    def __init__(self, address = 'http://localhost:8090',
                    lat = -30.717972,
                    lon = 21.413028,
                    altitude = 1086,
                    name = 'meerkat_site',
                    country = 'South Africa'):
        """interfacing class for a stellarium program with remote control enabled

        Args:
            address (str, optional): the uri address for the stellarium program. Defaults to 'http://localhost:8090'.
            lat (float, optional): the latitude location to set. Defaults to -30.717972.
            lon (float, optional): the longitude location to set. Defaults to 21.413028.
            altitude (int, optional): the altitude to set (in meter). Defaults to 1086.
            name (str, optional): the name to give the location. Defaults to 'meerkat_site'.
        """
        self.address = address
        self.lat = lat
        self.lon = lon
        self.altitude = altitude
        self.loc_name = name
        self.country = country
        # self.channels = ['acu.azimuth.p_enc', 'acu.elevation.p_enc']
        self.channels = ['acu.azimuth.p_act', 'acu.elevation.p_act']
        
    def ping(self):
        """ping the stellarium api

        Returns:
            dict: empty if not available otherwise the current status
        """
        r = requests.get(self.address + '/api/main/status')
        if r.status_code != 200:
            return {}
        else:
            return r.json()

    def get_status(self):
        """get current status in stellarium

        Returns:
            dict: status of the program as dict
        """
        r = requests.get(self.address + '/api/main/status')
        r.raise_for_status()
        return r.json()
    
    def set_loc(self):
        """set the location as given during construction to the stellarium api
        """


        r = requests.post(self.address + '/api/location/setlocationfields', params = {                      
            'latitude': self.lat,
            'longitude': self.lon,
            'altitude': self.altitude,
            'name': self.loc_name,
            'country': self.country
        })
        r.raise_for_status()


    def set_boresight(self, az, el):
        """set the boresight location

        Args:
            az (float): azimuth position in DEGREE
            el (float): elevation position in DEGREE
        """
        az = (180 - az) % 360 # stellarium az definition != mke az definition MKE 0 = North +90 = East
        r = requests.post(self.address + '/api/main/view', params={'az': np.deg2rad(az), 'alt': np.deg2rad(el)})
        r.raise_for_status()


    def move_boresight(self, x, y):
        """joystick like move the boresight (setting an angular speed)

        Args:
            x (float): number -1...+1 with neg = move left and pos = move right
            y (float): number -1...+1 with neg = move down pos = move up
        """
        r = requests.post(self.address + '/api/main/move', params={'x': np.clip(x, -1, 1), 'y': np.clip(y, -1, 1)})
        r.raise_for_status()


    def set_time(self, time):
        """set the internal time in stellarium

        Args:
            time (astropy.time.Time): the internal telescope time
        """
        r = requests.post(self.address + '/api/main/time', params={'time': time.jd})
        r.raise_for_status()

    def _run_init(self, scu_api, verb):
        if verb: 
            print('initializing contact with app...')
            
        status = self.ping()
        if not status:
            raise ConnectionError('Could not connect to the stellarium program. Make sure the program is running and has remote control plugin enabled')
        if verb:
            print('--> OK')
            print('current status ins stellarium:')
            print(status)
            print('Setting config...')
        self.set_time(scu_api.t_internal)
        self.set_loc()
        if verb:
            print('--> OK')
            print('current status ins stellarium:')
            print(self.get_status())
            print('starting periodic update...')
            print('')
            print(' TIME (UTC)          | AZIMUTH (deg) | ELEVATION (deg) | FPS')

    
    
    def run(self, scu_api, use_async=True, verb=True, use_socket=False):
        """runs a continious feedthrough interface to 
            translate between a Meerkat Extension Dish 
            and Stellarium.

        Args:
            scu_api (mke_sculib.scu.scu): an MKE scu object
            use_async (bool, optional): True to use parallelism to speedup the loop. Defaults to True.
            verb (bool, optional): true to give stdout info. Defaults to True.
            use_socket (bool, optional): (ONLY VALID used with use_async) true to use the websocket interface of an ACU else the http statusValue path is used. Defaults to False.
        """
        self.loc_name += '-' + scu_api.address
        self._run_init(scu_api, verb)

        if use_async:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._loop_run_async(scu_api, verb=verb, use_socket=use_socket))
            loop.close()
        else:
            self._loop_run_sync(scu_api, verb)
    

    def _loop_run_sync(self, scu_api, verb=True, use_socket=False):

        t = datetime.datetime.now(datetime.timezone.utc)
        if use_socket:
            t, fields = next(gen)
        
        gen = scu_api.sock_listen_forever(self.channels)

        while 1:
            # tt = time.time()
            if use_socket:
                t, fields = next(gen)
                az, el = fields.values()
            else:
                az, el = scu_api.azel
            # print('azel', round(1.0 / (time.time() - tt), 3))

            if verb:
                t_last = t
                t = datetime.datetime.now(datetime.timezone.utc)
                dt = abs((t - t_last).total_seconds())
                fps = 0. if dt <= 0 else 1/dt
                print(' {} | {: 10.4f}    | {: 10.4f}      | {: 4.2f}'.format(t.isoformat().split('.')[0], az % 360, el, fps), end='\r')
            # tt = time.time()
            self.set_boresight(az, el)
            # print('setb', round(1.0 / (time.time() - tt), 3))

    async def _loop_run_async(self, scu_api, verb=True, use_socket=False):

        import aiohttp, json

        channels = self.channels
        # channels = ['acu.azimuth.p_enc', 'acu.elevation.p_enc']

        print('Using channels:' + str(channels) + '\n\n')

        url = self.address + '/api/main/view'
        
        if use_socket:
            gen = scu_api.sock_listen_forever_async(channels)

        data = {}
        t = datetime.datetime.now(datetime.timezone.utc)

        async with aiohttp.ClientSession() as session:
            async def send(data):
                if data:
                    async with session.post(url, data=data) as r:
                        await r.read()
                        return r.status
                else:
                    return 0
                
            async def get(channel):
                async with session.get(scu_api.address + '/devices/statusValue', params={'path': channel}) as r:
                    txt = await r.text()
                    r.raise_for_status()
                    return json.loads(txt)['value']
                    
            

            while True:
                if use_socket:
                    resp_post, (_, fields) = await asyncio.gather(send(data), gen.__anext__())
                    az, el = fields.values()
                else:
                    resp_post, az, el = await asyncio.gather(send(data), get(channels[0]), get(channels[1]))

                assert resp_post in [0, 200], 'post failed'
                az = (180 - az) % 360 # stellarium az definition != mke az definition MKE 0 = North +90 = East
                data = {'az': np.deg2rad(az), 'alt': np.deg2rad(el)}
                    
                if verb:
                    t_last = t
                    t = datetime.datetime.now(datetime.timezone.utc)
                    dt = abs((t - t_last).total_seconds())
                    fps = 0. if dt <= 0 else 1/dt
                    print(' {} | {: 10.4f}    | {: 10.4f}      | {: 4.2f}'.format(t.isoformat().split('.')[0], az % 360, el, fps), end='\r')
                    


if __name__ == "__main__":
    
    import sys
    args = sys.argv[1:]

    from mke_sculib.scu import scu as scu_api
    


    if args:
        api = stellarium_api()
        api.run(scu_api(args[0], use_socket=False), use_socket=True)
    else:

        dc = requests.get('http://10.98.76.45:8990/antennas/121B').json()
        api = stellarium_api(name=dc['id'], lat=dc['lat'], lon=dc['lon'], altitude=dc['altitude'])

                     
        api.run(scu_api('http://{}:8080'.format(dc['address']), use_socket=False, wait_done_by_uuid=False), use_socket=True)
        # api.run(scu_api('http://localhost:8080'), use_async=False, use_socket=True)    

