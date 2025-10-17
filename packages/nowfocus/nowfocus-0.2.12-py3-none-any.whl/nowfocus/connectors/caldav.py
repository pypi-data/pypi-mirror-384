# pip install caldav
# See https://github.com/python-caldav/
# And https://github.com/python-caldav/caldav/blob/master/examples/basic_usage_examples.py
import caldav
import concurrent.futures
import conf
import utils
import datetime
import uuid

def add_new_task(user_conf,list,task_label):
    uidNew = str(uuid.uuid1())

    with caldav.DAVClient(url=user_conf['url'], username=user_conf['username'], password=user_conf['password']) as client:

        calendar = client.calendar(url=list['id'])
        result = calendar.add_todo(
            summary=task_label,
            # due="Some Date",
            # categories="Some Category",
            id=uidNew
        )
        print('add_task result',result)

        t = {
            'id':uidNew,
            'label':task_label,
            'parent_id':list['id'],
            'parent_label':list['label'],
            'todolist':user_conf['id'],
            'data':{}
        }

        return t
        
def mark_task_done(task):

    print("Mark "+task['label']+" done" )
    user_conf = conf.user['todolists'][task['todolist']]

    with caldav.DAVClient(url=user_conf['url'], username=user_conf['username'], password=user_conf['password']) as client:

        calendar = client.calendar(url=task['parent_id'])
        print("got calendar")
        print(calendar)

        taskFetched = calendar.search(
            todo=True,
            uid=taskToModify["UID"],
            )


        # Extremely slow, not sure if it's the client or the server implementation 
        for t in calendar.todos():
            if str(t.icalendar_component["uid"]) == task['id']:
                print("found the task!")
                print(t.icalendar_component)
                print("t in mark done calendar")
                t.complete()
                return True

        # How it's supposed to work but doesn't 
        # # event = caldav.Event(client=client, parent=calendar, url=task['id'])
        # todo = caldav.Todo(client=client, parent=calendar, url=task['id'])

        # print("got 'todo' ?")
        # print(todo)
        # todo.load()
        # print('\nSummery after load()')
        # print(todo.icalendar_component["summary"])

        # result = todo.complete()

# def load_calendar_todo_data(i):
    
def load_calendar_todo_index(i):
    # print('load_calendar_todos',i)
    
    c = i['c']
    user_conf = i['user_conf']

    
    start_time = utils.now()

    print(c.name, ': start caldav todos in thread')
    # caldav_tasks = c.todos()

    caldav_tasks = c.search(
    #     # start=datetime.today(),
    #     # end=datetime(date.today().year + 5, 1, 1),
    #     # event=True,
        todo=True,
        expand=False,
    )
    todo_function_time = utils.now()

    print(c.name, ': caldav calendar.search took',utils.now() - start_time )

    tasks = {}
    for t in caldav_tasks:
        tasks[str(t.icalendar_component["uid"])] = {
                'id':str(t.icalendar_component["uid"]),
                'label':str(t.icalendar_component["summary"]),
                'parent_label':str(c.name),
                'parent_id':str(c.url),
                'todolist':user_conf['id'],
                'data':{}
            }
        # print('speed test ')
        # print(t.data)t
        # print(t.icalendar_component)
        # print("loaded: "+ str(t.icalendar_component["summary"]))
    total_time = utils.now() - start_time
    print(c.name, ':',len(caldav_tasks), ' tasks, total time ',total_time )
    return tasks


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

    with caldav.DAVClient(url=user_conf['url'], username=user_conf['username'], password=user_conf['password']) as client:

        principal = client.principal()
        calendars = principal.calendars()
            
        print("loading %i CalDav lists:" % len(calendars))
        params = []
        
        # For faster testing
        # calendars = [calendars[1]]
        # calendars = [calendars[1],calendars[2]] 
        for c in calendars:
            print(c.name +" url:"+str(c.url))
        
            lists[c.url] = {
                'id':str(c.url),
                'label':str(c.name),
                'parent_id':user_conf['id'],
                'parent_label':user_conf['label'],
                'todolist':user_conf['id'],
                'status':1,
                'data':{
                    'accepts_tasks':True,
                }
            }

            params.append({'c':c,'user_conf': user_conf})

        # print('params',params)


        with concurrent.futures.ThreadPoolExecutor() as executor:
           result = executor.map(load_calendar_todo_index, params)

        for list_tasks in result:
            tasks.update(list_tasks)

    return {'tasks':tasks,'lists':lists}

    