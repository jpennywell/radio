''' LED Settings '''

''' Listener host and ports '''
LED_HOST = 'localhost'
LED_DIAL_PORT = 6000
LED_POWER_PORT = 6001
LED_AUTH_KEY = 'salt'

''' Power and operating settings '''
PWM_FREQ = 50 # Frequency for LED PWM
LED_MIN_DUTY = 1.		# Minimum duty cycle (default = 1.)
LED_DUTY_CYCLE = 30.	# Default duty cycle for an led (default = 30.)

LED_RAMP_START = 8. # Starting ramp value (larger = slower, default = 9)
LED_RAMP_RATE = 12. # Rate to fade by (larger = slower, default = 20)
LED_RAMP_CUTOFF = 1.1 # Breakpoint to stop fading (larger=sooner, default=1.1)

POWER_FLICKER_FREQ = 1	# At what frequency the power led is flickered.
						# (Between 1 and 10, default = 1.)

