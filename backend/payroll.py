import sqlite3
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

DB_NAME = "payroll.db"

def connect_db():
    return sqlite3.connect(DB_NAME)

def add_employee(name, role, base_salary, hra_percent, tax_percent):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (name, role, base_salary, hra_percent, tax_percent, leaves_taken)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (name, role, base_salary, hra_percent, tax_percent))
    conn.commit()
    conn.close()
    print(f"✅ Employee '{name}' added successfully.")

def view_employees():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, name, role FROM employees")
    employees = cursor.fetchall()
    conn.close()
    print("\n📋 Employee List:")
    for emp in employees:
        print(f"ID: {emp[0]} | Name: {emp[1]} | Role: {emp[2]}")
    return employees

def calculate_salary(emp_id, month, leaves):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name, base_salary, hra_percent, tax_percent FROM employees WHERE emp_id = ?", (emp_id,))
    row = cursor.fetchone()
    if not row:
        print("❌ Employee not found.")
        return

    name, base_salary, hra_percent, tax_percent = row
    total_salary = base_salary + (base_salary * hra_percent / 100)
    salary_after_tax = total_salary - (total_salary * tax_percent / 100)
    leave_penalty = (salary_after_tax / 30) * leaves
    net_salary = round(salary_after_tax - leave_penalty, 2)

    cursor.execute("""
        INSERT INTO payroll (emp_id, month, net_salary, generated_on)
        VALUES (?, ?, ?, ?)
    """, (emp_id, month, net_salary, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    print(f"\n💸 Payroll for {name} (Month: {month})")
    print(f"Net Salary after tax and {leaves} leaves: ₹{net_salary}")

    return net_salary

# ✅ Export all payroll records to CSV
def export_all_payroll_to_csv(filename="payroll_export.csv"):
    conn = connect_db()
    df = pd.read_sql_query("SELECT * FROM payroll", conn)
    df.to_csv(filename, index=False)
    conn.close()
    return filename

# ✅ Generate payslip for a specific employee and month as PDF
def generate_payslip_pdf(emp_id, month, filename="payslip.pdf"):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.name, e.role, p.net_salary, p.generated_on
        FROM employees e
        JOIN payroll p ON e.emp_id = p.emp_id
        WHERE e.emp_id=? AND p.month=?
    """, (emp_id, month))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    name, role, net_salary, date = result
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 780, "Company Name Pvt. Ltd.")
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Employee Name: {name}")
    c.drawString(100, 730, f"Role: {role}")
    c.drawString(100, 710, f"Month: {month}")
    c.drawString(100, 690, f"Net Salary: ₹{net_salary}")
    c.drawString(100, 670, f"Generated on: {date}")
    c.save()
    return filename

# Example usage (Optional for manual testing)
if __name__ == "__main__":
    add_employee("Ravi Kumar", "Software Engineer", 50000, 20, 10)
    view_employees()
    calculate_salary(emp_id=1, month="June", leaves=2)
    export_all_payroll_to_csv()
    generate_payslip_pdf(emp_id=1, month="June")
