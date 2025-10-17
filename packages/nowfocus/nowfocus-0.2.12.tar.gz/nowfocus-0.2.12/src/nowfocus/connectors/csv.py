import os
import time
from datetime import datetime, timezone

import csv

import conf

import utils


# csv time tracking 
def save_session(session,user_conf):
    # date,duration,project,task,start time

    session['start_time'] = session['start_time'].astimezone()

    row = [session['start_time'].date(),str(round(session['duration']) / 60) +" minutes",session['task']['parent_label'],session['label'],session['start_time'].strftime('%H:%M:%S')]
    # row = [session['start_time'].date(),(round(session['duration']) / 60),session['parent'],session['label'],session['start_time'].time()]
    # row = [session['start_time'].date(),(round(session['duration']) / 60),session['label'],session['start_time'].time()]


    with open(user_conf['file'],'a') as f:
        writer = csv.writer(f)
        writer.writerow(row)
