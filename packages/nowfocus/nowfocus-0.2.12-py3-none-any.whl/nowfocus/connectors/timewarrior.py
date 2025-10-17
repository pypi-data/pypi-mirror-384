import os
import time
from datetime import datetime, timezone, timedelta

import conf

import utils

from timew import TimeWarrior

timew = TimeWarrior()

# timew time tracking 
def save_session(session,user_conf):

    global timew

    out = {}

    out['start_time'] = session['start_time'].astimezone()    

    out['tags'] = [session['task']['parent_label'],session['label']]
    
    out['tags'] = list(filter(None, out['tags']))
    
    out['end_time'] = out['start_time'] + timedelta(seconds=session['duration'])    
    
    utils.dbg(out,s="timewarrior",l=2)
    
    timew.track(start_time=out['start_time'], end_time=out['end_time'], tags=out['tags'])
 
