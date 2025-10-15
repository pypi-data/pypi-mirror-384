from email.mime.text import MIMEText
import smtplib

otp_store = {}


def otpEmailService(to_email: str, email_body: str) -> bool:
    try:
        senderEmail = "magizhchisk@gmail.com"
        gmailAppPassword = "avqkjxqzjsrnqims"

        # MIMEText is used to format the body of the email
        msg = MIMEText(email_body, "plain")
        msg["Subject"] = "Notification"
        msg["From"] = senderEmail
        msg["To"] = to_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(senderEmail, gmailAppPassword)
            server.send_message(msg)

        return True
    except Exception as e:
        print("Error sending email:", e)
        return False