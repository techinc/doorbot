#!/usr/bin/env python

import logging

import userdb

log = logging.getLogger("doorbot")

AUTH_MODE, OPEN_MODE = range(2)

class Doorbot(object):

	def __init__(self, dbconn):
		self._dbconn = dbconn
		self._mode = AUTH_MODE
		self._pin = ''

	def open_mode(self):
		return []

	def auth_mode(self):
		return []

	def door_open(self):
		log.info("door open")
		return []

	def door_closed(self):
		log.info("door closed")
		return []

	def key_pressed(self, c):
		log.info("key pressed: " + c)
		if mode == OPEN_MODE:
			if c == "B":
				return ['UNLOCK', 'UNLOCK TIMEOUT']
		else:
			return ['BEEP']

	def rfid_scanned(self, code):
		log.info("rfid code: " + code)
		return ['PIN TIMEOUT', 'LED BLINK']

	def timeout(self):
		log.info("timeout")
		return ['DENIED', 'LED OFF', 'LOCK', 'RELOCK TIMEOUT']

