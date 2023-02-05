from email.message import EmailMessage
import smtplib


class EmailHandler:
    def __init__(self, config):
        self.can_send_emails = config.send_emails
        self.from_email = config.from_email
        self.from_email_pass = config.from_email_pass
        self.to_email = config.to_email

    def send_email(self, subject, msg_content):
        if self.can_send_emails:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg.set_content(msg_content)
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(self.from_email, self.from_email_pass)
                    smtp.send_message(msg)
            except Warning:
                print("email credentials not accepted")
                print("Failed to send email with subject: " + msg['Subject'])
