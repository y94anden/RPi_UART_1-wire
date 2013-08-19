Raspberry PI UART 1-wire master
===============================

A simple attempt for a 1-wire master for the Raspberry PI using the UART
written in python3.

This solution uses the hardware timing of the UART to realize the 1-wire
protocol. The circuit supplied also enables the 1-wire bus to run at 5V,
which might be needed if the bus is long.

Source code
-----------
* `onewire.py` contains the actual implementation of the 1-wire master.
* `enum.py` is a simple enum class.
* `simulator.py` simulates the UART and some 1-wire devices on the bus.
* `test_onewire.py` runs a few testcases using the simulator.
* `test_hardware.py` can be used to test the hardware. It sets output and reads 
  input.

Subfolders
-----------
* `circuit` contains a buffer circuit for this project. 
* `doc` contains notes on how to setup the raspberry and how the timing of 
  the 1-wire corresponds to the UART baudrates.

This project is based on an application note from Maxim:
http://www.maximintegrated.com/app-notes/index.mvp/id/214
