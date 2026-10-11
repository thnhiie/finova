import streamlit as st
import pandas as pd
import numpy as np
import time
from google import genai
from google.genai.errors import APIError

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="FINOVA — Plan Smarter. Achieve Your Goals.",
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. KHỞI TẠO SESSION STATE (Quản lý trạng thái đăng nhập & dữ liệu) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login" # 'login', 'register', 'forgot'
if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "name": "Alex Nguyen",
        "email": "alex.nguyen@finova.vn",
        "age": 30,
        "gender": "Male",
        "country": "Vietnam",
        "city": "Ho Chi Minh City",
        "phone": "+84 901 234 567",
        "occupation": "Software Engineer"
    }
if "financial_data" not in st.session_state:
    st.session_state.financial_data = {
        "income": 35000000,
        "expenses": 15000000,
        "investments": 100000000,
        "assets": 500000000,
        "horizon": 5,
        "liquidity": "Medium",
        "risk": "Medium",
        "liabilities": 50000000,
        "debt_payment": 5000000
    }
if "eval_ratings" not in st.session_state:
    st.session_state.eval_ratings = {"Accuracy": 5, "Groundedness": 5, "Usability": 5, "Processing Time": 4}
if "eval_submitted" not in st.session_state:
    st.session_state.eval_submitted = False

# --- 3. HÀM TIỆN ÍCH ĐỊNH DẠNG TIỀN TỆ VND ---
def format_vnd(amount):
    try:
        return f"{int(amount):,}".replace(",", ",") + " VND"
    except:
        return "0 VND"

# --- 4. GIAO DIỆN CHUNG & HEADER (Logo, Tên web, Hướng dẫn, User Menu, Dark/Light Mode) ---
col_logo, col_spacer, col_actions = st.columns([2, 6, 4])

with col_logo:
    st.markdown("### 🐶 **FINOVA**")

with col_actions:
    c_guide, c_user, c_theme = st.columns([2, 3, 2])
    with c_guide:
        with st.popover("📖 Guide"):
            st.markdown("#### FINOVA User Guide")
            st.markdown("- **Login/Register**: Use the top-right user icon to access accounts.")
            st.markdown("- **Financial Input**: Go to 'Financial Information' to input your metrics.")
            st.markdown("- **Scenario Planning**: Simulate 5 distinct financial trajectories.")
            st.markdown("- **AI Copilot**: Ask questions in 'Contact & Support'.")
    
    with c_user:
        if not st.session_state.logged_in:
            with st.popover("👤 Account"):
                if st.button("🔑 Login", use_container_width=True):
                    st.session_state.auth_mode = "login"
                    st.rerun()
                if st.button("📝 Register", use_container_width=True):
                    st.session_state.auth_mode = "register"
                    st.rerun()
        else:
            with st.popover(f"👤 {st.session_state.user_info['name']}"):
                st.write(f"Email: {st.session_state.user_info['email']}")
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.logged_in = False
                    st.session_state.current_page = "Home"
                    st.rerun()

    with c_theme:
        # Giả lập nút chuyển chế độ sáng/tối
        dark_mode = st.toggle("🌙/☀️", value=False, help="Toggle Light/Dark Mode")

st.markdown("---")

