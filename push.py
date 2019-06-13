import asyncio
import base64
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import http_ece
from py_vapid import Vapid02 as Vapid
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec

"""
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/e_VeBBSIT4U:APA91bFPAqKfpgNvJL53b0ztMawQZyNSj9Vl9qU9VQ37h2Y9kxQOSKFLYrYvmvTMQSVuqnaxgaZMQDQq_3xrY3HRQ_esfJEk1vAB6yPeKY9gzkBFN4BjyntJluci6-Uj57Bt7rQ0iZf4",
  "expirationTime": null,
  "keys": {
    "p256dh": "BB9VI8Aud-V2zXwzQzqRTQEGBipFFCr9Y0IRTTY7aRC6dJXowEZoCHS_xMTl_dc0cSmvl6_c9oWssQNrdzoj87o",
    "auth": "WPIxwcp38j79qh_mbp_IAg"
  }
},
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/e_VeBBSIT4U:APA91bFPAqKfpgNvJL53b0ztMawQZyNSj9Vl9qU9VQ37h2Y9kxQOSKFLYrYvmvTMQSVuqnaxgaZMQDQq_3xrY3HRQ_esfJEk1vAB6yPeKY9gzkBFN4BjyntJluci6-Uj57Bt7rQ0iZf4",
  "expirationTime": null,
  "keys": {
    "p256dh": "BB9VI8Aud-V2zXwzQzqRTQEGBipFFCr9Y0IRTTY7aRC6dJXowEZoCHS_xMTl_dc0cSmvl6_c9oWssQNrdzoj87o",
    "auth": "WPIxwcp38j79qh_mbp_IAg"
  }
},
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/f9phu1upti8:APA91bFW9w4AOrsr34ms2YQhhtn1jLGGqEB5hED8x0xEcx0w9mn0iXJdQNeV2NtNr_ACrjf0K8dtMz3wlQjHqgAjtK_8eGV9zT9sIO-tBnC1YNkSo8BHqhHImHetFshJQA_NmeZYPRgE", 
  "expirationTime": null, 
  "keys": { 
    "p256dh": "BOc2CGQyH0gzVW8gEaVV6H2gGCrBzhQaIBntRcXOCL7zhRgBc9QUygy0ZXluPeqznyV06tnnq1NJD54_qGSO54s", 
    "auth": "YHJsztzGoGNCOydlPKw6BA" 
  }
}
"""
subscriptions = """
[
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/e_VeBBSIT4U:APA91bFPAqKfpgNvJL53b0ztMawQZyNSj9Vl9qU9VQ37h2Y9kxQOSKFLYrYvmvTMQSVuqnaxgaZMQDQq_3xrY3HRQ_esfJEk1vAB6yPeKY9gzkBFN4BjyntJluci6-Uj57Bt7rQ0iZf4",
  "expirationTime": null,
  "keys": {
    "p256dh": "BB9VI8Aud-V2zXwzQzqRTQEGBipFFCr9Y0IRTTY7aRC6dJXowEZoCHS_xMTl_dc0cSmvl6_c9oWssQNrdzoj87o",
    "auth": "WPIxwcp38j79qh_mbp_IAg"
  }
},
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/f9phu1upti8:APA91bFW9w4AOrsr34ms2YQhhtn1jLGGqEB5hED8x0xEcx0w9mn0iXJdQNeV2NtNr_ACrjf0K8dtMz3wlQjHqgAjtK_8eGV9zT9sIO-tBnC1YNkSo8BHqhHImHetFshJQA_NmeZYPRgE",
  "expirationTime": null,
  "keys": {
    "p256dh": "BOc2CGQyH0gzVW8gEaVV6H2gGCrBzhQaIBntRcXOCL7zhRgBc9QUygy0ZXluPeqznyV06tnnq1NJD54_qGSO54s",
    "auth": "YHJsztzGoGNCOydlPKw6BA"
  }
},
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/fZ-1EpsdyKU:APA91bELz1mAx5hPvMwyr5yEmAp1uk2jg-pywauVjgbMMYS1esJEwUITeIqX7Lu9HZ4eb7AnmA6FmSYuJrzcO5ZFO2pRy80AAAadIeg9Wu3WLNcgWtS5v2EnEHYpdrFyCPJFhNzicDz2",
  "expirationTime": null,
  "keys": {
    "p256dh": "BJpYv7NU1pjT3T-le_0Zv57LW9cAHRshK3NaMg6Kl412ngTcybNMQw9jvFHEpqq8Sc2oxN382vkSfZiV2ul_CLQ",
    "auth": "9z4xquuNpVxHOdBnSGkvSw"
  }
}
]
"""

subscriptions = json.loads(subscriptions)
vapid_private_key = Path('private_key.txt').read_text()
encoding = 'aes128gcm'


def auth_headers(subscription_info):
    url = urlparse(subscription_info['endpoint'])
    aud = "{}://{}".format(url.scheme, url.netloc)
    vapid_claims = {
        'aud': aud,
        'sub': 'mailto:samcolvin@gmail.com',
        'ext': int(time.time()) + 12 * 3600,
    }
    return Vapid.from_string(private_key=vapid_private_key).sign(vapid_claims)


def prepare_key(data: str) -> bytes:
    """
    Add base64 padding to the end of a string, if required
    """
    data = data.encode() + b'===='[:len(data) % 4]
    return base64.urlsafe_b64decode(data)


async def post(data: str):
    # The server key is an ephemeral ECDH key used only for this transaction
    async with aiohttp.ClientSession() as session:
        for subscription_info in subscriptions:
            server_key = ec.generate_private_key(ec.SECP256R1, default_backend())
            body = http_ece.encrypt(
                data.encode(),
                private_key=server_key,
                dh=prepare_key(subscription_info['keys']['p256dh']),
                auth_secret=prepare_key(subscription_info['keys']['auth']),
                version=encoding,
            )
            headers = {
                'ttl': '60',
                'content-encoding': encoding,
                'accept': 'text/plain',
                **auth_headers(subscription_info)
            }
            async with session.post(subscription_info['endpoint'], data=body, headers=headers) as r:
                text = await r.text()
                debug(r.status, text, dict(r.headers))
                assert r.status in {201, 410}, r.status

msg = 'this is a test message'
if len(sys.argv) > 1:
    msg = sys.argv[1]
asyncio.run(post(msg))
