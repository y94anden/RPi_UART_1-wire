#!/usr/bin/python3
# -*- Coding: utf-8 -*-

import serial
import logging
from datetime import datetime

import simulator
from enum import enum

# Define the used port below
usedSerialPort = '/dev/ttyAMA0'


"""
This module implements the various 1-wire commands using the UART

Connect the TX to the 1-wire bus via two transistors connected as
NOT-ports (5V -> resistor -> transistor -> GND, output between resistor and
transistor) to the 1-wire bus.

Connect the 1-wire bus directly to RX or via a voltage converting
transistor (3.3V -> resistor -> transistor -> GND, output between resistor
and transistor).

When TX signals HIGH, the first NOT goes low and makes the second NOT leave
the pullup of the 1-wire bus.

When TX signals LOW, the first NOT goes high and grounds the 1-wire via the
second transistor.
"""

class BadWiring(Exception): pass
class BadByte(Exception): pass
class CommError(Exception): pass
class BadCRC(Exception): pass


commands = enum(CONVERTTEMP=0x44,
                RSCRATCHPAD=0xbe,
                WSCRATCHPAD=0x4e,
                CPYSCRATCHPAD=0x48,
                RECEEPROM=0xb8,
                RPWRSUPPLY=0xb4,
                SEARCHROM=0xf0,
                READROM=0x33,
                MATCHROM=0x55,
                SKIPROM=0xcc,
                ALARMSEARCH=0xec)

