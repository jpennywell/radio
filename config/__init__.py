"""
ConfSet

A Global collection of separate configurations
"""
class ConfSet(object):
	''' the configurations array '''
	configs = {}

	def __init__(self):
		pass

	def add_conf_set(self, fpath, name=''):
		''' Import a configuration file, naming it if so chosen '''
		try:
			if name == '':
				name = fpath
			self.configs[name] = __import__(fpath)
		except ImportError:
			logging.error("Could not import " + str(fpath))

	def get_conf(self, name):
		''' Return a configuration set '''
		return self.configs[name]

	def set_exists(self, name):
		''' True if name is in the ConfSet '''
		return name in self.configs

	def get_sets(self):
		''' Read all keys (named conf sets) '''
		return self.configs.keys()

