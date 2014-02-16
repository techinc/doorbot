#!/usr/bin/env python

import collections
import re
import socket
import sqlite3
import sys
import os

import userdb

try:
    from rfidconv import valid_rfid, encode_rfid, decode_rfid
except ImportError:
    def valid_rfid(rfid):
        return True
    def encode_rfid(rfid):
        return rfid
    def decode_rfid(rfid):
        return rfid

def path_relative(name):
    return os.path.join(os.path.dirname(__file__), name)

dbfile = path_relative("db/user.db")

host, port = '::1', 4242

conn = None

def get_conn():
    global conn
    if conn == None:
        conn = sqlite3.connect(dbfile)
    return conn

def list_users():
    users = userdb.get_users(get_conn())
    users.sort(key=lambda x:x['rfid'])
    for row in users:
        row['rfid'] = decode_rfid(row['rfid'])
        row['authorised'] = ('disabled','enabled')[int(row['authorised']==True)]
        sys.stdout.write('{rfid} {authorised}\n'.format(**row))

def export_users():
    for row in userdb.get_users(get_conn()):
        row['rfid'] = decode_rfid(row['rfid'])
        sys.stdout.write('{rfid} {authorised} {hash}\n'.format(**row))

def change_pin(rfid, pin):

    dbrfid = encode_rfid(rfid)

    if not re.match("^[0-9]*$", pin):
        raise ValueError("bad pin")

    if not userdb.update_pin(get_conn(), dbrfid, pin):
        raise ValueError("fob {0} does not exists".format(rfid))


def import_user(rfid, authorised, pin, plain=False):

    dbrfid = encode_rfid(rfid)

    if authorised not in '01':
        raise ValueError("bad authorised field")

    if plain:
        if not re.match("^[0-9]*$", pin):
            raise ValueError("bad pin")

        func = userdb.add_user
    else:
        if not re.match("^[0-9a-fA-F]*$", pin):
            raise ValueError("bad pin hash")

        func = userdb.import_user

    if not func(get_conn(), dbrfid, pin, int(authorised)):
        raise ValueError("fob {0} already exists".format(rfid))

def import_users(plain=False):
    for line in sys.stdin:
        line = line.rstrip('\n\r\0')
        fields = line.split(' ')
        try:
            if len(fields) != 3:
                raise ValueError("bad input")

            rfid, authorised, pin = fields
            import_user(rfid, authorised, pin)

            print "fob {0} imported".format(rfid)

        except ValueError as e:
            print str(e)

def import_plain():
    import_users(plain=True)

def delete(rfid):
    if valid_rfid(rfid):
        if userdb.del_user(get_conn(), encode_rfid(rfid)):
            print "fob deleted"
        else:
            print "fob not in the system"
    else:
        print "bad fob code {0}".format(rfid)

def enable(rfid):
    if valid_rfid(rfid):
        if userdb.enable(get_conn(), encode_rfid(rfid)):
            print "fob enabled"
        else:
            print "fob not in the system"
    else:
        print "bad fob code {0}".format(rfid)

def disable(rfid):
    if valid_rfid(rfid):
        if userdb.disable(get_conn(), encode_rfid(rfid)):
            print "fob disabled"
        else:
            print "fob not in the system"
    else:
        print "bad fob code {0}".format(rfid)

sock_commands = ('addkey', 'openmode', 'authmode', 'resetpin', 'rfidlisten', 'shutdown', 'restart')

db_commands = collections.OrderedDict([
    ( 'initdb'       , (userdb.init_db, 0, '') ),
    ( 'list'         , (list_users, 0, '') ),
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
        func(*args)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()

    doorctl(*sys.argv[1:])

