import sqlite3
from . import config_defaults

"""
OptionLoader

Loads a sqlite database and coordinates reading from it.
"""
class OptionLoader(object):
	_db_name = ''
	_config = {}

	def __init__(self, db_name):
		self._config = {}
		self._db_name = db_name

		conn = sqlite3.connect(self._db_name)
		with conn:
			cur = conn.cursor()
			for row in cur.execute("SELECT * FROM options"):
				(opt_name_u, opt_val_u) = row
				opt_name = str(opt_name_u)
				opt_type = config_defaults.defaults[opt_name][0]
				if type(opt_type) is type:
					opt_val = opt_type(opt_val_u)
				else:
					opt_val = str(opt_val_u)
				self._config[opt_name] = opt_val


	def fetch(self, opt_name):
		"""
		Look up an option by name.
		"""
		try:
			return self._config[opt_name]
		except KeyError:
			return None


	def set(self, opt_name, opt_value):
		"""
		Set an option to a value.
		"""
		try:
			conn = sqlite3.connect(self._db_name)
			with conn:
				cur = conn.cursor()
				try:
					sql = "UPDATE options SET value=? WHERE option='{}'".format(str(opt_name))
					args = (opt_value,)
					cur.execute(sql, args)
				except sqlite3.OperationalError as e:
					return False

			self._config[opt_name] = opt_value
			return True
		except KeyError as e:
			return False

#End of OptionLoader class
