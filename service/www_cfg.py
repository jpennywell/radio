WEB_HOST = 'localhost'
WEB_HTTP_PORT = 80

WEB_LISTEN_PORT = 6010
WEB_AUTH_KEY = 'secret'


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

