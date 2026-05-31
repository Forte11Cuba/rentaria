import os

from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        try:
            import resend as resend_client
        except ImportError:
            return 0

        api_key = os.environ.get('RESEND_API_KEY', '')
        if not api_key:
            return 0

        resend_client.api_key = api_key
        num_sent = 0

        for message in email_messages:
            try:
                html_body = None
                if hasattr(message, 'alternatives'):
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            html_body = content
                            break

                params = {
                    'from': message.from_email,
                    'to': list(message.to),
                    'subject': message.subject,
                    'text': message.body,
                }
                if html_body:
                    params['html'] = html_body

                resend_client.Emails.send(params)
                num_sent += 1
            except Exception:
                if not self.fail_silently:
                    raise

        return num_sent
