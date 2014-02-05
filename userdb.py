#!/usr/bin/env python

import sys, sqlite3, scrypt


def randstr(length):
    return ''.join(chr(random.randint(0,255)) for i in range(length))

def create_hash(pin):
    return scrypt.encrypt(randstr(64), pin, maxtime=1.)

def verify_hash(pin_hash, pin):
    try:
        scrypt.decrypt(pin_hash, pin)
        return True
    except scrypt.error:
        return False

USER_FIELDS = {
	'id': int,
	'name': str,
	'rfid': str,
	'hash': str,
	'authorised': int
}

def user_dict(row):
	return dict( zip( USER_FIELDS, row) )

def init_db(conn):
	c = conn.cursor()
	c.execute('''CREATE TABLE users '''+\
	          '''(id integer primary key, name text, rfid text, hash text, authorised integer)''')
	conn.commit()

def get_users(conn):
	c = conn.cursor()
	c.execute('''SELECT id, name, rfid, hash, authorised FROM users''')
	return [ user_dict(row) for row in c ]

def verify_login(conn, rfid, pin):
	c = conn.cursor()
	c.execute('''SELECT id, name, rfid, hash, authorised FROM users WHERE rfid=?''', (rfid,) )
	for name, pin_hash, authorised in c.fetchall():
		if verify_hash(pin_hash, pin):
			return user_dict(row)
	else:
		return None

def add_user(conn, name, rfid, pin, authorised):
	c = conn.cursor()
	c.execute('''UPDATE INTO users (name, rfid, hash, authorised) VALUES (?,?,?,?)''',
	          (name, rfid, create_hash(pin), int(authorised)) )
	conn.commit()
	
def del_user(conn, user):
	fields = [ (k,v,USER_FIELDS[k]) for k,v in user.iteritems() if k in USER_FIELDS ]
	values = tuple( t(v) for k,v,t in fields )
	keys = ' AND '.join( k+'=?' for k,v,t in fields )
	if keys != '':
		c = conn.cursor()
		c.execute('''DELETE FROM users WHERE '''+keys, values )
		conn.commit()

