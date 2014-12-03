import GPIO, logging
import led

def main():
	GPIO.setmode(GPIO.BCM)

	logging.basicConfig(level=logging.DEBUG)

	logging.debug('Startup leds.')
	DialLed = Led(pin=LED_PIN_DIAL, port=LED_PORT_DIAL)
	PowerLed = Led(pin=LED_PIN_POWER, port=LED_PORT_POWER)

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

