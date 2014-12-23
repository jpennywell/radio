#!/usr/bin/env python

import RPi.GPIO as GPIO
import logging
import service.led as led
import service.option_loader as OL

def main():
#	GPIO.setmode(GPIO.BCM)

	logging.basicConfig(level=logging.DEBUG)

	logging.debug('[ Led ] Startup leds.')

	opt_ldr = OL.OptionLoader('config.db')

	DialLed = led.Led(pin=opt_ldr.fetch('LED_DIAL_PIN'))
	DialLed.svc_setup(port=opt_ldr.fetch('LED_DIAL_PORT'))
	DialLed.svc_loop()
	logging.debug('[ Led ] One Loop begun.')

	PowerLed = led.Led(pin=opt_ldr.fetch('LED_POWER_PIN'))
	PowerLed.svc_setup(port=opt_ldr.fetch('LED_POWER_PORT'))
	PowerLed.svc_loop()
	logging.debug('[ Led ] Two Loop begun.')

	try:
		while True:
			pass
	except KeyboardInterrupt as e:
		logging.info("[ Led ] Ctrl-C: Quitting: " + str(e))
		DialLed.svc_cleanup()
		DialLed.stop()

		PowerLed.svc_cleanup()
		PowerLed.stop()

		GPIO.cleanup()

		logging.debug("[ Led ] main() done")
		return 0

	return 0


if __name__ == "__main__":
	status = main()
	logging.info('[ Led ] all done')

