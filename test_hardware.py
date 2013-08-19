#!/usr/bin/python3
# -*- Coding: utf-8 -*-
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need "
          "superuser privileges.  You can achieve this by using 'sudo' to "
          "run your script")

# Make sure the cleanup is called at exit
import atexit
atexit.register(GPIO.cleanup)



class Hardware:
    def __init__(self):
        # use P1 header pin numbering convention
        GPIO.setmode(GPIO.BOARD)

        # Set up the GPIO channels - one input and one output
        GPIO.setup(8, GPIO.OUT, initial=GPIO.HIGH)  # UART0_TXD
        GPIO.setup(10, GPIO.OUT) # UART0_RXD

    def __del__(self):
        print('Cleaning up GPIO')
        GPIO.cleanup()

    def release_bus(self):
        GPIO.output(8, GPIO.HIGH)

    def high(self):
        self.release_bus()

    def pulldown_bus(self):
        GPIO.output(8, GPIO.LOW)

    def low(self):
        self.pulldown_bus()


    def read(self):
        result = GPIO.input(10)
        if result:
            print('High')
        else:
            print('Low')


if __name__ == '__main__':
    h = Hardware()
    r = 'help'
    while r and r != 'q':
        if r == 'r' or r == '':
            h.read()
        elif r in ['1', 'h']:
            h.high()
        elif r in ['0', 'l']:
            h.low()
        else:
            print('Press r for read, 1 for high, 0 for low or q for quit')
        print('Now reading ', end = '')
        h.read()
        r = input()