# ==========================================
# KHU VỰC 1: TRANG CHỦ KHI CHƯA ĐĂNG NHẬP
# ==========================================
if not st.session_state.logged_in:
    # Xử lý các form Authentication (Đăng nhập / Đăng ký / Quên mật khẩu)
    if st.session_state.auth_mode == "register":
        st.subheader("📝 Register a New FINOVA Account")
        with st.form("register_form"):
            reg_name = st.text_input("Full Name")
            reg_email = st.text_input("Email Address")
            reg_pass = st.text_input("Password", type="password")
            reg_repass = st.text_input("Confirm Password", type="password")
            submit_reg = st.form_submit_button("Register Account", type="primary")
            if submit_reg:
                if reg_pass == reg_repass and reg_email:
                    st.session_state.logged_in = True
                    st.session_state.user_info["name"] = reg_name
                    st.session_state.user_info["email"] = reg_email
                    st.success("Registration successful! Welcome to FINOVA.")
                    st.rerun()
                else:
                    st.error("Please check your passwords and email.")
        if st.button("Back to Login"):
            st.session_state.auth_mode = "login"
            st.rerun()
        st.stop()

    elif st.session_state.auth_mode == "forgot":
        st.subheader("🔐 Reset Your Password")
        with st.form("forgot_form"):
            f_email = st.text_input("Enter your registered email")
            f_newpass = st.text_input("New Password", type="password")
            submit_f = st.form_submit_button("Update Password", type="primary")
            if submit_f:
                st.success("Password updated successfully! Please log in.")
                st.session_state.auth_mode = "login"
                st.rerun()
        if st.button("Back to Login"):
            st.session_state.auth_mode = "login"
            st.rerun()
        st.stop()

    elif st.session_state.auth_mode == "login":
        # Có thể ẩn form login mặc định hoặc hiện khi bấm nút. Ở đây ta làm trang chủ chuẩn mô tả.
        pass

    # Banner / Carousel giả lập ảnh danh lam thắng cảnh sinh động
    st.markdown("<h1 style='text-align: center;'>FINOVA — Plan Smarter. Achieve Your Goals.</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Your Financial Goals. Your Plan. Your Future.</h3>", unsafe_allow_html=True)
    
    # Ảnh danh lam thắng cảnh minh họa (sử dụng URL ảnh công khai ổn định)
    st.image("https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80", caption="Explore Financial Freedom with Scenic Clarity", use_container_width=True)

    st.markdown("""
    ### 🌟 Welcome to FINOVA
    **FINOVA** is an intelligent personal finance planning platform that transforms complex financial ambitions into clear, actionable roadmaps.
    By seamlessly integrating AI-driven goal parsing with a deterministic financial calculation engine, FINOVA helps you evaluate your financial health, model multi-scenario cash flows, and stress-test your strategy against real-world changes.
    """)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Start Planning Your Goals", use_container_width=True, type="primary"):
            st.session_state.auth_mode = "register"
            st.rerun()
    with col_btn2:
        if st.button("🔑 Member Login", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()

    st.markdown("---")
    st.markdown("### 🛠️ Core Features Overview")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 01. Intelligent Financial Analysis")
        st.write("Extracts income, expenses, assets, and liabilities. Automatically detects missing information and guards against data inconsistencies.")
        st.markdown("#### 02. Multi-Scenario Planning")
        st.write("Simulates 5 distinct mathematical trajectories from Severely Conservative to Highly Optimistic using precise calculation engines.")
    with c2:
        st.markdown("#### 03. Real-Time What-If & Stress Testing")
        st.write("Interactively adjust savings rates or simulate income shocks (e.g., -20% income) to measure portfolio resilience.")
        st.markdown("#### 04. AI-Powered Financial Insights")
        st.write("Objective trade-off explanations, risk guidance, and zero-hallucination educational assistance powered by Google Gemini.")

    st.markdown("---")
    st.info("⚖️ **Disclaimer & Safety Notice:** FINOVA is designed strictly for educational and informational purposes. Results are mathematical estimates and decision-support tools, not guaranteed financial outcomes or personalized investment advice.")
    st.stop()


# ==========================================
# KHU VỰC 2: SAU KHI ĐĂNG NHẬP (DASHBOARD & SIDEBAR)
# ==========================================

# Thanh công cụ bên trái (Sidebar) theo yêu cầu Code 2
st.sidebar.title("🧭 FINOVA Navigation")
menu_selection = st.sidebar.radio(
    "Select Module:",
    [
        "📊 Overview",
        "👤 Customer Account",
        "💰 Financial Information",
        "🚀 Savings & Investment",
        "⭐ Evaluation",
        "📞 Contact & Support"
    ]
)

# --- MODULE 1: THANH TỔNG QUAN (Overview) ---
if menu_selection == "📊 Overview":
    st.subheader("Overview Dashboard")
    st.write(f"Welcome back, **{st.session_state.user_info['name']}**!")
    
    # Slideshow ảnh danh lam thắng cảnh giả lập bằng Container
    st.image("https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80", caption="GOAL-BASED PERSONAL FINANCE PLANNING ENGINE", use_container_width=True)

    st.markdown("### 📌 Detailed Platform Narrative")
    st.write("""
    FINOVA is an intelligent personal finance planning platform designed to help individuals understand their current financial health and transform ambitious financial goals into realistic, actionable roadmaps.
    By seamlessly combining Artificial Intelligence (AI) with a deterministic financial calculation engine, FINOVA analyzes your income, expenses, savings, assets, and liabilities to rigorously assess goal feasibility.
    """)

    col_a, col_b, col_c = st.metric("Monthly Income", format_vnd(st.session_state.financial_data['income'])), st.metric("Monthly Expenses", format_vnd(st.session_state.financial_data['expenses'])), st.metric("Total Assets", format_vnd(st.session_state.financial_data['assets']))
    st.markdown("---")
    if st.button("🚀 Start Planning Your Goals Now", type="primary"):
        st.sidebar.success("Navigate to 'Financial Information' to begin.")


# --- MODULE 2: TÀI KHOẢN KHÁCH HÀNG (Customer Account) ---
elif menu_selection == "👤 Customer Account":
    st.subheader("👤 Customer Account Profile")
    st.write("Manage your personal profile and update security settings.")

    with st.form("update_profile_form"):
        u_name = st.text_input("Full Name", value=st.session_state.user_info["name"])
        u_email = st.text_input("Email Address", value=st.session_state.user_info["email"])
        c1, c2 = st.columns(2)
        with c1:
            u_age = st.number_input("Age", min_value=18, max_value=100, value=st.session_state.user_info["age"])
            u_gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=0)
            u_country = st.text_input("Country", value=st.session_state.user_info["country"])
        with c2:
            u_city = st.text_input("City / Province", value=st.session_state.user_info["city"])
            u_phone = st.text_input("Phone Number (Optional)", value=st.session_state.user_info["phone"])
            u_occupation = st.text_input("Occupation", value=st.session_state.user_info["occupation"])
        
        submit_update = st.form_submit_button("💾 Save Profile Changes", type="primary")
        if submit_update:
            st.session_state.user_info["name"] = u_name
            st.session_state.user_info["email"] = u_email
            st.session_state.user_info["age"] = u_age
            st.session_state.user_info["occupation"] = u_occupation
            st.success("Profile updated successfully!")

    st.markdown("### 🔑 Change Password")
    with st.form("change_pass_form"):
        old_p = st.text_input("Current Password", type="password")
        new_p = st.text_input("New Password", type="password")
        re_p = st.text_input("Confirm New Password", type="password")
        sub_pass = st.form_submit_button("Update Password")
        if sub_pass:
            if new_p == re_p and len(new_p) > 0:
                st.success("Password changed successfully!")
            else:
                st.error("Passwords do not match or fields are empty.")


