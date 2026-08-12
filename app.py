"""
SDMSMK aThon 2026 - 12-Hour Ideathon Registration & Management Portal
Sri Durga Malleswara Siddhartha Mahila Kalasala
In association with Anitha Technologies & Services

Run:
    pip install -r requirements.txt
    python app.py

Configure SMTP credentials as environment variables before running:
    SMTP_EMAIL, SMTP_PASSWORD  (use a Gmail App Password, not your normal password)
"""

import os
import threading
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for, request,
    session, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from mailer import send_confirmation_email

# ---------------------------------------------------------------------------
# App / DB config
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Use an external Postgres database (e.g. Neon, Supabase) when DATABASE_URL is set —
# this is REQUIRED on Render's free tier, since its local disk is wiped on every
# restart/redeploy/sleep-wake cycle and SQLite data would be lost otherwise.
_db_url = os.environ.get("DATABASE_URL", "sqlite:///ideathon.db")
if _db_url.startswith("postgres://"):
    # SQLAlchemy requires the "postgresql://" scheme; some providers still hand out "postgres://"
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

EVENT_NAME = "SDMSMK aThon 2026 — 12-Hour Ideathon"
EVENT_DATE = "14-08-2026"
INDIVIDUAL_FEE = 200
GROUP_FEE = 800

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin@123")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    college = db.Column(db.String(200), nullable=False)
    batch = db.Column(db.String(50), nullable=False)   # e.g. 2024-2027, CSE-A
    reg_type = db.Column(db.String(20), nullable=False)  # individual / group
    team_name = db.Column(db.String(120))
    team_members = db.Column(db.Text)  # comma separated, only for group
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="pending")        # pending / approved
    payment_status = db.Column(db.String(20), default="pending")  # pending / paid
    payment_screenshot = db.Column(db.String(255))
    email_status = db.Column(db.String(20), default="not_sent")  # not_sent / sending / sent / failed
    email_error = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def fee(self):
        return INDIVIDUAL_FEE if self.reg_type == "individual" else GROUP_FEE


class OrgMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    role = db.Column(db.String(100), nullable=False)  # coordinator / volunteer etc.
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Judge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    expertise = db.Column(db.String(150))
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    judge_id = db.Column(db.Integer, db.ForeignKey("judge.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    round = db.relationship("Round")
    student = db.relationship("Student")
    judge = db.relationship("Judge")

    __table_args__ = (
        db.UniqueConstraint("round_id", "student_id", "judge_id", name="uniq_score_per_judge"),
    )


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def login_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if session.get("role") != role:
                flash("Please log in to continue.", "error")
                return redirect(url_for(f"{role}_login"))
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template(
        "index.html",
        event_name=EVENT_NAME,
        event_date=EVENT_DATE,
        individual_fee=INDIVIDUAL_FEE,
        group_fee=GROUP_FEE,
    )


@app.route("/contact")
def contact():
    chief_patrons = [
        {"name": "Sri. M. Rajaiah", "role": "President — SAGTE"},
        {"name": "Sri. P. Lakshman Rao", "role": "Secretary — SAGTE"},
        {"name": "Sri. S. Venkateswara Rao", "role": "Treasurer — SAGTE"},
        {"name": "Sri Ch. Krishna Rao", "role": "Vice President — SAGTE & Convenor, SDMSMK"},
        {"name": "Sri L. K. Mohana Rao", "role": "Administrative Academic Officer — SDMSMK"},
    ]
    staff_coordinators = [
        {"name": "S. Gokila", "role": "Lecturer, Department of Computer Science", "phone": "99441 30943"},
        {"name": "P. Meghana Durga", "role": "Lecturer, Department of Computer Science", "phone": "90144 79634"},
        {"name": "N. Yamini Babitha", "role": "Lecturer, Department of Electronics", "phone": "70328 51740"},
        {"name": "N. Himaja", "role": "Lecturer, Department of Electronics", "phone": "91606 75285"},
    ]
    patrons = [
        {"name": "Dr. P. V. Durgavathi", "role": "Principal"},
        {"name": "Smt. M. Praveena", "role": "Convenor, HOD Department of Computer Science"},
        {"name": "Kum. J. Parasmal Kanti", "role": "HOD, Department of Electronics"},
        {"name": "V. Siva Krishnaveni", "role": "Co-Convenor, Asst. Professor, Computer Science"},
        {"name": "P. Harika", "role": "Assistant Professor, Department of Computer Science"},
        {"name": "Ch. Manohari", "role": "Lecturer, Department of Electronics"},
    ]
    company_contacts = [
        {"name": "V. Uma Manikanta", "role": "CEO & Director, Anitha Technologies & Services", "phone": "91823 65689"},
        {"name": "Anitha Technologies & Services", "role": "Event Organizing Company — General Enquiries", "phone": "72076 60201"},
    ]
    return render_template(
        "contact.html",
        chief_patrons=chief_patrons,
        staff_coordinators=staff_coordinators,
        patrons=patrons,
        company_contacts=company_contacts,
        event_date=EVENT_DATE,
    )


# ---------------------------------------------------------------------------
# Student: register / login / dashboard
# ---------------------------------------------------------------------------
@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if Student.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return redirect(url_for("student_register"))

        student = Student(
            name=request.form["name"].strip(),
            email=email,
            phone=request.form["phone"].strip(),
            college=request.form["college"].strip(),
            batch=request.form["batch"].strip(),
            reg_type=request.form["reg_type"],
            team_name=request.form.get("team_name", "").strip(),
            team_members=request.form.get("team_members", "").strip(),
            password_hash=generate_password_hash(request.form["password"]),
        )
        db.session.add(student)
        db.session.commit()
        flash("Registration submitted! Your account is pending admin approval.", "success")
        return redirect(url_for("student_login"))

    return render_template("student_register.html", individual_fee=INDIVIDUAL_FEE, group_fee=GROUP_FEE)


@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        student = Student.query.filter_by(email=email).first()
        if student and check_password_hash(student.password_hash, request.form["password"]):
            session.clear()
            session["role"] = "student"
            session["user_id"] = student.id
            return redirect(url_for("student_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("student_login.html")


@app.route("/student/dashboard")
@login_required("student")
def student_dashboard():
    student = Student.query.get_or_404(session["user_id"])
    return render_template("student_dashboard.html", student=student, event_date=EVENT_DATE)


@app.route("/student/logout")
def student_logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Organizing team: register / login / dashboard
# ---------------------------------------------------------------------------
@app.route("/org/register", methods=["GET", "POST"])
def org_register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if OrgMember.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return redirect(url_for("org_register"))

        member = OrgMember(
            name=request.form["name"].strip(),
            email=email,
            phone=request.form["phone"].strip(),
            role=request.form["role"].strip(),
            password_hash=generate_password_hash(request.form["password"]),
        )
        db.session.add(member)
        db.session.commit()
        flash("Registration submitted! Your account is pending admin approval.", "success")
        return redirect(url_for("org_login"))

    return render_template("org_register.html")


@app.route("/org/login", methods=["GET", "POST"])
def org_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        member = OrgMember.query.filter_by(email=email).first()
        if member and check_password_hash(member.password_hash, request.form["password"]):
            session.clear()
            session["role"] = "org"
            session["user_id"] = member.id
            return redirect(url_for("org_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("org_login.html")


@app.route("/org/dashboard")
@login_required("org")
def org_dashboard():
    member = OrgMember.query.get_or_404(session["user_id"])
    students = Student.query.order_by(Student.created_at.desc()).all()
    return render_template("org_dashboard.html", member=member, students=students)


@app.route("/org/logout")
def org_logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Judge: register / login / dashboard (scoring)
# ---------------------------------------------------------------------------
@app.route("/judge/register", methods=["GET", "POST"])
def judge_register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if Judge.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return redirect(url_for("judge_register"))

        judge = Judge(
            name=request.form["name"].strip(),
            email=email,
            phone=request.form["phone"].strip(),
            expertise=request.form.get("expertise", "").strip(),
            password_hash=generate_password_hash(request.form["password"]),
        )
        db.session.add(judge)
        db.session.commit()
        flash("Registration submitted! Your account is pending admin approval.", "success")
        return redirect(url_for("judge_login"))

    return render_template("judge_register.html")


@app.route("/judge/login", methods=["GET", "POST"])
def judge_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        judge = Judge.query.filter_by(email=email).first()
        if judge and check_password_hash(judge.password_hash, request.form["password"]):
            if judge.status != "approved":
                flash("Your account is still pending admin approval.", "error")
                return redirect(url_for("judge_login"))
            session.clear()
            session["role"] = "judge"
            session["user_id"] = judge.id
            return redirect(url_for("judge_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("judge_login.html")


@app.route("/judge/dashboard", methods=["GET", "POST"])
@login_required("judge")
def judge_dashboard():
    judge = Judge.query.get_or_404(session["user_id"])
    rounds = Round.query.order_by(Round.created_at).all()
    students = Student.query.filter_by(status="approved", payment_status="paid").order_by(Student.name).all()

    if request.method == "POST":
        round_id = int(request.form["round_id"])
        student_id = int(request.form["student_id"])
        score_val = float(request.form["score"])
        remarks = request.form.get("remarks", "").strip()

        existing = Score.query.filter_by(round_id=round_id, student_id=student_id, judge_id=judge.id).first()
        if existing:
            existing.score = score_val
            existing.remarks = remarks
        else:
            db.session.add(Score(round_id=round_id, student_id=student_id, judge_id=judge.id,
                                  score=score_val, remarks=remarks))
        db.session.commit()
        flash("Score saved.", "success")
        return redirect(url_for("judge_dashboard"))

    my_scores = Score.query.filter_by(judge_id=judge.id).all()
    scored_keys = {(s.round_id, s.student_id) for s in my_scores}

    return render_template(
        "judge_dashboard.html",
        judge=judge, rounds=rounds, students=students, scored_keys=scored_keys,
    )


@app.route("/judge/logout")
def judge_logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session.clear()
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@login_required("admin")
def admin_dashboard():
    students = Student.query.order_by(Student.created_at.desc()).all()
    org_members = OrgMember.query.order_by(OrgMember.created_at.desc()).all()
    judges = Judge.query.order_by(Judge.created_at.desc()).all()
    rounds = Round.query.order_by(Round.created_at).all()
    return render_template(
        "admin_dashboard.html",
        students=students, org_members=org_members, judges=judges, rounds=rounds,
    )


@app.route("/admin/approve/<entity>/<int:entity_id>", methods=["POST"])
@login_required("admin")
def admin_approve(entity, entity_id):
    model = {"student": Student, "org": OrgMember, "judge": Judge}.get(entity)
    if not model:
        return jsonify({"ok": False}), 400
    obj = model.query.get_or_404(entity_id)
    obj.status = "approved"
    db.session.commit()
    flash(f"{entity.capitalize()} account approved.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/mark_payment/<int:student_id>", methods=["POST"])
@login_required("admin")
def admin_mark_payment(student_id):
    student = Student.query.get_or_404(student_id)
    student.payment_status = "paid"
    db.session.commit()
    flash(f"Payment marked as PAID for {student.name}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/send_confirmation/<int:student_id>", methods=["POST"])
@login_required("admin")
def admin_send_confirmation(student_id):
    student = Student.query.get_or_404(student_id)
    if student.payment_status != "paid":
        flash("Mark the payment as paid before sending a confirmation email.", "error")
        return redirect(url_for("admin_dashboard"))

    student.email_status = "sending"
    student.email_error = None
    db.session.commit()

    app_obj = app  # captured for the thread's app-context

    def _send_in_background(student_id, event_name, event_date):
        with app_obj.app_context():
            s = Student.query.get(student_id)
            try:
                send_confirmation_email(s, event_name, event_date)
                s.email_status = "sent"
                s.email_error = None
            except Exception as exc:
                s.email_status = "failed"
                s.email_error = str(exc)[:290]
                print(f"[admin_send_confirmation] Failed for {s.email}: {exc}")
            db.session.commit()

    thread = threading.Thread(
        target=_send_in_background,
        args=(student.id, EVENT_NAME, EVENT_DATE),
        daemon=True,
    )
    thread.start()

    flash(f"Sending confirmation email to {student.email} in the background — refresh in a few seconds to see the result.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/create_round", methods=["POST"])
@login_required("admin")
def admin_create_round(name=None):
    r = Round(name=request.form["name"].strip(), description=request.form.get("description", "").strip())
    db.session.add(r)
    db.session.commit()
    flash(f"Round '{r.name}' created.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/leaderboard/<int:round_id>")
@login_required("admin")
def admin_leaderboard(round_id):
    rnd = Round.query.get_or_404(round_id)
    scores = Score.query.filter_by(round_id=round_id).all()
    tally = {}
    for s in scores:
        tally.setdefault(s.student_id, []).append(s.score)
    leaderboard = sorted(
        [(Student.query.get(sid), sum(vals) / len(vals)) for sid, vals in tally.items()],
        key=lambda x: x[1], reverse=True,
    )
    return render_template("leaderboard.html", round=rnd, leaderboard=leaderboard)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


# Create tables on startup. This runs at import time so it works both with
# `python app.py` locally AND under gunicorn in production (gunicorn imports
# this module directly and never executes the `if __name__ == "__main__"` block).
with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
