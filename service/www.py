#
# Classes from
# http://blog.gocept.com/2011/08/04/shutting-down-an-httpserver/
#

import BaseHTTPServer, cgi, logging, threading, urllib2
import socket, fcntl, struct
import sqlite3

from . import service
from . import www_cfg as config
from . import config_defaults

def html_input(name, value, placeholder=''):
	return "<input class='form-control' type='text' name='{}' value='{}' placeholder='{}'>".format(name, value, placeholder)

def html_checkbox(name, value=1, is_checked=False):
	check_text = "checked='checked'" if is_checked else ""
	return "<input type='checkbox' name='{}' value='{}' {}>".format(name, value, check_text)

def html_select(name, opt_list, active_elt=None):
	html = "<select class='form-control' name='{}'>"
	for elt in opt_list:
		selected_text = "selected='selected'" if elt == active_elt else ""
		html += "<option value='{}' {}>{}</option>".format(elt, selected_text, elt)
	html += "</select>"
	return html



"""
StoppableServer

This HTTPServer has a keepalive flag that turns on/off the server.
"""
class StoppableServer(BaseHTTPServer.HTTPServer):
	"""
	While this is True, the server keeps running.
	"""
	_keepalive = True

	"""
	Handle requests while _keepalive is True.
	"""
	def serve_until_shutdown(self):
		while self._keepalive:
			self.handle_request()

	"""
	Shutdown the server.
	"""
	def shutdown(self):
		self._keepalive = False

		try:
			urllib2.urlopen('http://%s:%s/' % (self.server_name, self.server_port))
		except urllib2.URLError:
			pass

		self.server_close()
#End of StoppableServer


"""
RadioWebServer

A webserver that runs in its own thread.
"""
class RadioWebServer(service.Service):
	"""
	The StoppableServer object.
	"""
	server = False

	def __init__(self, host, port):
		"""
		Start a server in a thread.
		"""
		self.host = host
		self.port = port

		self.config = {}

		try:
			self.server = StoppableServer((self.host, self.port), CustomHandler)
			self.server_t = threading.Thread(target=self.server.serve_until_shutdown)
			self.server_t.daemon = True
			self.server_t.start()
			logging.info(self.__class__.__name__ + "> WWW service running at " + self.host + ':' + str(self.port))
		except sqlite3.OperationalError as e:
			logging.critical(self.__class__.__name__ + "> Can't load config.db properly; " + str(e))
		except Exception as e:
			logging.critical(self.__class__.__name__ + "> Can't start web server: " + str(e))

		empty_data = {'':''}
		self.html(empty_data)


	def stop(self):
		"""
		Shutdown the server.
		"""
		if self.server is None:
			return

		logging.debug(self.__class__.__name__ + "> Shutting down server")
		self.server.shutdown()
		logging.debug(self.__class__.__name__ + "> Joining thread....")
		self.server_t.join()
		logging.debug(self.__class__.__name__ + "> ...thread done.")


	def html(self, data):
		try:
			target = open('index.html', 'w')
			target.write(config.HTML_HEADER)

			emptydata = {'artist':'Unknown', 'album':'Unknown', 'title':'Unknown', 'file':'Unknown', 'elapsed':0}
							
			for k in ('artist', 'album', 'title', 'file', 'elapsed'):
				if k not in data:
					data[k] = emptydata[k]

			total_secs = int(data['elapsed'])
			hours = total_secs // 3600
			mins = (total_secs - 3600*hours)//60
			secs = total_secs - 3600*hours - mins*60
			time = "{:0>2d}:{:0>2d}:{:0>2d}".format(int(hours),int(mins),int(secs))

			target.write('<h2>Artist: ' + data['artist'] + '</h2>')
			target.write('<h2>Album: ' + data['album'] + '</h2>')
			target.write('<h2>Song: ' + data['title'] + '</h2>')
			target.write('<h2>Elapsed: ' + time + '</h2>')

			target.write(config.HTML_FOOTER)
			target.close()
		except IOError as e:
			logging.error(self.__class__.__name__ + "> Can't open index.html for write: [" + str(e) + "]")

