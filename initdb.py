#!/usr/bin/env python

import os
import sqlite3
import userdb

def path_relative(name):
    return os.path.join(os.path.dirname(__file__), name)

os.mkdir(path_relative("db"))

dbfile  = path_relative("db/user.db")

conn = sqlite3.connect(dbfile)

userdb.init_db(conn)
