#
# Classes from
# http://blog.gocept.com/2011/08/04/shutting-down-an-httpserver/
#

import BaseHTTPServer, cgi, logging, threading, urllib2
import socket, fcntl, struct
import sqlite3

from . import service
from . import config_defaults

def html_hidden(name, value):
	return "<input type='hidden' name='{}' value='{}'/>".format(name,value)

def html_input(name, value, placeholder='', extra_data=''):
	return "<input class='form-control' type='text' name='{}' value='{}' placeholder='{}' {}>".format(name, value, placeholder, extra_data)

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

def html_glyph(glyph_class):
	return "<span class='glyphicon glyphicon-{}'></span> ".format(glyph_class)

def html_panel(panel_cls, title, *content):
	return "<div class='panel {}'><div class='panel-heading'><div class='panel-title'>{}</div></div><div class='panel-body'>{}</div></div>".format(panel_cls, title, ''.join(content))

def html_div(div_cls, *content):
	return "<div class='{}'>{}</div>".format(div_cls, ''.join(content))

def html_span(span_cls, *content):
	return "<span class='{}'>{}</span>".format(span_cls, ''.join(content))

def html_form(name, action, method, *content):
	return "<form name='{}' action='{}' method='{}'><div class='form-group'>{}</div></form>".format(name,action,method,''.join(content))

def html_submit(*content):
	return "<button type='submit' class='btn btn-defult'>{}</button>".format(''.join(content))

def html_table(header, *rows):
	return "<table class='table'><tr><th>{}</th></tr>{}</table>".format('</th><th>'.join(header), ''.join(rows))

def html_table_headerless(*rows):
	return "<table class='table'>{}</table>".format(''.join(rows))

def html_row(*content):
	return '<tr>{}</tr>'.format(''.join(content))

def html_rows_multi(*content):
	return '<tr>{}</tr>'.format('</tr><tr>'.join(content))

def html_cells(*cells):
	return '<td>' + '</td><td>'.join(cells) + '</td>'

def quick_query(sql, args):
	db_conn = sqlite3.connect('config.db')
	with db_conn:
		cur = db_conn.cursor()
		cur.execute(sql, args)


HTML_HEADER = "<!DOCTYPE html>\
<!DOCTYPE html>\
<html lang='en'>\
<head>\
<title>Radio Status</title>\
<link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css'>\
<link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap-theme.min.css'>\
<meta name='viewport' content='width=device-width, initial-scale=1'>\
<script src='www/jquery-2.1.3.min.js'></script>\
</head>\
<body>\
<div class='container'>\
<nav class='navbar navbar-default' role='navigation'><a class='navbar-brand'>Radio</a>\
<p class='navbar-text navbar-right'>\
<div class='btn-group navbar-right' role='group'>\
<a class='btn btn-default navbar-btn' href='/'><span class='glyphicon glyphicon-music'></span> Now Playing</a>\
<a class='btn btn-default navbar-btn' href='/config'><span class='glyphicon glyphicon-cog'></span> Settings</a>\
</p>\
</nav>"

HTML_FOOTER = "</div>\
</body>\
</html>"


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
			target.write(HTML_HEADER)

			emptydata = {'artist':'Unknown', 'album':'Unknown', 'title':'Unknown', 'file':'Unknown', 'elapsed':0}
							
			for k in ('artist', 'album', 'title', 'file', 'elapsed'):
				if k not in data:
					data[k] = emptydata[k]

			total_secs = int(data['elapsed'])
			hours = total_secs // 3600
			mins = (total_secs - 3600*hours)//60
			secs = total_secs - 3600*hours - mins*60
			time = "{:0>2d}:{:0>2d}:{:0>2d}".format(int(hours),int(mins),int(secs))

			target.write(
				html_panel('panel-primary',
							'Now Playing',
							html_table_headerless(
								html_rows_multi(
									html_cells(html_glyph('user') + ' Artist', data['artist']),
									html_cells(html_glyph('th-list') + ' Album', data['album']),
									html_cells(html_glyph('music') + ' Title', data['title']),
									html_cells(html_glyph('time') + ' Elapsed', time)
								)
							)
				)
			)

			target.write(HTML_FOOTER)
			target.close()
		except IOError as e:
			logging.error(self.__class__.__name__ + "> Can't open index.html for write: [" + str(e) + "]")

#End of RadioWebServer


