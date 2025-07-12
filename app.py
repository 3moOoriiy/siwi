import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# إعداد الاتصال بـ Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# تحميل بيانات credentials
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
client = gspread.authorize(creds)

# رابط Google Sheet الخاص بك
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1y4m9xHY2l3sMKwRiXm9aLVfmQoLErwJJAC4wuQ9zvaQ/edit"
spreadsheet = client.open_by_url(SPREADSHEET_URL)

# تحميل الأوراق المطلوبة
clients_ws = spreadsheet.worksheet("Clients")
calls_ws = spreadsheet.worksheet("Calls")
complaints_ws = spreadsheet.worksheet("Complaints")
pickups_ws = spreadsheet.worksheet("Pickups")

# تحويلها إلى DataFrames
clients_df = pd.DataFrame(clients_ws.get_all_records())
calls_df = pd.DataFrame(calls_ws.get_all_records())
complaints_df = pd.DataFrame(complaints_ws.get_all_records())
pickups_df = pd.DataFrame(pickups_ws.get_all_records())

# تصميم الواجهة
st.set_page_config(page_title="نظام بارفو", layout="wide")
st.title("📊 لوحة تحكم البيانات - Barvo")

# التبويبات
tab1, tab2, tab3, tab4 = st.tabs(["👥 العملاء", "📞 المكالمات", "❗ الشكاوى", "🚚 البيك أب"])

with tab1:
    st.subheader("👥 جدول العملاء")
    st.dataframe(clients_df)

with tab2:
    st.subheader("📞 جدول المكالمات")
    st.dataframe(calls_df)

with tab3:
    st.subheader("❗ جدول الشكاوى")
    st.dataframe(complaints_df)

with tab4:
    st.subheader("🚚 جدول البيك أب")
    st.dataframe(pickups_df)
