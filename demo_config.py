
demos = {

    "login_failed_password_invalid": {
        "api_endpoint": "track",
        "castle_name": "$login.failed",
        "friendly_name": "login failed (password invalid)",
        "first_step_action": "log in",
        "first_step_desc": "First, let's log in. On the back end, we're going to assume that this is a bad password, so the password does not matter."
    },
    "login_failed_username_invalid": {
        "api_endpoint": "track",
        "castle_name": "$login.failed",
        "friendly_name": "login failed (username invalid)",
        "username": "invalid.username@mailinator.com",
        "first_step_action": "log in",
        "first_step_desc": "First, let's log in. On the back end, we're going to assume that this is an invalid username. You'll see that we send a user_id=null kvp to Castle, to indicate that this request/device included an invalid username."
   },   
    "login_succeeded": {
        "api_endpoint": "authenticate",
        "castle_name": "$login.succeeded",
        "friendly_name": "login succeeded",
        "first_step_action": "log in",
        "first_step_desc": "First, let's log in. On the back end, we're going to assume that the username + password combo is valid (regardless of the password you put in). Castle will respond with a recommendation as to whether to allow, deny, or challenge the authentication."
    },
    "password_reset_succeeded": {
        "api_endpoint": "track",
        "castle_name": "$password_reset.succeeded",
        "friendly_name": "password reset succeeded",
        "new_password": True,
        "first_step_action": "reset password",
        "first_step_desc": "We're going to assume that the user has arrived on this screen after satisfying whatever challenges you have in place to reset their password. On the back end, Castle will track the successful password reset event."
    },
    "review_suspicious_activity": {
        "api_endpoint": "authenticate",
        "castle_name": "$login.succeeded",
        "friendly_name": "review suspicious activity",
        "first_step_action": "get a device token",
        "first_step_desc": "First, let's do a successful login to get a device token:"
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
