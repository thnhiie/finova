import os, sqlite3, json, math, io, csv
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "finova.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, age INTEGER, gender TEXT, country TEXT, city TEXT,
            phone TEXT, occupation TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS finances (
            user_id INTEGER PRIMARY KEY, income REAL DEFAULT 0, expenses REAL DEFAULT 0,
            investments REAL DEFAULT 0, assets REAL DEFAULT 0, years INTEGER DEFAULT 10,
            liquidity TEXT DEFAULT 'Medium', risk TEXT DEFAULT 'Medium', debt REAL DEFAULT 0,
            monthly_debt REAL DEFAULT 0, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, accuracy INTEGER,
            groundedness INTEGER, usability INTEGER, processing_time INTEGER, comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        con.execute("""CREATE TABLE IF NOT EXISTS support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, issue_type TEXT,
            subject TEXT, description TEXT, email TEXT, attachment_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
init_db()

def current_user():
    if not session.get("user_id"): return None
    with db() as con:
        return con.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to access your personal FINOVA workspace.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def get_finance(uid):
    with db() as con:
        row = con.execute("SELECT * FROM finances WHERE user_id=?", (uid,)).fetchone()
    return dict(row) if row else {"income":0,"expenses":0,"investments":0,"assets":0,"years":10,"liquidity":"Medium","risk":"Medium","debt":0,"monthly_debt":0}

def calculate(fin):
    income=float(fin.get("income") or 0); expenses=float(fin.get("expenses") or 0)
    debt=float(fin.get("debt") or 0); monthly_debt=float(fin.get("monthly_debt") or 0)
    assets=float(fin.get("assets") or 0); investments=float(fin.get("investments") or 0)
    net=income-expenses-monthly_debt
    expense_ratio=expenses/income*100 if income else 0
    dti=monthly_debt/income*100 if income else 0
    savings=max(0,net)
    # Assets and investments are shown separately; do not assume they are all liquid.
    net_worth=assets+investments-debt
    liquidity_label={"Low":"Low","Medium":"Moderate","High":"High"}.get(fin.get("liquidity"),"Moderate")
    if net < 0: cash_status="Negative"
    elif net == 0: cash_status="Balanced"
    else: cash_status="Positive"
    if income == 0: debt_status="Cannot assess without monthly income"
    elif dti >= 40: debt_status="High monthly debt burden"
    elif dti >= 20: debt_status="Moderate monthly debt burden"
    else: debt_status="Lower monthly debt burden"
    strengths=[]; actions=[]
    if net > 0: strengths.append("Monthly cash flow is positive before any unrecorded expenses.")
    else: actions.append("Review spending and debt obligations because current net monthly cash flow is not positive.")
    if income and expense_ratio < 60: strengths.append("Recorded living expenses are below 60% of monthly income.")
    if dti >= 40: actions.append("Prioritize reviewing monthly debt service and avoid adding obligations without a full affordability check.")
    if savings == 0: actions.append("Establish a sustainable positive monthly surplus before setting an aggressive savings target.")
    if fin.get("liquidity") == "Low": actions.append("Review emergency liquidity needs and consider keeping accessible funds for unexpected expenses.")
    if not actions: actions.append("Maintain a buffer for unexpected costs and revisit assumptions regularly.")
    return {"income":income,"expenses":expenses,"monthly_debt":monthly_debt,"net_cash":net,
            "expense_ratio":expense_ratio,"dti":dti,"savings":savings,"assets":assets,
            "investments":investments,"debt":debt,"net_worth":net_worth,"cash_status":cash_status,
            "debt_status":debt_status,"liquidity_label":liquidity_label,"strengths":strengths,"actions":actions}

def scenarios(fin, metrics):
    income=metrics["income"]; expenses=metrics["expenses"]; debtpay=metrics["monthly_debt"]
    rates=[
        ("Severely Conservative", .75, 1.25, "Severe stress: income falls 25%; expenses rise 25%."),
        ("Conservative", .90, 1.10, "Stress: income falls 10%; expenses rise 10%."),
        ("Baseline", 1.00, 1.00, "Uses the current values entered by the user."),
        ("Optimistic", 1.10, 1.00, "Illustrative improvement: income rises 10%; expenses unchanged."),
        ("Highly Optimistic", 1.20, .95, "Illustrative improvement: income rises 20%; expenses fall 5%."),
    ]
    out=[]
    for name, ir, er, desc in rates:
        adjusted_income=income*ir; adjusted_expenses=expenses*er
        cash=adjusted_income-adjusted_expenses-debtpay
        out.append({"name":name,"income":adjusted_income,"expenses":adjusted_expenses,
                    "cash":cash,"annual":cash*12,"description":desc})
    # These are transparent rule-based suitability indicators, not AI predictions.
    for s in out:
        score=50
        if s["cash"]>0: score += 25
        if s["cash"]>=metrics["savings"]*.8: score += 10
        if fin.get("risk")=="Low" and s["name"] in ("Conservative","Severely Conservative"): score += 10
        if s["cash"]<0: score -= 25
        s["score"]=max(5,min(95,score))
        s["status"]="More suitable" if s["score"]>=75 else ("Consider carefully" if s["score"]>=50 else "Risk contingency")
    return sorted(out,key=lambda x:x["score"],reverse=True)

@app.context_processor
def inject_globals():
    return {"user": current_user(), "year": datetime.now().year}

@app.route("/")
def home():
    return render_template("index.html", page="home")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower()
        password=request.form.get("password",""); confirm=request.form.get("confirm_password","")
        if not name or not email or len(password)<8:
            flash("Enter your name and email, and use a password with at least 8 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            try:
                with db() as con:
                    cur=con.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                                    (name,email,generate_password_hash(password)))
                    uid=cur.lastrowid
                    con.execute("INSERT INTO finances(user_id) VALUES(?)",(uid,))
                session["user_id"]=uid
                flash("Account created. Welcome to FINOVA.", "success")
                return redirect(url_for("overview"))
            except sqlite3.IntegrityError:
                flash("An account with this email already exists.", "error")
    return render_template("index.html", page="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        with db() as con: u=con.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        if u and check_password_hash(u["password_hash"],password):
            session["user_id"]=u["id"]; return redirect(url_for("overview"))
        flash("Email or password is incorrect.", "error")
    return render_template("index.html", page="login")

@app.route("/logout")
def logout():
    session.clear(); flash("You have been logged out.", "success"); return redirect(url_for("home"))

@app.route("/forgot-password", methods=["GET","POST"])
def forgot_password():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        new=request.form.get("new_password",""); confirm=request.form.get("confirm_password","")
        with db() as con: u=con.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        if not u: flash("No account was found for that email.", "error")
        elif len(new)<8: flash("Use a password with at least 8 characters.", "error")
        elif new!=confirm: flash("Passwords do not match.", "error")
        else:
            with db() as con: con.execute("UPDATE users SET password_hash=? WHERE id=?",(generate_password_hash(new),u["id"]))
            flash("Password updated. You can now log in.", "success"); return redirect(url_for("login"))
    return render_template("index.html", page="forgot")

@app.route("/overview")
@login_required
def overview():
    fin=get_finance(session["user_id"]); metrics=calculate(fin)
    return render_template("index.html",page="overview",fin=fin,m=metrics,scenarios=scenarios(fin,metrics))

@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    u=current_user()
    if request.method=="POST":
        with db() as con:
            con.execute("UPDATE users SET name=?, age=?, gender=?, country=?, city=?, phone=?, occupation=? WHERE id=?",
                (request.form.get("name","").strip(), request.form.get("age") or None,
                 request.form.get("gender"),request.form.get("country"),request.form.get("city"),
                 request.form.get("phone"),request.form.get("occupation"),u["id"]))
            old=request.form.get("old_password",""); new=request.form.get("new_password",""); confirm=request.form.get("confirm_password","")
            if old or new or confirm:
                if not check_password_hash(u["password_hash"],old): flash("Current password is incorrect.", "error")
                elif len(new)<8: flash("New password must contain at least 8 characters.", "error")
                elif new!=confirm: flash("New passwords do not match.", "error")
                else:
                    con.execute("UPDATE users SET password_hash=? WHERE id=?",(generate_password_hash(new),u["id"]))
                    flash("Profile and password updated.", "success")
            else: flash("Profile updated.", "success")
        return redirect(url_for("profile"))
    return render_template("index.html",page="profile",u=u)

@app.route("/financial-info", methods=["GET","POST"])
@login_required
def financial_info():
    fin=get_finance(session["user_id"])
    if request.method=="POST":
        try:
            def amount(key):
                raw=request.form.get(key,"0").replace(",","").replace(" ","")
                val=float(raw or 0)
                if not math.isfinite(val) or val<0: raise ValueError
                return val
            vals=(amount("income"),amount("expenses"),amount("investments"),amount("assets"),
                  int(request.form.get("years","10")),request.form.get("liquidity","Medium"),
                  request.form.get("risk","Medium"),amount("debt"),amount("monthly_debt"),session["user_id"])
            if vals[4]<1 or vals[4]>30: raise ValueError
            with db() as con:
                con.execute("""INSERT INTO finances(income,expenses,investments,assets,years,liquidity,risk,debt,monthly_debt,user_id,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id) DO UPDATE SET
                    income=excluded.income,expenses=excluded.expenses,investments=excluded.investments,
                    assets=excluded.assets,years=excluded.years,liquidity=excluded.liquidity,risk=excluded.risk,
                    debt=excluded.debt,monthly_debt=excluded.monthly_debt,updated_at=CURRENT_TIMESTAMP""",vals)
            return redirect(url_for("results"))
        except (ValueError,OverflowError):
            flash("Enter valid non-negative amounts. The planning horizon must be between 1 and 30 years.", "error")
    return render_template("index.html",page="financial",fin=fin)

@app.route("/results")
@login_required
def results():
    fin=get_finance(session["user_id"]); m=calculate(fin); ss=scenarios(fin,m)
    return render_template("index.html",page="results",fin=fin,m=m,scenarios=ss)

@app.route("/what-if", methods=["GET","POST"])
@login_required
def what_if():
    fin=get_finance(session["user_id"]); m=calculate(fin); result=None
    if request.method=="POST":
        try:
            def pct(k):
                v=float(request.form.get(k,"0") or 0)
                if not -100 <= v <= 500: raise ValueError
                return v
            inc=pct("income_change"); exp=pct("expense_change"); save=pct("savings_change")
            income=m["income"]*(1+inc/100); expenses=m["expenses"]*(1+exp/100)
            cash=income-expenses-m["monthly_debt"]
            result={"income_change":inc,"expense_change":exp,"savings_change":save,"income":income,
                    "expenses":expenses,"cash":cash,"annual":cash*12,
                    "variance":cash-m["net_cash"],"savings_capacity":max(0,cash)*(1+save/100)}
        except ValueError: flash("Enter valid percentage changes.", "error")
    return render_template("index.html",page="whatif",fin=fin,m=m,result=result)

@app.route("/goals", methods=["GET","POST"])
@login_required
def goals():
    fin=get_finance(session["user_id"]); m=calculate(fin); result=None
    if request.method=="POST":
        try:
            target=float(request.form.get("target","0").replace(",","")); existing=float(request.form.get("existing","0").replace(",",""))
            years=int(request.form.get("goal_years","5")); assumed_income=float(request.form.get("future_income","0").replace(",","") or 0)
            savings_rate=float(request.form.get("savings_rate","20")); ret=float(request.form.get("return_rate","0"))
            if min(target,existing,assumed_income,savings_rate)<0 or not 1<=years<=50 or savings_rate>100 or not -100<=ret<=100: raise ValueError
            remaining=max(0,target-existing); months=years*12
            monthly_required=remaining/months if months else remaining
            monthly_capacity=(assumed_income if assumed_income>0 else m["income"])*savings_rate/100
            monthly_gap=monthly_capacity-monthly_required
            # Illustrative monthly compounding assumption, not a promised return.
            r=ret/1200
            if abs(r)<1e-10: future=existing+monthly_capacity*months
            else: future=existing*((1+r)**months)+monthly_capacity*(((1+r)**months-1)/r)
            feasible=future>=target
            result={"target":target,"existing":existing,"remaining":remaining,"years":years,"monthly_required":monthly_required,
                    "monthly_capacity":monthly_capacity,"gap":monthly_gap,"future":future,"feasible":feasible,
                    "return_rate":ret,"assumed_income":assumed_income or m["income"],"savings_rate":savings_rate,
                    "months":months,"shortfall":max(0,target-future)}
        except (ValueError,OverflowError): flash("Check the goal amounts, timeframe, savings rate, and return assumption.", "error")
    return render_template("index.html",page="goals",fin=fin,m=m,result=result)

@app.route("/evaluation", methods=["GET","POST"])
@login_required
def evaluation():
    if request.method=="POST":
        try:
            vals=[int(request.form.get(k,"0")) for k in ("accuracy","groundedness","usability","processing_time")]
            if any(v<1 or v>5 for v in vals): raise ValueError
            with db() as con:
                con.execute("INSERT INTO ratings(user_id,accuracy,groundedness,usability,processing_time,comment) VALUES(?,?,?,?,?,?)",
                            (session["user_id"],*vals,request.form.get("comment","")[:2000]))
            flash("Thank you. Your evaluation has been recorded.", "success")
            return redirect(url_for("evaluation"))
        except ValueError: flash("Please rate each criterion from 1 to 5 stars.", "error")
    with db() as con:
        agg=con.execute("SELECT AVG((accuracy+groundedness+usability+processing_time)/4.0) AS avg, COUNT(*) AS n FROM ratings").fetchone()
        recent=con.execute("SELECT * FROM ratings ORDER BY id DESC LIMIT 8").fetchall()
    avg=agg["avg"] or 0
    return render_template("index.html",page="evaluation",avg=avg,count=agg["n"],recent=recent)

@app.route("/support", methods=["GET","POST"])
@login_required
def support():
    if request.method=="POST":
        f=request.files.get("attachment"); name=""
        if f and f.filename:
            name=os.path.basename(f.filename)[:180]
        with db() as con:
            con.execute("INSERT INTO support_requests(user_id,issue_type,subject,description,email,attachment_name) VALUES(?,?,?,?,?,?)",
                (session["user_id"],request.form.get("issue_type"),request.form.get("subject","")[:250],
                 request.form.get("description","")[:5000],request.form.get("email","")[:250],name))
        flash("Support request submitted. The demo stores the request in its database; email delivery is not configured.", "success")
        return redirect(url_for("support"))
    return render_template("index.html",page="support")

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    message=request.form.get("message","").strip()
    if not message: return jsonify({"answer":"Please enter a question."})
    # Without a configured LLM provider, give grounded rule-based assistance instead of pretending to call AI.
    fin=get_finance(session["user_id"]); m=calculate(fin)
    low=message.lower()
    if any(x in low for x in ["cash flow","dòng tiền","net cash"]):
        answer=f"Your recorded net monthly cash flow is {m['net_cash']:,.0f} VND (income minus living expenses and monthly debt service). This result depends on the information entered in FINOVA."
    elif any(x in low for x in ["dti","debt-to-income","nợ"]):
        answer=f"Your monthly debt-to-income ratio is {m['dti']:.1f}% based on recorded monthly debt payments divided by monthly income. {m['debt_status']}."
    elif any(x in low for x in ["net worth","tài sản ròng"]):
        answer=f"Estimated net worth in this demo is {m['net_worth']:,.0f} VND = recorded assets + investments − total current debt. This estimate is only as complete as your input data."
    elif any(x in low for x in ["scenario","kịch bản","stress","what-if"]):
        answer="FINOVA compares five illustrative paths: Severely Conservative, Conservative, Baseline, Optimistic, and Highly Optimistic. Each changes declared assumptions; optimistic paths are not guaranteed outcomes. Open What-If Analysis to adjust income and expenses."
    elif any(x in low for x in ["goal","mục tiêu","save","tiết kiệm","investment","đầu tư"]):
        answer="Open Savings & Investment, enter a target amount, current funds allocated to the goal, timeframe, savings rate, and an optional assumed return. The result is a mathematical simulation, not a guaranteed return or personalized investment advice."
    else:
        answer="I can help explain FINOVA workflows and the metrics available in your current profile. Try asking about cash flow, DTI, net worth, scenarios, or savings goals. For questions requiring a configured language model or documentation not included in this demo, the answer may be limited."
    return jsonify({"answer":answer})

@app.route("/export.xlsx")
@login_required
def export_xlsx():
    # CSV is used as a dependency-free fallback, with Excel-compatible encoding.
    fin=get_finance(session["user_id"]); m=calculate(fin); ss=scenarios(fin,m)
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(["FINOVA Financial Report"]); w.writerow(["Generated",datetime.now().isoformat(timespec="seconds")])
    w.writerow([]); w.writerow(["Financial Summary","Value","Unit"])
    rows=[("Total Monthly Income",m["income"],"VND/month"),("Total Monthly Expenses",m["expenses"],"VND/month"),
          ("Monthly Debt Service",m["monthly_debt"],"VND/month"),("Net Monthly Cash Flow",m["net_cash"],"VND/month"),
          ("Expense-to-Income Ratio",round(m["expense_ratio"],2),"%"),("Debt-to-Income Ratio",round(m["dti"],2),"%"),
          ("Monthly Savings Capacity",m["savings"],"VND/month"),("Total Assets",m["assets"],"VND"),
          ("Investments",m["investments"],"VND"),("Total Current Liabilities",m["debt"],"VND"),
          ("Estimated Net Worth",m["net_worth"],"VND")]
    w.writerows(rows); w.writerow([]); w.writerow(["Scenario","Monthly income","Monthly expenses","Net monthly cash flow","Annual cash flow","Suitability score","Assumptions"])
    for s in ss: w.writerow([s["name"],s["income"],s["expenses"],s["cash"],s["annual"],s["score"],s["description"]])
    data="\ufeff"+out.getvalue()
    return send_file(io.BytesIO(data.encode("utf-8")),mimetype="text/csv",as_attachment=True,download_name="FINOVA_Financial_Report.csv")

@app.route("/help")
def help_page():
    return render_template("index.html",page="help")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
