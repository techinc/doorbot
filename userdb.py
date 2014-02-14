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
    'rfid',
    'hash',
    'authorised',
]

USER_TYPES = {
    'rfid': str,
    'hash': str,
    'authorised': int
}

def user_dict(row):
    return dict( zip( USER_FIELDS, row) )

def init_db(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE users '''+\
              '''(rfid text unique, hash text, authorised integer)''')
    conn.commit()

def verify_login(conn, rfid, pin):
    c = conn.cursor()
    c.execute('''SELECT rfid, hash, authorised FROM users WHERE rfid=?''', (rfid,) )
    result = c.fetchall()

    # prevent infoleak :-)
    c.execute('''SELECT rfid, hash, authorised FROM users LIMIT 1''' )
    result_fake = c.fetchall()

    if len(result) > 0:
        pin_hash = result[0][1]
        authorised = result[0][2]
    elif len(result_fake) > 0:
        pin_hash = result_fake[0][1]
        authorised = 0
    else:
        return None

    if verify_hash(pin_hash, pin) and authorised:
        return user_dict(result[0])
    else:
        return None

def import_user(conn, rfid, pinhash, authorised):
    c = conn.cursor()
    c.execute('''INSERT INTO users (rfid, hash, authorised) VALUES (?,?,?)''',
              (rfid, pinhash, int(authorised)) )
    conn.commit()

def add_user(conn, rfid, pin, authorised):
    import_user(conn, rfid, create_hash(pin), authorised)

def update_pin(conn, rfid, pin):
    c = conn.cursor()
    c.execute('''UPDATE users SET hash=? WHERE rfid=?''',
              (create_hash(pin), rfid) )
    conn.commit()

def enable(conn, rfid):
    c = conn.cursor()
    c.execute('''UPDATE users SET authorised=1 WHERE rfid=?''', (rfid,))
    conn.commit()

def disable(conn, rfid):
    c = conn.cursor()
    c.execute('''UPDATE users SET authorised=0 WHERE rfid=?''', (rfid,))
    conn.commit()

def find_user(conn, rfid):
    c = conn.cursor()
    c.execute('''SELECT rfid, hash, authorised FROM users WHERE rfid=?''', (rfid,) )
    result = c.fetchall()
    if len(result) > 0:
        return user_dict(result[0])
    else:
        return None

def get_users(conn):
    c = conn.cursor()
    c.execute('''SELECT rfid, hash, authorised FROM users''')
    return [ user_dict(row) for row in c ]

def user_exists(conn, rfid):
    return find_user(conn, rfid) != None

def del_user(conn, rfid):
    c = conn.cursor()
    c.execute('''DELETE FROM users WHERE rfid=?''', (rfid,) )
    conn.commit()

