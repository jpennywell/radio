import sqlite3
from . import config_defaults

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
		try:
			return self._config[opt_name]
		except KeyError:
			return None

	def set(self, opt_name, opt_value):
		try:
			conn = sqlite3.connect(self._db_name)
			with conn:
				cur = conn.cursor()
				try:
					cur.execute("UPDATE options SET value='" + str(opt_value) + "' WHERE option='" + str(opt_name) + "'")
				except sqlite3.OperationalError as e:
					return False

			self._config[opt_name] = opt_value
			return True
		except KeyError as e:
			return False

#End of OptionLoader class
