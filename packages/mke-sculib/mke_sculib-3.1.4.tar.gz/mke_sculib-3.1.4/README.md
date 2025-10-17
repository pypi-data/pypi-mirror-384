# mke_sculib

MeerKAT Extension (MKE)
(SCU) Science Computation Unit interface (lib)rary for the MKE antennas and some basic simulators



See also `examples` (especially `examples/getting_started.ipynb`) for examples on how to use this library.

___

## Installing


```bash
    pip install mke_sculib
```
   

---

## Usage for Antenna Control:



The main class is scu_api.scu.scu which can be loaded as `scu_api` from `mke_sculib`. This class provides an interface to the MeerKAT Extension Telescopes' dish structure controllers.

It does so by connecting to the Antenna Control Unit (ACU) via the HTTP REST API and websockets 
of the Science Computation Unit (SCU) both developed by OHB Digital Connect GmbH. 
It's designed for use with the SKA-MPI Demonstrator Radio Telescope in South Africa and the MeerKAT
Extension Radio Telescopes.



#### Construct
In order to connect to the REST API of the Telescope SCU use the library as follows:

```python
   import mke_sculib
   dish = mke_sculib.scu_api(ip='134.104.22.44')
   dish.determine_dish_type()
   dish.status()
```

#### Load

NOTE: This only works for telescopes in the Karoo with access to the Karoo site network (engineering network)

```python
   import mke_sculib
   # direct loading by full name
   dish = mke_sculib.load('skampi')
   dish.status()
   # partial names "119" vs "119A" also work
   dish = mke_sculib.load('119')
   dish.status()
   # If you want to interactively select which dish to load use load withut an antenna_id
   dish = mke_sculib.load()
   dish.status()
```



#### Dish Status

show full status by:
```python
dish = mke_sculib.scu_api(ip='134.104.22.44')
dish.show() # dish.print_info() to force ascii
```


#### Antenna Movement

This is how to control the dish:

```python
dish.status()
dish.start()
dish.move(az=15, el=85) # or equivalent dish.move(15, 85)
dish.status()
dish.move(band='Band 5b')
dish.shutdown()
dish.status()
```

#### Minimal Tracking Table Example

minimal example

```python
import pandas as pd
import numpy as np

tmjd = (Time.now() + np.arange(-10, 30, 0.5) * u.s).mjd
azs = np.arange(0, 40, 0.5)
els = np.arange(90, 50, 0.5)
dish.run_track_table(tmjd, azs, els)
history = dish.get_session_as_df()
```

#### Minimal Tracking Table Example for a Position On Sky

this is how to observe an astronomical Target using a tracking table

```python
import pandas as pd
import numpy as np
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import get_icrs_coordinates, EarthLocation, AltAz, SkyCoord


# make a tracking table for 'HIP104382' using astropy
loc = EarthLocation(lat = -30.778551, lon = 21.397161, height = 1094.6*u.m)  
t = Time.now() + np.arange(-10, 60, 1.0) * u.s
altaz = get_icrs_coordinates('HIP104382').transform_to(AltAz(location=loc, obstime=t))
tracking_table = pd.DataFrame({'time': t.mjd, 'az': altaz.az.deg, 'el': altaz.alt.deg})


with dish.with_tt(df=tracking_table) as track:
    print('tracking...')
    while track.get_t_remaining() > 0:
        print(f'{track.get_t_remaining()=} {dish.azel=} {dish.get_state()}')
        dish.wait_duration(1)

last_session = track.session
mke_sculib.plot_motion(last_session, df_tt = tracking_table)

```

#### Interfacing with a Local Instance of Stellarium

