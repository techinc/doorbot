#!/usr/bin/env python

import sqlite3

import userdb

dbfile  = "user.db"

conn = sqlite3.connect(dbfile)

userdb.init_db(conn)
