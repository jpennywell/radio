import sqlite3
from . import config_defaults

"""
OptionLoader

Loads a sqlite database and coordinates reading from it.
"""
class OptionLoader(object):
	_db_name = ''
	_config = {}
	_defaults = config_defaults.defaults

	def __init__(self, db_name):
		self._config = {}
		self._db_name = db_name

		try:
			conn = sqlite3.connect(self._db_name)
			with conn:
				cur = conn.cursor()
				for row in cur.execute("SELECT * FROM options"):
					''' Everything is stored in unicode in the DB '''
					(opt_name_u, opt_val_u) = row

					''' The option name is always a string... '''
					opt_name = str(opt_name_u)

					''' Load up defaults '''
					try:
						(opt_type, def_val) = self._defaults[opt_name]
					except KeyError:
						(opt_type, def_val) = (str, '')

					'''
					Cast the unicode value as the right python type.
					This is usually str or int, but even for a tuple,
					the opt_val_u will be a string.
					'''
					if type(opt_type) is type:
						opt_val = opt_type(opt_val_u)
					else:
						opt_val = str(opt_val_u)

					self._config[opt_name] = opt_val
		except sqlite3.OperationalError:
			raise


	def option_exists(self, opt_name):
		"""
		Check to see if opt_name exists as an option.
		"""
		return opt_name in self._config


	def default(self, opt_name):
		"""
		Look up the default value for an option.
		"""
		try:
			(opt_type, def_val) = self._defaults[opt_name]
			return def_val
		except KeyError:
			return ''

	def get_opt_type(self, opt_name):
		"""
		Look up the type for a given option.
		"""
		try:
			(opt_type, def_val) = self._defaults[opt_name]
			return opt_type
		except KeyError:
			return None

	def fetch(self, opt_name):
		"""
		Look up an option by name.
		"""
		try:
			return self._config[opt_name]
		except KeyError:
			return ''


	def val_type_ok(self, opt_name, opt_value):
		"""
		Make sure that opt_value is the right type for opt_name.
		"""
		try:
			(opt_type, def_val) = self._defaults[opt_name]
			if type(opt_type) is type:
				if type(opt_value) is not opt_type:
					return False
			elif type(opt_type) is tuple:
				if opt_value is not tuple:
					return False

			return True
		except KeyError:
			return False


	def set(self, opt_name, opt_value):
		"""
		Set an option to a value.
		"""
		try:
			if opt_name is not in self._config:
				return False

			''' Make sure that the supplied value matches the type. '''
			if not self.val_is_right_type(opt_name, opt_value):
				return False

			conn = sqlite3.connect(self._db_name)
			with conn:
				cur = conn.cursor()
				sql = "UPDATE options SET value=? WHERE option='{}'".format(str(opt_name))
				args = (opt_value,)
				cur.execute(sql, args)

			self._config[opt_name] = opt_value
			return True
		except KeyError:
			return False
		except sqlite3.OperationalError:
			return False
		except UnknownDefault:
			return False

#End of OptionLoader class

