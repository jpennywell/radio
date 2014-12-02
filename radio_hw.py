import RPi.GPIO as GPIO
import os, spidev, math
from radio_config import PWM_FREQ, LED_MIN_DUTY, LED_DUTY_CYCLE, \
							LED_RAMP_START, LED_RAMP_RATE, LED_RAMP_CUTOFF, \
							POWER_FLICKER_FREQ, GAP_FACTOR, \
							SPICLK, SPIMISO, SPIMOSI, SPICS

"""
PotChange

PotReader classes can raise this.
Catch it to act on a changed pot value.
"""
class PotChange(Exception):
	pass


"""
Led

Led interface class.

This class has two 'modes' of operation: discrete & pwm.

The discrete methods are on() and off().

The pwm methods are threaded, except for adjust_brightness().

"""
class Led:
	"""
	Hardware pin.
	"""
	pin = -1

	"""
	Toggle on to use PWM to flicker, blink, fade, etc.
	"""
	pwm = False

	"""
	A thread variable for splitting-off fading, blinking, etc.
	"""
	led_t = False

	"""
	Set this flag to True to tell internal threads to stop.
	"""
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


	def adjust_brightness(self, b):
		"""
		Adjust brightness by a new duty cycle 'b'
		"""
		if self.led_t:
			self.stop()
		if not self.pwm:
			self.pwm = GPIO.PWM(self.pin, PWM_FREQ)
		self.pwm.start(0)
		self.pwm.ChangeDutyCycle(b)


	def _start_thread(self, target_func):
		"""
		Start a thread with function 'target_func'.
		Used internally only.
		"""
		try:
			if self.led_t:
				self.stop()
			if not self.pwm:
				self.pwm = GPIO.PWM(self.pin, PWM_FREQ)
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


	def stop(self, do_stop = True):
		"""
		Stop any led thread.
		"""
		if self.led_t:
			self.led_t_stop_flag = do_stop
			self.led_t.join()

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
			if flicker <= POWER_FLICKER_FREQ:
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
			self.pwm.ChangeDutyCycle(LED_DUTY_CYCLE)
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
		led_ramp_fac = LED_RAMP_CUTOFF + 1
		dc = 0
		while led_ramp_fac > LED_RAMP_CUTOFF:
			if self.led_t_stop_flag:
				break
			dc += 1
			led_ramp_fac = 1. + math.exp(LED_RAMP_START - dc/LED_RAMP_RATE)
			self.pwm.ChangeDutyCycle(LED_DUTY_CYCLE/led_ramp_fac)
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
		for dc in range(int(LED_DUTY_CYCLE), 0, -5):
			if self.led_t_stop_flag:
				break
			self.pwm.ChangeDutyCycle(dc)
			time.sleep(0.2)

# End of class Led


"""
PotReader

A general hardware class that reads from a pot and updates an internal
variable with its value.

The function 'self.update()' stores the pot value last read.

Instances of this class can override 'self.update()' to do more
with the read value.
"""
class PotReader:
	"""
	The hardware pin of the pot.
	"""
	pot_pin = -1

	"""
	The most recently read pot value.
	Used to compare changes in the pot.
	Set to halfway around the pot.
	"""
	last_read = 512

	"""
	A smoothing factor for averaging-out read values.
	(1 = ignore old values, 0 = ignore newly-read values)
	"""
	smooth_fac = 0.6

	"""
	Use a SPI interface instead of the ADC.
	"""
	use_spi = False

	"""
	The SPI device object.
	"""
	spi = False


	def __init__(self, pin):
		"""
		Sets the pin to use.
		"""
		self.pot_pin = pin


	def update(self, pot_val):
		"""
		Store the pot value.
		"""
		self.last_read = pot_val
		raise PotChange


	def enable_spi():
		"""
		Use a SPI interface instead of the ADC.
		If this fails, it will fallback to the ADC.
		"""
		try:
			import spidev
			self.spi = spidev.SpiDev()
			self.use_spi = True
			return True
		except:
			self.disable_spi()
			return False


	def disable_spi():
		"""
		Turns off the SPI hooks.
		"""
		self.spi = False
		self.use_spi = False


	def _readadc(self, adcnum, clockpin, mosipin, misopin, cspin):
		"""
		Reads SPI data from the MCP3008 chip, 8 possible ADC's (0 - 7)
		From adafruit.com
		"""
		if ((adcnum > 7) or (adcnum < 0)):
			return -1
		GPIO.output(cspin, True)

		GPIO.output(clockpin, False)  # start clock low
		GPIO.output(cspin, False)     # bring CS low

		commandout = adcnum
		commandout |= 0x18  # start bit + single-ended bit
		commandout <<= 3    # we only need to send 5 bits here
		for i in range(5):
			if (commandout & 0x80):
				GPIO.output(mosipin, True)
			else:
				GPIO.output(mosipin, False)
			commandout <<= 1
			GPIO.output(clockpin, True)
			GPIO.output(clockpin, False)

		adcout = 0
		# read in one empty bit, one null bit and 10 ADC bits
		for i in range(12):
			GPIO.output(clockpin, True)
			GPIO.output(clockpin, False)
			adcout <<= 1
			if (GPIO.input(misopin)):
				adcout |= 0x1

		GPIO.output(cspin, True)
		
		adcout >>= 1       # first bit is 'null' so drop it

		return adcout


	def _readspi(self, channel):
		"""
		Reads SPI data over the SPI bus,
		and not through the MCP3008 chip.
		"""
		adc = self.spi.xfer2([1,(8+channel)<<4,0])
		data = ((adc[1]&3) << 8) + adc[2]
		return data


	def read_pot(self):
		"""
		Reads a pot value from a pot and calculate a smoothed average.
		"""
		if self.use_spi:
			pot_read = self._readspi(self.pot_pin)
		else:
			pot_read = self._readadc(self.pot_pin, SPICLK, SPIMOSI, SPIMISO, SPICS)

		smoothed_read = int(self.smooth_fac * pot_read + (1 - self.smooth_fac) * self.last_read)
		self.last_read = smoothed_read
		self.update(smoothed_read)

		return smoothed_read