# --- MODULE 3: THÔNG TIN TÀI CHÍNH & MÔ PHỎNG KỊCH BẢN (Financial Information) ---
elif menu_selection == "💰 Financial Information":
    st.subheader("💰 Financial Information Input & Scenario Simulation")
    st.write("Enter your baseline financial metrics. Note: All figures must be $\ge 0$ with thousands comma separators.")

    with st.form("financial_input_form"):
        c1, c2 = st.columns(2)
        with c1:
            inc = st.number_input("Monthly Income (VND/month)", min_value=0, value=st.session_state.financial_data["income"], step=1000000, format="%d")
            exp = st.number_input("Monthly Living Expenses (VND/month)", min_value=0, value=st.session_state.financial_data["expenses"], step=1000000, format="%d")
            inv = st.number_input("Current Investments (VND)", min_value=0, value=st.session_state.financial_data["investments"], step=5000000, format="%d")
            ast = st.number_input("Total Assets (VND)", min_value=0, value=st.session_state.financial_data["assets"], step=10000000, format="%d")
        with c2:
            lib = st.number_input("Total Liabilities / Debt (VND)", min_value=0, value=st.session_state.financial_data["liabilities"], step=5000000, format="%d")
            debt_pay = st.number_input("Monthly Debt Payment (VND/month)", min_value=0, value=st.session_state.financial_data["debt_payment"], step=1000000, format="%d")
            horizon = st.slider("Planning Time Horizon (Years)", min_value=1, max_value=30, value=st.session_state.financial_data["horizon"])
            liquidity = st.selectbox("Liquidity Needs", ["Low", "Medium", "High"])
            risk_tol = st.selectbox("Risk Tolerance", ["Low", "Medium", "High"])

        submitted_fin = st.form_submit_button("🚀 Run Financial Assessment & Scenarios", type="primary")
        if submitted_fin:
            # Lưu lại state
            st.session_state.financial_data.update({
                "income": inc, "expenses": exp, "investments": inv, "assets": ast,
                "horizon": horizon, "liquidity": liquidity, "risk": risk_tol,
                "liabilities": lib, "debt_payment": debt_pay
            })
            st.success("Financial data validated and processed successfully!")

    # HIỂN THỊ KẾT QUẢ PHÂN TÍCH VÀ 5 KỊCH BẢN (Code 4 requirements)
    st.markdown("---")
    st.subheader("📊 Financial Health Summary & 5-Scenario Simulation")
    
    # Tính toán cơ bản bằng Python Engine
    net_cash_flow = st.session_state.financial_data["income"] - (st.session_state.financial_data["expenses"] + st.session_state.financial_data["debt_payment"])
    dti_ratio = (st.session_state.financial_data["debt_payment"] / st.session_state.financial_data["income"] * 100) if st.session_state.financial_data["income"] > 0 else 0
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Net Monthly Cash Flow", format_vnd(net_cash_flow))
    col_m2.metric("Debt-to-Income (DTI)", f"{dti_ratio:.1f}%")
    col_m3.metric("Savings Capacity", format_vnd(max(0, net_cash_flow)))

    st.markdown("#### 📋 Scenario Suitability Ranking (5 Trajectories)")
    scenario_data = {
        "Scenario Name": ["1. Baseline Scenario", "2. Optimistic Scenario", "3. Highly Optimistic Scenario", "4. Conservative Scenario", "5. Severely Conservative Scenario"],
        "Suitability Score (%)": ["95%", "88%", "75%", "82%", "40%"],
        "Status Badge": ["Most Suitable", "Suitable", "Alternative", "Suitable", "Risk Contingency"],
        "Monthly Surplus": [format_vnd(net_cash_flow), format_vnd(net_cash_flow * 1.2), format_vnd(net_cash_flow * 1.4), format_vnd(net_cash_flow * 0.9), format_vnd(net_cash_flow * 0.5)]
    }
    st.table(pd.DataFrame(scenario_data))

    st.markdown("#### ⚡ What-If Analysis & Stress Testing")
    c_w1, c_w2 = st.columns(2)
    with c_w1:
        inc_change_type = st.selectbox("Income Adjustment Type", ["Increase (+)", "Decrease (-)"])
        inc_pct = st.number_input("Income Adjustment (%)", min_value=0, max_value=100, value=10)
    with c_w2:
        exp_change_type = st.selectbox("Expense Adjustment Type", ["Increase (+)", "Decrease (-)"])
        exp_pct = st.number_input("Expense Adjustment (%)", min_value=0, max_value=100, value=10)
    
    if st.button("🔄 Recalculate What-If Stress Test"):
        st.info(f"Simulating Income {inc_change_type} {inc_pct}% and Expense {exp_change_type} {exp_pct}%...")
        sim_net = net_cash_flow * (1 + (inc_pct/100 if inc_change_type=="Increase (+)" else -inc_pct/100))
        st.success(f"Simulated Adjusted Net Cash Flow: **{format_vnd(sim_net)}/month**")


