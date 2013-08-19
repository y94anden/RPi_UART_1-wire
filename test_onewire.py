#!/usr/bin/python3
# -*- Coding: utf-8 -*-

import unittest, sys
import onewire, simulator

class TestOW(unittest.TestCase):
    def setUp(self):
        self.ow = onewire.OneWire(simulated  = True)
        self.stdout = sys.stdout
        sys.stdout = None

    def tearDown(self):
        sys.stdout = self.stdout

    def testReset(self):
        # Test response with no devices on bus.
        self.ow.uart.setNextReadByte(0xF0)
        self.assertFalse(self.ow.reset())

        # Test response with devices on the bus.
        self.ow.uart.setNextReadByte(0xE0)
        self.assertTrue(self.ow.reset())

        # Test with badly connected electronics.
        # (no bytes will be read from bus)
        self.assertRaises(onewire.BadWiring, self.ow.reset)

    def testSearch(self):
        devices = ['2b0000047ff88528', # Cold medium in 
                   '4e0000047fae9428', # Head medium return
                   '5400000480970528', # Hot water pipe
                   '570000047fedf828', # Head medium out
                   'ca0000047ff8df28', # Cold medium out
                   '3b00000480a27d28', # Computer room basement
                   '580000047ffbdb28', # Guest room basement
                   '630000047ff26128', # Attic
                   '7d000004807d2e28', # Hallway living area
                   'f60000047ff5b128', # Garage
                   'a80000047fa59d28', # Outside under porch south side
                   '5f0000047fee9f28', # Outside under roof north side
                   ]
        for deviceID in devices:
            self.ow.uart.attachOWdevice(simulator.OWdevice(int(deviceID,16)))

        foundDevices = self.ow.search()

        self.assertEqual(len(devices), len(foundDevices))

        for d in foundDevices:
            self.assertTrue('%16x'%d in devices)

if __name__ == '__main__':
    unittest.main()
