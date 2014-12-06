#!/usr/bin/env python

import logging

import service.www as www
import service.www_cfg as config

def main():
	logging.basicConfig(level=logging.DEBUG)

	logging.debug('Startup server')

	server = www.RadioWebServer(config.WEB_HOST, config.WEB_HTTP_PORT)
	server.svc_setup(port=config.WEB_LISTEN_PORT)
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