class OneWire():
    """
    Implementation of various 1-wire functions
    """
    def __init__(self, simulated = False):
        if simulated:
            self.uart = simulator.UART()
        else:
            self.uart = serial.Serial(port = usedSerialPort, timeout = 0.05)

        logging.basicConfig(format='%(asctime)s %(message)s',
                            level=logging.WARNING)

        # Make sure we have no data in the UART buffer
        while self.uart.read(1):
            logging.info('Read some data when opening UART initially')


    def prepareForReset(self):
        """ Make sure baudrate is set to 9600 """
        if self.uart.baudrate is not 9600:
            self.uart.baudrate = 9600
            logging.info('Setting baudrate to 9600')

    def prepareForSignalling(self):
        """ Make sure baudrate is set to 115200 """
        if self.uart.baudrate is not 115200:
            self.uart.baudrate = 115200
            logging.info('Setting baudrate to 115200')



    def writeAndReadByte(self, byte):
        """
        Write a byte on the bus, read the response and return the read byte.
        """
        data = b''.fromhex('%02x' % byte) # Ugly

        self.uart.write(data)
        logging.info('Wrote ' + str(data))

        # Read the result. We should only receive one byte, but read more
        # in case something strange has happened.
        response = self.uart.read(1)
        logging.info('Read ' + str(response))

        if not response:
            raise BadWiring('Did not read any serial data on reset(). Is '
                            'both TX and RX connected to the 1-wire bus?')

        if len(response) > 1:
            logging.error('Read %d bytes, but should only have read one.'
                          % len(response))

        # Convert the last byte of the bytes array to an int (it is probably
        # of length 1)
        response = response[-1]

        return response


    def reset(self):
        """
        Perform a reset on the 1-wire bus. Return True if devices are found

        This is done by setting the baudrate low (9600), and then pulling
        the bus low by sending four zeroes (plus a zero startbit), and
        then four ones (followed by a set stopbit). During the five ones,
        the devices on the bus will respond with zeroes which will be read
        somewhere in the following four bits.

        Since the bits are transferred least significant bit first, the
        byte to send is 0xF0
        """
        self.prepareForReset()

        # Send the 5 reset bits and the return the bus to high for 5 bits.
        # During the first bits of the response, we should sample what we
        # are sending, but during the last four bits, we should get some
        # zeroes if we have devices on the bus.
        response = self.writeAndReadByte(0xF0)

        return response < 0xF0

    def sendBits(self, bits):
        """
        Send an array of bits on the 1-wire net

        bits a list of elements that evaluate to True for ones and False
             for zeroes, ie bits = [1,1,0,0,1,0]. bits[0] is sent first on
             the bus.

        Since the UART communication always starts with a zero as start bit,
        the receiving devices will sample the bit somewhere around the first
        bit sent.
        """
        self.prepareForSignalling()

        for bit in bits:
            if bit:
                # Write all ones. The receiving device will sample a one.
                # Discard the read byte
                self.writeAndReadByte(0xFF)
            else:
                # Write all zeroes. The receiving device will sample a zero
                # Discard the read byte
                self.writeAndReadByte(0x00)

    def sendByte(self, byte):
        """
        Send a byte of data, least significant bit first.
        """
        if type(byte) != int or byte < 0 or byte > 255:
            raise BadByte('The byte supplied to sendByte does not seem to be a '
                          'proper byte')


        bits = []
        for mask in range(8):
            bits.append((byte & (2**mask)) > 0)

        self.sendBits(bits)

    def sendInt(self, value, bits):
        """
        Send an integer, in total bits long
        """
        # Convert to string of bits
        v = bin(value)[2:].zfill(bits) #Remove leading 0b and leftfill with 0
        v = v[-bits:] # Remove any bits in beginning that should not be used

        # Convert '1' and '0' to list of True/False
        b = []
        for bit in v:
            b.append(bit == '1')

        # Put LSB first in list
        b.reverse()

        self.sendBits(b)

    def readBit(self):
        """
        Read one bit from the 1-wire bus.

        This is done by writing 0xFF, which will first output a startbit which
        pulls the bus low, and then release the bus so that the device can
        respond.

        If the read byte is FF, a one was sent and if it is anything lower a
        zero was sent.
        """
        self.prepareForSignalling()

        response = self.writeAndReadByte(0xFF)


        return response == 0xFF

    def readBits(self, numberOfBits):
        """
        Read a number of bits from the bus
        """
        bits = []
        for i in range(numberOfBits):
            bits.append(self.readBit())

        return bits

    def readByte(self):
        """
        Read one byte from the bus and return it as an int.

        Bits are sent least significant first.
        """
        bits = self.readBits(8)
        byte = 0
        for i in range(8):
            if bits[i]:
                byte +=  (2**i)

        return byte

    def readBytes(self, numberOfBytes, reverse = False):
        """
        Read a number of bytes and return them as an array of ints

        The first byte read from the bus is placed first in the return
        array, unless reverse == True
        """
        response = []
        for i in range(numberOfBytes):
            response.append(self.readByte())

        if reverse:
            response.reverse()

        return response

    def search(self, warningsOnly = False):
        """
        Search the bus for device ID's.

        If warningsOnly is True, only devices with a warning condition
        are sought.

        Returns a list of all found device ID's
        """
        devices = []

        discrepancyMask = 0
        result = self.searchNext(discrepancyMask, warningsOnly)
        while result:
            previousDiscrepancyMask = discrepancyMask
            # We did find a device
            deviceID, discrepancyMask = result

            # Verify CRC
            self.clearCRC()
            for i in range(64):
                self.CRC((deviceID >> i) & 0x01)

            if self.getCRC():
                print('Bad CRC. Trying again.')
                discrepancyMask = previousDiscrepancyMask
            else:
                devices.append(deviceID)
                if discrepancyMask:
                    # If discrepancyMask != 0, there are still positions
                    # in which we need to go the other way.
                    result = self.searchNext(discrepancyMask, warningsOnly)
                else:
                    # All devices have been found
                    result = None

        return devices

    def oneOrZero(self, bit):
        if bit:
            return 1
        return 0

    def searchNext(self, discrepancyMask, warningsOnly=False):
        """
        This function will search the network for 1-wire devices.
        If two devicID's differ at a certain bit, the 1-branch is
        selected, and the discrepancyMask is set to 1 at this
        position. If the same discrepancy mask is supplied at the
        next call, next device is returned.

        For the first call, set discrepancyMask = 0

        If the discrepancyMask is 0 after a search command, all
        devices have been enumerated.

        The function returns the first deviceID after the last found
        or None if none is found.
        """
        logging.info('Entering searchNext with buffer 0x%16x' % 
                     discrepancyMask)
        if not self.reset():
            logging.warning('No devices on bus')
            return None

        if warningsOnly:
            command = commands.ALARMSEARCH
        else:
            command = commands.SEARCHROM

        # Start search
        self.sendByte(command)

        deviceID = 0
        for position in range(64):
            bits = self.readBits(2) # Read bit and its complement bit

            normalBit = self.oneOrZero(bits[0]) # Store the bit as an int: 1 / 0
            complementBit = self.oneOrZero(bits[1])

            if normalBit == 0 and complementBit == 0:
                """
                Active devices have different bits in current pos
                Check if this is the most significant bit in the
                discrepancyMask. If so, take the other route at this
                position (zero that is)
                 Ex:
                 0000100101001 <- least significant
                     ^ ^  ^  <--- If current position is here:
                     | |  |
                     | |  +--We have more to investigate higher up,
                     | |     select bit = 1
                     | +-----We have been here already and are now in the
                     |       bit=0 branch
                     +-------Time to take the other route (bit = 0). Reset
                             the mask and go with bit = 0.
                """
                if (discrepancyMask & (1 << position)):
                    """
                    Devices have different bits, and the mask is 1.
                    If this is the most significant bit in the mask,
                    we should try the other branch now (bit=0). We
                    should also reset the mask here to indicate we
                    are done with the 1-branch.
                    If this is not the most sigificant bit, we need
                    to keep investigating the 1-branch.
                    """
                    if (discrepancyMask < (1 << (position+1))):
                        #the mask is less than a 1 in the next position =>
                        #this is the most significant bit in the mask.

                        #reset the mask
                        #Use XOR - we know it is a one
                        discrepancyMask ^= (1 << position)
                        selectedNextBit = 0 # Go with the 0-branch now.
                    else:
                        #This is not the most significant bit. Keep
                        #investigating the 1-branch and leave the mask as is
                        selectedNextBit = 1

                else:
                    """
                    Devices have different bits, but the mask is zero
                    If we have passed the MSB of the mask, we have found
                    a new discrepancy. Set the mask to 1, and go for the
                    1-branch.
                    If we have not passed the MSB, this means we have
                    already investigated the 1-branch from this position and
                    we should keep investigating the 0-branch.
                    """
                    if ( discrepancyMask < (1 << position)):
                        #the mask is less than a 1 in the current position =>
                        #we have passed the MSB of the mask => we have found
                        #a new discrepancy
                        discrepancyMask |= (1 << position)
                        selectedNextBit = 1
                    else:
                        #We have not passed MSB => the 1-branch of this
                        #discrepancy have been searched already => keep
                        #going to the 0-branch.
                        selectedNextBit = 0;


            elif normalBit and complementBit:
                # No good? No device responded. This is OK in an alarm search
                # but not in a normal search
                if not warningsOnly:
                    logging.error('No devices responded eventhough someone '
                                 'responded to a reset')
                return None

            else:
                # Bits differed. All active devices had the same bit
                selectedNextBit = normalBit;


            # Update the deviceID with the read/selected bit
            deviceID |= (selectedNextBit << position)

            # Write the selected bit to continue out in the tree.
            self.sendBits([selectedNextBit])

        return deviceID, discrepancyMask;

    def clearCRC(self):
        self.shiftReg = 0

    def CRC(self, bit):
        # exclusive or least sig bit of current shift reg with the data bit
        fb = (self.shiftReg & 0x01) ^ self.oneOrZero(bit)

        # shift one place to the right
        self.shiftReg >>= 1

        if fb:
            self.shiftReg ^= 0x8C # CRC ^ binary 1000 1100

    def getCRC(self):
        return self.shiftReg


