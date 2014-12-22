import socket, fcntl, struct
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

WEB_HOST = get_ip_address('eth0')
WEB_HTTP_PORT = 80

WEB_LISTEN_HOST = 'localhost'
WEB_LISTEN_PORT = 6010

HTML_HEADER = "<!DOCTYPE html>\
<!DOCTYPE html>\
<html lang='en'>\
<head>\
<title>Radio Status</title>\
<link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css'>\
<link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap-theme.min.css'>\
<meta name='viewport' content='width=device-width, initial-scale=1'>\
<style type='text/css'>.input-group-addon{background:white !important;}</style>\
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

