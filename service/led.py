import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

import math, logging, sys, threading, time, random

from multiprocessing.connection import Listener, Client
from array import array

from . import service
from . import led_cfg as config


"""
Led

Led interface class.

This class has two 'modes' of operation: discrete & pwm.

The discrete methods are on() and off().

The pwm methods are threaded, except for adjust_brightness().
"""
class Led(service.Service):
	''' Hardware pin '''
	pin = -1

	''' Used to flicker, blink, fade, etc. '''
	pwm = False

	''' A thread variable for splitting-off fading, blinking, etc. '''
	led_t = False

	''' Set this flag to True to tell internal threads to stop. '''
	led_t_stop_flag = False


	def __init__(self, pin):
		"""
		Setup GPIO for this pin.
		"""
		self.pin = pin
		GPIO.setup(self.pin, GPIO.OUT)


	def _discrete_change(self, toggle):
		"""
		Make a discrete (high-low/True-False) change to the led.
		"""
		if self.led_t:
			self.stop()
		GPIO.output(self.pin, toggle)


	def on(self):
		"""
		Turn on the led. Stop any existing threads.
		"""
		self._discrete_change(True)


	def off(self):
		"""
		Turn off the led. Stop any existing threads.
		"""
		self._discrete_change(False)


	def adjust_brightness(self, p):
		"""
		Adjust brightness by a new duty cycle percentage 'p'
		"""
		if self.led_t:
			self.stop()
		if not self.pwm:
			self.pwm = GPIO.PWM(self.pin, config.PWM_FREQ)
		self.pwm.start(0)

		br = config.LED_MIN_DUTY if p == 0 else p * config.LED_DUTY_CYCLE
		self.pwm.ChangeDutyCycle(br)


	def _start_thread(self, target_func):
		"""
		Start a thread with function 'target_func'.
		Used internally only.
		"""
		try:
			if self.led_t:
				self.stop()
			if not self.pwm:
				self.pwm = GPIO.PWM(self.pin, config.PWM_FREQ)
				self.pwm.start(0)
			self.led_t = threading.Thread(target=target_func)
			self.led_t.start()
		except:
			pass


	def wait_for_done(self):
		"""
		Halts action until the thread stops.
		"""
		self.stop(False)


	def stop(self, do_thread_stop = True):
		"""
		Stop any led thread.
		"""
		if self.led_t:
			# do_stop=False means we wait on the thread to finish
			logging.info("Stopping...")
			self.led_t_stop_flag = do_thread_stop
			self.led_t.join()

			# Reset thread objects and flags
			self.led_t = False
			self.led_t_stop_flag = False
			self.pwm = False


	def flicker(self):
		"""
		Call a thread to flicker the led.
		"""
		self._start_thread(self._flicker_t_func)


	def _flicker_t_func(self):
		"""
		The flicker function called by 'self.flicker()'
		"""
		self.pwm.ChangeDutyCycle(100)
		
		while not self.led_t_stop_flag:
			flicker = random.randrange(0,10,1)
			if flicker <= config.POWER_FLICKER_FREQ:
				dc = random.randrange(30, 100, 5)
			else:
				dc = 100
			self.pwm.ChangeDutyCycle(dc)
			time.sleep(0.1)


	def blink(self):
		"""
		Call a thread to blink the led.
		"""
		self._start_thread(self._blink_t_func)


	def _blink_t_func(self):
		"""
		The blink function called by 'self.blink()'
		"""
		count = 0
		while count < 2:
			if self.led_t_stop_flag:
				break
			self.pwm.ChangeDutyCycle(0)
			time.sleep(0.5)
			self.pwm.ChangeDutyCycle(config.LED_DUTY_CYCLE)
			time.sleep(0.5)
			count += 1


	def fade_up(self):
		"""
		Call a thread to fade in the led.
		"""
		self._start_thread(self._fade_up_t_func)


	def _fade_up_t_func(self):
		"""
		The fade-in function called by 'self.fade_up()'
		"""
		led_ramp_fac = config.LED_RAMP_CUTOFF + 1
		dc = 0
		while led_ramp_fac > config.LED_RAMP_CUTOFF:
			if self.led_t_stop_flag:
				break
			dc += 1
			led_ramp_fac = 1. + math.exp(config.LED_RAMP_START - dc/config.LED_RAMP_RATE)
			self.pwm.ChangeDutyCycle(config.LED_DUTY_CYCLE/led_ramp_fac)
			time.sleep(0.1)


	def fade_down(self):
		"""
		Call a thread to fade out the led.
		"""
		self._start_thread(self._fade_down_t_func)


	def _fade_down_t_func(self):
		"""
		The fade-out function called by 'self.fade_down()'
		"""
		for dc in range(int(config.LED_DUTY_CYCLE), 0, -5):
			if self.led_t_stop_flag:
				break
			self.pwm.ChangeDutyCycle(dc)
			time.sleep(0.2)

# End of class Led



