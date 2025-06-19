from transformers import pipeline
import sqlite3
import pandas as pd

DB_NAME = "payroll.db"

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def fetch_payroll_data(month):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM payroll WHERE month=?", conn, params=(month,))
    conn.close()
    return df

def generate_summary(month="June"):
    df = fetch_payroll_data(month)
    if df.empty:
        return "No payroll data available for this month."

    text = ""
    for _, row in df.iterrows():
        text += f"Employee ID {row['emp_id']} received ₹{row['net_salary']} in {row['month']}. "

    if len(text) < 50:
        return text

    summary = summarizer(text, max_length=60, min_length=20, do_sample=False)
    return summary[0]['summary_text']
