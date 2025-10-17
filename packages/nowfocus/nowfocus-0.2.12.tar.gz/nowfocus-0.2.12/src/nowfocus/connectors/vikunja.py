import json
import time
from datetime import datetime, timezone

from urllib.request import urlopen

import requests

import conf
import utils

# UPDATE sessions SET task_id = "Vikunja_t" || task_id WHERE todolist = 'Vikunja';
# UPDATE sessions SET parent_id = "Vikunja_l" || parent_id WHERE todolist = 'Vikunja';

def vikunja_item_id(id, item_type, user_conf):
    return user_conf['id'] +'_'+ item_type[0] + str(id)

def add_new_task(user_conf,parent_list,task_label):
    head = {'Authorization': 'Bearer {}'.format(user_conf['token'])}
    headers = {'content-type': 'application/json'}
    data = {'title': task_label}

    utils.dbg('add_new_task() parent_list',parent_list, l=0)

    response = requests.put(user_conf['url']+"api/v1/projects/"+str(parent_list['data']['id'])+"/tasks",json=data, headers=head)

    task_data = response.json()

    print("Add task "+task_label+" to "+str(parent_list['id'])+" Response",task_data)

    id = vikunja_item_id(task_data['id'], 'task', user_conf)

    task = {
            'id':id,
            'label':task_data['title'],
            'parent_id':parent_list['id'],
            'parent_label':parent_list['label'],
            'todolist':user_conf['id'],
            'data':task_data
        }

    return task


def mark_task_done(task):
    user_conf = conf.user['todolists'][task['todolist']]
   
    head = {'Authorization': 'Bearer {}'.format(user_conf['token'])}
    headers = {'content-type': 'application/json'}
    data = {'done': True,}
    response = requests.post(user_conf['url']+"api/v1/tasks/"+str(task['data']['id']),json=data, headers=head)

    # print(response.json()['done'])
    return response.json()['done']
    
    # print('\nresponse.url')
    # print(response.url)

    # print('\nresponse.status_code')
    # print(response.status_code)

    # print('\nrequest.body')
    # print(response.request.body)

    # print('\nresponse')
    # print(response.json())


# Token auth for this doesn't seem to work propery, boo, get it from the user  

# def get_vikunja_user_data(user_conf,user_data_cache = {}):
#     ''' get (and cache) vikunja user data from API 
#     '''
#     # See https://try.vikunja.io/api/v1/docs#tag/user/paths/~1user/get

