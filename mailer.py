"""
Handles sending the payment-confirmation email over SMTP (Gmail by default).

Set these environment variables before running the app:
    SMTP_EMAIL     -> the sending Gmail address, e.g. events.sdmsmk@gmail.com
    SMTP_PASSWORD  -> a 16-character Gmail "App Password"
                      (Google Account -> Security -> 2-Step Verification -> App Passwords)

Never hard-code real credentials in this file.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "your-email@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "your-app-password")
SENDER_NAME = "SDMSMK aThon 2026 Team"


def _confirmation_html(student, event_name, event_date):
    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0b0f2b;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0b0f2b;padding:30px 0;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#13183f;border-radius:16px;overflow:hidden;border:1px solid #2a2f66;">

        <tr>
          <td style="background:linear-gradient(90deg,#00d4ff,#7b2ff7,#ff2e9a);padding:26px 30px;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;letter-spacing:1px;">
              ✅ Registration Confirmed!
            </h1>
          </td>
        </tr>

        <tr>
          <td style="padding:30px;">
            <p style="color:#e7e9ff;font-size:15px;line-height:1.6;">
              Hi <strong style="color:#00d4ff;">{student.name}</strong>,
            </p>
            <p style="color:#c7cbf5;font-size:15px;line-height:1.6;">
              Great news! We've received your payment and your registration for
              <strong style="color:#ff2e9a;">{event_name}</strong> is now
              <strong style="color:#4dff88;">CONFIRMED</strong>.
            </p>

            <table width="100%" cellpadding="8" cellspacing="0"
                   style="background:#0b0f2b;border-radius:10px;margin:20px 0;border:1px solid #2a2f66;">
              <tr>
                <td style="color:#9aa0e8;font-size:13px;">Participant</td>
                <td style="color:#ffffff;font-size:13px;text-align:right;">{student.name}</td>
              </tr>
              <tr>
                <td style="color:#9aa0e8;font-size:13px;">Registration Type</td>
                <td style="color:#ffffff;font-size:13px;text-align:right;">{student.reg_type.title()}</td>
              </tr>
              <tr>
                <td style="color:#9aa0e8;font-size:13px;">College</td>
                <td style="color:#ffffff;font-size:13px;text-align:right;">{student.college}</td>
              </tr>
              <tr>
                <td style="color:#9aa0e8;font-size:13px;">Batch</td>
                <td style="color:#ffffff;font-size:13px;text-align:right;">{student.batch}</td>
              </tr>
              <tr>
                <td style="color:#9aa0e8;font-size:13px;">Amount Paid</td>
                <td style="color:#4dff88;font-size:13px;text-align:right;">₹{student.fee}</td>
              </tr>
              <tr>
                <td style="color:#9aa0e8;font-size:13px;">Event Date</td>
                <td style="color:#ffffff;font-size:13px;text-align:right;">{event_date}</td>
              </tr>
            </table>

            <p style="color:#c7cbf5;font-size:14px;line-height:1.6;">
              Please log in to your student dashboard and carry a copy of this email
              (or your dashboard screen) to the venue on the day of the event.
            </p>

            <p style="color:#c7cbf5;font-size:14px;line-height:1.6;">
              See you at the Ideathon — bring your best ideas! 🚀
            </p>
          </td>
        </tr>

        <tr>
          <td style="background:#0b0f2b;padding:18px 30px;border-top:1px solid #2a2f66;">
            <p style="margin:0;color:#7d82c2;font-size:12px;">
              Sri Durga Malleswara Siddhartha Mahila Kalasala &middot; Department of Computer Science
              &amp; Department of Electronics<br>
              In association with Anitha Technologies &amp; Services
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_confirmation_email(student, event_name, event_date):
    """Send the payment confirmation email to a student. Raises on failure."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"✅ Payment Confirmed — {event_name}"
    msg["From"] = f"{SENDER_NAME} <{SMTP_EMAIL}>"
    msg["To"] = student.email

    text_body = (
        f"Hi {student.name},\n\n"
        f"Your payment for {event_name} has been received and confirmed.\n"
        f"Registration type: {student.reg_type}\n"
        f"Amount paid: Rs.{student.fee}\n"
        f"Event date: {event_date}\n\n"
        f"See you there!\n- SDMSMK aThon Team"
    )
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(_confirmation_html(student, event_name, event_date), "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [student.email], msg.as_string())
