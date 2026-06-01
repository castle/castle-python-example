
import os

#################################

demos = {
    "login": {
        "friendly_name": "login (risk / filter)",
        "wsd": "https://www.websequencediagrams.com/files/render?link=Q9WYp8rNThVZhA1inf2FSLfjChYZTdHXyGB9zqvMNpsaAvKvJPARgo5LI5fM5K4D"
    },
    "password_reset": {
        "friendly_name": "password reset (log)"
    },
    "lists": {
        "friendly_name": "lists"
    },
    "privacy": {
        "friendly_name": "privacy"
    },
    "events": {
        "friendly_name": "events"
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
