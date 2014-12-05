#!/usr/bin/env python

import RPi.GPIO as GPIO
import logging
import led.led as led

led_power_pin = 17
led_dial_pin = 27
led_power_port = 6000
led_dial_port = 6001

def main():
	GPIO.setmode(GPIO.BCM)

	logging.basicConfig(level=logging.DEBUG)

	logging.debug('Startup leds.')
	DialLed = led.Led(pin=led_dial_pin, port=led_dial_port)
	PowerLed = led.Led(pin=led_power_pin, port=led_power_port)

	logging.debug('Loop begun.')
	DialLed.c_loop()
	PowerLed.c_loop()

	try:
		while True:
			pass
	except KeyboardInterrupt as e:
		logging.info("Ctrl-C: Quitting: " + str(e))
		DialLed.c_cleanup()
		DialLed.stop()

		PowerLed.c_cleanup()
		PowerLed.stop()

		GPIO.cleanup()

		logging.debug("main() done")
		return 0

	return 0


if __name__ == "__main__":
	status = main()
	logging.info('all done')

