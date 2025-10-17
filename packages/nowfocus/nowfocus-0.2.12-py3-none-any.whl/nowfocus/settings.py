import json
import importlib
import copy

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import Notify as notify
from gi.repository import Gtk, GLib, Gdk

import conf 

import utils 
from utils import *

from session_edit_dialog import SessionEditDialog

def update_user_setting(widget = None, conf_ref = None, key = None, val = None, callback = None):
    ''' Update conf.user by passing a conf_ref user.conf pointer (exe. ' conf.user['task_commands']['task_id_email']) plus key for the value to be updated and a new value for it
    val can be a callable (with no required parameters), (so a widgets get_active can be used) in which case it's return value will be used  '''

    print("update user_setting")
    print('old value for '+key)
    print(conf_ref[key])    
    print('new value')

    if callable(val):
        print('calling callable update_user_setting' )
        val = val()

    # print(val)

    # print("widget.get_active()")
    # print(widget.get_active())

    if conf_ref and key:
        conf_ref[key] = val

        save_user_settings()

    if callback:
        callback() # Can you do that?


def update_user_settings_value(widget = None, key_val = None):
    print("update user_setting_value ")
    print(key_val)
    # TODO: migrate to new update_user_setting 

    if key_val:
        conf.user[key_val['key']] = key_val['value']
        save_user_settings()


def update_connector_status(widget, app, connector_category, id, key, widget_getter = "Add this feature! :)"):
    conf.user[connector_category][id][key] = widget.get_active()
    save_user_settings()
    after_todo_settings_change(app,id)
    # app.async_refresh()


def after_todo_settings_change(app, todo = None):
    if todo:
        todo = utils.get_todo_by_id(todo)
        if todo['status']:

            app.async_refresh(todo)
            utils.stop_todo_file_watchers(todo)
            utils.start_todo_file_watchers(todo)

        else:
            utils.db_deactivate_todo(todo['id'])
            utils.reindex()
            utils.stop_todo_file_watchers(todo)
            app.update_menu()
            
    else:
        app.async_refresh()
        utils.stop_todo_file_watchers()
        utils.start_todo_file_watchers()


