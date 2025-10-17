import json
import time
from datetime import datetime, timezone
from urllib.request import urlopen
import requests
from dateutil import tz

import conf

from utils import time_to_sec, sec_to_time, now, time_difference, open_external, get_lists_for_item,  lists_cache


def save_session(session,user_conf):

    # TODO: fix this (seems to create "/ FINAL_LIST ")
    tree = " / ".join(get_lists_for_item(session['task'])['labels'])

    payload = {
        "timestamp":session['start_time'].replace(tzinfo=tz.tzlocal()).astimezone(timezone.utc).isoformat(), 
        "duration":session['duration'],
        "data":{
            "running":False,
            "label":tree +" / "+ session['label'],
            "id":str(session['task']['id']),
            "project":session['task']['parent_label'],
        }
    }

    print(payload)

    r = requests.post(user_conf['url']+'api/0/buckets/aw-stopwatch/events', json=payload)