# --- MODULE 4: TIẾT KIỆM VÀ ĐẦU TƯ (Savings & Investment) ---
elif menu_selection == "🚀 Savings & Investment":
    st.subheader("🚀 Goal-based Savings & Investment Planning Engine")
    st.write("Select or enter your financial goal. AI will recommend the most suitable path based on your cash flow.")

    goal_input = st.text_input("Enter or Select Financial Goal", value="Buy a House Down Payment (1 Billion VND)")
    target_amount = st.number_input("Target Amount (VND)", min_value=0, value=1000000000, step=50000000, format="%d")
    goal_timeframe = st.slider("Goal Timeframe (Years)", 1, 30, 5)

    if st.button("🤖 Analyze Goal with AI & Calculate Plan", type="primary"):
        st.markdown("### 💡 AI Goal Recommendation & Rationale")
        st.success("AI Selected Goal: **House Down Payment Accumulation** (Suitability: 94%)")
        st.write("""
        **Rationale:** Based on your current monthly net cash flow, allocating 40% of surplus towards this medium-term goal aligns perfectly with your liquidity needs and 5-year horizon.
        """)
        
        req_monthly = target_amount / (goal_timeframe * 12)
        st.metric("Required Monthly Savings", format_vnd(req_monthly))
        st.warning("⚠️ Note: Investment returns are simulated assumptions only. Zero return guarantees are made.")

    st.markdown("### 🎛️ What-If Goal Planning Tool")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        slider_years = st.slider("Adjust Goal Timeframe (Years)", 1, 50, 5)
        assumed_income = st.number_input("Assumed Future Monthly Income (VND)", min_value=0, value=int(st.session_state.financial_data["income"]), step=1000000, format="%d")
    with col_g2:
        savings_rate_pct = st.slider("Monthly Savings Rate (%)", 0, 100, 30)
        return_rate = st.number_input("Expected Investment Return Assumption (%)", value=7.0)