# End of class PotReader


"""
TunerKnob

This extends PotReader.
"""
class TunerPotReader(PotReader):
	"""
	Gap between stations, measured in pot ticks (0 - 1023)
	"""
	cfg_st_gap = 106

	"""
	Tuning radius of each station, measured in pot ticks (0 - 1023)
	"""
	cfg_st_radius = 100 

	"""
	Will hold the list of stations
	"""
	station_list = []

	"""
	Will hold the list of 'frequencies', measured in pot ticks (0 - 1023)
	"""
	freq_list = []

	"""
	The current tuning
	"""
	tuning = -1

	"""
	The current station id
	"""
	SID = -1


	def __init__(self, pin, stations):
		"""
		Populate self.station_list with the station data, and
		Calculate dial frequencies.
		"""
		self.pot_pin = pin

		self.station_list.extend(stations)

		num_st = len(self.station_list)

		"""
		We setup our dial with each station's tuning in an interval of radius
		self.cfg_st_radius, separated by a gap of size self.cfg_st_gap.

		For three stations, the dial will be separated as:
			.5g r1r g r2r g r3r .5g,
		so that
			num_gaps = num_st,
			num_radii = 2 * num_st.

		The gaps will be of length
			len_gaps = GAP_FACTOR * len_radii.

		We solve then
			1023 = num_gaps * len_gaps + num_radii * len_radii
			1023 = num_st * len_radii * GAP_FACTOR + num_st * len_radii * 2
			len_radii = 1023 / (num_st * (GAP_FACTOR + 2))

		We then calculate our dial frequencies as starting at .5g + r, and
		increasing by two radii and a gap:
			.5g r1
			.5g r1r g r2
			.5g r1r g r2r g r3
		"""

		num_st = len(self.station_list)
		self.cfg_st_radius = 1023 / (num_st * (GAP_FACTOR + 2))
		self.cfg_st_gap = self.cfg_st_radius * GAP_FACTOR

		for t in range(0, len(self.station_list), 1):
			fr = (0.5 * self.cfg_st_gap + self.cfg_st_radius) + \
					t * (2 * self.cfg_st_radius + self.cfg_st_gap)
			self.freq_list.append(fr)


	def get_closest_freqs(self):
		"""
		Return the two station frequencies closest to
		the current tuning.
		"""
		# We temporarily insert the current tuning to sort the list
		# and pick out the left-most and right-most frequencies.
		self.freq_list.append(self.tuning)
		self.freq_list.sort()
		idx = self.freq_list.index(self.tuning)
		if (idx == 0):
			st_L = 0
		else:
			st_L = self.freq_list[idx-1]
		if (idx == len(self.freq_list) - 1):
			st_R = 1023
		else:
			st_R = self.freq_list[idx+1]
		self.freq_list.remove(self.tuning)
		return (st_L,st_R)


	def tuned_to(self):
		"""
		Returns the station the radio is tuned to.
		If no station is tuned, then returns -1 and sets self.SID to -1.
		""" 
		(st_L, st_R) = self.get_closest_freqs()

		dist_L = self.tuning - st_L
		dist_R = st_R - self.tuning

		if (dist_L == dist_R):
			self.SID = -1
			return -1 

		dist_closest = min(dist_L, dist_R)
		if (dist_closest > self.cfg_st_radius):
			self.SID = -1
			return -1
		else:
			if (dist_closest == dist_L) and (st_L != 0):
				return st_L
			elif (dist_closest == dist_R) and (st_R != 1023):
				return st_R
			else:
				self.SID = -1
				return -1


	def is_tuned(self):
		"""
		Returns a bool to indicate if we're tuned to a station or not.
		"""
		return (self.tuned_to() != -1)


	def update(self, tuning):
		"""
		Updates the tuning.
		If the radio is tuned to a station, raises a PotChange exception
		"""

		self.tuning = tuning

		if self.is_tuned():
			new_station_id = self.freq_list.index(self.tuned_to())

			# New station
			if new_station_id != self.SID:
				self.SID = new_station_id
				raise PotChange

# End of class TunerKnob


"""
VolumeKnob

This extends PotReader.

Adjusts OS volume based on the set volume, but also allows for a volume cap
set by tuning distance.

The pot volume is still stored as-read even if the cap limits it.

This uses the default PotReader init-function: __init__(self, pin).
"""
class VolumePotReader(PotReader):
	"""
	Current radio volume
	"""
	volume = 0

	"""
	A secondary volume limited by the amount of tuning
	away from the correct frequency.
	"""
	volume_cap = 0


	def get_volume(self):
		"""
		Returns the current volume, limited by the cap
		"""
		return min(self.volume, self.volume_cap)


	def update(self, volume):
		"""
		Updates internal volume variable, and sets volume.
		"""
		if (int(round(volume/10.24)) != int(round(self.volume/10.24))):
			self.volume = volume
			self.volumize(self.get_volume())
			raise PotChange


	def volumize(self, volume):
		"""
		Sets OS volume
		"""
		set_volume = int(round(volume / 10.24))
		set_vol_cmd = 'sudo amixer cset numid=1 -- {volume}% > /dev/null' . format(volume = set_volume)
		os.system(set_vol_cmd)

# End of class VolumeKnob

