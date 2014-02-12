#!/usr/bin/env python

import sys, sqlite3, scrypt, random


def randstr(length):
    return ''.join(chr(random.randint(0,255)) for i in range(length))

def create_hash(pin):
    return scrypt.encrypt(randstr(64), pin, maxtime=1.).encode('hex')

def verify_hash(pin_hash, pin):
    try:
        scrypt.decrypt(pin_hash.decode('hex'), pin)
        return True
    except scrypt.error:
        return False

USER_FIELDS = [
	'id',
	'rfid',
	'hash',
	'authorised',
]

USER_TYPES = {
	'id': int,
	'rfid': str,
	'hash': str,
	'authorised': int
}

def user_dict(row):
	return dict( zip( USER_FIELDS, row) )

def init_db(conn):
	c = conn.cursor()
	c.execute('''CREATE TABLE users '''+\
	          '''(id integer primary key, text, rfid text, hash text, authorised integer)''')
	conn.commit()

def verify_login(conn, rfid, pin):
	c = conn.cursor()
	c.execute('''SELECT id, rfid, hash, authorised FROM users WHERE rfid=?''', (rfid,) )
	for row in c.fetchall():
		pin_hash = row[2]
		if verify_hash(pin_hash, pin) and row[3]:
			return user_dict(row)
	else:
		return None

def add_user(conn, rfid, pin, authorised):
	c = conn.cursor()
	c.execute('''INSERT INTO users (rfid, hash, authorised) VALUES (?,?,?)''',
	          (rfid, create_hash(pin), int(authorised)) )
	conn.commit()

def update_pin(conn, rfid, pin):
	c = conn.cursor()
	c.execute('''UPDATE users SET hash=? WHERE rfid=?''',
	          (create_hash(pin), rfid) )
	conn.commit()

def find_users(conn, user):
	fields = [ (k,v,USER_TYPES[k]) for k,v in user.iteritems() if k in USER_FIELDS ]
	values = tuple( t(v) for k,v,t in fields )
	keys = ' AND '.join( k+'=?' for k,v,t in fields )

	where_clause = ''
	if keys != '':
		where_clause = 'WHERE ' + keys

	c = conn.cursor()
	c.execute('''SELECT id, rfid, hash, authorised FROM users '''+where_clause, values )
	return [ user_dict(row) for row in c ]

def get_users(conn):
	return find_users(conn, {})

def user_exists(conn, user):
	return len(find_users(conn, user)) > 0

def del_user(conn, user):
	fields = [ (k,v,USER_TYPES[k]) for k,v in user.iteritems() if k in USER_FIELDS ]
	values = tuple( t(v) for k,v,t in fields )
	keys = ' AND '.join( k+'=?' for k,v,t in fields )
	if keys != '':
		c = conn.cursor()
		c.execute('''DELETE FROM users WHERE '''+keys, values )
		conn.commit()

