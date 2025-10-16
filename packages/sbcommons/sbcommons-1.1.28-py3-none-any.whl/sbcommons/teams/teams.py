from sbcommons.messaging import webhooks


def send_message(webhook_url: str, title: str, msg: str) -> bool:
    data = {
        "Text": msg,
        "TextFormat": "markdown",
        "Title": title
    }

    webhooks.post_to_webhook(service='teams', webhook_url=webhook_url, json=data)
