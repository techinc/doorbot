#!/usr/bin/env python

import argparse
import logging
import select
import sys
import sqlite3
import time
import re

import doorbot
import recoverserial
import userdb

#
# UDEV Rules:
#
# SUBSYSTEMS=="usb", KERNEL=="ttyUSB*", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="XXXXXXXX", SYMLINK+="ttyAUTH"
# SUBSYSTEMS=="usb", KERNEL=="ttyUSB*", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="XXXXXXXX", SYMLINK+="ttyLOCK"
#

auth_dev = {
	'dev'      : "/dev/ttyAUTH",
	'baudrate' : 9600,
}

lock_dev = {
	'dev'      : "/dev/ttyLOCK",
	'baudrate' : 9600,
}


userdb  = "user.db"
logfile = "doorbot.log"

timeouts = {
	'PIN TIMEOUT'    :    10,
	'UNLOCK TIMEOUT' :     5,
	'RELOCK TIMEOUT' :     1,
	'STOP TIMEOUT'   :  None,
}

logging.basicConfig(filename=logfile, format="%(asctime)-15s: %(message)s", level=logging.DEBUG)
log = logging.getLogger("doorbotd")

log.info("Doorbot started")

conn = sqlite3.connect(userdb)

auth = recoverserial.RecoverSerial(auth_dev['dev'], auth_dev['baudrate'])
lock = recoverserial.RecoverSerial(lock_dev['dev'], lock_dev['baudrate'])
cmd_in = sys.stdin
cmd_out = sys.stdout

doorbot = doorbot.Doorbot(conn)
timeout = None

while True:
	waitlist = [ f.fileno() for f in (auth, lock, cmd_in) ]

	if timeout:
		pre_time = time.time()

   	r,w,x = select.select(waitlist, [], [], timeout)

	if timeout:
		timeout -= time.time()-pre_time
		doorbot.timeout()
		timeout = None

	actions = []
	if lock.fileno() in r:
		line = lock.readline().rstrip('\r\n\0')
		if line == 'OPEN':
			actions += doorbot.door_open()
		elif line == 'CLOSED':
			actions += doorbot.door_closed()

	if auth.fileno() in r:
		line = auth.readline().rstrip('\r\n\0')
		if line.startswith("KEY "):
			key = line.strip("KEY ")
			if key in "0123456789BC":
				actions += doorbot.key_pressed(key)

		if line.startswith("RFID "):
			code = line.strip("RFID ")
			if re.match("^[01]{34}$", code):
				actions += doorbot.rfid_scanned(code)

	if cmd_in.fileno() in r:
		print "COMMAND:" + cmd_in.readline(),

	for action in actions:
		print "action: " + action

		if action in ('DENIED', 'GRANTED', 'BEEP', 'LED ON', 'LED OFF', 'LED BLINK'):
			auth.write(action+"\n")

		if action in ('UNLOCK', 'LOCK'):
			lock.write(action+"\n")

		if action in timeouts.keys():
			timeout = timeouts[action]
