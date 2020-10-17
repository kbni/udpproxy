#!/usr/bin/env python3

"""

udpproxy.py: Quick & nasty UDP proxy intended for massaging syslog

  Arguments:
    -s --send   actually send on to SEND_HOST:SEND_PORT
    -d --debug  enable debug
	-h --help   show this message

  Env Vars:
    RECV_HOST   address to bind to (default 0.0.0.0)
    RECV_PORT   port to listen on (default 55514)
    SEND_HOST   address to pass our data onto (default 127.0.0.1)
    SEND_PORT   port to pass our data onto (default RECV_PORT+1)

github: https://github.com/kbni/udpproxy

"""

import re
import os
import sys
import socket
import socketserver
from datetime import datetime

def find_shortarg(char):
	return bool(re.findall(f'(^|\s+)(-[a-z]*{char})', ' '.join(sys.argv[1:])))

RECV_HOST = os.environ.get('RECV_HOST', '0.0.0.0')
RECV_PORT = int(os.environ.get('RECV_PORT', 55514))
SEND_HOST = os.environ.get('SEND_HOST', '127.0.0.1')
SEND_PORT = int(os.environ.get('SEND_PORT', RECV_PORT+1))
DEBUG = '--debug' in sys.argv or find_shortarg('d')
SEND = '--send' in sys.argv or find_shortarg('s')
HELP = '--help' in sys.argv or find_shortarg('h')


class SyslogUDPHandler(socketserver.BaseRequestHandler):
	def handle(self):
		# Convert our incoming data to a string, trim whitespace
		data = str(bytes.decode(self.request[0].strip()))

		if DEBUG: print(f'!\n orig: {data}')

		# Process our data
		data = self.fix_watchguard_date(data)

		if DEBUG: print(f'     new: {self.client_address[0]} - {data}')
		if SEND: self.send_data(data)

	def fix_watchguard_date(self, data):
		'''
		If we are able to find a date using this format there's a good chance it has come from
		WatchGuard or some other source where the time sent is not UTC, but that's how graylog
		will interpret it. So we will replace it with a new ISO8601 timestamp.
		'''
		for old_date in re.findall(r'>([a-zA-Z]+ \d+ \d{2}:\d{2}:\d{2})\s', data):
			new_date = datetime.utcnow().isoformat().split('.')[0] + 'Z'
			if DEBUG: print(f' replace: {old_date} with {new_date}')
			data = data.replace(old_date, new_date)
		return data

	def send_data(self, data):
		if DEBUG: print(f' sending: to {SEND_HOST}:{SEND_PORT}')
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.sendto(data.encode('utf-8'), (SEND_HOST, SEND_PORT))
		sock.close()


class ThreadingUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass


if __name__ == "__main__":
	if HELP:
		output = False
		with open(__file__, 'r') as fh:
			for line in [l.rstrip() for l in fh.readlines()]:
				if line == '"""':
					if output:
						sys.exit(0)
					else:
						output = True
				elif output:
					print(line)
	try:
		server = ThreadingUDPServer((RECV_HOST, RECV_PORT), SyslogUDPHandler)
		server.serve_forever(poll_interval=0.25)
	except (IOError, SystemExit):
		raise
		sys.exit(1)
	except KeyboardInterrupt:
		if DEBUG:
			print('\nShutting down.')
		sys.exit(0)
