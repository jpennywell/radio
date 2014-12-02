import logging

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

