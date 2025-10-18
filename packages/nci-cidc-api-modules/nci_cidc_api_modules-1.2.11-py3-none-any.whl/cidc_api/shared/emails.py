"""Template functions for CIDC email bodies."""

import html
from functools import wraps
from typing import List

from . import gcloud_client
from ..config.settings import ENV

# emails this list for
# - new user registration,
# - new upload alerts, and
# - upon intaking metadata
# cloud-functions also emails for
# - an inactive user being disabled in disable_inactive_users,
# - errors from CSMS in update_cidc_from_csms,
# - errors from kicking off permissions in grant_download_permissions, and
# - errors from implementing permissions in worker > permissions_worker
CIDC_MAILING_LIST = ["essex-alert@cimac-network.org"]


def sendable(email_template):
    """
    Adds the `send` kwarg to an email template. If send_email=True,
    send the email on function call.
    """

    @wraps(email_template)
    def wrapped(*args, send_email=False, **kwargs):
        email = email_template(*args, **kwargs)
        if send_email:
            gcloud_client.send_email(**email)
        return email

    return wrapped


@sendable
def confirm_account_approval(user) -> dict:
    """Send a message to the user confirming that they are approved to use the CIDC."""

    subject = "CIDC Account Approval"

    html_content = f"""
    <p>Hello {user.first_n},</p>
    <p>
        Your CIMAC-CIDC Portal account has been approved! 
        To begin browsing and downloading data, visit https://cidc.nci.nih.gov.
    </p>
    <p>
        <strong>Note:</strong> If you haven't already, please email NCICIDCAdmin@mail.nih.gov to request permission to view data for the trials and assays relevant to your work.</p>
    <p>Thanks,<br/>The CIDC Project Team</p>
    """

    email = {
        "to_emails": [user.email],
        "subject": subject,
        "html_content": html_content,
    }

    return email


@sendable
def new_user_registration(email: str) -> dict:
    """Alert the CIDC admin mailing list to a new user registration."""

    subject = "New User Registration"

    html_content = (
        f"A new user, {email}, has registered for the CIMAC-CIDC Data Portal ({ENV}). If you are a CIDC Admin, "
        "please visit the accounts management tab in the Portal to review their request."
    )

    email = {
        "to_emails": CIDC_MAILING_LIST,
        "subject": subject,
        "html_content": html_content,
    }

    return email


@sendable
def new_upload_alert(upload, full_metadata) -> dict:
    """Alert the CIDC administrators that an upload succeeded."""
    possible_manifest_info = ""
    if upload.metadata_patch and "shipments" in upload.metadata_patch and upload.metadata_patch["shipments"]:
        manifest_id = upload.metadata_patch["shipments"][0].get("manifest_id")
        possible_manifest_info = f" manifest {manifest_id}"

    subject = f"[UPLOAD SUCCESS]({ENV}) {upload.upload_type}{possible_manifest_info} uploaded to {upload.trial_id}"

    html_content = f"""
    <ul>
        <li><strong>upload job id:</strong> {upload.id}</li>
        <li><strong>trial id:</strong> {upload.trial_id}</li>
        <li><strong>type:</strong> {upload.upload_type}</li>
        <li><strong>uploader:</strong> {upload.uploader_email}</li>
    </ul>
    """

    email = {
        "to_emails": CIDC_MAILING_LIST,
        "subject": subject,
        "html_content": html_content,
    }

    return email


@sendable
def intake_metadata(user, trial_id: str, assay_type: str, description: str, xlsx_gcp_url: str) -> dict:
    """
    Send an email containing a metadata xlsx file and description of that file to the
    CIDC Admin mailing list.
    """
    subject = f"[METADATA SUBMISSION]({ENV}) {user.email} submitted {trial_id}/{assay_type}"
    html_content = f"""
    <p><strong>user:</strong> {user.first_n} {user.last_n} ({user.email})</p>
    <p><strong>contact email:</strong> {user.contact_email}</p>
    <p><strong>protocol identifier:</strong> {html.escape(trial_id)}</p>
    <p><strong>assay type:</strong> {html.escape(assay_type)}</p>
    <p><strong>metadata file:</strong> <a href={xlsx_gcp_url}>{xlsx_gcp_url}</a></p>
    <p><strong>description:</strong> {html.escape(description)}</p>
    """

    email = {
        "to_emails": CIDC_MAILING_LIST,
        "subject": subject,
        "html_content": html_content,
    }

    return email


def notify_manifest_errors(subject_message: str, errors: List[str], send_email=True) -> dict:
    """Alert the CIDC administrators of errors in an attempted upload."""
    subject = f"[UPLOAD FAILURE]({ENV}) {subject_message}"
    html_content = f"<ul>{''.join(f'<li>{error}</li>' for error in errors)}</ul>"
    return notify_mailing_list(subject, html_content, send_email=send_email)


@sendable
def notify_mailing_list(subject: str, html_content: str) -> dict:
    """Generic notification to the CIDC administrators based on info passed."""
    email = {
        "to_emails": CIDC_MAILING_LIST,
        "subject": subject,
        "html_content": html_content,
    }
    return email
