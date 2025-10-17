from typing import Tuple
import json
import logging
import requests

from fastdup.vl.common.settings import Settings

from typing import List, Dict, Optional

API_KEY = Settings.EMAIL_API_KEY


def compute_recipients(user_email, user_fullname, bcc_support=False) -> Optional[List[Dict[str, str]]]:
    recipients = [{
        'email': user_email,
        'name': user_fullname,
        'type': 'to'
    }]
    if bcc_support:
        recipients.append(
            {
                'email': 'support@visual-layer.com',
                'type': 'bcc'
            }
        )
    return recipients


def _post_email(url, headers, data) -> Tuple[int, str]:
    # to mock this function in tests use the following decorator:
    # @mock.patch('utils.email_notifier._post_email')
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code, response.text


def send_mailchimp_template(template_name: str, template_content: List[Dict[str, str]], subject: str,
                            recipients: List[Dict[str, str]]) -> tuple[int, str]:
    url = 'https://mandrillapp.com/api/1.0/messages/send-template'

    headers = {
        "Content-Type": "application/json",
    }

    data = {
        'key': API_KEY,
        'template_name': template_name,
        'template_content': template_content,
        'message': {
            'subject': subject,
            'from_email': 'no-reply@visual-layer.com',
            'from_name': 'Visual Layer',
            'to': recipients,
            'track_opens': 'TRUE',
            'track_clicks': 'TRUE'
        }
    }

    response_status_code, response_text = _post_email(url, headers, data)

    if response_status_code == 200:
        logging.info(f"Email successfully sent", data)
    else:
        logging.error(f"Failed to send email. Status code: {response_status_code}, response: {response_text}", data)

    return response_status_code, response_text
