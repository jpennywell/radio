#!/usr/bin/env python

import RPi.GPIO as GPIO
import logging
import service.led as led

led_power_pin = 17
led_dial_pin = 27

led_power_port = 6000
led_dial_port = 6001

def main():
#	GPIO.setmode(GPIO.BCM)

	logging.basicConfig(level=logging.DEBUG)

	logging.debug('Startup leds.')
	DialLed = led.Led(pin=led_dial_pin, port=led_dial_port)
	PowerLed = led.Led(pin=led_power_pin, port=led_power_port)

	logging.debug('One Loop begun.')
	DialLed.svc_loop()
	logging.debug('Two Loop begun.')
	PowerLed.svc_loop()

	try:
		while True:
			pass
	except KeyboardInterrupt as e:
		logging.info("Ctrl-C: Quitting: " + str(e))
		DialLed.svc_cleanup()
		DialLed.stop()

		PowerLed.svc_cleanup()
		PowerLed.stop()

		GPIO.cleanup()

		logging.debug("main() done")
		return 0

	return 0


if __name__ == "__main__":
	status = main()
	logging.info('all done')

