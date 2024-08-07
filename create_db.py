import sqlite3
import os
from config import db_name

# create db if not exists
if not os.path.exists(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    #users
    c.execute('''CREATE TABLE users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  uid TEXT NOT NULL,
                  username TEXT,
                  first_name TEXT NOT NULL,
                  surname TEXT NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT NOT NULL,
                  phone TEXT,
                  verified_email BOOLEAN DEFAULT FALSE,
                  pending_deletion BOOLEAN DEFAULT FALSE,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()

    #2fa codes
    c.execute('''CREATE TABLE otp_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  uid TEXT NOT NULL,
                  code TEXT NOT NULL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # reset codes
    c.execute('''CREATE TABLE reset_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email_username TEXT NOT NULL,
                  code TEXT NOT NULL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # accounts
    c.execute('''CREATE TABLE accounts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  uid TEXT NOT NULL,
                  username TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()

    conn.close()

    print("Database created successfully")

else:
    print("Database already exists")
