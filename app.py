import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# إعداد الصفحة
st.set_page_config(
    page_title="إدارة بيانات الكول سنتر",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# إعداد CSS للتصميم
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .stTab > div > div > div > div {
        font-size: 18px;
        font-weight: bold;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# فئة لإدارة الاتصال مع Google Sheets
class GoogleSheetsManager:
    def __init__(self, credentials_json, spreadsheet_id):
        self.credentials_json = credentials_json
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.workbook = None
        self.connect()
    
    def connect(self):
        """الاتصال بـ Google Sheets"""
        try:
            if isinstance(self.credentials_json, str):
                credentials_dict = json.loads(self.credentials_json)
            else:
                credentials_dict = self.credentials_json
            
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            credentials = Credentials.from_service_account_info(
                credentials_dict, scopes=scope
            )
            self.client = gspread.authorize(credentials)
            self.workbook = self.client.open_by_key(self.spreadsheet_id)
            return True
        except Exception as e:
            st.error(f"خطأ في الاتصال بـ Google Sheets: {e}")
            return False
    
    def get_worksheet_data(self, worksheet_name):
        """جلب البيانات من ورقة عمل محددة"""
        try:
            worksheet = self.workbook.worksheet(worksheet_name)
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"خطأ في جلب البيانات من {worksheet_name}: {e}")
            return pd.DataFrame()
    
    def add_record(self, worksheet_name, record):
        """إضافة سجل جديد"""
        try:
            worksheet = self.workbook.worksheet(worksheet_name)
            worksheet.append_row(record)
            return True
        except Exception as e:
            st.error(f"خطأ في إضافة السجل: {e}")
            return False
    
    def update_record(self, worksheet_name, row_index, record):
        """تحديث سجل موجود"""
        try:
            worksheet = self.workbook.worksheet(worksheet_name)
            for i, value in enumerate(record, 1):
                worksheet.update_cell(row_index, i, value)
            return True
        except Exception as e:
            st.error(f"خطأ في تحديث السجل: {e}")
            return False

# إعداد البيانات التجريبية
@st.cache_data
def load_sample_data():
    """تحميل بيانات تجريبية للعرض"""
    customers_data = {
        'رقم العميل': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'اسم العميل': ['أحمد محمد', 'فاطمة أحمد', 'خالد علي', 'مريم سعد', 'عمر حسن'],
        'رقم الهاتف': ['01234567890', '01123456789', '01012345678', '01234567891', '01123456780'],
        'البريد الإلكتروني': ['ahmed@email.com', 'fatima@email.com', 'khaled@email.com', 'mariam@email.com', 'omar@email.com'],
        'المدينة': ['القاهرة', 'الإسكندرية', 'الجيزة', 'المنصورة', 'أسوان'],
        'تاريخ التسجيل': ['2024-01-15', '2024-01-20', '2024-01-25', '2024-02-01', '2024-02-05']
    }
    
    call_center_data = {
        'رقم المكالمة': ['CC001', 'CC002', 'CC003', 'CC004', 'CC005'],
        'رقم العميل': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'نوع المكالمة': ['استفسار', 'شكوى', 'طلب خدمة', 'متابعة', 'إلغاء'],
        'الموظف المسؤول': ['سارة أحمد', 'محمد علي', 'نورا حسن', 'أحمد محمود', 'ليلى عبدالله'],
        'تاريخ المكالمة': ['2024-07-10', '2024-07-11', '2024-07-11', '2024-07-12', '2024-07-12'],
        'وقت المكالمة': ['10:30', '14:15', '16:20', '09:45', '11:30'],
        'مدة المكالمة (دقيقة)': [15, 25, 8, 12, 18],
        'الحالة': ['مكتمل', 'قيد المعالجة', 'مكتمل', 'مكتمل', 'قيد المعالجة']
    }
    
    complaints_data = {
        'رقم الشكوى': ['S001', 'S002', 'S003', 'S004', 'S005'],
        'رقم العميل': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'نوع الشكوى': ['تأخير في التسليم', 'جودة المنتج', 'خدمة العملاء', 'فواتير', 'تقني'],
        'الوصف': ['تأخير في تسليم الطلب لمدة 3 أيام', 'المنتج لا يطابق المواصفات', 'سوء معاملة من فريق الدعم', 'خطأ في الفاتورة', 'مشكلة في التطبيق'],
        'الأولوية': ['متوسط', 'عالي', 'منخفض', 'متوسط', 'عالي'],
        'تاريخ الشكوى': ['2024-07-08', '2024-07-09', '2024-07-10', '2024-07-11', '2024-07-12'],
        'الحالة': ['قيد المعالجة', 'تم الحل', 'جديد', 'قيد المعالجة', 'تم الحل'],
        'الموظف المسؤول': ['أحمد سعد', 'مها محمد', 'كريم علي', 'دينا أحمد', 'حسام محمود']
    }
    
    pickup_data = {
        'رقم البيك أب': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'رقم العميل': ['C001', 'C002', 'C003', 'C004', 'C005'],
        'العنوان': ['شارع النيل، المعادي', 'شارع الجمهورية، وسط البلد', 'شارع الهرم، الجيزة', 'شارع الجلاء، المنصورة', 'شارع النيل، أسوان'],
        'تاريخ البيك أب': ['2024-07-13', '2024-07-13', '2024-07-14', '2024-07-14', '2024-07-15'],
        'الوقت المطلوب': ['10:00-12:00', '14:00-16:00', '09:00-11:00', '16:00-18:00', '11:00-13:00'],
        'نوع الخدمة': ['استلام', 'تسليم', 'استلام وتسليم', 'استلام', 'تسليم'],
        'السائق': ['محمد أحمد', 'أحمد محمود', 'سامي علي', 'عمر حسن', 'خالد سعد'],
        'الحالة': ['مجدول', 'في الطريق', 'مكتمل', 'مجدول', 'في الطريق']
    }
    
    return (
        pd.DataFrame(customers_data),
        pd.DataFrame(call_center_data),
        pd.DataFrame(complaints_data),
        pd.DataFrame(pickup_data)
    )

# دالة لعرض الإحصائيات
def display_metrics(df, title):
    """عرض الإحصائيات الأساسية"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("إجمالي السجلات", len(df))
    
    with col2:
        if 'الحالة' in df.columns:
            active_count = len(df[df['الحالة'].isin(['نشط', 'مكتمل', 'تم الحل'])])
            st.metric("السجلات النشطة", active_count)
        else:
            st.metric("السجلات الحديثة", len(df))
    
    with col3:
        if 'تاريخ' in str(df.columns):
            date_col = [col for col in df.columns if 'تاريخ' in col][0]
            today_count = len(df[df[date_col] == datetime.now().strftime('%Y-%m-%d')])
            st.metric("اليوم", today_count)
        else:
            st.metric("هذا الأسبوع", len(df))
    
    with col4:
        if 'الأولوية' in df.columns:
            high_priority = len(df[df['الأولوية'] == 'عالي'])
            st.metric("أولوية عالية", high_priority)
        else:
            st.metric("معدل النجاح", "95%")

# دالة لإنشاء الرسوم البيانية
def create_charts(df, chart_type, title):
    """إنشاء الرسوم البيانية"""
    if chart_type == "pie" and 'الحالة' in df.columns:
        status_counts = df['الحالة'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index, 
                     title=f"توزيع الحالات - {title}")
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "bar" and 'تاريخ' in str(df.columns):
        date_col = [col for col in df.columns if 'تاريخ' in col][0]
        df[date_col] = pd.to_datetime(df[date_col])
        daily_counts = df.groupby(df[date_col].dt.date).size().reset_index()
        daily_counts.columns = ['التاريخ', 'العدد']
        fig = px.bar(daily_counts, x='التاريخ', y='العدد', 
                     title=f"الإحصائيات اليومية - {title}")
        st.plotly_chart(fig, use_container_width=True)

# دالة لإدارة النماذج
def manage_forms(sheet_name, df):
    """إدارة النماذج لإضافة وتعديل البيانات"""
    st.subheader(f"إدارة بيانات {sheet_name}")
    
    # إضافة سجل جديد
    with st.expander("➕ إضافة سجل جديد"):
        st.write("### إضافة سجل جديد")
        
        if sheet_name == "العملاء":
            col1, col2 = st.columns(2)
            with col1:
                customer_id = st.text_input("رقم العميل")
                customer_name = st.text_input("اسم العميل")
                phone = st.text_input("رقم الهاتف")
            with col2:
                email = st.text_input("البريد الإلكتروني")
                city = st.text_input("المدينة")
                reg_date = st.date_input("تاريخ التسجيل")
            
            if st.button("إضافة عميل جديد"):
                new_record = [customer_id, customer_name, phone, email, city, str(reg_date)]
                st.success("تم إضافة العميل بنجاح!")
        
        elif sheet_name == "الكول سنتر":
            col1, col2 = st.columns(2)
            with col1:
                call_id = st.text_input("رقم المكالمة")
                customer_id = st.text_input("رقم العميل")
                call_type = st.selectbox("نوع المكالمة", ["استفسار", "شكوى", "طلب خدمة", "متابعة", "إلغاء"])
                employee = st.text_input("الموظف المسؤول")
            with col2:
                call_date = st.date_input("تاريخ المكالمة")
                call_time = st.time_input("وقت المكالمة")
                duration = st.number_input("مدة المكالمة (دقيقة)", min_value=1, max_value=120)
                status = st.selectbox("الحالة", ["مكتمل", "قيد المعالجة", "ملغى"])
            
            if st.button("إضافة مكالمة جديدة"):
                new_record = [call_id, customer_id, call_type, employee, 
                             str(call_date), str(call_time), duration, status]
                st.success("تم إضافة المكالمة بنجاح!")
        
        elif sheet_name == "الشكاوى":
            col1, col2 = st.columns(2)
            with col1:
                complaint_id = st.text_input("رقم الشكوى")
                customer_id = st.text_input("رقم العميل")
                complaint_type = st.selectbox("نوع الشكوى", 
                                            ["تأخير في التسليم", "جودة المنتج", "خدمة العملاء", "فواتير", "تقني"])
                description = st.text_area("الوصف")
            with col2:
                priority = st.selectbox("الأولوية", ["منخفض", "متوسط", "عالي"])
                complaint_date = st.date_input("تاريخ الشكوى")
                status = st.selectbox("الحالة", ["جديد", "قيد المعالجة", "تم الحل", "مغلق"])
                employee = st.text_input("الموظف المسؤول")
            
            if st.button("إضافة شكوى جديدة"):
                new_record = [complaint_id, customer_id, complaint_type, description,
                             priority, str(complaint_date), status, employee]
                st.success("تم إضافة الشكوى بنجاح!")
        
        elif sheet_name == "البيك أب":
            col1, col2 = st.columns(2)
            with col1:
                pickup_id = st.text_input("رقم البيك أب")
                customer_id = st.text_input("رقم العميل")
                address = st.text_area("العنوان")
                pickup_date = st.date_input("تاريخ البيك أب")
            with col2:
                time_slot = st.selectbox("الوقت المطلوب", 
                                       ["09:00-11:00", "10:00-12:00", "14:00-16:00", "16:00-18:00"])
                service_type = st.selectbox("نوع الخدمة", ["استلام", "تسليم", "استلام وتسليم"])
                driver = st.text_input("السائق")
                status = st.selectbox("الحالة", ["مجدول", "في الطريق", "مكتمل", "ملغى"])
            
            if st.button("إضافة بيك أب جديد"):
                new_record = [pickup_id, customer_id, address, str(pickup_date),
                             time_slot, service_type, driver, status]
                st.success("تم إضافة البيك أب بنجاح!")

# الواجهة الرئيسية
def main():
    # الهيدر الرئيسي
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; text-align: center; margin: 0;">
            📊 نظام إدارة بيانات الكول سنتر
        </h1>
        <p style="color: white; text-align: center; margin: 10px 0 0 0;">
            إدارة شاملة للعملاء والمكالمات والشكاوى وخدمات البيك أب
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # تحميل البيانات التجريبية
    customers_df, call_center_df, complaints_df, pickup_df = load_sample_data()
    
    # الشريط الجانبي للإعدادات
    st.sidebar.header("⚙️ إعدادات الاتصال")
    
    # إعدادات Google Sheets
    with st.sidebar.expander("🔗 إعدادات Google Sheets"):
        st.write("لربط التطبيق بـ Google Sheets:")
        spreadsheet_id = st.text_input("معرف الجدول (Spreadsheet ID)")
        credentials_file = st.file_uploader("ملف الاعتماد JSON", type=['json'])
        
        if st.button("اتصال بـ Google Sheets"):
            if spreadsheet_id and credentials_file:
                try:
                    credentials_dict = json.load(credentials_file)
                    gs_manager = GoogleSheetsManager(credentials_dict, spreadsheet_id)
                    st.success("تم الاتصال بنجاح!")
                    st.session_state['gs_connected'] = True
                except Exception as e:
                    st.error(f"خطأ في الاتصال: {e}")
    
    # إعدادات العرض
    st.sidebar.header("🎨 إعدادات العرض")
    show_charts = st.sidebar.checkbox("عرض الرسوم البيانية", value=True)
    show_metrics = st.sidebar.checkbox("عرض الإحصائيات", value=True)
    auto_refresh = st.sidebar.checkbox("التحديث التلقائي", value=False)
    
    if auto_refresh:
        refresh_interval = st.sidebar.slider("فترة التحديث (ثانية)", 30, 300, 60)
    
    # التبويبات الرئيسية
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 العملاء", 
        "📞 الكول سنتر", 
        "❗ الشكاوى", 
        "🚚 البيك أب",
        "📈 التقارير"
    ])
    
    # تبويب العملاء
    with tab1:
        st.header("👥 إدارة العملاء")
        
        if show_metrics:
            display_metrics(customers_df, "العملاء")
        
        if show_charts:
            col1, col2 = st.columns(2)
            with col1:
                city_counts = customers_df['المدينة'].value_counts()
                fig = px.pie(values=city_counts.values, names=city_counts.index, 
                           title="توزيع العملاء حسب المدينة")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                customers_df['تاريخ التسجيل'] = pd.to_datetime(customers_df['تاريخ التسجيل'])
                monthly_reg = customers_df.groupby(customers_df['تاريخ التسجيل'].dt.to_period('M')).size()
                fig = px.bar(x=monthly_reg.index.astype(str), y=monthly_reg.values,
                           title="تسجيل العملاء الشهري")
                st.plotly_chart(fig, use_container_width=True)
        
        # فلترة البيانات
        st.subheader("🔍 فلترة البيانات")
        col1, col2 = st.columns(2)
        with col1:
            city_filter = st.selectbox("فلترة حسب المدينة", 
                                     ["الكل"] + list(customers_df['المدينة'].unique()))
        with col2:
            search_term = st.text_input("البحث في أسماء العملاء")
        
        # تطبيق فلاتر الشكاوى
        filtered_complaints = complaints_df.copy()
        if complaint_type_filter != "الكل":
            filtered_complaints = filtered_complaints[filtered_complaints['نوع الشكوى'] == complaint_type_filter]
        if priority_filter != "الكل":
            filtered_complaints = filtered_complaints[filtered_complaints['الأولوية'] == priority_filter]
        if complaint_status_filter != "الكل":
            filtered_complaints = filtered_complaints[filtered_complaints['الحالة'] == complaint_status_filter]
        
        st.dataframe(filtered_complaints, use_container_width=True, height=400)
        
        # نموذج إدارة الشكاوى
        manage_forms("الشكاوى", complaints_df)
    
    # تبويب البيك أب
    with tab4:
        st.header("🚚 إدارة البيك أب")
        
        if show_metrics:
            display_metrics(pickup_df, "البيك أب")
        
        if show_charts:
            col1, col2 = st.columns(2)
            with col1:
                service_types = pickup_df['نوع الخدمة'].value_counts()
                fig = px.pie(values=service_types.values, names=service_types.index,
                           title="توزيع أنواع الخدمات")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                driver_workload = pickup_df['السائق'].value_counts()
                fig = px.bar(x=driver_workload.index, y=driver_workload.values,
                           title="عدد المهام لكل سائق")
                st.plotly_chart(fig, use_container_width=True)
        
        # جدولة البيك أب
        st.subheader("📅 جدولة البيك أب")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            scheduled_pickups = len(pickup_df[pickup_df['الحالة'] == 'مجدول'])
            st.metric("مجدول", scheduled_pickups)
        
        with col2:
            in_progress = len(pickup_df[pickup_df['الحالة'] == 'في الطريق'])
            st.metric("في الطريق", in_progress)
        
        with col3:
            completed = len(pickup_df[pickup_df['الحالة'] == 'مكتمل'])
            st.metric("مكتمل", completed)
        
        # فلترة البيك أب
        st.subheader("🔍 فلترة البيك أب")
        col1, col2, col3 = st.columns(3)
        with col1:
            service_filter = st.selectbox("نوع الخدمة", 
                                        ["الكل"] + list(pickup_df['نوع الخدمة'].unique()))
        with col2:
            driver_filter = st.selectbox("السائق", 
                                       ["الكل"] + list(pickup_df['السائق'].unique()))
        with col3:
            pickup_status_filter = st.selectbox("حالة البيك أب", 
                                              ["الكل"] + list(pickup_df['الحالة'].unique()))
        
        # تطبيق فلاتر البيك أب
        filtered_pickup = pickup_df.copy()
        if service_filter != "الكل":
            filtered_pickup = filtered_pickup[filtered_pickup['نوع الخدمة'] == service_filter]
        if driver_filter != "الكل":
            filtered_pickup = filtered_pickup[filtered_pickup['السائق'] == driver_filter]
        if pickup_status_filter != "الكل":
            filtered_pickup = filtered_pickup[filtered_pickup['الحالة'] == pickup_status_filter]
        
        st.dataframe(filtered_pickup, use_container_width=True, height=400)
        
        # نموذج إدارة البيك أب
        manage_forms("البيك أب", pickup_df)
    
    # تبويب التقارير
    with tab5:
        st.header("📈 التقارير والإحصائيات")
        
        # نظرة عامة على النظام
        st.subheader("📊 نظرة عامة على النظام")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("إجمالي العملاء", len(customers_df))
        with col2:
            st.metric("إجمالي المكالمات", len(call_center_df))
        with col3:
            st.metric("إجمالي الشكاوى", len(complaints_df))
        with col4:
            st.metric("إجمالي البيك أب", len(pickup_df))
        
        # الرسوم البيانية المتقدمة
        st.subheader("📊 الرسوم البيانية المتقدمة")
        
        # تحليل الأداء الشهري
        col1, col2 = st.columns(2)
        
        with col1:
            # إنشاء بيانات الأداء الشهري
            monthly_data = {
                'الشهر': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو'],
                'المكالمات': [120, 135, 150, 165, 180, 195, 210],
                'الشكاوى': [15, 12, 18, 20, 14, 16, 22],
                'البيك أب': [85, 90, 95, 100, 105, 110, 115]
            }
            monthly_df = pd.DataFrame(monthly_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=monthly_df['الشهر'], y=monthly_df['المكالمات'],
                                   mode='lines+markers', name='المكالمات'))
            fig.add_trace(go.Scatter(x=monthly_df['الشهر'], y=monthly_df['الشكاوى'],
                                   mode='lines+markers', name='الشكاوى'))
            fig.add_trace(go.Scatter(x=monthly_df['الشهر'], y=monthly_df['البيك أب'],
                                   mode='lines+markers', name='البيك أب'))
            fig.update_layout(title='الأداء الشهري للأقسام')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # تحليل معدل الرضا
            satisfaction_data = {
                'القسم': ['الكول سنتر', 'الشكاوى', 'البيك أب', 'خدمة العملاء'],
                'معدل الرضا': [85, 78, 92, 88]
            }
            satisfaction_df = pd.DataFrame(satisfaction_data)
            
            fig = px.bar(satisfaction_df, x='القسم', y='معدل الرضا',
                        title='معدل رضا العملاء حسب القسم',
                        color='معدل الرضا',
                        color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
        
        # تحليل الاتجاهات
        st.subheader("📈 تحليل الاتجاهات")
        
        # مقارنة الأداء اليومي
        daily_performance = {
            'اليوم': ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'],
            'المكالمات': [45, 52, 48, 55, 60, 35, 25],
            'الشكاوى': [5, 7, 6, 8, 9, 4, 3],
            'البيك أب': [20, 22, 25, 28, 30, 15, 12]
        }
        daily_df = pd.DataFrame(daily_performance)
        
        fig = px.line(daily_df, x='اليوم', y=['المكالمات', 'الشكاوى', 'البيك أب'],
                     title='الأداء اليومي للأقسام')
        st.plotly_chart(fig, use_container_width=True)
        
        # تقرير تفصيلي
        st.subheader("📋 تقرير تفصيلي")
        
        report_type = st.selectbox("نوع التقرير", 
                                 ["تقرير شامل", "تقرير العملاء", "تقرير المكالمات", 
                                  "تقرير الشكاوى", "تقرير البيك أب"])
        
        if st.button("إنشاء التقرير"):
            with st.spinner("جاري إنشاء التقرير..."):
                time.sleep(2)  # محاكاة وقت المعالجة
                
                if report_type == "تقرير شامل":
                    st.success("تم إنشاء التقرير الشامل بنجاح!")
                    
                    # إحصائيات عامة
                    st.markdown("### الإحصائيات العامة")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**إجمالي العملاء:** {len(customers_df)}")
                        st.write(f"**إجمالي المكالمات:** {len(call_center_df)}")
                        st.write(f"**إجمالي الشكاوى:** {len(complaints_df)}")
                        st.write(f"**إجمالي البيك أب:** {len(pickup_df)}")
                    
                    with col2:
                        resolved_complaints = len(complaints_df[complaints_df['الحالة'] == 'تم الحل'])
                        resolution_rate = (resolved_complaints / len(complaints_df)) * 100
                        st.write(f"**معدل حل الشكاوى:** {resolution_rate:.1f}%")
                        
                        completed_calls = len(call_center_df[call_center_df['الحالة'] == 'مكتمل'])
                        completion_rate = (completed_calls / len(call_center_df)) * 100
                        st.write(f"**معدل إكمال المكالمات:** {completion_rate:.1f}%")
                
                elif report_type == "تقرير العملاء":
                    st.success("تم إنشاء تقرير العملاء بنجاح!")
                    st.dataframe(customers_df, use_container_width=True)
                
                elif report_type == "تقرير المكالمات":
                    st.success("تم إنشاء تقرير المكالمات بنجاح!")
                    st.dataframe(call_center_df, use_container_width=True)
                
                elif report_type == "تقرير الشكاوى":
                    st.success("تم إنشاء تقرير الشكاوى بنجاح!")
                    st.dataframe(complaints_df, use_container_width=True)
                
                elif report_type == "تقرير البيك أب":
                    st.success("تم إنشاء تقرير البيك أب بنجاح!")
                    st.dataframe(pickup_df, use_container_width=True)
        
        # تصدير البيانات
        st.subheader("📤 تصدير البيانات")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("صيغة التصدير", ["CSV", "Excel", "JSON"])
        
        with col2:
            export_data = st.selectbox("البيانات المراد تصديرها", 
                                     ["جميع البيانات", "العملاء", "المكالمات", "الشكاوى", "البيك أب"])
        
        if st.button("تصدير البيانات"):
            st.success(f"تم تصدير {export_data} بصيغة {export_format} بنجاح!")
            st.info("يمكنك تحميل الملف من الرابط أعلاه.")
    
    # تحديث تلقائي
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()
    
    # معلومات النظام في أسفل الصفحة
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 2rem;">
        <p>تطبيق إدارة بيانات الكول سنتر - مطور باستخدام Streamlit</p>
        <p>آخر تحديث: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </div>
    """, unsafe_allow_html=True)

