# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2025 TU Wien.
#
# Invenio-Config-TUW is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Celery tasks running in the background."""

import re
from difflib import HtmlDiff
from html import unescape as html_unescape
from time import sleep
from typing import Dict, Iterable, List, Optional, Tuple

import bleach
from celery import shared_task
from celery.schedules import crontab
from email_validator import EmailNotValidError, validate_email
from flask import current_app, render_template
from invenio_access.permissions import system_identity
from invenio_accounts.models import User
from invenio_accounts.proxies import current_datastore as datastore
from invenio_base.urls import invenio_url_for
from invenio_db import db
from invenio_files_rest.models import FileInstance
from invenio_mail.tasks import send_email
from invenio_notifications.registry import (
    EntityResolverRegistry as NotificationsResolverRegistry,
)
from invenio_notifications.tasks import broadcast_notification
from invenio_rdm_records.proxies import current_rdm_records_service as records_service

from .notifications import UserNotificationBuilder


def _resolve_users(users: Iterable[User | str]):
    """Resolve all users for the given list of users or email addresses."""
    resolved_users = []
    for u in users:
        if isinstance(u, str):
            if (user := datastore.get_user_by_email(u)) is None:
                raise LookupError(f"Cannot find user '{u}'")
        else:
            user = u

        resolved_users.append(user)

    return resolved_users


@shared_task()
def send_outreach_emails(
    subject: str,
    users: Iterable[User | str],
    sleep_time: float | int = 1,
    retry_failed: bool = True,
    msg: Optional[str] = None,
    html_msg: Optional[str] = None,
    txt_msg: Optional[str] = None,
    sender: Optional[str] = None,
) -> Tuple[List[str], List[str]]:
    """Send an outreach email to all of the specified users.

    The function will return a tuple with two lists containing email addresses of users:
    Successful mail submissions and failures.

    The list of ``users`` can consist of either ``User`` objects, or email addresses.
    This is primarily useful when using this function as background task, since
    that only supports primitive data types as arguments.

    To help avoid rate limiting issues, email submissions will be spaced out by
    ``sleep_time`` seconds each.

    If the flag ``retry_failed`` is set, failed mail submissions are retried once.

    The arguments ``msg``, ``html_msg``, ``txt_msg``, ``sender``, and ``subject`` are
    simply passed on to ``send_outreach_email()``.
    """
    users = _resolve_users(users)
    successes, failures = [], []
    sleep_time = abs(sleep_time)
    last_idx = len(users) - 1
    for i, user in enumerate(users):
        try:
            send_outreach_email(
                recipient=user,
                subject=subject,
                msg=msg,
                html_msg=html_msg,
                txt_msg=txt_msg,
                sender=sender,
            )
            successes.append(user.email)
            current_app.logger.debug(
                f"Successfully sent outreach email to {user.email}"
            )
        except ValueError as e:
            raise e
        except Exception as e:
            failures.append(user.email)
            current_app.logger.error(e)
        finally:
            if i != last_idx:
                sleep(abs(sleep_time))

    if retry_failed:
        new_successes, failures = send_outreach_emails(
            subject,
            failures,
            sleep_time=sleep_time,
            retry_failed=False,
            msg=msg,
            html_msg=html_msg,
            txt_msg=txt_msg,
            sender=sender,
        )
        successes.extend(new_successes)

    return successes, failures


def format_plaintext(html: Optional[str] = None, txt: Optional[str] = None) -> str:
    """Transform the given HTML message into a plaintext variant."""
    if txt:
        return txt

    # bleach likes to replace pointy brackets with HTML entities,
    # which we don't want for plaintext messages - that's why we use `html.unescape()`
    cleaned_msg = bleach.clean(html or "", tags=[], strip=True)
    return html_unescape(cleaned_msg)


def format_html(txt: Optional[str] = None, html: Optional[str] = None) -> str:
    """Mark up the given plaintext message with some HTML."""
    if not html:
        html = "<br />".join((txt or "").splitlines())

    if not re.search(r"(</[a-z]>|<[a-z]\s*/?>)$", html):
        html += "<br />"

    return html


def render_outreach_email(
    user: User,
    msg: Optional[str] = None,
    html_msg: Optional[str] = None,
    txt_msg: Optional[str] = None,
    subject: Optional[str] = None,
) -> Dict[str, str]:
    """Render the outreach email template with the message in various formats.

    If both ``html_msg`` and ``txt_msg`` are provided, they'll be used for the HTML
    and plaintext bodies respectively.
    Otherwise, a little bit of auto-transforming magic from one format to another
    will be performed.
    """
    html_templates = ["invenio_theme_tuw/mails/outreach.html", "outreach_email.html"]
    txt_templates = ["invenio_theme_tuw/mails/outreach.txt", "outreach_email.txt"]
    return {
        "body": render_template(
            txt_templates,
            subject=subject,
            text_message=format_plaintext(html=(msg or html_msg), txt=txt_msg),
            user=user,
        ),
        "html": render_template(
            html_templates,
            subject=subject,
            html_message=format_html(html=html_msg, txt=(msg or txt_msg)),
            user=user,
        ),
    }


