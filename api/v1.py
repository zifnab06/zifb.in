import json

from app import app, database
from util import random_string
from flask import request
from hashlib import sha1

import pendulum


@app.route("/api/v1/paste", methods=("POST",))
def paste():  # noqa: C901
    paste = None
    language = None
    user = None
    expiration = None
    domain = "https://zifb.in/"
    try:
        data = json.loads(request.data)
    except ValueError:
        return json.dumps({"error": "invalid json"}), 400

    # Get Paste
    if "paste" not in data:
        return json.dumps({"error": "paste not found"}), 400
    paste = data.get("paste")

    # Get Language
    if "language" in data:
        language = data.get("language")

    # Get API_KEY/User
    if "api_key" in data:
        user = database.ApiKey.objects(key=data.get("api_key")).first().user

    # Get Expiration
    if "expiration" in data:
        s = data.get("expiration")
        try:
            s = int(s)
        except ValueError:
            return json.dumps(
                {"error": "invalid expiration format, should be number of seconds"}
            )
        if s is None or s == 0:
            expiration = None
        else:
            expiration = pendulum.now("UTC").add(seconds=s)

    if not user and not expiration:
        expiration = pendulum.now("UTC").add(hours=1)

    # Get Domain
    if "domain" in data:
        domain = "https://{0}/".format(data.get("domain"))

    paste = database.Paste(
        name="testing",
        paste=paste,
        digest=sha1(paste.encode("utf-8")).hexdigest(),
        time=pendulum.now("utc"),
        expire=expiration,
        user=user,
        language=language,
    )
    paste.name = random_string()
    while database.Paste.objects(name=paste.name).first():
        paste.name = random_string()

    paste.save()
    return json.dumps(
        {
            "paste": "{0}{1}".format(domain, paste.name),
            "expires": pendulum.instance(paste.expire).to_datetime_string(),
        }
    )
