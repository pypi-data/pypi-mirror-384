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



from mke_sculib.scu import scu


class TestScu(unittest.TestCase):
    def test_construct(self):


        mpi = scu('10.98.76.45', '8997')
        self.assertEqual(mpi.ip, '10.98.76.45')
        self.assertEqual(mpi.port, '8997')

        mpi = scu('10.98.76.45', 8997)
        self.assertEqual(mpi.ip, '10.98.76.45')
        self.assertEqual(mpi.port, '8997')

        mpi = scu('10.98.76.45', port='8997')
        self.assertEqual(mpi.ip, '10.98.76.45')
        self.assertEqual(mpi.port, '8997')

        mpi = scu('10.98.76.45')
        self.assertEqual(mpi.ip, '10.98.76.45')
        self.assertEqual(mpi.port, '8080')

        mpi = scu(ip='10.98.76.45:8081')
        self.assertEqual(mpi.ip, '10.98.76.45')
        self.assertEqual(mpi.port, '8081')

        mpi = scu('http://134.104.22.44:8080/')
        self.assertEqual(mpi.ip, '134.104.22.44')
        self.assertEqual(mpi.port, '8080')
        
        mpi = scu('http://134.104.22.44:1234/')
        self.assertEqual(mpi.ip, '134.104.22.44')
        self.assertEqual(mpi.port, '1234')

        mpi = scu('http://134.104.22.44/')
        self.assertEqual(mpi.ip, '134.104.22.44')
        self.assertEqual(mpi.port, '8080')

        mpi = scu('http://localhost:1234')
        self.assertEqual(mpi.ip, 'localhost')
        self.assertEqual(mpi.port, '1234')

        mpi = scu('http://localhost/')
        self.assertEqual(mpi.ip, 'localhost')
        self.assertEqual(mpi.port, '8080')

    def test_export_session(self):
        api = scu('http://10.98.76.45:8997/')
        api.export_session()
    
    # def test_get_session_as_df():
    #     api = scu('http://10.98.76.45:8997/')
    #     api.get_session_as_df()

    def test_get_errors(self):

        for dish, dish_type in [('10.96.64.10', 'skampi'), ('10.96.66.10', 'mke')]:
            
            for use_socket, wait_done_by_uuid in [(True, True), (False, False), (True, False)]:
                print(f"test_get_errors {dish=} {dish_type=} {use_socket=} {wait_done_by_uuid=}")
                api = scu(dish, wait_done_by_uuid=wait_done_by_uuid, use_socket=use_socket)
                self.assertEqual(api.determine_dish_type(), dish_type)
                # just test that there is no exceptions and all have 'err' in them
                errs = api.get_errors(warnings=False)
                self.assertIsInstance(errs, dict)
                non_errors = [k for k in errs if not 'err' in k]
                self.assertFalse(non_errors, f'found channels which should not be errors! {non_errors=}')
                print('OK!')

    def test_get_warnings(self):

        for dish, dish_type in [('10.96.64.10', 'skampi'), ('10.96.66.10', 'mke')]:
            
            for use_socket, wait_done_by_uuid in [(True, True), (False, False), (True, False)]:
                print(f"test_get_warnings {dish=} {dish_type=} {use_socket=} {wait_done_by_uuid=}")
                api = scu(dish, wait_done_by_uuid=wait_done_by_uuid, use_socket=use_socket)
                self.assertEqual(api.determine_dish_type(), dish_type)
                # just test that there is no exceptions and all have 'warn' in them
                errs = api.get_warnings()
                self.assertIsInstance(errs, dict)
                non_errors = [k for k in errs if not 'warn' in k]
                self.assertFalse(non_errors, f'found channels which should not be errors! {non_errors=}')
                print('OK!')

    def test_interlock_ackn(self):
        for dish, dish_type in [('10.96.64.10', 'skampi')]:
            for use_socket, wait_done_by_uuid in [(True, True), (False, False), (True, False)]:
                print(f"test_interlock_ackn {dish=} {dish_type=} {use_socket=} {wait_done_by_uuid=}")
                api = scu(dish, wait_done_by_uuid=wait_done_by_uuid, use_socket=use_socket)
                uuid = api.interlock_acknowledge_dmc()
                self.assertTrue(uuid, f'UUID evaluated to false {uuid=}')
                print('OK!')

if __name__ == "__main__":
    # sim = TestAcuSim()
    # sim.test_unstow()

    # TestScu().test_get_errors()
    # TestScu().test_get_warnings()
    TestScu().test_interlock_ackn()

    # unittest.main()
