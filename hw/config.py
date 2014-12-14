"""
Configuration constants
"""

''' Hardware flags '''
# Enable SPI access to pots
ENABLE_SPI = False

# MCP3008 pins on the RPi
# This IC does the ADC conversion for reading from the pots
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

''' Tuning config '''
# Factor by which the tuning gaps should be larger than the station radii.
# Default = 1.18 (18% larger) for a 1-turn pot
# Default = 1.4 (40% larger) for a 10-turn pot
GAP_FACTOR = 1.4

