#!/usr/bin/env python3
"""
Radio & LED Services Startup Manager

This will start up the LED service, followed by the radio service.
If either quits, this script will restart them. If either respawns too quickly,
then this script will abort.
"""
import logging, os, subprocess, sys, threading, time

if (os.getuid() != 0):
	logging.critical("This process must be run as root. Exiting.")
	sys.exit(0)


"""
RespawningProcess

An exception class raised when a Process spawns too quickly.
"""
class RespawningProcess(Exception):
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
		if self.is_running():
			return time.time() - self.startup_timestamp
		else:
			return 0

	def restart(self):
		''' Respawn, unless it's too soon after a respawn. '''
		now = time.time()
		if (now - self.startup_timestamp < self.respawn_threshold):
			raise RespawningProcess
			return False
		else:
			''' Keep a running measure of respawn time. '''
			self.respawn_threshold = now - self.startup_timestamp
			self.start()
			return True



def main():
	led_control = Process('./svc_led.py')
	led_control.start()
	if not led_control.is_running():
		logging.critical("[ Error ] Cannot start LED service. Aborting...")
		return 0

	logging.info("[ Ok ] LED service")

	www = Process('./svc_web.py')
	www.start()
	logging.info("[ Ok ] WWW service")

	radio = Process('./svc_radio.py')
	radio.start()
	try:
		while True:

			if not led_control.is_running():
				try:
					logging.warning("[ Respawn ] LED service")
					led_control.restart()
				except RespawningProcess:
					logging.critical("[ Abort ] LED spawning too quickly")
					try:
						www.stop()
						radio.stop()
					except Exception as e:
						logging.critical("[ Error ] Can't stop: " + str(e))
						pass
					break
	
			if not www.is_running():
				try:
					logging.warning("[ Respawn ] WWW service")
					www.restart()
				except RespawningProcess:
					logging.critical("[ Abort ] WWW spawning too quickly")
					break

			if not radio.is_running():
				try:
					logging.warning("[ Respawn ] Radio service")
					radio.restart()
				except RespawningProcess:
					logging.critical("[ Abort ] Radio spawning too quickly")
					break

	except Exception as e:
		logging.critical("[ Error ] Some other error: " + str(e))
	except KeyboardInterrupt as e:
		logging.debug("[ Startup ] Ctrl-C. Quitting.")
		www.stop()
		led_control.stop()
		radio.stop()
		logging.debug("[ Startup ] Done.")

	return 0


if __name__ == "__main__":
	sys.exit( main() )


