import os
import subprocess, sys
import signal
import json
import time
from datetime import datetime, timezone, timedelta
import importlib
from urllib.request import urlopen
import requests
import threading
import copy
from playsound3 import playsound
import setproctitle
import psutil
import argparse 

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, Gio

gi.require_version('Notify', '0.7')
from gi.repository import Notify as notify

try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as appindicator
except Exception as e:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator 

from dbus_idle import IdleMonitor

# Set working dir to file location 
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# Add working dir to path
sys.path.append(os.path.dirname(__file__))

# from . import conf # this works in module context but not running as pile-of-files 
import conf # this works running as pile-of-files but not in module context without sys.path.append 

import utils
from utils import *

from settings import SettingsWindow
from task_window import TaskWindow
from new_task_dialog import NewTaskWDialog
from session_options import SessionOptionsDialog 

dbg(conf.user,l=3,s='user_settings')

setproctitle.setproctitle(conf.app_name)

print(conf.app_name +" running from " + os.path.dirname(os.path.realpath(__file__)))

class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="org.example.myapp", **kwargs)
        
        self.window = None

        self.is_running = False
        self.session = {
            "label":"Randomness",
            "extended_label": 'Randomness',
            "start_time":datetime.now(),
            "duration":0,
            'task':{},
            'notes':'',
        }

        self.menu_tasks = {}
        self.list_menus = {}

        self.indicator = appindicator.Indicator.new(conf.app_name, os.path.abspath('icon/icon-1.svg'), appindicator.IndicatorCategory.APPLICATION_STATUS)

        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

        self.menu = Gtk.Menu()
        # menu.set_reserve_toggle_size(False) # skip menu left padding,  doesn't work 

        utils.db_init()
        utils.db_update()


        # self.update_menu()
        self.async_refresh()

        # utils.db_cleanup()

        self.indicator.set_menu(self.menu)

        # main_tick_timer = GLib.timeout_add_seconds(conf.user['tick_interval'], self.tick)
        main_tick_timer = GLib.timeout_add_seconds(1, self.tick)

        try:
            db_session = db_query("SELECT value FROM system WHERE field = 'session'")

            if db_session:
                s = json.loads(db_session[0]['value'])
                s['start_time'] = datetime.strptime(s['start_time'],'%Y-%m-%d %H:%M:%S.%f')
                self.session = s
                self.is_running = True
                dbg("resuming session",s['label'],l=2, s='session')
        except Exception as e:
            dbg("Error resuming session",e,l=1)

        utils.start_todo_file_watchers()

        self.pipethread = threading.Thread(target=self.check_pipe)
        self.pipethread.daemon = True
        self.pipethread.start()

        # Testing
        # time.sleep(3)
        # self.open_session_options_dialog('test_param')

        # self.open_settings_window() #for testing
        # self.open_task_window() #for testing

        # time.sleep(2)
        # self.open_new_task_dialog() #for testing

        # time.sleep(2)
        # self.print_time_totals()

        # signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGUSR1, self.signal_handler)
        signal.signal(signal.SIGUSR2, self.signal_handler)

        Gtk.main()




    def print_time_totals(self = None, widget = None):

        # SELECT extended_label, (SUM(duration) / 60 ) FROM sessions GROUP BY extended_label
        # SELECT extended_label, (SUM(duration) / 60 ) FROM sessions GROUP BY parent_id

        timeframe = hours_search_timeframes(conf.user['hours_search_timeframe'])

        print("\n\n\n ####  SESSION TOTALS "+utils.sessions_timeframe_sql()+" ### \n\n\n")

        l = ''

        for t in db_query("SELECT DISTINCT id, parent_id, label, parent_label FROM tasks WHERE id IN(SELECT DISTINCT task_id FROM sessions WHERE "+utils.sessions_timeframe_sql()+") ORDER BY extended_label ASC "):
            if t['parent_id'] and l != t['parent_id']:
                l = t['parent_id']
                
                print(extended_label(db_get_item_by_id(t['parent_id'],'lists')) +": "+ sec_to_time(get_total_time(l,'lists',timeframe[0],timeframe[1])))

            print("   "+ t['label']  +": "+  sec_to_time(get_total_time(t['id'],'tasks',timeframe[0],timeframe[1])))
            # def get_total_time(id, category = 'tasks', start_time = None, end_time = None, get_minutes = None):


    def quit(self, widget_or_signal_source=None, condition=None):
        print("Adios ", conf.app_name)
        # print("widget_or_signal_source ", widget_or_signal_source)
        # print("condition ", condition)
        
        if self.is_running:
            print('Caching active session', self.session['label'])
            db_set_session_cache(self.session)
        try:
            # print("before os.remove(conf.pipe)")
            os.remove(conf.pipe)
            print("Pipe removed")
        except Exception as e:
            print("Error removing conf.pipe in quit",e)

        notify.uninit()
        Gtk.main_quit()
        exit()


    def check_afk_time(self):
        # returns seconds of inactivity
        # See https://stackoverflow.com/questions/67083083/how-to-get-idle-time-in-linux  or 

        # Works on x11 but not wayland
        # Requires xprintidle (sudo apt install xprintidle)
        # idle_time = int(int(subprocess.getoutput('xprintidle')) / 1000)

        # Currently using: https://github.com/bkbilly/dbus_idle
        # Requires: 
        #   sudo apt install meson libdbus-glib-1-dev patchelf
        #   pip install dbus-idle

        idle_time = int(int(IdleMonitor().get_dbus_idle()) / 1000)
        return idle_time


    def toggle_do_not_disturb(self, widget):
        if 'do-not-disturb' in self.session:
            del self.session['do-not-disturb']
            self.do_not_disturb_menu_item.set_label("Enable Do Not Disturb")
            self.indicator.set_label("Do Not Disturb Disabled", "")

        else:
            self.session['do-not-disturb'] = True
            self.indicator.set_label("Do Not Disturb Enabled", "")
            self.do_not_disturb_menu_item.set_label("Disable Do Not Disturb")

        return True

    def tock(self):

        if 'do-not-disturb' in self.session:
            return None

        afk_time = self.check_afk_time()
        # print("Idle time: "+str(afk_time))

        dbg('Last todo todo_sync_time', conf.todo_sync_time, 'Time diff',int(time_difference(conf.todo_sync_time)),'Auto refresh interval * 60', (conf.user['todolist_refresh_interval'] * 60), s="todoloading", l=3 )

        if (int(time_difference(conf.todo_sync_time)) / 60) > conf.user['todolist_refresh_interval'] * 60 :
            self.async_refresh()

        # TODO: use individual todo_refresh_times

        minutes = (int(self.session['duration']) / 60)
        
        if(self.is_running == False):

            if float(minutes / conf.user['randomness_interrupt_interval']).is_integer():
                if afk_time < 30:
                    
                    notify.Notification.new("What Am I doing?","Your randomness timer is at "+str(minutes)+" minutes. ", None).show()

                    self.open_task_window()
                        
                    playsound('sound/dinner-bell.mp3',False)

                elif afk_time > 120:
                    self.session['duration'] = 0
                    self.session['start_time'] = now()
                    print("Idle time reset. afk:",  afk_time, self.session)

        else:
            if afk_time > 120:
                # only show this once
                if afk_time < 181:
                    self.open_task_window(None,{'afk_time':afk_time})
                    # session_options_dialog(None, 'test input_data')
            else:
                if self.session['label'] in conf.user['custom_pomodoro_intervals']:
                    check = conf.user['custom_pomodoro_intervals'][self.session['label']]
                else:
                    check = conf.user['pomodoro_interval']
                
                if float(minutes / check ).is_integer():
                    notify.Notification.new("Time for a Break?","You've been working on "+self.session['label']+" for "+str(minutes)+" minutes. ", None).show()

                    playsound('sound/bell-xylophone-g.mp3',False)


                if 'target' in self.session:
                    t = self.session['target']

                    t['percent'] = round(( (t['starting_value'] + minutes) / t['value'] ) * 100,1)
                    print("At ", t['percent'], "% of ", t['scope'],  " target")

                    if t['type'] == 'max':
                        if t['percent'] >= 100:

                            notify.Notification.new("Time is up for this "+t['scope'],"You'r at "+str(round(t['percent']))+"% of your "+str(t['value'])+" minutes in the last "+str(t['within_value'])+" "+ t['within_unit'], None).show()

                            playsound('sound/dinner-bell.mp3',False)

                    elif t['type'] == 'min' and round(t['starting_value'] + minutes) == t['value']:
                        notify.Notification.new("Good job on doing "+self.session['label'],"You've reached your target of "+str(t['value'])+" minutes "+str(t['within_value'])+" "+ t['within_unit'], None).show()
                        
                        playsound('sound/xylophone-chord.mp3',False)

                        
                    # maybe add a target % to the session and show with tick

    icon_tick_number = 0

    def tick(self):
        menu = self.menu    
        indicator = self.indicator

        # check for suspend indicated by gap in tick intervals
        time_since_last_tick = round(time_difference(self.session['start_time'])  - self.session['duration'])
        if time_since_last_tick > 10:
            print(time_since_last_tick, " seconds since last tick. Probably just woke from suspend. ")
            
            if self.is_running:
                self.open_task_window(None,{'afk_time':time_since_last_tick})
            else:
                print("resetting randomness timer")
                self.session['duration'] = 0
                self.session['start_time'] = now()

        # print("tick!")
        self.session['duration'] = int(time_difference(self.session['start_time']))

        if(self.session['duration'] > 2 and (int(self.session['duration']) / 60).is_integer()):
            self.tock()

        if(self.is_running == True):
            self.icon_tick_number = self.icon_tick_number + 1
            
            if self.icon_tick_number > 8:
                self.icon_tick_number = 1    

            label = self.session['label'] + ": " + sec_to_time(self.session['duration'])

            indicator.set_icon_full(os.path.abspath('icon/icon-'+str(self.icon_tick_number)+'.svg'),label) 
        
        else:

            # label = random.choice(conf.idle_messages) # Cool but makes menu bounce around #Could be paused when the menu opens
            label = conf.user['default_text']
            if self.session['duration'] > 60 and self.session['duration'] % 2:
                indicator.set_icon_full(os.path.abspath('icon/icon-red.svg'),label)
            else:
                indicator.set_icon_full(os.path.abspath('icon/icon-1.svg'),label)

        # https://lazka.github.io/pgi-docs/#AyatanaAppIndicator3-0.1/classes/Indicator.html#AyatanaAppIndicator3.Indicator.set_label
        indicator.set_label(label, "Wide")

        for todo in conf.todo_sync_required:
            # print('tick noticed a todo needing refreshment, time since refresh: ',time_difference(conf.todo_sync_times[todo]))

            if time_difference(conf.todo_sync_times[todo]) > 4:
                # print('tick noticed a todo needing refreshment')
                self.async_refresh(None,conf.user['todolists'][todo])
        conf.todo_sync_required = {}
        return True


    def start_task(self, w = None, task_data_or_id = None, transfer_current_session_time = False):

        if isinstance(task_data_or_id, dict):
            task_data = task_data_or_id
        else:
            task_data = utils.db_get_item_by_id(task_data_or_id)

        task_label = task_data['label']
        dbg("starting "+ task_label,l=1)

        if transfer_current_session_time:
            start_time = self.session['start_time']
            duration = self.session['duration']

            if(self.is_running == True):
                self.stop_task(None,'cancel')

        else:
            start_time = now()
            duration = 0

            if(self.is_running == True):
                self.stop_task()
            
        
        self.is_running = True
        
        s = {
            "label": task_label,
            "extended_label": utils.extended_label(task_data),
            "start_time": start_time,
            "duration":duration,
            "task":task_data,
            "notes":'',
        }

        if s['task']['id'] in conf.user['time_targets']['tasks']:
            s['target'] = copy.copy(conf.user['time_targets']['tasks'][s['task']['id']])
            s['target']['scope'] = 'task' 
            target_start = datetime_minus_calendar_unit(s['target']['within_unit'],s['target']['within_value'])

            s['target']['starting_value'] = utils.get_total_time(task_data['id'],'task', target_start,None,"get_minutes")
            s['target']['percent'] = s['target']['starting_value'] / s['target']['value'] * 100

        if s['task']['parent_id'] in conf.user['time_targets']['lists']:
            s['target'] = copy.copy(conf.user['time_targets']['lists'][s['task']['parent_id']])
            s['target']['scope'] = 'list' 
            target_start = datetime_minus_calendar_unit(s['target']['within_unit'],s['target']['within_value'])

            s['target']['starting_value'] = utils.get_total_time(task_data['parent_id'],'list', target_start,None,"get_minutes")
            s['target']['percent'] = s['target']['starting_value'] / s['target']['value'] * 100
            
            dbg("session with list target started",s,s="targets",l=3)

        self.session = s       

        utils.db_set_session_cache(self.session)

        self.tick()

        # print('total times for task ',task_label, utils.get_times(task_data))    

        self.task_running_menu_additions()

        self.menu.show_all()
        print("task data",task_data['data'])

        if task_data['id'] in conf.user['task_commands']:
            command_data = conf.user['task_commands'][task_data['id']]
            if command_data['status']:
                thread = threading.Thread(target=self.run_task_command,args=(command_data['command'],))
                print("found task command:", command_data['command'])
                thread.start()


    def run_task_command(self,command):
        print("running task command:", command)

        self.running_command_task_label = copy.copy(self.session['label'])

        # Check if already running 
        process = None
        for proc in psutil.process_iter():
            pinfo = proc.as_dict(attrs=['pid', 'name'])
            print("Check process", pinfo['name'])
            if pinfo['name'] == command:
                process = proc
                break
            else:
                continue
                
        if process:
            print("waiting for already running command with psutils", command)
            # subprocess.run('wmctrl', '-a', command) # Doesn't work on wayland
            process.wait()
        else:
            print("Launching command with subprocess.run", command)
            subprocess.run(command) 

        print("running task command complete:", command)

        if self.session['label'] == self.running_command_task_label:
            GLib.idle_add(self.stop_task)
            GLib.idle_add(self.open_task_window)


    def mark_done(self, w=None, task = None):
        ''' second (task) argument is required and must be a task object '''
        
        print("Mark Task done")
        print(task)

        todolist_conf = conf.user['todolists'][task['todolist']]

        try:

            done_thread = threading.Thread(target=conf.todo_connectors[todolist_conf['type']].mark_task_done, args=(task,) )
            conf.todo_sync_times[todolist_conf['id']] = now() # this is to avoid causing a refresh, perhaps not the best though
            
            # Other Options: 
            #   make a custom class extending Thread with callback method that runs del conf.file_watch_ignores[todolist_conf['id']]
            #       Complicated
            #   deal with file_watch_ignores in the connector
            #       poor seperation
            #   
            done_thread.start()
            
            db_query("UPDATE tasks set status = '0' WHERE id = ? ",(task['id'],) )
            utils.reindex_one(task)

            # print('remove menu item')
            self.menu_tasks[task['id']].destroy()
                
            playsound('sound/xylophone-chord.mp3',False)

        except Exception as e:
            error_notice('Error Marking Task Done'," Marking "+ task['label']+" as done in "+todolist_conf['label']+" had a serious failure",e )



    def stop_task(self, w = '', action = 'save', custom_end_time=None):
        ''' supported actions are save, cancel, mark_done '''

        list_menus = self.list_menus
        menu_tasks = self.menu_tasks
        session = self.session
        
        print("Stopping ", session['label'])
        task = session['task']
        if self.is_running == True:
            session['duration'] = time_difference(session['start_time'],custom_end_time)
            db_query("DELETE FROM system WHERE field = 'session' ")

            if action != 'cancel':

                # Get time tracker for this tasks todolist 
                todolist_conf = conf.user['todolists'][task['todolist']]
                timetracker_conf = conf.user['timetrackers'][todolist_conf['timetracker']]

                dbg("Save Session to "+ todolist_conf['timetracker'])
                try:
                    save_thread = threading.Thread(target=conf.timetracker_connectors[timetracker_conf['type']].save_session, args=(session,timetracker_conf) )
                    save_thread.start()
                except Exception as e:
                    error_notice('Error Saving Time Data'," Recording timetracking for "+ task['label']+"  in "+timetracker_conf['label']+" had a serious failure",e )

                session['timetracker'] = todolist_conf['timetracker']

                utils.db_save_session(session)

                if action == 'mark_done':
                    self.mark_done(None,task)

                else: 
                    # print("add ",utils.extended_label(task)," to recent tasks")
                    i = Gtk.MenuItem.new_with_label(utils.extended_label(task))
                    i.connect('activate',self.start_task,task)
                    list_menus['recent'].prepend(i)
                    try:
                        list_menus['recent'].get_children()[11].destroy()
                    except Exception as e:
                        dbg("Exception trying to rotate recent tasks. probably are less than 11",l=2,s="recent")

                    # Check de-hoist completed time targets
                    ballance = utils.check_time_target(task)
                    dbg('time target ballance:', ballance,l=2,s='time_targets')

                    if ballance != False and ballance < 0:
                        dbg('un-hoist completed time target',l=2,s='time_targets')
                        try:
                            self.menu.remove(menu_tasks[task['id']]) # how to check that this actually worked/ it was hoisted?
                            list_menus[task['parent_id']].append(menu_tasks[task['id']])
                        except Exception as e:
                            # Boo Hoo?
                            dbg('de-hoisting failed',e)
                        playsound('sound/xylophone-chord.mp3',False)

                    self.menu.show_all()

            self.is_running = False
            # print(utils.get_times(task))
            if action != 'cancel':
                notify.Notification.new("Focused on "+session['label']+" for "+sec_to_time(session['duration']),utils.pretty_dict(utils.get_times(task)), None).show()
                # notify.Notification.new(action.capitalize()+" "+session['label']+" "+sec_to_time(session['duration']),utils.pretty_dict(utils.get_times(task)), None).show()
        
            # Start randomness timer
            self.session = {
                "label": 'Randomness',
                "extended_label": 'Randomness',
                "start_time": now(),
                "duration":0,
                "task":{}
            }

            self.tick()

            # Rm stop task menu item
            self.menu.get_children()[0].destroy()
            self.menu.get_children()[0].destroy()
            self.do_not_disturb_menu_item.set_label("Do Not Disturb")

        else:
            print('no task running!')


    def task_running_menu_additions(self):
        
        i = Gtk.ImageMenuItem.new_with_label("Edit Session")
        i.set_image(Gtk.Image.new_from_file(os.path.abspath('icon/edit.svg'))) 

        i.set_always_show_image(True) 
        i.connect("activate", self.open_session_options_dialog,'from_menu')
        self.menu.insert(i,0)    

        i = Gtk.ImageMenuItem.new_with_label("Pause" )
        i.set_image(Gtk.Image.new_from_file(os.path.abspath('icon/pause.svg'))) 

        i.set_always_show_image(True) 
        i.connect("activate", self.stop_task)
        self.menu.insert(i,0)


    def async_refresh(self, w=None, single_todo = None):

        self.indicator.set_label("Refreshing Todolists", "Wide")
        menu_item = Gtk.MenuItem.new_with_label("Refreshing Todolists")
        self.menu.append(menu_item) 
        self.menu.show_all()

        connectors_thread = threading.Thread(target=self.async_refresh_inner,args=(single_todo,))
        connectors_thread.start()


    def async_refresh_inner(self, single_todo = None):
        # dbg("async refresh started",s="todoloading",l=3)
        if single_todo:
            utils.refresh_todolist(single_todo)
            utils.reindex()

        else:
            utils.get_todolists()

        dbg("async refresh complete",s="todoloading",l=3)
        GLib.idle_add(self.update_menu)
        


    def update_menu(self, w = ''):
        # print("update_menu")
        menu = self.menu

        self.menu_tasks = {}
        self.list_menus = {}

        menu_tasks = self.menu_tasks
        list_menus = self.list_menus


        menu.foreach(lambda child: child.destroy()) 

        utils.add_todos_to_menu(menu, menu_tasks, list_menus, self.start_task)

        menu.append(Gtk.SeparatorMenuItem.new())

        # Recent Tasks Menu
        list_menus['recent'] = Gtk.Menu() # the sub_list that items get added to
        recents = Gtk.MenuItem.new_with_mnemonic("Recent Tasks") # the "item" that gets added 
        recents.set_submenu(list_menus['recent'])
        menu.append(recents)

        for id, t in utils.get_recent_tasks().items():
            # print('recent task',t)
            try:
                i = Gtk.MenuItem.new_with_label(utils.extended_label(t))
                i.connect('activate',self.start_task,t)
                list_menus['recent'].append(i)

            except Exception as e:
                # Because a key error if the task has was completed or todolist removed
                print('recent_tasks error', e)
        menu.append(Gtk.SeparatorMenuItem.new())


        # Todolist openables
        openables = []
        for id, todolist in conf.user['todolists'].items():
            if todolist['status']:
                openable = get_connector_openable(None, todolist,False)
                if openable not in openables:            
                    openables.append(openable)
                    
                    menu_aw = Gtk.MenuItem.new_with_label("Open "+todolist['label']+" ")
                    menu_aw.connect("activate", get_connector_openable, todolist)
                    menu.append(menu_aw)
            
        # Timetrackers
        for id, timetracker in conf.user['timetrackers'].items():
            if timetracker['status']:
                openable = get_connector_openable(None, timetracker,False)
                if openable not in openables:            
                    openables.append(openable)
                    menu_aw = Gtk.MenuItem.new_with_label("Open "+timetracker['label']+" ")
                    menu_aw.connect("activate", get_connector_openable, timetracker)
                    menu.append(menu_aw)

        # Update List
        # Lots of spaces to make menu wide-ish in preparation for opening wide sub menus 
        menu_update = Gtk.MenuItem.new_with_label("Refresh Lists                                                                    ")
        menu_update.connect("activate", self.async_refresh)
        menu.append(menu_update)

        setting_menu_item = Gtk.MenuItem.new_with_label("Settings")
        setting_menu_item.connect("activate",self.open_settings_window)
        menu.append(setting_menu_item)    
        
        task_window_menu_item = Gtk.MenuItem.new_with_label("Tasks")
        task_window_menu_item.connect("activate",self.open_task_window)
        menu.prepend(task_window_menu_item)
        self.indicator.set_secondary_activate_target(task_window_menu_item)


        new_task_menu_item = Gtk.MenuItem.new_with_label("New Task")
        new_task_menu_item.connect("activate",self.open_new_task_dialog)
        menu.append(new_task_menu_item)
        
        self.do_not_disturb_menu_item = Gtk.MenuItem.new_with_label("Do Not Disturb")
        if 'do-not-disturb' in self.session:
            self.do_not_disturb_menu_item.set_label("Disable Do Not Disturb")
        self.do_not_disturb_menu_item.connect("activate",self.toggle_do_not_disturb)
        menu.append(self.do_not_disturb_menu_item)
        
        quit_menu_item = Gtk.MenuItem.new_with_label("Quit")
        quit_menu_item.connect("activate",self.quit)
        menu.append(quit_menu_item)
        
        if self.is_running:
            self.task_running_menu_additions()

        menu.show_all()


    def open_session_options_dialog(self, w = None, params = None):

        if hasattr(self, 'session_options_dialog'):
            # print("present existing session_options_dialog",self.session_options_dialog)
            self.session_options_dialog.present()
        else:
            self.session_options_dialog = SessionOptionsDialog(self,params)
            self.session_options_dialog.show_all()


    def open_settings_window(self, w = None, **kwargs):

        if hasattr(self, 'settings_window'):
            self.settings_window.present()
        else:
            self.settings_window = SettingsWindow(self,**kwargs)
            self.settings_window.show_all()


    def open_task_window(self, w = None, data = None):
        self.taskwindow = TaskWindow(self, data)


    def open_new_task_dialog(self, w = None, passed_data = None):

        if hasattr(self, 'new_task_dialog'):
            self.new_task_dialog.present()
        else:
            self.new_task_dialog = NewTaskWDialog(self,passed_data)
            self.new_task_dialog.show_all()


    def signal_handler(self, sig, frame):
        dbg('Signal received',sig,s='signals')

        if sig == signal.SIGUSR1:
            # try:
            #     print('TaskWindow._instance',TaskWindow._instance)
            #     if TaskWindow._instance:
            #         self.taskwindow.destroy()
            #     else:
            #         self.open_task_window()

            # except AttributeError:
            self.open_task_window()

        elif sig == signal.SIGUSR2:
            self.open_session_options_dialog()

        else: 
            dbg("no handler for received signal",s='signals',l=3)

    def check_pipe(self):
        # print("Listening to pipe at ",conf.pipe)

        try:
            with open(conf.pipe, "r") as pipe:
                data = pipe.read().strip()

            print("check_pipe ")
            print(data)

            pipe.close()

            # TODO: add registry of special commands 
            # How to handle function arguments? (for example refresh a todolist with it's id)
            # if data in ['quit','open_task_window']:

            if data == 'quit':
                GLib.idle_add(self.quit)

            elif data == 'open_task_window':
                GLib.idle_add(self.open_task_window)            
                
            elif data == 'stop':
                GLib.idle_add(self.stop_task)


            else:
                search_results = utils.taskindex_search('"'+str(data)+'"')
                if len(search_results) > 0:
                    self.start_task(None, utils.first(search_results)['id'])
                
                else:
                    error_notice('Commandline Task failed','Could not find a task matching argument '+str(data))
         
        except FileNotFoundError as e:
            print("Error starting pip listener, CLI will not work",e)

        # keep listening
        self.check_pipe()


