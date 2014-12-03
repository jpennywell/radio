#!/usr/bin/env python
"""
Radio & LED Services Startup Manager

This will start up the LED service, followed by the radio service.
If either quits, this script will restart them. If either respawns too quickly,
then this script will abort.
"""
import sys, subprocess, threading, time, logging

"""
RunawayProcess

An exception class raised when a Process spawns too quickly.
"""
class RunawayProcess(Exception):
	pass


"""
Process

Handles the (re)starting of a process.
"""
class Process:
	''' The command being run. '''
	command = ''

	''' The Popen object that handles the process management '''
	popen = None

	''' When the process started. Used for the respawning check. '''
	startup_timestamp = 0

	''' The time under which a respawned process won't be started. '''
	respawn_threshold = 10

	def __init__(self, command):
		''' Store the command. '''
		self.command = command

	def start(self):
		''' Start the process. '''
		self.popen = subprocess.Popen(self.command)
		if self.is_running():
			self.startup_timestamp = time.time()
			return True
		else:
			return False

	def stop(self):
		''' Let the Popen object stop the process. '''
		self.popen.terminate()

	def is_running(self):
		''' Popen.poll() returns None if it's still running. '''
		return self.popen.poll() is None

	def uptime(self):
		''' How long the process has been running. '''
		is self.is_running():
			return time.time() - self.startup_timestamp
		else
			return 0

	def restart(self):
		''' Respawn, unless it's too soon after a respawn. '''
		now = time.time()
		if (now - self.startup_timestamp < self.respawn_threshold):
			raise RunawayProcess
			return False
		else:
			''' Keep a running measure of respawn time. '''
			self.respawn_threshold = now - self.startup_timestamp
			self.start()
			return True



def main():
	led_control = Process('led_service.py')
	led_control.start()
	if not led_control.is_running():
		logging.critical("Cannot start LED service. Aborting...")
		return 0

	logging.info("LED service started.")

	radio = Process('radio.py')
	radio.start()
	try:
		while True:
			if not led_control.is_running():
				try:
					logging.warning("LED not running. Restarting.")
					led_control.restart()
				except RunawayProcess:
					logging.critical("LED spawning too quickly. Aborting.")
					try:
						radio.stop()
					except:
						pass
					break
	
			if not radio.is_running():
				try:
					logging.warning("Radio not running. Restarting.")
					radio.restart()
				except RunawayProcess:
					logging.critical("Radio spawning too quickly. Aborting.")
					break
	except Exception as e:
		logging.critical("Some other error: " + str(e))

	return 0


if __name__ == "__main__":
	sys.exit( main() )