If you have [Stellarium](https://stellarium.org/) installed on a machine somewhere (or locally) and have ["remote control" plugin](https://stellarium.org/doc/24.0/remoteControlDoc.html) enabled (see below for instructions how to do this) you can interface between a MKE dish and Stellarium like this. 

```python
dish = scu('134.104.22.44', use_socket=True, wait_done_by_uuid=True)
dish.link_stellarium() # url for stellatium is 'http://localhost:8090' by default
```

or in one go using the convenience function in the `mke_sculib` root library:

```python
import mke_sculib
 # will query data for dish on pad 119 automatically and interface with stellarium
mke_sculib.link_stellarium('119')
```


The remote Control Plugin in Stellarium can be enabled by 
1. starting or opening Stellarium
1. opening "Config" (the "Wrench" icon in the lower left corner menu), 
1. opening Tab "Plugins"
1. selecting "Remote Control" on the left
1. click "configure"
1. check "Server enabled"
1. check "Enable automatically on startup"
1. set your desired port (8090 recommended)
1. click "Save setting"
1. close window
1. check "Load at startup" in the previous menu
1. close window
1. restart Stellarium

you now able to interface between stellarium and the mke_sculib as shown above.

#### Subscribing to callbacks

Data callbacks subscription example: 

```python
# this is a simple logging function, which will log data updates to stdout
def print_new_data(time_astropy, data_dict):
    print(f'{time.time():.2f} new data tick at {time_astropy.iso}, with data for N={len(data_dict)} channels | {id(data_dict)=}, {sys.getsizeof(data_dict)=}')

dish.callbacks_on_new_data.append(print_new_data)
```

Event callback subscription example:

```python
def on_new_event(e):
    print(f'{time.time():.2f}, new event wiith uuid {e.uuid}!')
    print(e.to_str())
dish.callbacks_on_new_events.append(on_new_event)
```

clear callbacks like this:

```python
dish.clear_all_callbacks()
```



---

## Usage as Simulator:


Using the simulator with the same script as used for operating the telescope can be 
achieved like this:

```python
   from mke_sculib.sim import plot_motion_pyplot as plot_motion
   
   # instead of THIS:
   # from mke_sculib.scu import scu
   # mpi = scu('134.104.22.44', '8080')

   # do THIS for simulation:
   from mke_sculib.sim import scu_sim as scu
   mpi = scu()
```

After a test has been done, the whole test history can be plotted in pyplot via:


```python
   # show the history data
   dfh = mpi.get_history_df(interval_ms = None)
   axs = plot_motion(dfh)
```

___

## Using the library within Test Scripts:


After installation, the library can be used to script automatic tests. A minimal 
example for a tracking test is given below:


```python
   # Init
   import astropy.units as u
   from astropy.time import Time
   import numpy as np
   import pandas as pd

   import matplotlib.pyplot as plt
   from mke_sculib.sim import plot_motion_pyplot as plot_motion
   from mke_sculib.sim import scu_sim as scu

   mpi = scu()

   # Startup 
   mpi.unstow()
   mpi.wait_duration(30) # sec
   mpi.activate_dmc()
   mpi.wait_duration(wait10)

   # Move to starting az, el
   mpi.abs_azimuth(-90, 3) # degree, degree / s
   mpi.abs_elevation(53, 1) # degree, degree / s
   mpi.wait_settle()
   mpi.wait_duration(5) # sec

   # move to Band 2
   mpi.move_to_band('Band 2')
   mpi.wait_settle()
   mpi.wait_duration(wait5)

   # make a dummy tracking table
   t = mpi.t_internal + (np.arange(5) * astropy.units.u.s)
   az = np.linspace(-90, -89, len(t))
   el = np.linspace(53, 54, len(t))

   # start a tracking table
   mpi.upload_track_table(t, az, el)

   # start logging for my testrun
   mpi.start_logger('full_configuration')
   
   # wait for track table to finish
   mpi.wait_duration(np.ptp(t) + 5)

   # shut down
   mpi.stop_logger()
   mpi.wait_duration(5)
   mpi.deactivate_dmc()
   mpi.wait_duration(10)
   mpi.stow()

   # show the sessions data
   df = mpi.get_session_as_df(interval_ms = 100)
   plot_motion(df)
   df.to_csv('testdata_acu.csv')
```


---

# HTTP Dummy server


This library has a dummy server with dashboard implemented which can run on any machine with anaconda installed. 

See: `servers` for the examples. 

NOTE: Change the absolut path in the files if necessary

```bash
   python /servers/dashboard.py
```

