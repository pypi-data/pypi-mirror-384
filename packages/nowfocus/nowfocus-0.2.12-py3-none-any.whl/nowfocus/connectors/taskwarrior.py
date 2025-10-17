import os
import conf
import utils 
from taskw import TaskWarrior

# lists and tasks are each a dicts of dicts with following shape 
# tasks[task_id] = {
#     'id':task_id,
#     'label':label,
#     'parent_id':parent_id,
#     'parent_label':parent_label,
#     'todolist':user_conf['id'],
#     'data':{
#         # Any additional data
#     }
# }

def add_new_task(user_conf,list,task_label):
    ''' Adds the label to the provided list in the specified todo and returns a task dict'''
    w = TaskWarrior()
    twt = w.task_add(task_label, project=list['label'])

    # {'id': 2, 'description': 'TW add task W SCP', 'entry': '20241024T013615Z', 'modified': '20241024T013615Z', 'project': 'SCP', 'status': 'pending', 'uuid': '240f964e-e459-4f04-8a28-cbf61f44a82a', 'urgency': 1}

    t = {
        'id':twt['uuid'],
        'label':twt['description'],
        'parent_id':user_conf['id'],
        'parent_label':user_conf['label'],
        'todolist':user_conf['id'],
        'data':twt
    }

    if 'project' in twt:
        t['parent_id'] = twt['project']
        t['parent_label'] = twt['project']

    if 'priority' in twt:
        if twt['priority'] == 'H':
            t['priority'] = 1

        if twt['priority'] == 'M':
            t['priority'] = 3
    dbg('add_new_task result',t,s='TaskWarrior')
    return t
            

def mark_task_done(task):
    '''Return True on success False on error'''
    w = TaskWarrior()
    w.task_done(id=task['data']['id'])


def get_todos(user_conf):
    '''Return {'lists':lists,'tasks':tasks} '''
    
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
                'accepts_tasks':True
            }
        }
    }

    
    w = TaskWarrior()
    tw_tasks = w.load_tasks()

    # TODO: also add tasks from tw_tasks['completed'] with status 0

    for twt in tw_tasks['pending']:
        t = {
            'id':twt['uuid'],
            'label':twt['description'],
            'parent_id':user_conf['id'],
            'parent_label':user_conf['label'],
            'todolist':user_conf['id'],
            'data':twt
        }

        tasks[twt['uuid']] = t

        if 'project' in twt:

            t['parent_id'] = twt['project']
            t['parent_label'] = twt['project']

            if twt['project'] not in lists:
                lists[twt['project']] = {
                    'id':twt['project'],
                    'label':twt['project'],
                    'parent_id':user_conf['id'],
                    'parent_label':user_conf['label'],
                    'todolist':user_conf['id'],
                    'data':{
                        'accepts_tasks': True
                    }
                }

        if 'priority' in twt:
            if twt['priority'] == 'H':
                t['priority'] = 5

            if twt['priority'] == 'M':
                t['priority'] = 2


    todos =  {'lists':lists,'tasks':tasks}
    return todos

# testing
# print(get_todos())