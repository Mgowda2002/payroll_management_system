import sqlite3
import pandas as pd
from dotenv import load_dotenv
import os

# ✅ New imports (RECOMMENDED)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import HuggingFaceHub
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document

# ✅ Load environment variables from .env
load_dotenv()
token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# 📄 Load payroll data as plain text
def load_payroll_text():
    conn = sqlite3.connect("payroll.db")
    df = pd.read_sql_query("SELECT * FROM payroll", conn)
    conn.close()

    if df.empty:
        return ""

    text = ""
    for _, row in df.iterrows():
        text += f"Employee ID {row['emp_id']} received ₹{row['net_salary']} for {row['month']}. "
    return text

# 🔍 Ask question using LangChain
def ask_question(query):
    text = load_payroll_text()
    if not text:
        return "❌ No payroll data available."

    docs = [Document(page_content=text)]
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    relevant_docs = vectorstore.similarity_search(query)

    llm = HuggingFaceHub(
        repo_id="google/flan-t5-small",
        model_kwargs={"temperature": 0.5},
        huggingfacehub_api_token=token  # ✅ Use .env token
    )

    chain = load_qa_chain(llm=llm, chain_type="stuff")
    result = chain.run(input_documents=relevant_docs, question=query)
    return result
