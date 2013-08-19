The buffer circuit
==================
The Raspberry PI operates at 3.3V, but to run long 1-wire networks it is
desirable to operate it at 5V. To enable this, a simple buffer circuit is 
used.

UART TX
-------
The TX of the UART is connected via two 2N7000 in a NOT layout so that a 
logical 0 on TX pulls the bus low, and a 1 releases it. If the resistor
of the first NOT is more than 10kOhm, the bus will go low too slowly.

UART RX
-------
The RX of the UART is also connected to the bus, but via a 2N7000 to reduce
the 5V levels to 3.3V. 

It seems that the UART in the RPi has its own internal pullup, so anything 
higher than 10kOhm in this part does not work.

Another solution to the RX issue is to actually use the internal pullup, and 
connect two 2N7000 in NOT configuration to pull the RX low instead.


Software used
-------------
The buffer_circuit.sch is drawn using gschem, part of gEDA.

The blackboard_layout.bb is drawn using blackboard, an application to create
perfboards (stripboards) easily.
