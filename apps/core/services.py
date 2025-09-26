from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

def send_html_email(subject, template_name, from_email=None, recipient_list=None, context=None):
    """
    Send an HTML email.

    :param subject: Subject of the email
    :param to: Recipient list (list of email addresses)
    :param html_content: HTML content of the email
    :param from_email: Sender's email address (optional)
    """
    
    if recipient_list is None:
        recipient_list = []
    
    if context is None:
        context = {}

    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
      subject=subject, 
      body=text_content, 
      from_email=from_email or settings.DEFAULT_FROM_EMAIL, 
      to=recipient_list
      )
    email.attach_alternative(html_content, "text/html")


    email.send()
    
    
    