#!/usr/bin/env python

import collections
import re
import socket
import sqlite3
import sys
import os

import userdb

try:
    from rfidconv import encode_rfid, decode_rfid
except ImportError:
    def encode_rfid(rfid):
        return rfid
    def decode_rfid(rfid):
        return rfid

def path_relative(name):
    return os.path.join(os.path.dirname(__file__), name)

dbfile  = path_relative("db/user.db")

host, port = '::1', 4242

def print_users(conn):
    for row in userdb.get_users(conn):
        row['rfid'] = decode_rfid(row['rfid'])
        row['authorised'] = ('disabled','enabled')[int(row['authorised']==True)]
        sys.stdout.write('{rfid} {authorised}\n'.format(**row))

def export_users(conn):
    for row in userdb.get_users(conn):
        row['rfid'] = decode_rfid(row['rfid'])
        sys.stdout.write('{rfid} {authorised} {hash}\n'.format(**row))

def import_users(conn):
    users = []
    for line in sys.stdin:
        line = line.rstrip('\n\r\0')
        fields = line.split(' ')
        if len(fields) != 3:
            raise ValueError("bad input")

        rfid = encode_rfid(fields[0])
        authorised = int(fields[1])
        if not 0 <= authorised <= 1:
            raise ValueError("bad authorised value")
        pinhash = fields[2]
        if not re.match("^[0-9a-fA-F]*$", pinhash):
            raise ValueError("bad pin hash")
        users += [ (rfid, pinhash, authorised) ]

    for rfid, pinhash, authorised in users:
        userdb.import_user(conn, rfid, pinhash, authorised)

def import_plain(conn):
    users = []
    for line in sys.stdin:
        line = line.rstrip('\n\r\0')
        fields = line.split(' ')
        if len(fields) != 3:
            raise ValueError("bad input")

        rfid = encode_rfid(fields[0])
        authorised = int(fields[1])
        if not 0 <= authorised <= 1:
            raise ValueError("bad authorised value")
        pin = fields[2]
        if not re.match("^[0-9]*$", pin):
            raise ValueError("bad pin")

        users += [ (rfid, pin, authorised) ]

    for rfid, pin, authorised in users:
        userdb.add_user(conn, rfid, pin, authorised)

def delete(conn, rfid):
    userdb.del_user(conn, encode_rfid(rfid))

def enable(conn, rfid):
    userdb.enable(conn, encode_rfid(rfid))

def disable(conn, rfid):
    userdb.disable(conn, encode_rfid(rfid))

sock_commands = ('addkey', 'openmode', 'authmode', 'resetpin', 'rfidlisten', 'shutdown', 'restart')

db_commands = collections.OrderedDict([
    ( 'initdb'       , (userdb.init_db, 0, '') ),
    ( 'print'        , (print_users, 0, '') ),
    ( 'export'       , (export_users, 0, '') ),
    ( 'import'       , (import_users, 0, ' < file') ),
    ( 'import-plain' , (import_plain, 0, ' < file') ),
    ( 'delete'       , (delete, 1, ' <key-id>') ),
    ( 'enable'       , (enable, 1, ' <key-id>') ),
    ( 'disable'      , (disable, 1, ' <key-id>') ),
])

def usage():
    subcmds = sock_commands+tuple(k+v[2] for k,v in db_commands.iteritems())

    pre = "Usage: "+sys.argv[0]
    for cmd in subcmds:
        print pre+' '+cmd
        pre = "       "+sys.argv[0]
    sys.exit(1)

def socket_command(command, close=True):
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.connect( (host, port) )
    s.send(command+'\n')
    if close:
        s.close()
    else:
        return s

def doorctl(cmd, *args):

    if cmd in sock_commands:
        if cmd == 'rfidlisten':
            for line in socket_command(cmd, close = False).makefile():
                print decode_rfid(line.rstrip('\n\r\0'))
        else:
            socket_command(cmd)
    elif cmd in db_commands:
        func, n_args, _ = db_commands[cmd]
        if len(args) != n_args:
            usage()
        conn = sqlite3.connect(dbfile)
        func(conn, *args)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()

    doorctl(*sys.argv[1:])

