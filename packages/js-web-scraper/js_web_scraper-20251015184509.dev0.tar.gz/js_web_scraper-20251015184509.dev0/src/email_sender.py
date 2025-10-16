import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO

from dotenv import load_dotenv
from pandas import DataFrame


def send_email(new_cars: DataFrame):
    csv_buf = StringIO()

    new_cars.to_csv(csv_buf, index=False)

    html = f"""
        <html>
            <body>
                {new_cars.to_html()}
            </body>
        </html>"""
    __send_email__("New Car Listings", html, csv_buf)


def send_email_str(text: str):
    html = f"""
        <html>
            <body>
                {text}
            </body>
        </html>"""
    __send_email__("Tesla NACS Website Update", html)


def __send_email__(subject: str, html: str, attachment: StringIO = None):
    load_dotenv()
    sender_email = os.environ["SENDER_EMAIL"]
    from_email = os.environ["FROM_EMAIL"]
    receiver_email = os.environ["RECEIVER_EMAIL"]
    password = os.environ["PASSWORD"]
    smtp_server = os.environ["SMTP_SERVER"]
    smtp_port: int = int(os.environ["SMTP_PORT"])
    tls: bool = bool(os.environ["TLS"])

    message = MIMEMultipart("related")
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = receiver_email

    html_part = MIMEMultipart("related")

    html_part.attach(MIMEText(html, "html"))
    message.attach(html_part)

    if attachment:
        attach_part = MIMEMultipart("mixed")

        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.getvalue())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename="new_cars.csv")
        attach_part.attach(part)
        message.attach(attach_part)

    if tls:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)

            server.sendmail(from_email, receiver_email, message.as_string())
    else:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)

            server.sendmail(from_email, receiver_email, message.as_string())
