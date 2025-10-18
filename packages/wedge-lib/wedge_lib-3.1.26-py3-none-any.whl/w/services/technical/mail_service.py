import os
from django.core.mail import (
    EmailMessage,
    get_connection,
)
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from w.services.abstract_service import AbstractService


class EmailService(AbstractService):
    @classmethod
    def get_email_object(
        cls, recipients, subject, message, attach_files=None, **options
    ):
        """
        Return an EmailMessage object

        Args:
            recipients(str|list|dict): email or list of emails or dict
                {
                  "to": <email or list of emails>
                  "bcc": <email or list of emails>
                  "cc": <email or list of emails>
                }
            subject (str|dict): subject or template (as dict) :
                {"template_name": <str>, "context": <dict> }
            message (str|dict): message or template (as dict) :
                {"template_name": <str>, "context": <dict> }
            attach_files (list[str|tuple]): list of file to attach
                <str:filename full path> or
                <tuple:(<str:filename>, <bytes:content>, <str:mimetypes>)>
            **options (dict):
                    'from_email': <from_email, default is settings.DEFAULT_FROM_EMAIL>,
                    'reply_to' : <reply to email, None by default>,
                    'send_on' : <date to send the mail, now by default>,

        Returns:
            EmailMessage: email object
        """
        default_params = {
            "from_email": settings.DEFAULT_FROM_EMAIL,
            "to": None,
            "bcc": None,
            "cc": None,
            "connection": None,
            "attachments": None,
            "headers": None,
            "reply_to": settings.DEFAULT_REPLY_TO,
        }

        if not isinstance(recipients, dict):
            recipients = {"to": recipients}

        send_on = options.pop("send_on", timezone.now())

        # noinspection PyDictCreation
        params = {**default_params, **recipients, **options}

        # convert str recipient to list
        for key in ["to", "bcc", "cc", "reply_to"]:
            if params[key] and not isinstance(params[key], list):
                params[key] = [params[key]]

        if isinstance(subject, dict):
            subject = render_to_string(**subject)

        is_html = False
        if isinstance(message, dict):
            _, ext = os.path.splitext(message["template_name"])
            is_html = ext == ".html"
            message = render_to_string(**message)

        params["subject"] = subject
        params["body"] = message
        email = EmailMessage(**params)

        if is_html:
            email.content_subtype = "html"

        if attach_files:
            for file in attach_files:
                if isinstance(file, tuple):
                    email.attach(*file)
                    continue
                email.attach_file(file)

        email.send_on = send_on

        return email

    @classmethod
    def send(cls, recipients, subject, message, attach_files=None, **options):
        """
        Send an email

        Args:
            recipients(str|list|dict): email or list of emails or dict
                {
                  "to": <email or list of emails>
                  "bcc": <email or list of emails>
                  "cc": <email or list of emails>
                }
            subject (str|dict): subject or template (as dict) :
                {"template_name": <str>, "context": <dict> }
            message (str|dict): message or template (as dict) :
                {"template_name": <str>, "context": <dict> }
            attach_files:  (dict) list of file to attach
                {"attach_files": [<str>], "context": <dict> }
            **options (dict):
                    'from_email': <from_email, default is settings.DEFAULT_FROM_EMAIL>,
                    'reply_to' : <reply to email, None by default>,
                    'send_on' : <date to send the mail, now by default>,

        Returns:
            int: number of email sent
        """
        email = cls.get_email_object(
            recipients, subject, message, attach_files, **options
        )

        return email.send()

    @classmethod
    def send_mass_mail(cls, datatuple):
        """
        Given a datatuple of (subject, message, from_email, recipient_list), send
        each message to each recipient list. Return the number of emails sent.
        """
        connection = get_connection()

        messages = [
            cls.get_email_object([recipient], subject, message, **options)
            for recipient, subject, message, options in datatuple
        ]
        return connection.send_messages(messages)
