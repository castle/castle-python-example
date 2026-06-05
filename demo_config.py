
import os

#################################

demos = {
    "signup": {
        "friendly_name": "sign up",
        "blurb": "Evaluate a registration ($registration) with the risk endpoint."
    },
    "login": {
        "friendly_name": "login",
        "blurb": "Evaluate a login with the risk and filter endpoints.",
        "wsd": "https://www.websequencediagrams.com/files/render?link=Q9WYp8rNThVZhA1inf2FSLfjChYZTdHXyGB9zqvMNpsaAvKvJPARgo5LI5fM5K4D"
    },
    "account": {
        "friendly_name": "account",
        "blurb": "Update your profile, send a custom event, and log out."
    },
    "password_reset": {
        "friendly_name": "password reset",
        "blurb": "Record a password-reset event with the non-blocking log endpoint."
    },
    "lists": {
        "friendly_name": "lists",
        "blurb": "Create and fetch lists with the Lists API."
    },
    "privacy": {
        "friendly_name": "privacy",
        "blurb": "Request or delete a user's data with the Privacy API."
    },
    "webhooks": {
        "friendly_name": "webhooks",
        "blurb": "Verify and inspect incoming Castle webhooks."
    }
}

#################################

demo_list = []

for k, v in demos.items():

    e = {}

    e["url"] = k

    for key, value in v.items():
        e[key] = value

    demo_list.append(e)

#################################

valid_urls = []

for k, v in demos.items():
    valid_urls.append(k)
