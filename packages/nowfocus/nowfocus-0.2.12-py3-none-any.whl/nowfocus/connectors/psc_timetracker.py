import requests
import json
from datetime import datetime, timezone, timedelta
import uuid

import conf
import utils

from utils import time_to_sec, sec_to_time, now, time_difference, open_external, get_lists_for_item, lists_cache


def item_is_from_psc_timetracker_todolist(i):
    if conf.user['todolists'][i['todolist']]['type'] == 'psc_timetracker':
        return True
    else:
        utils.dbg('Item is not from a psc_timetracker todolist',i,s="psc_timetracker",l=0)
        return False


def mark_task_done(task):
    utils.error_notice("Sorry, you can't mark this task as done","This feature doesn't seem to be working with PSC timetracker tasks right now. Sorry! You'll have to open timetracker and use the web interface.")
    user_conf = conf.user['todolists'][task['todolist']]
    
    utils.dbg(user_conf['label']+" " +task['label']+" mark_task_done",s="psc_timetracker")

    data = assemble_task_synch_data(task,{'status':'complete'})
    utils.dbg('NEW system data',data, s="psc_timetracker")

    # lists = lists_cache()
    # data = task['data']
    # list_ids = get_lists_for_item(task)['ids']
    # data['clients'][list_ids[1]]['projects'][list_ids[2]]['tasks'][task['id']]['status'] = 'complete'
    
    # utils.dbg('OLD system data',data, s="psc_timetracker")
    # utils.dbg(data, s="psc_timetracker")

    response = requests.post(user_conf['url']+"synch.php?action=synchToServer&key="+user_conf['key'],json=data)
    
    print(response.json())
    return response


def add_new_task(user_conf,parent_list,task_label):
    
    id = str(uuid.uuid4())

    t = {
        'id':id,
        'label':task_label,
        'parent_id':parent_list['id'],
        'parent_label':parent_list['label'],
        'todolist':user_conf['id'],
        'data':{

        }
    }

    # data = {
    #     'clients':{
    #         parent_list['parent_id']:{
    #             'id':parent_list['parent_id'],
    #             'name':parent_list['parent_label'],
    #             'projects':{
    #                 parent_list['id']:{
    #                     'id':parent_list['id'],
    #                     'name':parent_list['label'],
    #                     'tasks':{
    #                         id:{
    #                         'id':id,
    #                         'name':task_label
    #                         }
    #                     }
    #                 }
    #             }
    #         }
    #     }
    # }
    # utils.dbg("old system synchToServer data", data, s="psc_timetracker",l=1)
   
    data = assemble_task_synch_data(t)
    utils.dbg("new system synchToServer data", data, s="psc_timetracker",l=3)

    response = requests.post(user_conf['url']+"synch.php?action=synchToServer&key="+user_conf['key'],json=data)
    
    print(response.json())

    # TODO: check what success and fail messages are returned and check for those
    if response.status_code != 200:
        error_notice("Failed to add tasks","")
        dbg('psc timetracker add task error',response,l=0,s='psc_timetracker')
        return False

    print("Add task "+task_label+" to "+str(parent_list['id'])+" Response",t)

    return t


def assemble_task_synch_data(t, passed_task_data = None):
    ''' return a dict collected from 'project' level list with client, project, task, {t['id']: passed_task_data)'''

    p = utils.db_get_item_by_id(t['parent_id'],'lists')

    list_ids = get_lists_for_item(t)['ids']

    print("psc assemble_task_synch_data")
    
    o = p['data']['sync_obj']

    task_data = {'id':t['id'],'name':t['label']} 

    if type(passed_task_data) == dict:
        task_data = task_data | passed_task_data

    o['clients'][list_ids[1]]['projects'][list_ids[2]]['tasks'] = {t['id']: task_data } 

    return o


