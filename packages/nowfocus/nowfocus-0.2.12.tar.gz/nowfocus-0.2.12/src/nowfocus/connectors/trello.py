import requests
import json

import conf
from utils import * 

# get an api ky by "Creating a power up"
# https://developer.atlassian.com/cloud/trello/guides/power-ups/managing-power-ups/#adding-a-new-custom-power-up

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

    # Get boards 
    # https://developer.atlassian.com/cloud/trello/rest/api-group-members/#api-members-id-boards-get 
    # auth.trello_user_id 
    
    # url = "https://api.trello.com/1/members/me/boards" # Works 
    url = "https://api.trello.com/1/members/me/boards?lists=open&fields=name,url,starred,subscribed,closed&list_fields=name,url,starred,subscribed,closed"

    headers = {
        "Accept": "application/json"
    }

    query = {
        'key': user_conf['APIKey'],
        'token': user_conf['token']
    }

    boards_request = requests.request(
        "GET",
        url,
        headers=headers,
        params=query
    )


    boards = boards_request.json()
    
    dbg('trello boards',boards,s='trello',l=2)

    # print("\n\n--- Boards --- \n")
    # print(json.dumps(json.loads(boards_request.text), sort_keys=True, indent=4, separators=(",", ": ")))

    for board in boards:
        
        # print("\n\n--- Board --- \n")
        # pretty_print(board)

        if board['closed']:
            continue

        lists[board['id']] = {
            'id':board['id'],
            'label':board['name'],
            'parent_id':user_conf['id'],
            'parent_label':user_conf['label'],
            'todolist':user_conf['id'],
            'data':{
                'url':board['url'],
                'accepts_tasks':False,
            }
        }

        # print("\n\n--- Board formatted as lists --- \n")
        # print(lists[board['id']])

        for bucket in board['lists']:
            
            # print("\n\n--- bucket --- \n")
            # pretty_print(bucket)

            if bucket['closed']:
                continue

            lists[bucket['id']] = {
                'id':bucket['id'],
                'label':bucket['name'],
                'parent_id':board['id'],
                'parent_label':board['name'],
                'todolist':user_conf['id'],
                'data':{
                    'url':board['url'],
                    'accepts_tasks':True,
                }
            }

            # print("\n\n--- Board formatted as lists --- \n")
            # print(lists[board['id']])

            # TODO: add bucket board_lists=all as list

            # url = "https://api.trello.com/1/boards/"+str(board['id'])+"/cards?cards=all&fields=name,url,idList,due,closed" // Does't seem to get 

        url = "https://api.trello.com/1/boards/"+str(board['id'])+"/cards?cards=all&fields=name,url,idList,due,closed,dueComplete,due,start"

        cards_request = requests.request(
            "GET",
            url,
            params=query
        )

        cards = cards_request.json()

        dbg('trello cards',cards,s='trello',l=2)
        
        for t in cards:

            tasks[t['id']] = {
                'id':t['id'],
                'label':t['name'],
                'parent_id':t['idList'],
                'parent_label':lists[t['idList']]['label'],
                'todolist':user_conf['id'],
                'status':1,
                'data':t
            }

            if t['closed'] or t['dueComplete']:
                tasks[t['id']]['status'] = 0

            # Prioritize tasks due today 
            if t['due']:

                due_date = datetime.strptime(t['due'],'%Y-%m-%dT%H:%M:%S.%fZ')
                # print(t['title'],"task has a due_date", str(t['due_date']) )
                due_seconds = time_difference(due_date,datetime.now())
                # due in next 48 hrs (2 * 24 * 60 * 60) = 172800
                # due today (24 * 60 * 60) = 86400
                if due_seconds > -86400:
                    tasks[t['id']]['priority'] = 2


    todos = {'lists':lists,'tasks':tasks}
    # dbg('trello todos',todos,s='trello',l=2)
    return todos


def add_new_task(user_conf,list,task_label):
    ''' Adds the label to the provided list in the specified todo and returns a task dict '''

    url = "https://api.trello.com/1/cards"

    headers = {
        "Accept": "application/json"
    }

    query = {
        'idList': list['id'],
        'name': task_label,
        'key': user_conf['APIKey'],
        'token': user_conf['token'],
    }

    response = requests.request(
        "POST",
        url,
        headers=headers,
        params=query
    )

    r = response.json()

    # print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
    

    t = {
        'label': task_label,
        'id':r['id'],
        'parent_id':list['id'],
        'parent_label':list['label'],
        'todolist':user_conf['id'],
        'status':1,
        'data':r
    }
    
    dbg('trello add card response',r,s='trello')
    dbg('Newly minted trello task',t,s='trello')

    return t


def mark_task_done(task):
    ''' Mark Trello card closed ''' 
    user_conf = conf.user['todolists'][task['todolist']]

    url = "https://api.trello.com/1/cards/"+task['id']

    headers = {
        "Accept": "application/json"
    }

    query = {
        'key': user_conf['APIKey'],
        'token': user_conf['token'],
        'closed':1
    }

    response = requests.request(
        "PUT",
        url,
        headers=headers,
        params=query
    )

    # print("response.text")
    # print(response.text)

    return response.text



def launch(user_conf, item = None, category = None):
    ''' Open Trello '''
    url = "https://www.trallo.com"

    if item and 'url' in item['data']:
       url = item['data']['url']

    open_external(url)