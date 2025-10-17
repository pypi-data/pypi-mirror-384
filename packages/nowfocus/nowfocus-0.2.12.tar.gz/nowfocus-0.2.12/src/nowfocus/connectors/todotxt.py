import os
import datetime

import pytodotxt

import conf
import utils 

# lists and tasks are each a dict of dicts with following shape 
# tasks[task_id] = {
#     'id':task_id,
#     'label':label,
#     'parent_id':parent_id,
#     'parent_label':parent_label,
#     'status':1, #( 1 pending, 0 done, -1 deleted)
#     'priority':1 max, 5 min, 0 none,
#     'todolist':user_conf['id'],
#     'data':{
#         # Any additional data
#     }
# }


def task_id(user_conf, t):
    ''' The task parameter must have at least "label", "todolist" and "parent_id" '''
    id = user_conf['id']+">"+t.bare_description() # TODO: better id!

    # id = conf.user['todolists'][task['todolist']]['file']+":"+"/".join(utils.get_lists_for_item(task)['labels'])+":"+task['label']
    # print('generated task id',id )
    return id


def add_new_task(user_conf,list,task_label):
    ''' Adds the label to the provided list in the specified todo and returns a task dict'''
    todotxt = pytodotxt.TodoTxt(user_conf['file'])
    todotxt.parse()

    task = pytodotxt.Task(task_label +"+"+list['label'])

    todotxt.add(task)
    todotxt.save()
    # task.add_project

    t = {
            'id':task_label,
            'label':task_label,
            'parent_id':list['label'],
            'parent_label':list['label'],
            'status':1,
            # 'priority':1 max, 5 min, 0 none,
            'todolist':user_conf['id'],
            'data':{
            }
        }
    return t


def mark_task_done(task):
    '''Return True on success False on error'''
    
    todotxt = pytodotxt.TodoTxt(conf.user['todolists'][task['todolist']]['file'])

    for t in todotxt.parse():
        if t.bare_description() == task['label']:
            t.completion_date = datetime.date.today()
            t.is_completed = True
            break

    todotxt.save()


def get_todos(user_conf):
    '''Return {'lists':lists,'tasks':tasks} '''

    tasks = {}
    lists = {}

    lists[user_conf['id']] = {
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


    todotxt = pytodotxt.TodoTxt(user_conf['file'])
    for t in todotxt.parse():

        id = task_id(user_conf,t)

        tasks[id] = {
            'id':id,
            'label':t.bare_description(),
            'parent_id':user_conf['id'],
            'parent_label':user_conf['label'],
            'status':1,
            # 'priority':1 max, 5 min, 0 none,
            'todolist':user_conf['id'],
            'data':t.attributes #TODO: add other things like date etc
        }

        if t.is_completed:
            tasks[id]['status'] = 0


        if t.projects:
            l = t.projects[0]
            tasks[id]['parent_id'] = l
            if l not in lists:
                lists[l] = {
                    'id':l,
                    'label':l,
                    'parent_id':user_conf['id'],
                    'parent_label':user_conf['label'],
                    'status':1, 
                    'priority':0,
                    'todolist':user_conf['id'],
                    'data':{
                        'accepts_tasks':True
                    }
                }


    todos =  {'lists':lists,'tasks':tasks}

    return todos

# testing
# print(get_todos())


def launch(user_conf, item = None, category = None):
    ''' Open todolist '''

    # It would b very nice to open a the right line number but xdg-open doesn't support that...
    utils.open_external(user_conf['file'])