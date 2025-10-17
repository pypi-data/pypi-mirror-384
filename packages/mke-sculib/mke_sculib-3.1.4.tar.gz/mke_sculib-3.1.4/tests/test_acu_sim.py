import unittest
import astropy.units as u
from astropy.time import Time
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt


import os, inspect, sys
# path was needed for local testing
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
print(parent_dir)
sys.path.insert(0, parent_dir + '/src')
print(sys.path)



from mke_sculib.sim import plot_motion_pyplot as plot_motion
from mke_sculib.sim import scu_sim as scu
from mke_sculib.sim import Telescope


class TestAcuSim(unittest.TestCase):
    def test_error_free_move_bands(self):

        # Init
        mpi = scu()

        # Startup 
        mpi.unstow()
        mpi.wait_duration(30) # sec
        mpi.activate_dmc()
        mpi.wait_duration(10)

        # Move to starting az, el
        mpi.abs_azimuth(-90, 3) # degree, degree / s
        mpi.abs_elevation(53, 1) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec

        # move to Band 2
        mpi.move_to_band('Band 2')
        mpi.wait_settle()
        mpi.wait_duration(10)

    def test_move_bands_state(self):

        # Init
        mpi = scu()

        # Startup 
        mpi.unstow()
        mpi.wait_duration(30) # sec
        mpi.activate_dmc()
        mpi.wait_duration(10)

        # move to Band 2
        statei = mpi.get_state('acu.feed_indexer.state')
        self.assertTrue(statei <= 110, 'state was expected to be lower or equal to 110, but is {}'.format(statei))


        mpi.move_to_band('Band 2')
        mpi.wait_duration(2)
        statei = mpi.get_state('acu.feed_indexer.state')
        self.assertTrue(statei == 130, 'state was expected to be 130, but is {}'.format(statei))
        
        mpi.wait_settle()
        mpi.wait_duration(10)
        statei = mpi.get_state('acu.feed_indexer.state')
        self.assertTrue(statei <= 110, 'state was expected to be lower or equal to 110, but is {}'.format(statei))


    def test_move_to_azel_with_wait_settle(self):

        # Init
        mpi = scu()

        # Startup 
        mpi.unstow()
        mpi.wait_duration(30) # sec
        mpi.activate_dmc()
        mpi.wait_duration(10)

        # Move to starting az, el
        mpi.abs_azimuth(-90, 3) # degree, degree / s
        mpi.abs_elevation(53, 1) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec

        mpi.abs_azimuth(+180, 3) # degree, degree / s
        mpi.abs_elevation(85, 1) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec

        mpi.abs_azimuth(0, 3) # degree, degree / s
        mpi.abs_elevation(20, 1) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec


    def test_move_to_azel(self):

        # Init
        mpi = scu()

        # Startup 
        mpi.start()

        # Move to starting az, el
        mpi.move_to_azel(90, 53) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec

        mpi.move_to_azel(-90, 53) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec

        mpi.move_to_azel(-90, 53, 1.0, 1.0) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec



    def test_abs_azel(self):

        # Init
        mpi = scu()

        # Startup 
        mpi.start()

        # Move to starting az, el
        mpi.abs_azel(90, 53) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec

        mpi.abs_azel(-90, 53) # degree, degree / s
        mpi.wait_settle()
        mpi.wait_duration(5) # sec



    def test_tracking_table(self):

        mpi = scu()
        # Startup 
        mpi.unstow()
        mpi.wait_duration(30) # sec
        mpi.activate_dmc()
        mpi.wait_duration(10)

        # make a dummy tracking table
        t = (mpi.t_internal + (np.arange(5) * u.s)).mjd
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
        df = mpi.get_session_as_df(interval_ms = None)
        
        self.assertFalse(df.empty)
        self.assertFalse(df.isnull().values.any())

        df = mpi.get_session_as_df(interval_ms = 100)
        
        self.assertFalse(df.empty)
        self.assertFalse(df.isnull().values.any())


    def test_tracking_table2(self):

        mpi = scu()
        # Startup 
        mpi.unstow()
        mpi.wait_duration(30) # sec
        mpi.activate_dmc()
        mpi.wait_duration(10)

        vels = [0.001, 0.01, 0.05, 0.1, 0.3, 0.5, 1.0]
        test_points = [(0, 22.5), (0, 53), (0, 70), (0, 85)]
        dx = 5
        meas_points = []
        tracks = []

        def mk_track_slope(p_start, p_end, speed, dt=1.0, tslope = 5):
            dp = p_end - p_start
            s = np.sign(dp)
            n_wait = int(tslope/dt)
            
            
            dx = s * speed*dt
            tlen = dp / dx

            slope = list(np.arange(p_start, p_end, dx))  
            

            xa = list(np.ones(n_wait) * p_start)
            xb = list(np.ones(n_wait) * p_end)
            
            pos = np.array(xa + slope + xb)
            t = np.arange(len(pos)) * dt

            t_len = np.ptp(t)
            return t, pos, t_len
            
        for v in vels:
            # limit the distance to travel with very low speeds
            dxi = min(dx, 1.0) if v < 0.1 else dx
            
            # upgoing slope
            pstart, pend = -dxi/2, dxi/2
            meas_points.append((pstart, pend, v))
            t, pos, tlen = mk_track_slope(pstart, pend, v)
            tracks.append((t, pos, tlen))
            
            # downgoing slope
            pstart, pend = pend, pstart
            meas_points.append((pstart, pend, v))
            t, slope, tlen = mk_track_slope(pstart, pend, v)
            tracks.append((t, slope, tlen))
        
        for az0, el0 in test_points:
            for (p_start, p_end, v), (t, slope, tlen) in zip(meas_points, tracks):
                
                dxi = p_end - p_start
                print(f'TESTPOINT: AZ: {az0} deg | EL: {el0} deg | vel: {np.sign(dxi) * v} deg/s | dEL: {dxi} deg')
                az_start = az0
                el_start = p_start + el0
                
                print(az_start, el_start, type(az_start), type(el_start))
                
                mpi.move_to_azel(az_start, el_start)
                mpi.wait_settle()
                
                tt = (mpi.t_internal + (t * u.s)).mjd
                az = az0 * np.ones_like(tt)
                el = el0 + slope
        
                # start a tracking table
                mpi.upload_track_table(tt, az, el)

                # start logging for my testrun
                mpi.start_logger('full_configuration')

                # wait for track table to finish
                mpi.wait_duration(tlen + 10)

                mpi.stop_logger()
                        
                # show the sessions data

                df = mpi.get_session_as_df(interval_ms = None)
                self.assertFalse(df.empty)
                self.assertFalse(df.isnull().values.any())


                try:
                    df = mpi.get_session_as_df(interval_ms = 100)
                    
                    self.assertFalse(df.empty)
                    self.assertFalse(df.isnull().values.any())
            
                except Exception as err:
                    print(err)


        # shut down
        mpi.stop_logger()
        mpi.wait_duration(5)
        mpi.deactivate_dmc()
        mpi.wait_duration(10)
        mpi.stow()


    def test_unstow(self):

        mpi = scu()
        # Startup 
        mpi.unstow()
        mpi.wait_duration(10)
        self.assertTrue(mpi.t_elapsed > 10)


    def test_get_session_as_text(self):

        mpi = scu()
        # Startup 
        mpi.unstow()
        mpi.wait_duration(30) # sec
        mpi.activate_dmc()
        mpi.wait_duration(10)

        # make a dummy tracking table
        t = (mpi.t_internal + (np.arange(5) * u.s)).mjd
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
        
        txt = mpi.get_session_as_text(interval_ms=100)
        self.assertTrue(txt)
        print(txt)

        txt2 = mpi.export_session(mpi.last_session(), interval_ms=100)
        self.assertTrue(txt2)

        txt3 = mpi.export_session(mpi.last_session(), interval_ms=None)
        self.assertTrue(txt3)



if __name__ == "__main__":
    # sim = TestAcuSim()
    # sim.test_unstow()

    unittest.main()
