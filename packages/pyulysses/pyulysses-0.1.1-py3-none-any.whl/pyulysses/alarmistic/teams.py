import json
import os

import requests

from configs.env_loader import get_teams_config
from logger.logger_config import setup_logger

# -------- Setup Logger --------- #
logger = setup_logger()

# ------- Teams Config ---------- #
teams_config = get_teams_config()
teams_webhook_url = teams_config['teams_webhook_url']

# Webhook configurations
webhooks = {
    'teams': {
        'url': teams_webhook_url,
        'target': 'Teams',
        'message': 'Testing Alarmistic from py-galp-data-process',
    }
}


def send_message_to_webhook(
    webhook_url: str, target: str, message_text: str
) -> None:
    """
    Sends a formatted message to a given webhook (e.g., Slack or Teams) via JSON payload.
    """
    if not webhook_url:
        print(f'[!] Skipping {target}: Webhook URL not set.')
        return

    payload = {'text': message_text}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(
            webhook_url, headers=headers, data=json.dumps(payload)
        )
        response.raise_for_status()
        logger.info(f'Message successfully sent to {target}!')
    except requests.exceptions.RequestException as e:
        logger.info(f'Failed to send message to {target}: {e}')