def startup():
    # print("startup ",sys.argv)
    
    ''' if called with no arguments send shutdown to pipe, wait 2 seconds delete pipe file and launch application. if called with arguments send args to pipe if it exist otherwise ''' 

    parser = argparse.ArgumentParser(
                    # prog='ProgramName',
                    # description='What the program does',
                    # epilog='Text at the bottom of help'
                    )

    parser.add_argument('task',nargs='?')             # optional positional argument
    parser.add_argument('-s', '--debug_systems', nargs="*", default=[])      # option that takes a value
    parser.add_argument('-l', '--debug_level', default=1)       # option that takes a value
    parser.add_argument('-f', '--force', action='store_true', help="Force restart by deleting existing named pipe")  # on/off flag
    # parser.add_argument('-v', '--verbose', action='store_true')  # on/off flag

    args = parser.parse_args()
    dbg(args)

    conf.debug_level = int(args.debug_level)
    conf.debug_systems = args.debug_systems

    if args.force:
        print("Lanched with --force flag, forcibly deleting old pipe")
        try:
            os.remove(conf.pipe)
        except Exception as e:
            print(e)

            
    try:
        os.mkfifo(conf.pipe)
        dbg("Named pipe created successfully!", s="cli")

        signal.signal(signal.SIGUSR1, Application.signal_handler) 
        app = Application()

        if args.task:
            print("Writing args.task to pipe", args.task)
            with open(conf.pipe, "w") as pipeout:
                pipeout.write(args.task)
                pipeout.close()


    except FileExistsError:
        dbg("Named pipe exists, application must be running (or improperly shut down.) ",s="cli")

        # if args: pass to pipe and exit
        if args.task:
            pipe_line = args.task
        else:
            #otherwise open task window
            pipe_line = "open_task_window"
        

        dbg("Writing arg to pipe ",pipe_line, s="cli")

        with open(conf.pipe, "w") as pipeout:
            pipeout.write(pipe_line)
            pipeout.close()

        exit()



    except Exception as e:
        print(f"Named pipe creation failed: {e}")


if __name__ == "__main__":
    startup()
    # print("called with garv",sys.argv)
    # signal.signal(signal.SIGUSR1, Application.signal_handler) # works
    # app = Application()