#End of RadioWebServer


"""
IndexOnlyHandler

A GET request handler that returns only the index.html file.
"""
class CustomHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):
		"""
		Instead of serving up any requested file, serve up index.html.
		"""
		try:
			if self.path == '/config':
				try:
					html = config.HTML_HEADER

					try:
						form = cgi.FieldStorage(
									fp=self.rfile,
									headers=self.headers,
									environ={'REQUEST_METHOD':'POST',
											'CONTENT_TYPE':self.headers['Content-type']})
					except Exception as e:
						logging.error("No form? " + str(e))

					db_conn = sqlite3.connect('config.db')

					with db_conn:
						cur = db_conn.cursor()

						cur.execute("SELECT * FROM playlists")
						html += "<div class='panel panel-default'><div class='panel-heading''>"
						html += "<div class='input-group'>"
						html += "<span class='input-group-addon'>Radio Stations</span>"
						html += "<span class='input-group-btn'><a class='btn btn-success'><span class='glyphicon glyphicon-ok'></span> Save</a></span></div>"
						html += "</div><div class='panel-body'><i>Play function must be defined in the www_cfg.py file on the server.</i></div>"
						html += "<form role='form' method='POST' action='/config'>\n<div class='form-group'>\n"
						html += "<table class='table'>"
						html += "<tr><th>Playlist Name</th><th>URL/File</th><th>Randomize</th><th>Play function</th></tr>"
						while True:
							row = cur.fetchone()
							if row == None:
								break
							(pl_name, pl_url, pl_random, pl_func) = row

							html += "<tr><td>" + html_input('name', pl_name, 'Required') + "</td>"
							html += "<td>" + html_input('url', pl_url, 'Required') + "</td>"
							html += "<td>" + html_checkbox('random', is_checked=(int(pl_random) == 1)) + "</td>"
							html += "<td>" + html_input('play_function', pl_func) + "</td></tr>"

						html += "</table></div></form></div>"

						cur.execute("SELECT * FROM options")
						html += "<div class='panel panel-default'><div class='panel-heading''>"
						html += "<div class='input-group'>"
						html += "<span class='input-group-addon'>Radio Configuration</span>"
						html += "<span class='input-group-btn'><a class='btn btn-success'><span class='glyphicon glyphicon-ok'></span> Save</a></span></div>"
						html += "</div>"
						html += "<form role='form' method='POST' action='/config'>\n<div class='form-group'>\n"
						html += "<table class='table'>"
						html += "<tr><th>Option</th><th>Setting</th><th></th></tr>"
						while True:
							row = cur.fetchone()
							if row == None:
								break

							(opt_name_u, opt_val_u) = row
							opt_name = str(opt_name_u)

							(opt_type,opt_default) = config_defaults.defaults[opt_name]
							if type(opt_type) is type:
								opt_val = opt_type(opt_val_u)
							else:
								opt_val = str(opt_val_u)

							html += "<tr><td>" + opt_name + "</td>"
							if opt_type is bool:
								html += "<td>" + html_checkbox(opt_name, is_checked=(int(opt_val) == 1)) + "</td>"
							elif type(opt_type) is tuple:
								html += "<td>" + html_select(opt_name, opt_type, opt_val) + "</td>"
							else:
								html += "<td>" + html_input(opt_name, opt_val, str(opt_default)) + "</td>"

							html += "<td><a href='#' class='btn btn-default'><span class='glyphicon glyphicon-refresh'></span> Default</a></td></tr>"
						html += "</table></div></form>"
						html += config.HTML_FOOTER
				except IOError as e:
					html = "Nope: " + str(e)
				
			else:
				source = open('index.html', 'r')
				html = '\n'.join(source.readlines())
				source.close()
		except IOError:
			logging.error(self.__class__.__name__ + "> Can't read index.html")
			html = "Can't read index.html"
			
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.send_header("Content-length", len(html))
		self.end_headers()
		self.wfile.write(html)

#End of IndexOnlyHandler

