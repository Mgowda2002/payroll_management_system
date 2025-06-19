import sqlite3

conn = sqlite3.connect("payroll.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id INTEGER,
    date TEXT,
    reason TEXT,
    FOREIGN KEY(emp_id) REFERENCES employees(emp_id)
)
""")

conn.commit()
conn.close()
print("✅ Leave table created.")
