from sbcommons.messaging import webhooks


def send_message(webhook_url: str, title: str, msg: str) -> bool:
    data = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": msg
                }
            }
        ]
    }

    webhooks.post_to_webhook(service='slack', webhook_url=webhook_url, json=data)
