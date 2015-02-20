#!/usr/bin/env python3

import logging

import service.www as www
import service.option_loader as OL


import socket, fcntl, struct
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'UTF-8'))
    )[20:24])


def main():
	logging.basicConfig(level=logging.DEBUG)

	logging.debug('[ Web ] Startup server')

	opt_ldr = OL.OptionLoader('config.db')

	web_host = get_ip_address(opt_ldr.fetch('WEB_INTERFACE'))

	server = www.RadioWebServer(web_host, opt_ldr.fetch('WEB_HTTP_PORT'))
	server.svc_setup(port=opt_ldr.fetch('WEB_LISTEN_PORT'))
	server.svc_loop()

	logging.debug('[ Web ] Loop service started on port ' + str(opt_ldr.fetch('WEB_LISTEN_PORT')))

	try:
		while True:
			pass
	except KeyboardInterrupt as e:
		logging.debug('[ Web ] Ctrl-C. Quitting...')
		server.svc_cleanup()
		server.stop()

		logging.debug('[ Web ] Cleanup done.')
		return 0

	return 0


if __name__ == "__main__":
	status = main()
	logging.info('[ Web ] All Done')

