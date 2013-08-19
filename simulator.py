"""
This module simulates an uart in case there is no real UART.

There is also a class that can simulate a 1-wire device.
"""

import random
from enum import enum

random.seed()

class UART:
    baudrate = 9600
    timeout = None

    def __init__(self):
        # Define a buffer used for input to the uart from the serial
        # line, ie the data returned when calling read()
        self.inputBuffer = []

        # Define an output buffer which written bytes are put into
        # at write.
        self.outputBuffer = []

        # Define an optional list of attached 1-wire devices
        # based on the OWdevice class
        self.devices = []

    def setNextReadByte(self, byte):
        assert(byte > 0)
        assert(byte < 255)
        self.inputBuffer.append(byte)

    def readOutput(self):
        if self.outputBuffer:
            byte = self.outputBuffer[0]
            self.outputBuffer = self.outputBuffer[1:]
            return byte
        else:
            return None

    def read(self, nrBytes = 1):
        response = b''
        while nrBytes > 0 and self.inputBuffer:
            byte = self.inputBuffer[0]
            self.inputBuffer = self.inputBuffer[1:]
            response = response + b''.fromhex('%02x' % byte) # Ugly

        return response

    def write(self, data):
        assert(type(data) == bytes)
        for byte in data:
            self.outputBuffer.append(byte)

        # See if there are any devices to send to.
        self.sendToDevices(data)

    def attachOWdevice(self, device):
        self.devices.append(device)
        print('Attaching device %X to bus' % device.deviceID)

    def sendToDevices(self, data):
        """
        Parse data intelligently to determine what is sent (if it is reset
        for instance), and communicate with all devices.

        Also check with all devices if any of them wants to respond anything.
        If so, append it to the inputBuffer.
        """
        if not self.devices:
            return

        if data == b'\xF0' and self.baudrate == 9600:
            # We are sending a reset
            response = True # Initiate with a high bus
            for device in self.devices:
                response &= device.reset() # And all devices responses

            if response == False:
                # The devices have responded. Lower a bit on the input data.
                self.inputBuffer.append(0xE0) # One bit was lowered by devices
            else:
                self.inputBuffer.append(0xF0) # No change from input.
        elif self.baudrate == 115200:
            # We are communicating
            if data == b'\x00':
                # We are writing a zero.
                bitToSend = False
            elif data == b'\xFF':
                # We are either writing a one or initializing a read
                bitToSend = True
            else:
                raise ValueError('Can only receive 0x00 or 0xFF @ 115200 baud. '
                                 'Now received ' + str(data))

            response = True # Start with high bus
            for device in self.devices:
                response &= device.frame(bitToSend)

            if response:
                self.inputBuffer.append(0xFF) # All ones in reply.
            else:
                self.inputBuffer.append(0xFE) # The first bit zero.
        else:
            # We have sent a strange byte, or have the wrong baudrate
            raise ValueError('Unhandled data sent on UART @ %d baud: %s'
                             % (self.baudrate, str(data)))


state = enum('reset', 'romcommand', 'idle',
             'search', 'searchcomplement', 'searchselectbit')
romcommand  = enum(search=0xF0,
                   read=0x33,
                   match=0x55,
                   skip=0xCC,
                   alarmsearch=0xEC)

class OWdevice:
    """
    This class implements the logic of a 1-wire device. It is initialized with
    an ID (or generates one randomly).

    It can be attached to the simulated UART and will then receive data from
    it and will also be queried for responses.
    """
    def __init__(self, deviceID = None):
        if not deviceID:
            self.deviceID = random.getrandbits(64)
        else:
            self.deviceID = deviceID

    def reset(self):
        self.state = state.reset
        return False # Indicate a bus pulled low

    def frame(self, bit):
        """
        Figure out what to do with the frame that is initiated by the master.

        This could be a write of 0, 1 or an initialization of a read. This
        device will keep track of what to do.
        """

        #########################################
        #
        # Reset
        #
        #########################################
        if self.state is state.reset:
            # We need to move to romcommand
            self.state = state.romcommand
            self.romcommand = [bit]
            return False

        #########################################
        #
        # Rom Command
        #
        #########################################
        elif self.state is state.romcommand:
            self.romcommand.append(bit)
            if len(self.romcommand) == 8:
                self.parseRomCommand()
            return True

        #########################################
        #
        # Searching for a bit
        #
        #########################################
        elif self.state is state.search:
            # We are responding with our search bits.
            if not bit:
                raise ValueError('We are in search state, but got a zero bit')

            response = (self.deviceID & (2 ** self.position)) > 0

            self.state = state.searchcomplement
            return response

        #########################################
        #
        # Searching for complement bit
        #
        #########################################
        elif self.state is state.searchcomplement:
            if not bit:
                raise ValueError('We are in search state, but got a zero bit')

            response = (self.deviceID & (2 ** self.position)) == 0
            self.state = state.searchselectbit
            return response

        #########################################
        #
        # Reading the selected path for
        # continued search
        #
        #########################################
        elif self.state is state.searchselectbit:
            if bit and (self.deviceID & (2 ** self.position)):
                self.state = state.search
            elif not bit and not (self.deviceID & (2 ** self.position)):
                self.state = state.search
            else:
                print('%X withdrawing from search at bit %d' %
                      (self.deviceID, self.position))
                self.state = state.idle
                return True # Do not pull bus down.

            # Prepare for the next bit
            self.position += 1
            if self.position >= 64:
                self.state = state.idle
                print('%X is the found device' % self.deviceID)
            else:
                self.state = state.search

            return True # Do not pull bus down

        #########################################
        #
        # Idle
        #
        #########################################
        elif self.state is state.idle:
            # Do nothing
            return True
        else:
            raise ValueError('Unknown state')

        raise NotImplementedError('No return defined!')

    def bitsToByte(self, bits):
        assert(len(bits) == 8)
        mask = 1
        byte = 0
        for bit in bits:
            if bit:
                byte += mask
            mask <<= 1
        return byte

    def parseRomCommand(self):
        """
        Identify which rom command was sent and change state accordingly
        """
        command = self.bitsToByte(self.romcommand)
        if command == romcommand.search:
            self.state = state.search
            self.position = 0
        else:
            raise NotImplementedError('Cannot parse romcommand %02X yet' %
                                      command)
