#!/usr/bin/env python3

import threading, logging

class Service(threading.Thread):

	queue = None

	quit_cmd = 'quit'

	def __init__(self, queue):
		threading.Thread.__init__(self)
		self.queue = queue

	def run(self):
		while True:
			item = self.queue.get()
			if type(item) is str:
				cmd = item
				args = None
			elif type(item) is list:
				cmd = item.pop(0)
				if len(item) > 1:
					args = item
				elif len(item) == 1:
					args = item[0]
				else:
					args = None
			else:
				continue

			if cmd == self.quit_cmd:
				break

			try:
				logging.debug("[ Service ] : Received command '" + str(cmd) + "'")
				call = getattr(self, cmd)
				if callable(call):
					if args is None:
						call()
					else:
						call(args)
			except AttributeError:
				pass
			
