import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to_email, subject, html_content):
    message = Mail(
        from_email='asieniantour@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('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'))
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(e)
        return None
