
import os

#################################

demos = {
    "login": {
        "friendly_name": "login",
        "blurb": "Evaluate a login with the risk and filter endpoints.",
        "wsd": "https://www.websequencediagrams.com/files/render?link=Q9WYp8rNThVZhA1inf2FSLfjChYZTdHXyGB9zqvMNpsaAvKvJPARgo5LI5fM5K4D"
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
    "events": {
        "friendly_name": "events",
        "blurb": "Inspect your event schema and query events."
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
