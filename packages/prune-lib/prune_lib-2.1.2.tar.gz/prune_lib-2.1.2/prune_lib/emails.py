from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import models
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from pydantic import BaseModel, EmailStr


class SendEmailPayload(BaseModel):
    """feature
    :name: SendEmailPayload
    :description: Modèle Pydantic pour valider les données d’envoi d’e-mail.
    :return: instance validée contenant les données d’envoi.
    """

    to_emails: list[EmailStr]
    email_template: models.TextChoices
    context: dict
    subject: str
    with_copy: bool


def _verify_settings():
    """feature
    :name: _verify_settings
    :description: Vérifie la présence des variables de configuration nécessaires pour l’envoi d’e-mails.
    :return: None
    """
    settings_variables = [
        "EMAIL_BACKEND",
        "EMAIL_HOST",
        "EMAIL_USE_TLS",
        "EMAIL_PORT",
        "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD",
        "EMAIL_CUSTOM_TEMPLATES_DIRS",
        "EMAIL_CUSTOM_SUBJECT_PREFIX",
        "EMAIL_CUSTOM_FROM_ADDRESS",
        "EMAIL_CUSTOM_COPY_ADDRESS",
        "TESTING",
    ]
    for setting_variable in settings_variables:
        getattr(settings, setting_variable)


def send_emails_by_smtp(
    *,
    to_emails: list[str],
    email_template: models.TextChoices,
    context: dict,
    subject: str,
    with_copy: bool = True,
):
    """feature
    :name: send_emails_by_smtp
    :description: Envoie un e-mail basé sur un template via Django.
    :param to_emails: liste d’adresses des destinataires.
    :param email_template: nom du template d’e-mail.
    :param context: dictionnaire de variables pour le rendu du template.
    :param subject: sujet de l’e-mail.
    :param with_copy: booléen pour ajouter l’adresse de copie (par défaut True).
    :return: None.
    """
    SendEmailPayload(
        to_emails=to_emails,
        email_template=email_template,
        context=context,
        subject=subject,
        with_copy=with_copy,
    )
    _verify_settings()
    text_content = render_to_string(
        f"emails/{email_template}.txt",
        context=context,
    )
    html_content = None
    try:
        html_content = render_to_string(
            f"emails/{email_template}.html",
            context=context,
        )
    except TemplateDoesNotExist:
        pass
    if settings.TESTING:
        return
    with get_connection() as connection:
        for to_email in to_emails:
            bcc = [settings.EMAIL_CUSTOM_COPY_ADDRESS] if with_copy else []
            message = EmailMultiAlternatives(
                subject=f"[{settings.EMAIL_CUSTOM_SUBJECT_PREFIX}] {subject}",
                body=text_content,
                from_email=settings.EMAIL_CUSTOM_FROM_ADDRESS,
                to=[to_email],
                bcc=bcc,
                connection=connection,
            )
        if html_content:
            message.attach_alternative(html_content, "text/html")
        message.send()