"""
IndexOnlyHandler

A GET request handler that returns only the index.html file.
"""
class CustomHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_POST(self):
		"""
		Handles POSTed data, from the config page.
		Will then request self.do_GET_config() after.
		"""
		try:
			form = cgi.FieldStorage(
						fp=self.rfile,
						headers=self.headers,
						environ={'REQUEST_METHOD':'POST',
								'CONTENT_TYPE':self.headers['Content-type']})

			if 'table_is_options' in form.keys():
				for key in form.keys():
					sql = "UPDATE options SET value=? WHERE option='"+str(key)+"'"
					args = (form.getvalue(key),)
					quick_query(sql, args)
			else:
				if 'do_delete' in form.keys():
					sql = 'DELETE FROM playlists WHERE id=?'
					args = [form.getvalue('id'),]
					quick_query(sql, args)
				else:
					if form.getvalue('id') == 'NEW':
						sql = 'INSERT INTO playlists (name,url,random,play_function) VALUES (?,?,?,?)'
						args = [form.getvalue('name'),
								form.getvalue('url'),
								form.getvalue('random'),
								form.getvalue('play_function')]
						quick_query(sql, args)
					else:
						sql = 'UPDATE playlists SET name=?, url=?, random=?, play_function=? WHERE id=?'
						args = [form.getvalue('name'),
								form.getvalue('url'),
								form.getvalue('random'),
								form.getvalue('play_function'),
								form.getvalue('id')]
						quick_query(sql, args)
				
			pre_html = html_panel('panel-success', "Success", "Options saved.")
		except sqlite3.OperationalError as e:
			pre_html = html_panel('panel-danger', "DB Error", "Could not save data: ", str(e))
		except Exception as e:
			logging.info("No form data: " + str(e))

		self.do_GET_config(pre_html)


	def do_GET_config(self, pre_html = ''):
		"""
		Generate the config page.
		The argument 'pre_html' can be passed by do_POST with a return message.
		"""
		html = HTML_HEADER + pre_html

		try:
			db_conn = sqlite3.connect('config.db')

			with db_conn:
				cur = db_conn.cursor()

				cur.execute("SELECT * FROM playlists")
				tablerows = ''
				while True:
					row = cur.fetchone()
					if row == None:
						break
					(pl_id, pl_name, pl_url, pl_random, pl_func) = row
					pl_url = pl_url or ''
					pl_random = pl_random or 0
					pl_func = pl_func or ''

					tablerows += html_row(
									html_form('station_form_' + str(pl_id), '/config', 'POST',
										html_hidden('id', pl_id),
										html_cells(
											html_input('name', pl_name, 'Required'),
											html_input('url', pl_url, 'Required'),
											html_checkbox('random', is_checked=pl_random),
											html_input('play_function', pl_func),
											html_submit(html_glyph('ok'))
										)
									),
									html_form('station_delete_form_' + str(pl_id), '/config', 'POST',
										html_hidden('id', pl_id),
										html_hidden('do_delete', 'do_delete'),
										html_cells(
											html_submit(html_glyph('trash'))
										)
									)
								)
				#endwhile

				tablerows += html_row(
								html_form('station_add_form', '/config', 'POST',
									html_hidden('id', 'NEW'),
									html_cells(
										html_input('name', '', 'Required'),
										html_input('url', '', 'Required'),
										html_checkbox('random', 0),
										html_input('play_function', '')
									),
									"<td colspan='2'>",
									html_submit(html_glyph('plus')),
									"</td>"
								)
							)

				html += html_panel('panel-default',
							'Radio Stations',
							'<i>Play function must be defined in the www_cfg.py file on the server.</i>',
							html_table(('Playlist Name', 'URL/File', 'Randomize', 'Play Function'), tablerows))


				cur.execute("SELECT * FROM options")
				optionrows = ''
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

					if opt_type is bool:
						control = html_checkbox(opt_name, is_checked=(int(opt_val) == 1))
					elif type(opt_type) is tuple:
						control = html_select(opt_name, opt_type, opt_val)
					else:
						control = html_input(opt_name, opt_val, str(opt_default))

					optionrows += html_row(html_cells(opt_name, control))
				#endwhile

				html += html_form('option_form', '/config', 'POST',
							html_hidden('table_is_options', 'options'),
							html_panel('panel-default',
								html_div('input-group',
										html_span('input-group-addon', 'Radio Configuration'),
										html_span('input-group-btn', html_submit(html_glyph('ok')))
								),
								html_table(('Option', 'Setting'), optionrows)
							)
						)

				html += HTML_FOOTER
		except IOError as e:
			html = HTML_HEADER + html_panel('panel-danger', 'IOError!', str(e)) + HTML_FOOTER
		finally:
			return html


	def do_GET(self):
		"""
		Handle all GET requests.
		"""
		docRoot = self.server.docRoot
		docPath = "%s%s" % (docRoot, self.path)
		code = 200

		if self.path == '/config':
			html = self.do_GET_config()
		elif self.path in ('/now', '/index.html', '/'):
			source = open('index.html', 'r')
#			html = '\n'.join(source.readlines())
			html = source.read()
			source.close()
		elif self.path.startswith('../'):
			html = HTML_HEADER + html_panel('panel-danger', 'Bad path!', "Can't access files outside of the web tree.") + HTML_FOOTER
		elif os.path.exists(docPath):
			source = open(docPath, 'r')
			html = source.read()
			source.close()
		else:
			html = HTML_HEADER + html_panel('panel-danger', '404', 'No file available', self.path) + HTML_FOOTER
			code = 404

		self.push_output(html, code)


	def push_output(self, content, code=200, c_type='text/html'):
		"""
		Push 'content' out with the correct headers.
		"""
		self.send_response(code)
		self.send_header("Content-type", c_type)
		self.send_header("Content-length", len(content))
		self.end_headers()
		self.wfile.write(content)

#End of IndexOnlyHandler

