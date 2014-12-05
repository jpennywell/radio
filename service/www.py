#
# Classes from
# http://blog.gocept.com/2011/08/04/shutting-down-an-httpserver/
#

import BaseHTTPServer, logging, threading, urllib2

from . import service
from . import www_cfg

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

		try:
			self.server = StoppableServer((self.host, self.port),	IndexOnlyHandler)
			self.server_t = threading.Thread(target=self.server.serve_until_shutdown)
			self.server_t.daemon = True
			self.server_t.start()
			logging.info(self.__class__.__name__ + "> WWW service running at " + self.host + ':' + str(self.port))
		except Exception as e:
			logging.critical(self.__class__.__name__ + "> Can't start web server: " + str(e))


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

#End of RadioWebServer


"""
IndexOnlyHandler

A GET request handler that returns only the index.html file.
"""
class IndexOnlyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):
		"""
		Instead of serving up any requested file, serve up index.html.
		"""
		try:
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

HTML_HEADER = "<!DOCTYPE html>\
<html>\
<head>\
<title>Radio Status</title>\
<style>\
body {\
	font-family: sans-serif;\
}\
table {\
	border-collapse: collapse;\
}\
tr {\
}\
td {\
	border: solid 1px #ccc;\
	padding: 10px 15px;\
}\
tr > td {\
	background: red;\
}\
</style>\
</head>\
<body>\
<h1>Now Playing</h1>\
<table>\
"
HTML_FOOTER = "</table>\
</body>\
</html>"


def write_html_data(mpd):
	try:
		target = open('index.html', 'w')
		target.write(HTML_HEADER)

		songdata = mpd.currentsong()
		for k in songdata:
			target.write("<tr><td>" + str(k) + "</td><td>" + str(songdata[k]) + "</td></tr>\n")

		target.write(HTML_FOOTER)
		target.close()
	except IOError as e:
		logging.error("write_html_data()> Can't open index.html for write: [" + str(e) + "]")
	except mpd.CommandError as e:
		logging.error("write_html_data()> MPD command error: [" + str(e) + "]")
	except KeyError:
		pass

