#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
from service import newservice as service
import queue

class Led(service.NewService):
	pin = 0

	def __init__(self, queue, pin):
		self.pin = pin
		GPIO.setup(self.pin, GPIO.OUT)
		self.pwm = GPIO.PWM(self.pin, 30)
		self.pwm.start(0)
		super().__init__(queue)

	def fade(self):
                for dc in range(0, 50, 2):
                        self.pwm.ChangeDutyCycle(dc)
                        time.sleep(0.5)


def main():
	GPIO.setmode(GPIO.BCM)
	msgQ = queue.Queue()
	led = Led(msgQ, 27)
	led.start()
	print("LED Started.")
	print("Sleeping....")
	time.sleep(5)
	print("Fading...")
	msgQ.put('fade')
	print("Put onto the queue.")
	print("Doing other things:")
	for i in range(0,10):
		print(str(i))
	print("Quitting!")
	msgQ.put('quit')
	led.join()
	print("All done!")
	return 0



if __name__ == "__main__":
	main()
