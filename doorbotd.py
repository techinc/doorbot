#!/usr/bin/env python

import argparse
import logging
import select
import socket
import sys
import sqlite3
import time
import re

import doorbot
import doorio
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

dbfile  = "user.db"
logfile = "doorbot.log"

bindhost, port = '::1', 4242

sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind( (bindhost, port) )
sock.listen(5)

#logging.basicConfig(filename=logfile, format="%(asctime)-15s: %(message)s", level=logging.DEBUG)
logging.basicConfig(filename=logfile, format="%(asctime)-15s: %(message)s", level=logging.INFO)
log = logging.getLogger("doorbotd")

log.info("Doorbot started")

conn = sqlite3.connect(dbfile)

auth = recoverserial.RecoverSerial(auth_dev['dev'], auth_dev['baudrate'])
lock = recoverserial.RecoverSerial(lock_dev['dev'], lock_dev['baudrate'])
cmd_in = sys.stdin

door_io = doorio.DoorIO(auth_serial=auth, lock_serial=lock, socket=sock)
#door_io = doorio.DoorIO(auth_serial=auth, lock_serial=lock, cmd_in=cmd_in, socket=sock)

doorbot = doorbot.Doorbot(conn, door_io)
doorbot.run()