class DS18B20:
    def __init__(self, onewire, id):
        self.ow = onewire
        self.id = id

    def readTemp(self, checkCRC = False):

        #
        # Start temperature conversion
        #
        self.ow.reset()

        # Address the correct device
        self.ow.sendByte(commands.MATCHROM)
        self.ow.sendInt(self.id, 64)

        # Send command convert temperature
        self.ow.sendByte(commands.CONVERTTEMP)

        # Wait for conversion to finish.
        while self.ow.readBit() == False:
            pass

        #
        # Read the temperature
        #
        self.ow.reset()

        # Address the correct device
        self.ow.sendByte(commands.MATCHROM)
        self.ow.sendInt(self.id, 64)

        # Send command 'Read Scratchpad'
        self.ow.sendByte(commands.RSCRATCHPAD)

        # Read the first two bytes (which is the temperature)
        temp = self.ow.readBytes(2)

        if checkCRC:
            theRest = self.ow.readBytes(6)
            crc = self.ow.readBytes(1)

            self.ow.clearCRC()
            for byte in temp + theRest + crc:
                for i in range(8):
                    bit = ((byte >> i) & 1)
                    self.ow.CRC(bit)

            if self.ow.getCRC():
                raise BadCRC('Bad CRC when reading temperature')

        temperature = (temp[0] + temp[1] * 0x100) / 16
        return temperature

if __name__ == '__main__':
    import time
    o = OneWire()
    print('Searching for devices')
    devices = o.search()

    for d in devices:
        print('  %02x'%d)

    f = open('templog.txt','at')
    while True:
        for d in devices:
            if (d & 0xFF) == 0x28:
                #DS18B20
                t = DS18B20(o, d).readTemp()
                msg =  ('%s %016x %f' % (datetime.now().isoformat(), d,t))
                print(msg)
                f.write(msg + '\n')
                f.flush()
                time.sleep(1)