#     if not user_data_cache:
#         # try:
#         headers = {"Authorization": "Bearer "+user_conf['token']}
#         print("get_vikunja_user_data headers")
#         print(headers)
#         user_data_cache = requests.get(user_conf['url']+"api/v1/user", headers=headers).json()
#         # except Exception as e: 
#             # error_notice("Vikunja Error",e)
#     print("get_vikunja_user_data")
#     print(user_data_cache)
#     return user_data_cache

    
def get_todos(user_conf):

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
                'accepts_tasks':False
            }
        }
    

    priorities = {'DO NOW':1,'Urgent':2,'high':3}
    headers = {"Authorization": "Bearer "+user_conf['token']}
    projects_lists = requests.get(user_conf['url']+"api/v1/projects", headers=headers).json()

    # print("vikunja projects")
    # print(json.dumps(projects_lists, indent=4))

    # for i in projects_list:
    for i, itemIter in enumerate(projects_lists):

        p = projects_lists[i]

        #  Omit filter lists 
        if p['id'] < 0:
            continue 


        # print(p)
        # p['id'] = str(p['id'])
        id = vikunja_item_id(p['id'] , 'list', user_conf)

        # views are bulky and useless so remove them
        del p['views']
        
        lists[id] = {
            'id':id,
            'label':p['title'],
            'parent_id':user_conf['id'],
            'parent_label':user_conf['label'],
            'todolist':user_conf['id'],
            'data':p
        }
        
        lists[id]['data']['accepts_tasks'] = True

        if p['is_archived']: 
            lists[id]['status'] = -1
        else:
            lists[id]['status'] = 1

        if p['parent_project_id'] != 0: 
            parent_id = vikunja_item_id(p['parent_project_id'], 'list', user_conf)
            lists[id]['parent_id'] = parent_id


            if parent_id in lists:
                lists[id]['parent_label'] = lists[parent_id]['label']


        # NOTE: Originally tasks where queried per list, however this no longer works well because it requires a 'view' id, which comes wih various un-predictable baked-in filters (like done=true). Using the tasks/all api endpoint avoids this but quickly hits the default maxitemsperpage limit (which could, less obviously, show up in the per list method). 

        # else: print('parent_project_id', p['parent_project_id'], 'not in projects_lists')

        # view_id = p['views'][0]['id']
        # utils.dbg({'view_id':view_id},'vikunja')
        

        # Including 'done' tasks (Doesn't seem o includ them actually)'
        # projects_tasks = requests.get(user_conf['url']+"api/v1/projects/"+str(p['id'])+"/views/"+str(view_id)+"/tasks?sort_by[]=position&order_by[]=asc&equalspage=1", headers=headers).json()
        
        # Filtering out done tasks, Works
        # projects_tasks = requests.get(user_conf['url']+"api/v1/projects/"+str(p['id'])+"/views/"+str(view_id)+"/tasks?sort_by[]=position&order_by[]=asc&filter_by[]=done&filter_value[]=false&filter_comparator[]=equals&filter_comparator[]=equalspage=1", headers=headers).json()
        
        # projects_tasks = requests.get(user_conf['url']+"api/v1/projects/"+str(p['id'])+"/tasks", headers=headers).json()

        # print("vikunja projects_tasks")
        # print(json.dumps(projects_tasks, indent=4))
        # utils.pretty_print(projects_tasks)

        # for i, itemIter in enumerate(projects_tasks):

        #     t = projects_tasks[i]
        #     t['id'] = str(t['id'])

        #     tasks[t['id']] = {
        #         'id':t['id'],
        #         'label':t['title'],
        #         'parent_id':p['id'],
        #         'parent_label':p['title'],
        #         'todolist':user_conf['id'],
        #         'data':t
        #     }

        #     if t['done'] == True:
        #         tasks[t['id']]['status'] = False


        #     # Show favorites in main menu 
        #     if t['is_favorite'] == True:
        #         tasks[t['id']]['priority'] = 1
        #     elif t['priority'] in priorities:
        #         print("Priority task", t['title'])
        #         tasks[t['id']]['priority'] = priorities[t['priority']]
        #         print(tasks[t['id']])

    # beware per_page config ( generally in /opt/vikunja/config.yml) maxitemsperpage defaults to 20 so this really won't work on a default setup 
    #   maxitemsperpage: 5000
    # ?per_page=10000



    response = requests.get(user_conf['url']+"api/v1/tasks/all", headers=headers)
    all_tasks = response.json()

    # print("response.headers")
    # print(response.headers)
    if int(response.headers['X-Pagination-Total-Pages']) > 1:

        # TODO: instead of complaining, iterate through pages 
        utils.error_notice("Vikunja Task Loading Error "," Your vikunja Max items per page setting seems to be truncating your task list! Please increase 'maxitemsperpage' in your vikunja config yml file.")

    # print(json.dumps(all_tasks, indent=4))
    utils.dbg("Got ",len(all_tasks),"Vikunja tasks", s='vikunja', l=2 )

    utils.dbg("Got ",len(all_tasks),"Vikunja tasks", s='vikunja', l=2 )

    for i, itemIter in enumerate(all_tasks):

        t = all_tasks[i]
        id = vikunja_item_id(t['id'], 'task', user_conf)
        list_id = vikunja_item_id(t['project_id'], 'list', user_conf)

        # utils.dbg(t, s='vikunja', l=3)

        # Limit to asks assigned, created by, or favorated by user
        if user_conf["username"]:
            if t['is_favorite'] != True:

                if user_conf['username'] != t['created_by']['username']:

                    if not t['assignees'] or not any(assigned['username'] == user_conf['username'] for assigned in t['assignees']):
                       
                        utils.dbg("skipping "+str(t['title'])+" because it's not assigned to, created by, or a fave of the user",'created_by', t['created_by']['username'],'assignees',t['assignees'], s='vikunja', l=3)
                        continue
        else:
            utils.dbg('no username in vikunja user conf, can\'t limit to relevant tasks', s='vikunja', l=3)


        tasks[id] = {
            'id':id,
            'label':t['title'],
            'parent_id':list_id,
            'parent_label':'',
            'todolist':user_conf['id'],
            'status':1,
            'data':t
        }

        try:
            tasks[id]['parent_label'] = lists[list_id]['label']

            # If lists is inactive make task inactive (This is never the case AFAIK)
            if not lists[list_id]['status']:
                tasks[id]['status'] = 0            

            # If lists is archived make task deleted 
            if lists[list_id]['status'] == -1:
                tasks[id]['status'] = -1

        except Exception as e:
            print("No list found for", t['title']," list_id",list_id)
            # raise e

        if t['done'] == True:
            tasks[id]['status'] = 0

        # Prioritize if "due_date" is soon or passed (and not: "0001-01-01T00:00:00Z")
        if 'due_date' in t and t['due_date'] != "0001-01-01T00:00:00Z":

            due_date = datetime.strptime(t['due_date'],'%Y-%m-%dT%H:%M:%SZ')
            # print(t['title'],"task has a due_date", str(t['due_date']) )
            # print('time_difference', utils.time_difference(due_date,datetime.now()))
            due_seconds = utils.time_difference(due_date,datetime.now())
            # due in next 48 hrs (2 * 24 * 60 * 60) = 172800
            # due today (24 * 60 * 60) = 86400
            if due_seconds > -86400:
                tasks[id]['priority'] = 2

        # prioritize favorites
        if t['is_favorite'] == True:
            tasks[id]['priority'] = 2
        elif t['priority'] in priorities:
            print("Priority task", t['title'])
            tasks[id]['priority'] = priorities[t['priority']]
            # print(tasks[id])

    todos = {'lists':lists,'tasks':tasks}
    return todos


def launch(user_conf, item = None, category = 'task'):
    ''' Open Vikunja '''
    utils.dbg("vikunja.py launch","user_conf", user_conf,"item",item,'category',category,l=3, s='vikunja')

    url = user_conf['url']

    if item:
        if category in ('list','lists'):
            url += 'projects/'+str(item['data']['id'])
        else:
            url += 'tasks/'+str(item['data']['id'])

    utils.open_external(url)