#!/usr/bin/env python

import logging
import select
import re

class DoorIO(object):

	def __init__(self, auth_serial, lock_serial, cmd_in=None, socket=None):
		self._auth      = auth_serial
		self._lock      = lock_serial
		self._socklist  = []
		self._cmd_in    = cmd_in
		self._sock      = socket
		self._led_state = "LED OFF"

	def lock(self):
		self._lock.write('LOCK\n')

	def unlock(self):
		self._lock.write('UNLOCK\n')

	def beep(self):
		self._auth.write('BEEP\n')

	def denied(self):
		self._auth.write('DENIED\n')

	def granted(self):
		self._auth.write('GRANTED\n')

	def update_led(self):
		self._auth.write(self._led_state)

	def led_on(self):
		self._led_state = 'LED ON\n'
		self.update_led()

	def led_off(self):
		self._led_state = 'LED OFF\n'
		self.update_led()

	def led_blink(self):
		self._led_state = 'LED BLINK\n'
		self.update_led()

	def get_socket_line(self):
		for pair in self._socklist:
			s, data = pair
			if data.find('\n') >= 0:
				pair[1] = data[data.find('\n')+1:]
				data = data[:data.find('\n')+1]
				return data
		else:
			return None

	def read_socket_data(self, r):
		for pair in self._socklist:
			s, data = pair
			if s.fileno() in r:
				try:
					read_data = s.recv(1024)
				except IOError:
					read_data = ''

				if read_data == '':
					s.close()
					self._socklist.remove(pair)
				else:
					pair[1] += read_data

	def get_command(self, line):
		cmd = line.rstrip('\r\n\0')

		if cmd in ('addkey', 'openmode', 'authmode', 'resetpin'):
			return { 'type' :  cmd,      'value' : '' }
		else:
			return { 'type' : 'unknown', 'value' : 'unknown command:'+cmd }

	def get_event(self, timeout=None):
		sockets = [ s for s,_ in self._socklist ]
		waitlist = [ f.fileno() for f in sockets + [self._auth, self._lock, self._cmd_in, self._sock] if f != None ]
		line = ''

		line = self.get_socket_line()
		if line != None:
			return self.get_command(line)

	   	r,w,x = select.select(waitlist, [], [], timeout)

		if r == []:
			return { 'type': 'timeout', 'value': timeout }

		self.read_socket_data(r)
		line = self.get_socket_line()
		if line != None:
			return self.get_command(line)

		if self._cmd_in and self._cmd_in.fileno() in r:
			return self.get_command(self._cmd_in.readline())

		if self._sock.fileno() in r:
			new_sock,_ = self._sock.accept()
			self._socklist.append( [new_sock,''] )

		if self._lock.fileno() in r:
			line = self._lock.readline().rstrip('\r\n\0')
			if line in ('OPEN', 'CLOSED'):
				return { 'type': 'doorstate', 'value': line }

		if self._auth.fileno() in r:
			line = self._auth.readline().rstrip('\r\n\0')
			if line.startswith("KEY "):
				key = line.strip("KEY ")
				if key in "0123456789BC":
					return { 'type': 'keypress', 'value': key }

			if line.startswith("RFID "):
				code = line.strip("RFID ")
				if re.match("^[01]{34}$", code):
					return { 'type': 'rfid', 'value': code }

			if line == 'RESET':
				self.update_led()

		return { 'type' : 'unknown', 'value': line }
