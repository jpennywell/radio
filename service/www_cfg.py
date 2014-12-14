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
</head>\
<body>\
<div class='container'>\
<h1>Now Playing</h1>\
<div class='well'>"

HTML_FOOTER = "</div>\
</div>\
</body>\
</html>"

