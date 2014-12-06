#!/usr/bin/env python

import logging

import service.www as www

host = '192.168.0.12'
port = 80
www_listener_port = 6100

def main():
	logging.basicConfig(level=logging.DEBUG)

	logging.debug('Startup server')

	server = www.RadioWebServer(host, port)
	server.svc_setup(port=www_listener_port)
	server.svc_loop()

	try:
		while True:
			pass
	except KeyboardInterrupt as e:
		logging.debug('Ctrl-C. Quitting...')
		server.svc_cleanup()
		server.stop()

		logging.debug('Cleanup done.')
		return 0

	return 0


if __name__ == "__main__":
	status = main()
	logging.info('All Done')

