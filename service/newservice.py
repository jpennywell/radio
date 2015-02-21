#!/usr/bin/env python3

import threading

class NewService(threading.Thread):

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
				cmd = item.pop()
				if len(item) > 0:
					args = item
				else:
					args = None
			else:
				continue

			if cmd == self.quit_cmd:
				break

			try:
				call = getattr(self, item)
				if callable(call):
					if args is None:
						call()
					else:
						call(args)
			except AttributeError:
				pass
			
