#!/usr/bin/env python

import logging
import select
import re

class DoorIO(object):

	def __init__(self, auth_serial, lock_serial, cmd_in, cmd_out):
		self._auth    = auth_serial
		self._lock    = lock_serial
		self._cmd_in  = cmd_in
		self._cmd_out = cmd_out
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

	def get_event(self, timeout=None):
		waitlist = [ f.fileno() for f in (self._auth, self._lock, self._cmd_in) ]
		line = ''
	   	r,w,x = select.select(waitlist, [], [], timeout)

		if r == []:
			return { 'type': 'timeout', 'value': timeout }

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

		if self._cmd_in.fileno() in r:
			return {
				'type': 'command',
				'value': self._cmd_in.readline().rstrip('\r\n\0'),
				'out': self._cmd_out
			}

		return { 'type' : 'unknown', 'value': line }
