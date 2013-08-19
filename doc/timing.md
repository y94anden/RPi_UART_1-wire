Timing for 1-wire and UART
==========================

The UART is wired so that when TX is zero, the bus is pulled low and when it
is one, the bus is released (and pulled high by the pullup resistor). The
RX simply reads what is on the bus. When the master starts sending some serial
data on TX, it simultaneously reads it on RX.

For RESET, set baudrate 9600 and send byte 0xF0. This will show on the bus 
as five bitlengths of zeroes and five bitlengths of ones (the start bit is a 
zero and the stop bit is a one, and the least significant bit is  transferred 
first).

The 1-wire units will respond when the bus goes high by pulling it low again.

Thus, when the master sends 0xF0, it will read 0xF0 if there are no devices
on the bus. If there are devices on the bus, they will overwrite some of the
ones in the high nibble. This means that if we read anything lower than 0xF0,
we have devices that responds to the RESET. Depending on how quick the devices
are to respond, the results can be something like:
`
LSB  MSB
00001111 <- Bits sent (the 0xF0)
00000111 <- Bits received if devices respond quickly with a short presence pulse
00000011 <- quick response, with a longer presence pulse. 
00001011 <- Slow response, short presence pulse
00001001 <- Slow response, longer presence pulse
00001111 <- Bits received if no devices respond (same as sent, 0xF0)
`

To send and receive data (bits), the baudrate is set to 115200 to get better
resolution.

The UART
--------

The UART has IDLE level high, just as the 1-wire. When a byte is to be sent, 
first out on the wire is the start bit which is zero, followed by LSB, all the 
bits up to MSB possibly followed by a parity bit and then one or two stop bits
which are one. In this case, we do not use parity bits, and only one stop bit.

Example of bits on the wire:
`
------_xxxxxxxx-_xxxxxxxx-
  ^   ^^      ^^^
  |   ||      ||+---- The earliest next start bit (zero)
  |   ||      |+----- One (or possibly two) stop bits (one)
  |   ||      +------ MSB in sent byte
  |   |+------------- LSB in sent byte
  |   +-------------- Startbit (zero)
  +------------------ Idle (one) 
`

The RESET pulse
---------------
When running at 9600 baud, each bit is 104 µs.

The RESET pulse should be 480 µs low and 480 µs high. Start + 4 bit @ 9600 is
520 µs. The devices wait 15-60 µs (shorter than one bit length), and then pull
the bus low for 60-240 µs. 

In the shortest time scenario, the PRESENCE pulse will be released after 75 µs 
(15 µs wait + 60 µs low) which is more than half a bit length. If the UART 
samples this bit in the middle of the interval, it will see a zero. Next bit 
will be a one.

If the waiting is of maximum length, but the low time is at its minimum, the
first bit will be sampled high (it waits high 60 µs which is beyond the middle
of the bit, 52 µs). Now the signal goes low for 60 µs which only overlaps 16 µs
in the next bit which will make this device undetectable. Probably (hopefully),
the presence pulse will be longer if the wait time is long.

If both the waiting and presence times are long, the first bit will be sampled
high (after 52 µ2 in the waiting period). In total, the time will be 300 µs
which is just short of three bits.

Conclusions for the reset pulse
-------------------------------
Use 9600,N,8,1. Send four low bits (+start bit) and four high bits (+stop bit).
The units will pull the bus low for 1-3 bits.
TX: 0xF0
RX: 0x80, 0xC0, 0xE0 (Low nibble is sent zero, 0x8=1000, 0xC=1100, 0xE=1110)
    0xF0 if no devices are present.

Data transfer
-------------

For communication 115200,N,8,1 is used which will gives a bitlength of 8.68 µs.

Recoverytime is at least 1 µs, meaning that one stop bit of 8 µs is sufficient.

The start pulse from the master should be 1-15 µs, which is the length of the
start bit. To initiate a read frame or to write a one, send 0xFF. To write a
zero, send all zeroes, ie 0x00.

To read a zero, 0xFF is sent. The device responds for at least 15 µs. If the
unit responds at the first flank of the start bit, it will hold the bus low
during the start bit and almost the entire firt data bit (start+LSB = 17.4 µs).
This means that we will read at least one zero = 0xFE. If we are to read a one,
the bus will go high after the startbit and it will not be pulled low by anyone,
meaning that we will read 0xFF.
