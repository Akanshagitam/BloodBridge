import sqlite3

conn = sqlite3.connect("bloodbridge.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT,
    phone TEXT,
    blood_group TEXT,
    city TEXT,
    state TEXT,
    availability TEXT,
    last_donation_date TEXT,
    gender TEXT,
    contact_status TEXT,
    pulse TEXT,
spo2 TEXT,
bp TEXT

)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS blood_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT,
    blood_group TEXT,
    city TEXT
)
""")
conn.commit()
conn.close()

print("Database Created Successfully")