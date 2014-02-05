#!/usr/bin/env python

import logging
import serial
import time
from threading import Lock

log = logging.getLogger("recoverserial")

class RecoverSerial(serial.Serial):

	def log_error(self, e):
		msg = str(e)
		if msg != self.lasterror:
			log.error(msg)
			self.lasterror = msg

	def __init__(self, *args, **kwargs):
		self.object_nr = 0
		self.recover_lock = Lock()
		self.lasterror = None
		while True:
			try:
				return super(RecoverSerial, self).__init__(*args, **kwargs)
			except serial.SerialException as e:
				self.log_error(e)
				time.sleep(1)

	def recover(self, nr):
		self.recover_lock.acquire()
		while nr == self.object_nr:
			time.sleep(1)
			try:
				self.close()
				self.open()
				self.object_nr += 1
			except serial.SerialException as e:
				self.log_error(e)
				pass

		self.recover_lock.release()

	def readline(self, *args, **kwargs):
		nr = self.object_nr
		try:
			return super(RecoverSerial, self).readline(*args, **kwargs)
		except serial.SerialException as e:
			self.log_error(e)
			self.recover(nr)
			return ''

	def write(self, *args, **kwargs):
		while True:
			nr = self.object_nr
			try:
				return super(RecoverSerial, self).write(*args, **kwargs)
			except serial.SerialException as e:
				self.log_error(e)
				self.recover(nr)

