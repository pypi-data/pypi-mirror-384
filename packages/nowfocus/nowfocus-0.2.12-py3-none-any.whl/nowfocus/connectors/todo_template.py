import os
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

def add_new_task(user_conf,list,task_label):
    ''' Adds the label to the provided list in the specified todo and returns a task dict'''

    return t
            
def mark_task_done(task):
    '''Return True on success False on error'''

def get_todos(user_conf):
    '''Return {'lists':lists,'tasks':tasks} '''
    
    # todo_conf is conf.user['todolists'][user_conf['id']]
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


    todos =  {'lists':lists,'tasks':tasks}
    return todos


def launch(user_conf, item = None, category = None):
    ''' Open todolist '''

    # utils.open_external(user_conf['file']) # Simple file open 
    
    url = user_conf['url']

    if item and category:
        if category == 'list':
            url += ''
        elif category == 'task':
            url += ''

    utils.open_external(url)

# testing
# print(get_todos())