@shared_task()
def send_outreach_email(
    recipient: User | str,
    subject: str,
    msg: Optional[str] = None,
    html_msg: Optional[str] = None,
    txt_msg: Optional[str] = None,
    sender: Optional[str] = None,
) -> None:
    """Send an email with the outreach template to the given user.

    The email will send the ``html_msg`` as HTML message, and the ``txt_msg`` as
    plaintext message.
    If ``html_msg`` is not specified, ``msg`` or ``txt_msg`` will be marked up and used.
    Similarly, if ``txt_msg`` is not specified, ``msg`` or ``html_msg`` will be used
    (after stripping out HTML elements).
    As such, only one of ``msg``, ``html_msg``, or ``txt_msg`` *needs* to be given.
    """
    if not msg and not html_msg and not txt_msg:
        raise ValueError("None of 'msg', 'html_msg', or 'txt_msg' were specified")
    if sender:
        try:
            validate_email(sender)
        except EmailNotValidError as e:
            raise ValueError(f"Invalid sender ('{sender}'): {e}")
    if isinstance(recipient, str):
        recipient = datastore.get_user_by_email(recipient)

    send_email(
        {
            "subject": subject,
            "recipients": [recipient.email],
            "sender": sender or current_app.config["MAIL_DEFAULT_SENDER"],
            **render_outreach_email(
                user=recipient,
                msg=msg,
                html_msg=html_msg,
                txt_msg=txt_msg,
                subject=subject,
            ),
        }
    )


@shared_task(ignore_result=True)
def send_publication_notification(recid: str):
    """Send the record uploader an email about the publication of their record."""
    record = records_service.read(identity=system_identity, id_=recid)._obj
    record.relations.clean()
    if (owner := record.parent.access.owner) is None:
        current_app.logger.warning(
            f"Record '{recid}' has no owner to notify about its publication!"
        )
        return

    # build the message
    datacite_test_mode = current_app.config["DATACITE_TEST_MODE"]
    if "identifier" in record.get("pids", {}).get("doi", {}):
        doi = record["pids"]["doi"]["identifier"]

        if datacite_test_mode:
            base_url = "https://handle.test.datacite.org"
            pid_type = "DOI-like handle"
        else:
            base_url = "https://doi.org"
            pid_type = "DOI"

        pid_url = f"{base_url}/{doi}"

    else:
        pid_type = "URL"
        pid_url = invenio_url_for(
            "invenio_app_rdm_records.record_detail",
            pid_value=record.pid.pid_value,
        )

    # send the notification
    notification = UserNotificationBuilder.build(
        receiver=owner.dump(),
        subject=f'Your record "{record.metadata['title']}" was published',
        record=record,
        record_pid={"type": pid_type, "url": pid_url},
        template_name="record-publication.jinja",
    )
    broadcast_notification(notification.dumps())


@shared_task(ignore_reuslt=True)
def send_metadata_edit_notification(
    recid: str,
    publisher: dict,
    additions: list,
    removals: list,
    changes: list,
):
    """Send an email to the record's owner about a published edit."""
    record = records_service.read(identity=system_identity, id_=recid)._obj
    record.relations.clean()
    if (owner := record.parent.access.owner) is None:
        current_app.logger.warning(
            f"Record '{recid}' has no owner to notify about the published edit!"
        )
        return

    description_diff_table = None
    for change in changes:
        field_path, (old, new) = change
        if field_path[0] == "metadata" and field_path[1] == "description":
            diff = HtmlDiff(tabsize=4, wrapcolumn=100)
            old, new = old.splitlines(keepends=True), new.splitlines(keepends=True)
            description_diff_table = diff.make_table(old, new)

    # parse the most interesting changes for the user out of the dictionary diffs
    md_field_names = {"rights": "licenses"}
    updated_metadata_fields = set()
    updated_access_settings = False
    for change in [*additions, *removals, *changes]:
        field_path, *_ = change
        section, field_name = (
            (field_path[0], field_path[1])
            if len(field_path) > 1
            else (None, field_path[0])
        )
        if section == "metadata":
            field_name = md_field_names.get(field_name) or field_name
            updated_metadata_fields.add(field_name.replace("_", " ").capitalize())
        elif section == "access":
            updated_access_settings = True

    # note: in contrast to the "resolver registry" from Invenio-Requests, the one from
    # Invenio-Notifications resolves expanded service result item dictionaries that
    # can be passed on to notifications
    notification = UserNotificationBuilder.build(
        receiver=owner.dump(),
        subject=f'Edits for your record "{record.metadata['title']}" were published',
        recid=record.pid.pid_value,
        record=record,
        publisher=NotificationsResolverRegistry.resolve_entity(publisher),
        updated_access_settings=updated_access_settings,
        updated_metadata_fields=sorted(updated_metadata_fields),
        description_diff_table=description_diff_table,
        template_name="metadata-edit.jinja",
    )
    broadcast_notification(notification.dumps())


@shared_task
def remove_dead_files():
    """Remove dead file instances (that don't have a URI) from the database.

    These files seem to be leftovers from failed uploads that don't get cleaned up
    properly.
    """
    dead_file_instances = FileInstance.query.filter(FileInstance.uri.is_(None)).all()
    for fi in dead_file_instances:
        db.session.delete(fi)
        for o in fi.objects:
            db.session.delete(o)

    db.session.commit()


CELERY_BEAT_SCHEDULE = {
    "clean-dead-files": {
        "task": "invenio_config_tuw.tasks.remove_dead_files",
        "schedule": crontab(minute=1, hour=2),
    },
}
