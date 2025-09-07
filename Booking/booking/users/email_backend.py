# booking/users/email_backend.py
from django.core.mail.backends.smtp import EmailBackend
import ssl
import certifi

class TLSCertifiEmailBackend(EmailBackend):
    def _get_ssl_context(self):
        return ssl.create_default_context(cafile=certifi.where())

    def open(self):
        if self.connection:
            return False
        try:
            import smtplib
            self.connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            self.connection.ehlo()
            self.connection.starttls(context=self._get_ssl_context())
            self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except:
            if not self.fail_silently:
                raise
            return False