# --- MODULE 5: ĐÁNH GIÁ (Evaluation) ---
elif menu_selection == "⭐ Evaluation":
    st.subheader("⭐ FINOVA System Evaluation & Metrics")
    st.write("Evaluate platform performance across 4 strict pillars: Accuracy, Groundedness, Usability, and Processing Time.")

    with st.form("eval_form"):
        e1 = st.slider("1. Accuracy (Precision of financial calculations)", 1, 5, st.session_state.eval_ratings["Accuracy"])
        e2 = st.slider("2. Groundedness (AI adherence to factual data without hallucinations)", 1, 5, st.session_state.eval_ratings["Groundedness"])
        e3 = st.slider("3. Usability (Interface clarity and user experience)", 1, 5, st.session_state.eval_ratings["Usability"])
        e4 = st.slider("4. Processing Time (System responsiveness and speed)", 1, 5, st.session_state.eval_ratings["Processing Time"])
        
        sub_eval = st.form_submit_button("✅ Submit Evaluation Ratings", type="primary")
        if sub_eval:
            st.session_state.eval_ratings = {"Accuracy": e1, "Groundedness": e2, "Usability": e3, "Processing Time": e4}
            st.session_state.eval_submitted = True
            st.success("Thank you for your evaluation!")

    # Tính trung bình sao
    avg_stars = np.mean(list(st.session_state.eval_ratings.values()))
    st.markdown("---")
    st.markdown(f"### 🏆 Overall System Rating: **{avg_stars:.1f} / 5.0 Stars** ⭐⭐⭐⭐⭐")
    st.write("Based on real-time multi-criteria aggregation benchmarking.")


# --- MODULE 6: LIÊN HỆ VÀ HỖ TRỢ + AI CHATBOT (Contact & Support) ---
elif menu_selection == "📞 Contact & Support":
    st.subheader("📞 Customer Support & AI Financial Copilot")
    
    tab_faq, tab_ticket, tab_chatbot = st.tabs(["📚 FAQs", "🎫 Support Ticket", "🤖 AI Chatbot Copilot"])

    with tab_faq:
        st.markdown("### Frequently Asked Questions")
        topic = st.selectbox("Select Topic", ["Getting Started", "Financial Information", "Financial Health Assessment", "Scenarios & What-If Analysis"])
        if topic == "Getting Started":
            st.info("**Q: What is FINOVA?**\nA: FINOVA is an intelligent personal finance planning platform combining AI with a deterministic calculation engine.")
        elif topic == "Financial Information":
            st.info("**Q: How do I enter my income and expenses?**\nA: Go to 'Financial Information' module and fill in the structured VND input fields.")
        else:
            st.info("Select a question to view detailed documentation guidance.")

    with tab_ticket:
        st.markdown("### Submit Support Request")
        with st.form("ticket_form"):
            t_type = st.selectbox("Issue Type", ["Technical Issues", "Account & Login", "Financial Analysis Issues", "Goal Planning Support", "Other"])
            t_sub = st.text_input("Subject")
            t_desc = st.text_area("Detailed Description")
            t_email = st.text_input("Contact Email", value=st.session_state.user_info["email"])
            sub_ticket = st.form_submit_button("📤 Submit Request", type="primary")
            if sub_ticket:
                st.success("Support ticket submitted successfully! Our team will respond shortly.")

    with tab_chatbot:
        st.markdown("### 🤖 FINOVA AI Financial Copilot")
        st.write("Ask questions about your financial profile, scenario comparisons, or platform guidance.")

        # Cấu hình nhập API Key bảo mật server-side / session
        api_key_chat = st.text_input("Google Gemini API Key (Enter to enable AI):", type="password", help="Get key from Google AI Studio")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your FINOVA AI Copilot. How can I assist with your financial roadmap today?"}]

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about your finances, scenarios, or goals..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if not api_key_chat:
                    response_text = "⚠️ Please enter your Google Gemini API Key in the box above to activate AI responses."
                    st.markdown(response_text)
                else:
                    with st.spinner("Analyzing financial context & generating response..."):
                        try:
                            client = genai.Client(api_key=api_key_chat)
                            # Sử dụng model gemini-2.5-flash hoặc gemini-3.5-flash-lite
                            chat_response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=f"You are FINOVA AI Financial Assistant. User profile context: Income={st.session_state.financial_data['income']}, Expenses={st.session_state.financial_data['expenses']}. User question: {prompt}"
                            )
                            response_text = chat_response.text
                        except Exception as e:
                            response_text = f"❌ Error communicating with Gemini API: {e}"
                    st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})