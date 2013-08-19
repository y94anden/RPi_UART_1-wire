RPi_UART_1-wire
===============

A simple attempt for a 1-wire master for the Raspberry PI using the UART
written in python3.

This solution uses the hardware timing of the UART to realize the 1-wire
protocol. The circuit supplied also enables the 1-wire network to run at 5V,
which might be needed if the network is long.

Subfolder `circuit` contains a buffer circuit for this project. Subfolder `doc`
contains notes on how to setup the raspberry and how the timing of the 1-wire
corresponds to the UART baudrates.
