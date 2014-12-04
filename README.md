radio
=====

RPi internet radio with a tuning hardware interface

The split-service branch broke the led interface out to a separate service with a multiprocessing.Listener socket to accept requests.

The idea is that the LED service keeps running, even if the radio software fails. We could then use this to allow for error reporting, indepedent of the radio software.
