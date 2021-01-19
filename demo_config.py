
import os

#################################

demos = {
    "login": {
        "friendly_name": "login",
    },
    "password_reset": {
        "friendly_name": "password reset",
    },
    # "review_devices": {
    #     "friendly_name": "review devices",
    # },
    "review_suspicious_login": {
        "friendly_name": "review suspicious login",
        "wsd": "https://www.websequencediagrams.com/files/render?link=5X8mGAOurMFPpdmy3GnNhY12wXc55R903wDDF3G31UJirHP7j2OdckNb3M35WBPK"
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
