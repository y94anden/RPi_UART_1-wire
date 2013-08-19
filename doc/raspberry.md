Settings for the Raspberry
==========================

The Raspberry PI has an UART on the GPIO port. Default this is used as a 
terminal though.

Freeing the UART for use
------------------------
1. Remove `console=ttyAMA0,115200` and `kgdboc=ttyAMA0,115200` configuration 
   parameters from the `/boot/cmdline.txt`
2. Comment the last line on the `/etc/inittab` file. Put a '#' before 
   `T0:23:respawn:/sbin/getty -L ttyAMA0 115200 vt100`.

Install pyserial
-----------------
1. Check out the latest pyserial from sourceforge:
   `svn checkout svn://svn.code.sf.net/p/pyserial/code/trunk pyserial-code`
2. Install it with your preferred version of python:
   `cd pyserial-code/pyserial`
   `sudo python3 setup.py install`

Make sure your user can user the serial port without sudo
---------------------------------------------------------
`/dev/ttyAMA0` is only rw for root and group dialout. To be able to use it
without sudo, add your user to the group `dialout`:

1. `sudo usermod -a -G dialout <username>`
2. Log out and in to have the changes show.

Pins on the GPIO
----------------
The pins used on the GPIO are P1-08 (GPIO14) for TX and P1-10 (GPIO15) for RX.

