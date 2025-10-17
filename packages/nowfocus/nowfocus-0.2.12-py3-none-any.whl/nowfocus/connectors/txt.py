import os
import conf
import utils 

def add_new_task(user_conf,list,task_label):
    utils.dbg('Add_task list',list, 'task_label',task_label,s='txt',l=2)
    file_uri = user_conf['file']


    with open(file_uri, 'r') as file:
        # read a list of lines into data
        data = file.readlines()

        # New Version

        line_no = get_line_no(list,data) + 1
        new_line = list['data']['indent']+task_label+"\n"

        # # Old version without recorded indent

        # if list['id'] == user_conf['id']:
        #     # Top level insert
        #     new_line = task_label+"\n"
        #     line_no = len(data) + 1
        # else:
        #     Sub list insert
        #     TODO: Add it at the end of the list rather than the start ...
        #     Yup. rjust(indent + len)


        #     indent = len(list['data']['original_line']) - len(list['data']['original_line'].lstrip()) + 4 #BUG: check indent of next line instead of arbitrarily using 4 spaces
            
        #     new_line = task_label+"\n"
        #     # I'm sure there's a better way to add a bunch of spaces to to a string
        #     while indent > 0:
        #         new_line = " " + new_line
        #         indent = indent - 1

        #     line_no = get_line_no(list,data) + 1

        data.insert(line_no,new_line)
        
        # write everything back
        with open(file_uri, 'w') as file:
            file.writelines( data )

        t = {
            # 'id':,
            'label':task_label,
            'parent_id':list['id'],
            'parent_label':list['label'],
            'todolist':user_conf['id'],
            'data':{
                'line_no':line_no,
                'original_line':new_line
            }
        }
        t['id'] = task_id(t)

        if task_label[0].isdigit():
            t['priority'] = float(task_label.split()[0])
        print('new task',t)
        # now the line_no for everything after this will be screwed up...

    return t
            


def get_line_no(i,lines):
    if lines[i['data']['line_no']] == i['data']['original_line']:
        return i['data']['line_no']
    else:

        line_no = 0 #TODO: Improve, (better foreach with key)
        in_list = False
        
        for line in lines:

            # TODO: Find the list 
            if line == i['data']['original_line']:
                return line_no

            line_no = line_no + 1

    throw("Line not found error Ha!")

def task_id(task):
    ''' The task parameter must have at least "label", "todolist" and "parent_id" '''
    # file:sublist/sublist/sublist:label

    id = conf.user['todolists'][task['todolist']]['file']+":"+"/".join(utils.get_lists_for_item(task)['labels'])+":"+task['label']
    print('generated task id',id )
    return id


def mark_task_done(task):
    
    file_uri = conf.user['todolists'][task['todolist']]['file']
    line_no = task['data']['line_no']

    with open(file_uri, 'r') as file:
        # read a list of lines into data
        data = file.readlines()

        print(file_uri +' before mark done:\n')
        print(data)

        if data[line_no] == task['data']['original_line']:
            if data[line_no].strip().startswith('[ ]'):
                data[line_no] = data[line_no].replace('[ ]', '[x]')
            else:
                data[line_no] = data[line_no].replace(data[line_no].lstrip(), '[x] '+ data[line_no].lstrip() ) 

            # write everything back
            with open(file_uri, 'w') as file:
                file.writelines( data )
            return True

        else: 
            print("original line does not match current file line. perhaps it's been edited?")
            return False


def get_todos(user_conf):
    
    file_uri = user_conf['file']

    tasks = {}
    lists = {}
    lists[user_conf['id']] = {
                    'id':user_conf['id'],
                    'label':user_conf['label'],
                    'parent_id':'',
                    'parent_label':'',
                    'todolist':user_conf['id'],
                    'data':{
                        'line_no':0,
                        'original_line':'',
                        'accepts_tasks':True,
                        'indent':'',
                    }
                }

    current_list = []
    current_list_label = []
    current_indent = []
    current_indent.append(0)

    parent = ''
    prev_indent = 0
    prev_label = ''
    prev_id = ''

    # id syntax 
    # file:sublist/sublist/sublist:label

    #for testing
    # file_uri = "todo.txt"
    line_no = -1

    with open(file_uri,"r") as file:
        for line in file:

            line_no = line_no + 1

            # Skip blank lines 
            if line.strip() == "":
                continue
            
            label = line.strip()

            # Handle done tasks
            status = 1

            if label.startswith('[x]') or label.startswith('[X]'):
                label = label.removeprefix('[x]').removeprefix('[X]').strip()
                status = 0

            label = label.removeprefix('[ ]').removeprefix('[]').strip()
            #TODO: use markdown title syntax as list name in addition to indentation 

            indent = len(line) - len(line.lstrip())
            indent_str = line[0:indent]

            if indent > prev_indent:
                # prev item is a sub_list header, copy it to lists
                lists[prev_id] = tasks[prev_id]
                lists[prev_id]['data']['indent'] = indent_str
                # del tasks[prev_id]
                current_list.append(prev_id)
                current_list_label.append(prev_label)
                current_indent.append(indent)

                utils.dbg('Entered sublist: '+"/".join(current_list_label),s='txt',l=3)

            else: 
                if indent < prev_indent:
                
                    while indent < current_indent[-1]:
                        utils.dbg('Exit sublist: '+"/".join(current_list_label),s='txt',l=3)
                        if current_list:
                            del current_list[-1]
                            del current_list_label[-1]
                            del current_indent[-1]

                    
            utils.dbg(line.rstrip(),s='txt',l=3)
            
            task_id = file_uri+":"+"/".join(current_list_label)+":"+label

            if current_list:
                parent_id = current_list[-1]
                parent_label = current_list_label[-1]
            else:
                parent_id = user_conf['id']
                parent_label = user_conf['label']

            tasks[task_id] = {
                    'id':str(task_id),
                    'label':str(label),
                    'parent_id':str(parent_id),
                    'parent_label':str(parent_label),
                    'todolist':user_conf['id'],
                    'status': status,
                    'data':{
                        'line_no':line_no,
                        'original_line':line,
                        'accepts_tasks':True
                    }
                }

            # Get prioritized tasks (starting with a number)
            # if label[0].isdigit()
            if label.split()[0].isnumeric():
                tasks[task_id]['priority'] = float(label.split()[0])
                tasks[task_id]['label'] = label.removeprefix(label.split()[0]).strip()

            prev_indent = indent
            prev_label = label
            prev_id = task_id

    todos = {'lists':lists,'tasks':tasks}  
    utils.dbg('todos',todos,s='txt',l=3)
    return todos

# testing
# print(get_todos())



def launch(user_conf, item = None, category = None):
    ''' Open todolist '''

    # It would b very nice to open a the right line number but xdg-open doesn't support that...
    utils.open_external(user_conf['file'])