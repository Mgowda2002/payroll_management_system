import sqlite3

def create_tables():
    conn = sqlite3.connect("payroll.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT,
            base_salary REAL,
            hra_percent REAL,
            tax_percent REAL,
            leaves_taken INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER,
            month TEXT,
            net_salary REAL,
            generated_on TEXT,
            FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database and tables created successfully.")

if __name__ == "__main__":
    create_tables()
