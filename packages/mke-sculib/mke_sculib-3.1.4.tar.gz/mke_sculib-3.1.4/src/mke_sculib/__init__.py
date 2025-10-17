__version__ = '3.1.4'


from mke_sculib.scu import scu as scu_api
from mke_sculib.scu import load as _load
from mke_sculib.scu import plot_tt, print_color, colors, log, link_stellarium, activate_logging_mattermost
from mke_sculib.sim import scu_sim
from mke_sculib.stellarium_api import stellarium_api as stellar_api
from mke_sculib.sim import plot_motion_pyplot as plot_motion
from mke_sculib.helpers import get_utcnow, make_zulustr, parse_zulutime

from astropy.time import Time
import astropy.units as u
from astropy.coordinates import EarthLocation, get_sun, AltAz, get_body


def get_moon(*args, **kwargs):
    return get_body("moon", *args, **kwargs)


def load(antenna_id='', readonly=False, use_socket=True, debug=False, url_qry = 'http://10.98.76.45:8990/antennas', **kwargs):

    if not "requests" in locals():
        import requests
    if not "json" in locals():
        import json    

    log(f'INFO you are using mke_sculib version:"{__version__}" @ file_location:"{__file__}"', color=colors.OKBLUE)

    if antenna_id == 'test_antenna' or antenna_id == 'sim':
        antenna_dc = kwargs.pop('antenna_dc', {
  "address": "<no-ip>",
  "altitude": 1086,
  "lat": -30.717972,
  "comments": "UPDATE 2024-11-06: added calendar link to data_json",
  "params_json": "",
  "software_version": "sim",
  "data_json": "{\"calendar\": \"https://cloud.mpifr-bonn.mpg.de/remote.php/dav/calendars/tglaubach/dish-test_antenna-planning-sast/\"}",
  "lon": 21.413028,
  "id": "test_antenna",
  "configuration": None,
  "last_change_time_iso": "2024-11-06T09:03:31Z"
})
        return scu_sim(str(antenna_id), debug=debug, antenna_dc=antenna_dc, **kwargs)
    else:
        return _load(antenna_id, readonly=readonly, use_socket=use_socket, debug=debug, url_qry=url_qry, **kwargs)



def load_passive(antenna_id='', debug=False, url_qry = 'http://10.98.76.45:8990/antennas', use_socket=False, **kwargs):
    return load(antenna_id=antenna_id, readonly=True, use_socket=use_socket, debug=debug, url_qry=url_qry, **kwargs)
