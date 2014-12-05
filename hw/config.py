"""
Configuration constants
"""

''' Hardware flags '''
ENABLE_SPI = False	# Enable SPI access to pots

SPICLK = 18		# MCP3008 pins on the RPi
SPIMISO = 23		# This IC does the ADC conversion for reading from the pots
SPIMOSI = 24
SPICS = 25

''' Tuning config '''
GAP_FACTOR = 1.18	# Factor by which the tuning gaps should be larger than
			# the station radii. Default = 1.18 (18% larger)
