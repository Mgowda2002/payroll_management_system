import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
from backend.nlp_summary import generate_summary
from backend.langchain_chat import ask_question
from backend.payroll import generate_payslip_pdf, export_all_payroll_to_csv

DB_NAME = "payroll.db"

# ----------------- DB Connection -----------------
def connect_db():
    return sqlite3.connect(DB_NAME)

def add_employee(name, role, base_salary, hra, tax):
    conn = connect_db()
    conn.execute("""
        INSERT INTO employees (name, role, base_salary, hra_percent, tax_percent, leaves_taken)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (name, role, base_salary, hra, tax))
    conn.commit()
    conn.close()

def get_employees():
    conn = connect_db()
    df = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    return df

def calculate_salary(emp_id, leaves, month):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, base_salary, hra_percent, tax_percent FROM employees WHERE emp_id=?", (emp_id,))
    row = cursor.fetchone()
    if not row:
        return None
    name, base, hra, tax = row
    gross = base + (base * hra / 100)
    net_before_penalty = gross - (gross * tax / 100)
    penalty = (net_before_penalty / 30) * leaves
    net_salary = round(net_before_penalty - penalty, 2)
    cursor.execute("""
        INSERT INTO payroll (emp_id, month, net_salary, generated_on)
        VALUES (?, ?, ?, ?)
    """, (emp_id, month, net_salary, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return {
        "name": name,
        "base_salary": base,
        "hra_percent": hra,
        "tax_percent": tax,
        "leaves": leaves,
        "net_salary": net_salary
    }

# ------------------- Styling -------------------
def inject_theme(dark=False):
    if dark:
        css = """
        <style>
            html, body, [class*="css"]  {
                background-color: #121212 !important;
                color: white !important;
                font-family: 'Segoe UI', sans-serif;
            }
            .stApp {
                background-color: #1e1e1e;
            }
            h1, h2, h3 {
                color: #7fd4ff;
            }
            .stButton>button {
                background-color: #7fd4ff;
                color: black;
                font-weight: bold;
                border-radius: 8px;
            }
            .stButton>button:hover {
                background-color: #5fbce6;
            }
        </style>
        """
    else:
        css = """
        <style>
            html, body, [class*="css"]  {
                background-color: #f7f9fc !important;
                color: black !important;
                font-family: 'Segoe UI', sans-serif;
            }
            .stApp {
                background-color: #ffffff;
            }
            h1, h2, h3 {
                color: #1f4e79;
            }
            .stButton>button {
                background-color: #1f4e79;
                color: white;
                font-weight: bold;
                border-radius: 8px;
            }
            .stButton>button:hover {
                background-color: #163d5c;
            }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

# ------------------- Login -------------------
def show_login():
    inject_theme(st.session_state.get("dark_mode", False))
    st.title("🔐 Payroll Management Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state["logged_in"] = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

# ------------------- Dashboard -------------------
def show_dashboard():
    st.set_page_config(page_title="Payroll Dashboard", layout="wide")

    # Dark Mode Toggle
    col1, col2 = st.columns([9, 1])
    with col2:
        st.session_state.dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.get("dark_mode", False))
    inject_theme(st.session_state["dark_mode"])

    st.markdown("<h1 style='text-align: center;'>📋 Payroll Management Dashboard</h1>", unsafe_allow_html=True)

    tabs = st.tabs([
        "➕ Add Employee", "👥 View/Search Employees", "💰 Salary",
        "📄 Payslip/Reports", "🧠 AI Summary", "💬 Bot", "📊 Analytics",
        "📅 Leave Tracker", "🗓️ Attendance", "🚪 Logout"
    ])

    # ➕ Add Employee
    with tabs[0]:
        st.subheader("➕ Add New Employee")
        name = st.text_input("Name")
        role = st.text_input("Role")
        base = st.number_input("Base Salary", min_value=0.0)
        hra = st.slider("HRA %", 0, 50, 20)
        tax = st.slider("Tax %", 0, 30, 10)
        if st.button("Add Employee"):
            if name and role:
                add_employee(name, role, base, hra, tax)
                st.success(f"{name} added successfully!")
            else:
                st.warning("Please fill in all fields.")

    # 👥 View/Search Employees
    with tabs[1]:
        st.subheader("👥 Employee List & Search")
        df = get_employees()
        search = st.text_input("Search by Name or Role")
        if search:
            df = df[df['name'].str.contains(search, case=False) | df['role'].str.contains(search, case=False)]
        st.dataframe(df)
        if st.button("📥 Download Employee List"):
            df.to_csv("employee_list.csv", index=False)
            with open("employee_list.csv", "rb") as f:
                st.download_button("Download CSV", f, file_name="employee_list.csv")

    # 💰 Generate Salary
    with tabs[2]:
        st.subheader("💰 Generate Salary")
        df = get_employees()
        if not df.empty:
            emp_map = {f"{row['name']} (ID:{row['emp_id']})": row['emp_id'] for _, row in df.iterrows()}
            emp = st.selectbox("Select Employee", list(emp_map.keys()))
            leaves = st.slider("Leaves Taken", 0, 10, 0)
            month = st.text_input("Payroll Month", value="June")
            if st.button("Generate Salary"):
                result = calculate_salary(emp_map[emp], leaves, month)
                if result:
                    st.success(f"Net Salary: ₹{result['net_salary']}")
                    st.json(result)
        else:
            st.warning("No employees found.")

    # 📄 Payslip / Export
    with tabs[3]:
        st.subheader("📤 Export Payroll & Payslip")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export All Payroll to CSV"):
                file = export_all_payroll_to_csv()
                with open(file, "rb") as f:
                    st.download_button("Download CSV", f, file_name=file)
        with col2:
            df = get_employees()
            if not df.empty:
                emp_map = {f"{row['name']} (ID:{row['emp_id']})": row['emp_id'] for _, row in df.iterrows()}
                emp_sel = st.selectbox("Select Employee", list(emp_map.keys()), key="pdf_emp")
                month_sel = st.text_input("Month", value="June", key="pdf_month")
                if st.button("Generate Payslip PDF"):
                    file = generate_payslip_pdf(emp_map[emp_sel], month_sel)
                    if file:
                        with open(file, "rb") as f:
                            st.download_button("Download Payslip", f, file_name=file)
                    else:
                        st.error("No payroll record found for that month.")

    # 🧠 AI Summary
    with tabs[4]:
        st.subheader("🧠 AI Summary")
        month = st.text_input("Month", value="June", key="ai_month")
        if st.button("Generate Summary"):
            st.write(generate_summary(month))

    # 💬 Bot
    with tabs[5]:
        st.subheader("💬 Ask Payroll Bot")
        question = st.text_input("Ask your question (e.g., What is HRA?)")
        if st.button("Ask"):
            if question:
                st.write(ask_question(question))
            else:
                st.warning("Please type a question.")

    # 📊 Analytics
    with tabs[6]:
        st.subheader("📊 Payroll Analytics")
        conn = connect_db()
        df = pd.read_sql("SELECT * FROM payroll JOIN employees ON payroll.emp_id = employees.emp_id", conn)
        conn.close()
        if not df.empty:
            m = st.selectbox("Select Month", df['month'].unique())
            mdf = df[df['month'] == m]
            st.metric("Total Paid", f"₹{mdf['net_salary'].sum():,.2f}")
            top = mdf.loc[mdf['net_salary'].idxmax()]
            st.metric("Highest Paid", f"{top['name']} ₹{top['net_salary']}")
            st.bar_chart(mdf[['name', 'net_salary']].set_index('name'))
        else:
            st.warning("No payroll data yet.")

    # 📅 Leave Tracker
    with tabs[7]:
        st.subheader("📅 Leave Tracker")
        df = get_employees()
        if not df.empty:
            emp_map = {f"{row['name']} (ID:{row['emp_id']})": row['emp_id'] for _, row in df.iterrows()}
            emp = st.selectbox("Select Employee", list(emp_map.keys()), key="leave_emp")
            l_date = st.date_input("Leave Date")
            reason = st.text_input("Reason")
            if st.button("Record Leave"):
                conn = connect_db()
                conn.execute("INSERT INTO leaves (emp_id, date, reason) VALUES (?, ?, ?)", 
                             (emp_map[emp], l_date.strftime("%Y-%m-%d"), reason))
                conn.commit()
                conn.close()
                st.success("Leave Recorded.")
            conn = connect_db()
            df = pd.read_sql("""
                SELECT date, reason, name 
                FROM leaves JOIN employees ON leaves.emp_id = employees.emp_id 
                ORDER BY date DESC
            """, conn)
            conn.close()
            st.dataframe(df)
        else:
            st.warning("No employees found.")

    # 🗓️ Attendance
    with tabs[8]:
        st.subheader("🗓️ Attendance Tracker")
        df = get_employees()
        if not df.empty:
            emp_map = {f"{row['name']} (ID:{row['emp_id']})": row['emp_id'] for _, row in df.iterrows()}
            emp = st.selectbox("Select Employee", list(emp_map.keys()), key="att_emp")
            a_date = st.date_input("Date", value=date.today(), key="att_date")
            status = st.radio("Status", ["Present", "Absent"], horizontal=True)
            if st.button("Record Attendance"):
                conn = connect_db()
                conn.execute("INSERT INTO attendance (emp_id, date, status) VALUES (?, ?, ?)", 
                             (emp_map[emp], a_date.strftime("%Y-%m-%d"), status))
                conn.commit()
                conn.close()
                st.success("Attendance Recorded.")
            conn = connect_db()
            df = pd.read_sql("""
                SELECT date, status, name 
                FROM attendance JOIN employees ON attendance.emp_id = employees.emp_id 
                ORDER BY date DESC
            """, conn)
            conn.close()
            st.dataframe(df)
        else:
            st.warning("No employee data.")

    # 🚪 Logout
    with tabs[9]:
        st.subheader("🚪 Logout")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# ------------------- Main -------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    show_dashboard()
else:
    show_login()
