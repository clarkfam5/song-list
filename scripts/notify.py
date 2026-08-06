import smtplib
from email.mime.text import MIMEText


def build_review_email(pending_items, review_page_url):
    lines = [f"{len(pending_items)} video(s) need review before they go live:\n"]
    for item in pending_items:
        lines.append(f"- {item['title']} ({item['date']})")
    lines.append(f"\nReview them here: {review_page_url}")
    return "\n".join(lines)


def send_review_email(pending_items, recipients, smtp_user, smtp_pass, review_page_url):
    body = build_review_email(pending_items, review_page_url)
    msg = MIMEText(body)
    msg['Subject'] = f"Clark Family Creative: {len(pending_items)} cover(s) need review"
    msg['From'] = smtp_user
    msg['To'] = ", ".join(recipients)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, recipients, msg.as_string())
