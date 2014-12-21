#
# Classes from
# http://blog.gocept.com/2011/08/04/shutting-down-an-httpserver/
#

import BaseHTTPServer, cgi, logging, threading, urllib2, sqlite3

from . import service
from . import www_cfg as config

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
			self.server = StoppableServer((self.host, self.port), CustomHandler)
			self.server_t = threading.Thread(target=self.server.serve_until_shutdown)
			self.server_t.daemon = True
			self.server_t.start()
			logging.info(self.__class__.__name__ + "> WWW service running at " + self.host + ':' + str(self.port))
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
				form = cgi.FieldStorage(
							fp=self.rfile,
							headers=self.headers,
							environ={'REQUEST_METHOD':'POST',
									'CONTENT_TYPE':self.headers['Content-type']})
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