def save_session(session,user_conf):
    print('Save Session to PSC timtracker')
    # print(session)
    # print(user_conf)

    # Not a great test but probably sufficient
    if not item_is_from_psc_timetracker_todolist(session['task']):
        
        error_notice("TimeTracker Error","Can't log sessions to psc_timetracker unless the the task is from a timetracker list")
        # TODO: create new client/project/task object with reproducibly-hashed list names as ids?
        return False
    
    # print(session['task'])
    task = session['task']

    session_id = str(uuid.uuid4())

    end_time = session['start_time'] + timedelta(seconds=session['duration'])

    session = {
        session_id:{
            "id": session_id,
            "start_time": session['start_time'].strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": ""
        }
    }

    # old, Working, data attached to every task, version 
    # data = task['data']
    # list_ids = get_lists_for_item(task)['ids']
    # data['clients'][list_ids[1]]['projects'][list_ids[2]]['tasks'][task['id']]['sessions'] = session
    # print("old version synchToServer data",data)

    data = assemble_task_synch_data(task,{'sessions':session})
    # print("NEW version synchToServer data",data)

    # print('session')
    # print(session)
    # print('modified data')
    # print(data)

    response = requests.post(user_conf['url']+"synch.php?action=synchToServer&key="+user_conf['key'],json=data)
    
    print(response.json())
    if response.status_code == 200:
        return True
    else:
        return False

def get_todos(user_conf):

    tasks = {}
    lists = {
        user_conf['id']: {
            'id':user_conf['id'],
            'label':user_conf['label'],
            'parent_id':'',
            'parent_label':'',
            'todolist':user_conf['id'],
            'status': 1,
            'data':{
                'accepts_tasks':False
            }
        }
    }
    # TODO: detect and raise/hande connection error here 
    data = requests.get(user_conf['url']+"synch.php?action=synchFromServer&key="+user_conf['key']).json()
    
    for client_id in data['clients']:
        client = data['clients'][client_id]

        # This is implemented in the database but not the api
        # if client['status'] == 'completed':
        #     continue

        lists[client['id']] = {
            'id':client['id'],
            'label':client['name'],
            'parent_id':user_conf['id'],
            'parent_label':user_conf['label'],
            'todolist':user_conf['id'],
            'data':{
                'accepts_tasks':False
            }
        }

        print(client['name'])

        for p_id in client['projects']:

            p = client['projects'][p_id]
            # This is implemented in the database but not the api
            # if p['status'] == 'completed':
            #     continue
            
            if 'tasks' in p:

                lists[p['id']] = {
                    'id':p['id'],
                    'label':p['name'],
                    'parent_id':client['id'],
                    'parent_label':client['name'],
                    'todolist':user_conf['id'],
                    'data':{
                        'accepts_tasks':True,
                        'sync_obj':{
                            'clients':{ 
                                client['id']:{
                                    'id':client['id'],
                                    'name':client['name'],
                                    'projects':{
                                        p['id']:{
                                            'id':p['id'],
                                            'name':p['name'],
                                            
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                print('    '+p['name'])
            
                for t_id in p['tasks']:
                    t = p['tasks'][t_id] 
                    
                    if t['status'] == 'completed' or t['status'] == 'on hold':
                        # continue 
                        status = 0
                    else:
                        status = 1

                    if 'sessions' in t:
                        del t['sessions']

                    print('        '+t['name'])

                    tasks[t['id']] = {
                        'id':t['id'],
                        'label':t['name'],
                        'parent_id':p['id'],
                        'parent_label':p['name'],
                        'todolist':user_conf['id'],
                        'status':status,
                        # What has to be sent back to update the task or add sessions
                        'data':{
                            'clients':{
                                client['id']:{
                                    'id':client['id'],
                                    'name':client['name'],
                                    'projects':{
                                        p['id']:{
                                            'id':p['id'],
                                            'name':p['name'],
                                            'tasks':{
                                                t['id']:t
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                    if t['priority'].isnumeric():
                        tasks[t['id']]['priority'] = float(t['priority'])
                    
    todos = {'lists':lists,'tasks':tasks}
    return todos