class SettingsWindow(Gtk.Window):


    def show_sessions(self, widget = None, label_text = "Most Recent Sessions", order_by = 'start_time', limit = 35, passed_sessions = None):

        self.sessions_box.foreach(lambda child: child.destroy()) 
    
        if passed_sessions:
            dbg("using Passed_sessions",passed_sessions,s='settings')
            sessions = passed_sessions
        else:
            dbg("show_sessions: order_by:",order_by, 'limit',limit, s='settings')
            sessions = db_query(" SELECT * FROM sessions WHERE "+sessions_timeframe_sql()+" ORDER BY "+order_by+" DESC LIMIT ? ",(limit,)) 
        
        # print('sessions')
        # print(sessions)

        label = Gtk.Label()
        if passed_sessions:
            label.set_markup('<b>'+label_text+'</b>')
        else:
            label.set_markup('<b>'+str(limit)+' '+label_text+' of '+conf.user['hours_search_timeframe']+'</b>')
        self.sessions_box.add(label)

        for ls in sessions:
            dbg('Add session to session_box',ls['extended_label'],s='settings')
            btn = Gtk.Button(label=ls['extended_label']+' '+str(ls['duration'] / 60 / 60)[:4]+' hr on '+ls['start_time'][:10])

            btn.set_halign(Gtk.Align.START)
            btn.set_relief(Gtk.ReliefStyle.NONE)

            btn.connect('clicked', lambda button_widget, ls: SessionEditDialog(None, self, ls),ls )
            
            self.sessions_box.add(btn)

        self.sessions_box.show_all()

    def scroll_box(self, parent_widget = None, height = 300):

        # print('parent_widget')
        # print(parent_widget)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(-1, height)

        if parent_widget:
            # parent_widget.add(scrolled_window)
            parent_widget.pack_end(scrolled_window, True, True, 0)

        return scrolled_window



    def __init__(self, parent=None, **kwargs):
        self.app = parent #NOTE: This doens't look like it will work when called from task_window...
        Gtk.Window.__init__(self, title="Settings")
        self.set_border_width(15)
        self.set_position(position=1) 
        self.connect("destroy", self.on_close)

        self.notebook = Gtk.Notebook()
        self.add(self.notebook)


        row = 0
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_border_width(10)

        self.notebook.append_page(grid,Gtk.Label('Todolists and Time Trackers'))


        sub_head = Gtk.Label()
        sub_head.set_markup("<b>Todo Lists</b>")
        grid.attach(sub_head,0,(row:=row+1),5,1)

        self.boxes = {}
        self.inputs = {}

        self.boxes['todolists_outer'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        grid.attach(self.boxes['todolists_outer'],0,(row:=row+1),5,1)

        # Gets replaced when lists are loaded
        self.boxes['todolists_inner'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.boxes['todolists_outer'].add(self.boxes['todolists_inner'])

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.boxes['todolists_outer'].pack_start(separator, True, True, 0)
        
        self.show_connectors('todolists')


        grid.attach(Gtk.Label(label="Connect a new Todo List"),0,(row:=row+1),2,1)  
        self.inputs['new_todolists_type'] = Gtk.ComboBoxText()

        for item in conf.connectors['todolists']:
            self.inputs['new_todolists_type'].append(item,item)

        self.inputs['new_todolists_type'].set_active_id(list(conf.connectors['todolists'].keys())[0])
        grid.attach(self.inputs['new_todolists_type'],2,row,2,1)

        button = Gtk.Button(label="Go")
        button.connect("clicked", self.edit_add_connector,'todolists')
        grid.attach(button,4,row,1,1)



        grid.attach(Gtk.Box(border_width=10),0,(row:=row+1),5,1) # Spacer

        sub_head = Gtk.Label()
        sub_head.set_markup("<b>Time Trackers</b>")
        grid.attach(sub_head,0,(row:=row+1),5,1)

        self.boxes['timetrackers_outer'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        grid.attach(self.boxes['timetrackers_outer'],0,(row:=row+1),5,1)


        # Gets replaced when lists ar loaded
        self.boxes['timetrackers_inner'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.boxes['timetrackers_outer'].add(self.boxes['timetrackers_inner'])

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.boxes['timetrackers_outer'].pack_start(separator, True, True, 0)
        
        self.show_connectors('timetrackers')


        grid.attach(Gtk.Label(label="Connect a Time Tracker"),0,(row:=row+1),2,1)  
        self.inputs['new_timetrackers_type'] = Gtk.ComboBoxText()

        for item in conf.connectors['timetrackers']:
            self.inputs['new_timetrackers_type'].append(item,item)

        self.inputs['new_timetrackers_type'].set_active_id(list(conf.connectors['timetrackers'].keys())[0])
        grid.attach(self.inputs['new_timetrackers_type'],2,row,2,1)


        button = Gtk.Button(label="Add")
        button.connect("clicked", self.edit_add_connector,'timetrackers')
        grid.attach(button,4,row,1,1)
        




        # Settings
        row = 0
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        self.notebook.append_page(grid,Gtk.Label('Settings'))


        grid.attach(Gtk.Box(border_width=10),0,(row:=row+1),5,1) # Spacer

        grid.attach(self.settings_updater('default_text','What am I Doing?','Entry'),0,(row:=row+1),5,1)

        grid.attach(self.settings_updater('open_task_window_fullscreen',True,'Switch'),0,(row:=row+1),5,1)

        grid.attach(self.settings_updater('pomodoro_interval',25,'SpinButton',"(minutes)"),0,(row:=row+1),5,1)

        grid.attach(self.settings_updater('randomness_interrupt_interval', 3, 'SpinButton',"\nPop up todo menu every so many minutes if not doing a task"),0,(row:=row+1),5,1)

        grid.attach(self.settings_updater('todolist_refresh_interval', 3, 'SpinButton',"(hours)"),0,(row:=row+1),5,1)
        
        # grid.attach(self.settings_updater('tick_interval', 18, 'SpinButton',"\nMust be an even number fraction of 60. (requires restart)"),0,(row:=row+1),5,1)

        # grid.attach(self.settings_updater('invoice_hourly_rate', 33, 'SpinButton',""),0,(row:=row+1),5,1)
        
        grid.attach(self.settings_updater('hours_search_timeframe', 'auto', 'ComboBoxText',"\nDefault timetracking range for hours shown in main window and invoicing", options = list(hours_search_timeframes().keys())),0,(row:=row+1),5,1)
        
        grid.attach(self.settings_updater('prompts', None, 'TextView',""),0,(row:=row+1),5,1)

        grid.attach(self.settings_updater('display_todolist_as_top_level_list', 'auto', 'ComboBoxText',"", options = ['auto','always','never']),0,(row:=row+1),5,1)
 
        grid.attach(self.settings_updater('max_top_level_menu_items', 18, 'SpinButton',""),0,(row:=row+1),5,1)







        # Task Commands notebook page  
        self.task_commands_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.notebook.append_page(self.task_commands_box,Gtk.Label('Task Commands'))

        self.boxes['task_commands_outer'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        # self.boxes['task_commands_outer'] = self.scroll_box()
        self.task_commands_box.add(self.boxes['task_commands_outer'])

        # Gets replaced when commands are loaded
        self.boxes['task_commands_inner'] = Gtk.Box()
        self.boxes['task_commands_outer'].add(self.boxes['task_commands_inner'])

        self.show_task_commands()

        add_task_commands_button = Gtk.Button(label="Add a Task Command")
        add_task_commands_button.set_halign(Gtk.Align.CENTER)
        add_task_commands_button.connect("clicked", EditTaskCommandDialog, self)

        self.task_commands_box.add(add_task_commands_button)



        # Time Targets notebook page 
        self.targets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.notebook.append_page(self.targets_box, Gtk.Label('Time Targets'))

        self.boxes['lists_time_targets_outer'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        # self.targets_box.add(self.boxes['lists_time_targets_outer'])

        
        # self.boxes['test'] = self.scroll_box(None ,300) 
        # self.targets_box.add(self.boxes['test'])

        # self.boxes['lists_time_targets_outer'] = self.scroll_box(None ,300) 

        
        self.targets_box.add(self.boxes['lists_time_targets_outer'])


        # Gets replaced when targets are loaded
        self.boxes['lists_time_targets_inner'] = Gtk.Box()
        self.boxes['lists_time_targets_outer'].add(self.boxes['lists_time_targets_inner'])

        # separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        # self.boxes['lists_time_targets_outer'].pack_start(separator, True, True, 0)   

        # test_button = Gtk.Button(label="test")
        # self.boxes['lists_time_targets_inner'].add(test_button)

        
        self.show_time_targets('lists')

        add_lists_target_button = Gtk.Button(label="Add List Time Target")
        add_lists_target_button.set_halign(Gtk.Align.CENTER)
        add_lists_target_button.connect("clicked", self.edit_add_target,'lists')
        self.targets_box.add(add_lists_target_button)


        self.boxes['tasks_time_targets_outer'] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.targets_box.add(self.boxes['tasks_time_targets_outer'])
        # Gets replaced when targets are loaded
        self.boxes['tasks_time_targets_inner'] = Gtk.Box()
        self.boxes['tasks_time_targets_outer'].add(self.boxes['tasks_time_targets_inner'])

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.boxes['tasks_time_targets_outer'].pack_start(separator, True, True, 0)
        
        self.show_time_targets('tasks')

        add_tasks_target_button = Gtk.Button(label="Add Task Time Target")
        add_tasks_target_button.set_halign(Gtk.Align.CENTER)
        add_tasks_target_button.connect("clicked", self.edit_add_target,'tasks')
        self.targets_box.add(add_tasks_target_button)







        # Sessions notebook page  
        self.sessions_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.notebook.append_page(self.sessions_page,Gtk.Label('Sessions'))
        
        reconcile_db_button = Gtk.Button(label="Reconcile sessions database with tasks database")
        reconcile_db_button.connect("clicked", db_cleanup)
        self.sessions_page.add(reconcile_db_button)

        print_time_totals_button = Gtk.Button(label="Print time totals to console")
        print_time_totals_button.connect("clicked", self.app.print_time_totals)
        self.sessions_page.add(print_time_totals_button)

        show_recent_sessions_button = Gtk.Button(label="Show recent sessions")
        show_recent_sessions_button.connect("clicked", self.show_sessions, 'Recent Sessions', 'start_time')
        self.sessions_page.add(show_recent_sessions_button)

        show_long_sessions_button = Gtk.Button(label="Show long sessions")
        show_long_sessions_button.connect("clicked", self.show_sessions, 'Longest Sessions', 'duration')
        self.sessions_page.add(show_long_sessions_button)

        self.sessions_scroller = self.scroll_box(self.sessions_page)

        self.sessions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.sessions_scroller.add(self.sessions_box)

        self.show_sessions()

        self.show_all()

        



    def settings_updater(self, label, default_value = '', input_type = 'Entry', notes = '', options = False):
        ''' returns a box widget with a label and a input that live-updates user settings 
        input_type options are SpinButton,Entry,TextView,ComboBoxText,Switch '''

        
        if label in conf.user:
            value = conf.user[label]
        else: 
            value = default_value

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.set_hexpand(True)

        label_widget = Gtk.Label()
        label_widget.set_markup("<b>"+label.replace('_', ' ').title()+"</b> "+str(notes))
        box.pack_start(label_widget,False,False,5)

        match (input_type):
            case ("SpinButton"):
                adjustment = Gtk.Adjustment(value=int(value),
                            lower=0,
                            upper=999,
                            step_increment=1,
                            page_increment=5,
                            page_size=0)

                value_widget = Gtk.SpinButton(adjustment=adjustment,climb_rate=1,digits=1)

                value_widget.connect(
                    "value-changed", 
                    lambda value_widget : update_user_settings_value(None, {'key':label,'value':value_widget.get_value_as_int()})
                    )

            case ("Entry"):
                value_widget = Gtk.Entry() 
                value_widget.set_text(str(value))
                value_widget.connect("changed",
                    lambda value_widget: update_user_settings_value(None, {'key':label,'value':value_widget.get_text()})
                    ) 

            case ("Switch"):
                value_widget = Gtk.Switch()
                value_widget.set_active(value)
                box.pack_start(value_widget,False,False,5)
                value_widget.connect("state-set",
                    lambda value_widget, state: update_user_settings_value(None, {'key':label,'value':state})
                )

                    
            case ("TextView"):
                buffer = Gtk.TextBuffer()
                buffer.set_text(str(value))

                value_widget = Gtk.TextView(buffer=buffer) 
                buffer.connect("changed",
                    lambda value_widget: update_user_settings_value(None, {'key':label,'value':buffer.get_text(buffer.get_bounds()[0], buffer.get_bounds()[1], False)})
                    )
                    
            case ("ComboBoxText"):

                value_widget = Gtk.ComboBoxText() 
                for item in options:
                    value_widget.append(item,item)
                value_widget.set_active_id(str(value))
                value_widget.connect("changed",
                    lambda value_widget: update_user_settings_value(None, {'key':label,'value':value_widget.get_active_text()})
                    )

        box.pack_end(value_widget,False,False,5)
        
        return box

    def show_time_targets(self,category="tasks"):
        outer_box = self.boxes[category+"_time_targets_outer"]

        self.boxes[category+"_time_targets_inner"].destroy()

        self.boxes[category+"_time_targets_inner"] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        inner_box = self.boxes[category+"_time_targets_inner"]
        outer_box.add(inner_box)

        for id, data in conf.user['time_targets'][category].items():

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            checkbutton = Gtk.CheckButton()

            item_data = db_get_item_by_id(id,category)
            if not item_data:
                checkbutton.set_label("Error: '"+str(id)+"' didn't match anything " )
            else:     
                # print('Show time target',item_data)
                checkbutton.set_label(item_data['label']+": "+str(data['type'])+ " "+str(data['value'])+" minutes per "+str(data['within_value'])+" "+str(data['within_unit']) )
            checkbutton.set_active(data['status'])

            # checkbutton.connect("toggled", print, checkbutton.get_active())
            checkbutton.connect("toggled", update_user_setting, conf.user['time_targets'][category][id], 'status', checkbutton.get_active)

            edit_button = Gtk.Button(label="Edit")
            edit_button.connect("clicked", self.edit_add_target, category, id)
            box.pack_end(edit_button,False, False, 5)    
                
            box.add(checkbutton)
            
            del_button = Gtk.Button(label="Remove")
            del_button.connect("clicked", self.delete_time_target, category, id)
            box.pack_end(del_button,False, False, 5)

            inner_box.pack_start(box,True,True,5)

            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            inner_box.pack_start(separator, True, True, 0)

        inner_box.show_all()
        outer_box.show_all()


    def show_task_commands(self):
        outer_box = self.boxes["task_commands_outer"]

        self.boxes["task_commands_inner"].destroy()

        self.boxes["task_commands_inner"] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        inner_box = self.boxes["task_commands_inner"]
        outer_box.add(inner_box)

        for id, command_data in conf.user['task_commands'].items():

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            checkbutton = Gtk.CheckButton()
            
            task_data = db_get_item_by_id(id,"tasks")
            if not task_data:
                checkbutton.set_label("Error: '"+str(id)+"' task missing "+str(command_data['command']))
            else:     
                checkbutton.set_label(task_data['extended_label']+" "+str(command_data['command']) )
            checkbutton.set_active(command_data['status'])
            
            checkbutton.connect("toggled", update_user_setting, conf.user['task_commands'][id], 'status', checkbutton.get_active)

            edit_button = Gtk.Button(label="Edit")
            edit_button.connect("clicked", EditTaskCommandDialog, self, id)
            box.pack_end(edit_button,False, False, 5)    
                
            box.add(checkbutton)
            
            del_button = Gtk.Button(label="Remove")
            del_button.connect("clicked", self.delete_task_command, id)
            box.pack_end(del_button,False, False, 5)

            inner_box.pack_start(box,True,True,5)

            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            inner_box.pack_start(separator, True, True, 0)

        outer_box.show_all()



    def show_connectors(self, connector_category = 'todolists'):
        print("show_connectors: "+connector_category)

        outer_box = self.boxes[connector_category+"_outer"]
        outer_box.set_hexpand(True)
        
        self.boxes[connector_category+"_inner"].destroy()

        self.boxes[connector_category+"_inner"] = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        inner_box = self.boxes[connector_category+"_inner"]
        outer_box.add(inner_box)

        for id, data in conf.user[connector_category].items():

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

            checkbutton = Gtk.CheckButton(label=data['label'])
            checkbutton.set_active(data['status'])
            checkbutton.connect("toggled", update_connector_status, self.app, connector_category, id, 'status')
            box.pack_start(checkbutton,False,False,5)

            edit_button = Gtk.Button(label="Edit")
            edit_button.connect("clicked", self.edit_add_connector, connector_category, id)
            box.pack_end(edit_button,False, False, 5)        
            
            del_button = Gtk.Button(label="Remove")
            del_button.connect("clicked", self.delete_connector, connector_category, id)
            box.pack_end(del_button,False, False, 5)

            inner_box.pack_start(box,True,True,5)

            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            inner_box.pack_start(separator, True, True, 0)

        outer_box.show_all()


    def delete_connector(self, widget, connector_category, id):
        connector = conf.user[connector_category][id]
        print("delete "+connector_category+" connector "+ id)
        print(connector)

        if connector_category == 'todolists':
            db_query("DELETE FROM tasks WHERE todolist = ? AND id NOT IN (SELECT task_id FROM sessions)",(id,))
            db_query("DELETE FROM lists WHERE todolist = ?",(id,))
            utils.reindex()
            utils.stop_todo_file_watchers(connector)
            self.app.update_menu()

        del conf.user[connector_category][id]
        save_user_settings()
        
        self.show_connectors(connector_category)


    def delete_time_target(self, widget, category, id):
        target = conf.user['time_targets'][category][id]
        print("delete target ",target)
        del conf.user['time_targets'][category][id]
        save_user_settings()
        self.show_time_targets(category)


    def delete_task_command(self, widget, id):
        command = conf.user['task_commands'][id]
        print("delete target ",command)
        del conf.user['task_commands'][id]
        save_user_settings()
        self.show_task_commands()


    def edit_add_connector(self, widget, connector_category, id = None):

        # If id is set it will edit that connector entry, otherwise add a new one of type in self.inputs['new_'+connector_category+'_type'] 
        if id:
            connector_type = conf.user[connector_category][id]['type']
        else:
            connector_type = self.inputs['new_'+connector_category+'_type'].get_active_text()

        # print("type in edit_add_connector %s" % (connector_type))

        dialog = EditAddConnectorDialog(self, connector_category, connector_type, id)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:

            print("The OK button was clicked")
            self.show_connectors(connector_category)

        elif response == Gtk.ResponseType.CANCEL:
            print("The Cancel button was clicked")

        dialog.destroy()


    def edit_add_target(self, widget, category, id = None):
        ''' If id is set it will edit that entry, otherwise add a new one of category in self.inputs['new_'+_category+'_type'] '''

        print("category in edit_add_target %s" % (category))

        dialog = EditAddTargetDialog(self, category, id)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:

            print("The OK button was clicked")
            self.show_time_targets(category)

        elif response == Gtk.ResponseType.CANCEL:
            print("The Cancel button was clicked")

        
    def on_close(self, obj):
        print("good bie settings window ")
        del self.app.settings_window  








class EditTaskCommandDialog(Gtk.Dialog):

    def __init__(self, widget = None, parent = None, id = None):

        super().__init__(title="Set Task Command", transient_for=parent, flags=0)

        self.set_border_width(15)
        box = self.get_content_area()
        box.set_spacing(15)

        self.parent = parent

        item_data = None
        command = None
        status = True
        self.item_id = None
        self.initial_item_id = None
        self.menu_bar_item = Gtk.MenuItem(label="Select Task")

        if id:
            item_data = db_get_item_by_id(id)
            if item_data:
                self.menu_bar_item = Gtk.MenuItem(label=item_data['label'])

            if id in conf.user['task_commands']:
                command = conf.user['task_commands'][id]['command']
                status = conf.user['task_commands'][id]['status']
            
            self.item_id = id
            self.initial_item_id = id


        #Select task
        menubar = Gtk.MenuBar()
        menubar.append(self.menu_bar_item)
        change_task_menu = Gtk.Menu()
        self.menu_bar_item.set_submenu(change_task_menu)
        add_todos_to_menu(change_task_menu, {}, {}, self.set_item_id,True)
        box.add(menubar)


        self.command_entry = Gtk.Entry()
        if command: 
            self.command_entry.set_text(command)
        box.add(self.command_entry)


        self.status_switch = Gtk.CheckButton(label="Enabled")
        self.status_switch.set_active(status)
        box.add(self.status_switch)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.show_all()
        self.connect("response", self.on_response)



    def on_response(self, widget, response):

        if response == Gtk.ResponseType.OK:

            if self.initial_item_id and self.initial_item_id != self.item_id:
                del conf.user['task_commands'][self.initial_item_id]

            conf.user['task_commands'][self.item_id] = {'status':self.status_switch.get_active(), 'command': self.command_entry.get_text()}

            print("Save task command",self.item_id,conf.user['task_commands'][self.item_id])

            save_user_settings()
            
            try:
                self.parent.show_task_commands()
            except Exception as e:
                print("exception from parent.show_task_commands(), probably parent isn't SettingsWindown",e )


        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel button clicked")
 
        else:
            print("Dialog closed")

        self.destroy()

    def set_item_id(self,w=None, data=None):
        print("set_task",data)
        self.item_id = data['id']
        self.menu_bar_item.set_label(data['label'])


class EditAddTargetDialog(Gtk.Dialog):

    def __init__(self, parent, category, id = None):

        super().__init__(title="Set Time Target", transient_for=parent, flags=0)

        self.set_default_size(700,850)
        self.set_border_width(15)
        box = self.get_content_area()
        box.set_spacing(15)

        data = {
            "type": 'max',
            "value":15,
            "within_value":1,
            "within_unit":"days",
            "status": True,
        }

        if id: 
            if id in conf.user['time_targets'][category]:
                data = conf.user['time_targets'][category][id]
            self.item_id = id
            self.initial_item_id = id
        else:
            self.initial_item_id = None
            self.item_id = None

        self.entries = {}

        if id:
            item_data = db_get_item_by_id(id,category)
            self.menu_bar_item = Gtk.MenuItem(label=item_data['label'])
        else:
            item_data = None
            self.menu_bar_item = Gtk.MenuItem(label="Select "+ category)

        if category == 'tasks':
            box.add(Gtk.Label("Task"))
            menubar = Gtk.MenuBar()
            menubar.append(self.menu_bar_item)
            change_task_menu = Gtk.Menu()
            self.menu_bar_item.set_submenu(change_task_menu)
            add_todos_to_menu(change_task_menu, {}, {}, self.set_item_id,True)
            box.add(menubar)

        elif category == 'lists':
            set_list_widget = choose_from_lists(self.set_item_id, selected_list_id=item_data,accepts_tasks=False )
            box.add(set_list_widget)
        

        self.type_select = Gtk.ComboBoxText()
        self.type_select.append("max","max")
        self.type_select.append("min",'min')
        self.type_select.set_active_id(data['type'])
        box.add(self.type_select)
        
        value_adjustment = Gtk.Adjustment(
            value=int(data['value']),
            lower=0.01,
            upper=9999,
            step_increment=1,
            page_increment=5,
            page_size=0)

        box.add(Gtk.Label(label="Minutes"))
        self.value = Gtk.SpinButton(adjustment=value_adjustment,climb_rate=1,digits=1)

        box.add(self.value)

        box.add(Gtk.Label(label="within this many"))  

        # backward compatibility 
        if 'within_value' not in data:
            data['within_value'] = data['num_days']

                
        within_value_adjustment = Gtk.Adjustment(
            value=int(data['within_value']),
            lower=0.01,
            upper=9999,
            step_increment=1,
            page_increment=5,
            page_size=0)

        self.within_value = Gtk.SpinButton(adjustment=within_value_adjustment,climb_rate=1,digits=1)

        box.add(self.within_value)

        self.within_unit_select = Gtk.ComboBoxText()
        self.within_unit_select.append("days","days")
        self.within_unit_select.append("weeks",'weeks')
        self.within_unit_select.append("months",'months')
        self.within_unit_select.append("years",'years')
        if 'within_unit' in data:
            self.within_unit_select.set_active_id(data['within_unit'])
        box.add(self.within_unit_select)


        self.status_switch = Gtk.CheckButton(label="Enabled")
        self.status_switch.set_active(data['status'])
        box.add(self.status_switch)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.show_all()
        self.connect("response", self.on_response, category)


    def set_item_id(self,w=None,data=None):
        print("set_task",data)
        self.item_id = data['id']
        self.menu_bar_item.set_label(data['label'])


    def on_response(self, widget, response, category):

        if response == Gtk.ResponseType.OK:

            if self.initial_item_id and self.initial_item_id != self.item_id:
                del conf.user['time_targets'][category][self.initial_item_id]

            conf.user['time_targets'][category][self.item_id] = {
                'type':self.type_select.get_active_text(),
                'value': self.value.get_value(),
                'within_value': self.within_value.get_value(),
                'within_unit': self.within_unit_select.get_active_text(),
                'status':self.status_switch.get_active(),
                }
            
            print("save time target",conf.user['time_targets'][category][self.item_id])

            save_user_settings()
            reindex_one(db_get_item_by_id(self.item_id))

        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel button clicked")
            self.entries = {}
        else:
            print("Dialog closed")

        self.destroy()


            



















class EditAddConnectorDialog(Gtk.Dialog):

    def __init__(self, parent, connector_category, connector_type, id = None):

        super().__init__(title="Connect "+connector_category, transient_for=parent, flags=0)

        self.entries = {}

        self.app = parent.app
        self.set_default_size(400,400)


        self.set_border_width(15)

        box = self.get_content_area()
        box.set_spacing(15)

        print('EditAddConnectorDialog: arguments')
        print('connector_type: ',connector_type)
        print('id: ',id)
        fields = copy.copy(conf.connectors[connector_category][connector_type])
        print('fields',fields)
        
        if(id):
            data = conf.user[connector_category][id]
        else:
            data = fields

        print("connector data",data)

        for key in fields:

            if key in ['id','type','timetracker','status','watch_file']:
                continue

            label = Gtk.Label(label=key)
            box.add(label)


            if key in ['file']:
                self.entries[key] = Gtk.FileChooserButton(title="Select Todo File")
                self.entries[key].set_action(Gtk.FileChooserAction.OPEN)
                
            else:
                self.entries[key] = Gtk.Entry()
            
            if key in data:

                if key in ['file']:
                    self.entries[key].set_filename(str(data[key]))
                else:
                    self.entries[key].set_text(str(data[key]))

                if key in ['password','token','key']:
                    self.entries[key].set_visibility(False)

            box.add(self.entries[key])

        
        if connector_category == 'todolists':

            box.add(Gtk.Label(label="Time Tracker"))  
            self.timetracker_select = Gtk.ComboBoxText()

            for item in conf.user['timetrackers']:
                self.timetracker_select.append(item,item)

            if 'timetracker' not in data:
                data['timetracker'] = list(conf.user['timetrackers'].keys())[0]
            
            self.timetracker_select.set_active_id(data['timetracker'])
            box.add(self.timetracker_select)


        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK
        )

        self.show_all()
        self.connect("response", self.on_response, connector_category, connector_type, id, data)


    def on_response(self, widget, response, connector_category, connector_type, id, initial_data):
        if response == Gtk.ResponseType.OK:

            new = initial_data

            for key in self.entries:

                if key in ['file']:
                    new[key] = self.entries[key].get_filename()
                else:
                    new[key] = self.entries[key].get_text()
                dbg("value for "+ key +" is "+ new[key] )

            if not id:
                if new['label'] and new['label'] not in conf.user[connector_category]:
                    id = new['label']
                else:
                    # add a 2 char hash
                    import uuid
                    id = new['label']+"-"+str(uuid.uuid4())[:2]
            
            new['id'] = id

            if connector_category == 'todolists':
                new['timetracker'] = self.timetracker_select.get_active_text()

            conf.user[connector_category][id] = new

            save_user_settings()

            # load the connector module 
            if connector_category == 'timetrackers':
                conf.timetracker_connectors[new['type']] = importlib.import_module('connectors.'+new['type'])

            if connector_category == 'todolists':

                conf.todo_connectors[new['type']] = importlib.import_module('connectors.'+new['type'])

                utils.stop_todo_file_watchers(new)
                utils.start_todo_file_watchers(new)
                self.app.async_refresh(new)


        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel button clicked")
            self.entries = {}
        else:
            print("Dialog closed")


            