# تشغيل التطبيق
if __name__ == "__main__":
    main()ق الفلاتر
        filtered_df = customers_df.copy()
        if city_filter != "الكل":
            filtered_df = filtered_df[filtered_df['المدينة'] == city_filter]
        if search_term:
            filtered_df = filtered_df[filtered_df['اسم العميل'].str.contains(search_term, na=False)]
        
        st.dataframe(filtered_df, use_container_width=True, height=400)
        
        # نموذج إدارة العملاء
        manage_forms("العملاء", customers_df)
    
    # تبويب الكول سنتر
    with tab2:
        st.header("📞 إدارة الكول سنتر")
        
        if show_metrics:
            display_metrics(call_center_df, "المكالمات")
        
        if show_charts:
            col1, col2 = st.columns(2)
            with col1:
                call_types = call_center_df['نوع المكالمة'].value_counts()
                fig = px.pie(values=call_types.values, names=call_types.index,
                           title="توزيع أنواع المكالمات")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                avg_duration = call_center_df.groupby('الموظف المسؤول')['مدة المكالمة (دقيقة)'].mean()
                fig = px.bar(x=avg_duration.index, y=avg_duration.values,
                           title="متوسط مدة المكالمات لكل موظف")
                st.plotly_chart(fig, use_container_width=True)
        
        # فلترة المكالمات
        st.subheader("🔍 فلترة المكالمات")
        col1, col2, col3 = st.columns(3)
        with col1:
            call_type_filter = st.selectbox("نوع المكالمة", 
                                          ["الكل"] + list(call_center_df['نوع المكالمة'].unique()))
        with col2:
            status_filter = st.selectbox("الحالة", 
                                       ["الكل"] + list(call_center_df['الحالة'].unique()))
        with col3:
            employee_filter = st.selectbox("الموظف", 
                                         ["الكل"] + list(call_center_df['الموظف المسؤول'].unique()))
        
        # تطبيق الفلاتر
        filtered_calls = call_center_df.copy()
        if call_type_filter != "الكل":
            filtered_calls = filtered_calls[filtered_calls['نوع المكالمة'] == call_type_filter]
        if status_filter != "الكل":
            filtered_calls = filtered_calls[filtered_calls['الحالة'] == status_filter]
        if employee_filter != "الكل":
            filtered_calls = filtered_calls[filtered_calls['الموظف المسؤول'] == employee_filter]
        
        st.dataframe(filtered_calls, use_container_width=True, height=400)
        
        # نموذج إدارة المكالمات
        manage_forms("الكول سنتر", call_center_df)
    
    # تبويب الشكاوى
    with tab3:
        st.header("❗ إدارة الشكاوى")
        
        if show_metrics:
            display_metrics(complaints_df, "الشكاوى")
        
        if show_charts:
            col1, col2 = st.columns(2)
            with col1:
                complaint_types = complaints_df['نوع الشكوى'].value_counts()
                fig = px.bar(x=complaint_types.values, y=complaint_types.index,
                           orientation='h', title="أنواع الشكاوى")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                priority_status = complaints_df.groupby(['الأولوية', 'الحالة']).size().reset_index(name='العدد')
                fig = px.bar(priority_status, x='الأولوية', y='العدد', color='الحالة',
                           title="الشكاوى حسب الأولوية والحالة")
                st.plotly_chart(fig, use_container_width=True)
        
        # إحصائيات الشكاوى
        st.subheader("📊 إحصائيات الشكاوى")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_complaints = len(complaints_df)
            st.metric("إجمالي الشكاوى", total_complaints)
        
        with col2:
            resolved_complaints = len(complaints_df[complaints_df['الحالة'] == 'تم الحل'])
            st.metric("تم الحل", resolved_complaints)
        
        with col3:
            pending_complaints = len(complaints_df[complaints_df['الحالة'] == 'قيد المعالجة'])
            st.metric("قيد المعالجة", pending_complaints)
        
        with col4:
            high_priority = len(complaints_df[complaints_df['الأولوية'] == 'عالي'])
            st.metric("أولوية عالية", high_priority)
        
        # فلترة الشكاوى
        st.subheader("🔍 فلترة الشكاوى")
        col1, col2, col3 = st.columns(3)
        with col1:
            complaint_type_filter = st.selectbox("نوع الشكوى", 
                                               ["الكل"] + list(complaints_df['نوع الشكوى'].unique()))
        with col2:
            priority_filter = st.selectbox("الأولوية", 
                                         ["الكل"] + list(complaints_df['الأولوية'].unique()))
        with col3:
            complaint_status_filter = st.selectbox("حالة الشكوى", 
                                                 ["الكل"] + list(complaints_df['الحالة'].unique()))
        
        # تطبي
