import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import conf
import utils
from utils import *

class NewTaskWDialog(Gtk.Dialog):

    def __init__(self, parent=None, passed_data=None):

        if isinstance(parent,Gtk.Window):
            self.parent_window = parent
            if isinstance(parent,Gtk.Application):
                self.app = parent.app
            else:
                error_notice("Error: NewTaskWDialog called out of application context")

        elif isinstance(parent,Gtk.Application):
            # if called from main class
            self.parent_window = None
            self.app = parent
        else:
            error_notice("Error: NewTaskWDialog called out of application context")

        super().__init__(title="New Task ", transient_for=self.parent_window, flags=0)

        self.present() # try to focus the window
        self.set_position(position=1) # center dialog, doesn't work on wayland
        self.set_default_size(300,300)

        self.set_border_width(15)

        box = self.get_content_area()

        self.task_label_entry = Gtk.Entry()
        self.task_label_entry.set_placeholder_text('Task')

        if passed_data and 'label' in passed_data:
            self.task_label_entry.set_text(passed_data['label'])

        box.add(self.task_label_entry)

        box.add(Gtk.Box(border_width=10)) #spacer

        default_list = get_most_recent_list(self.app.session)
        if default_list:
            self.selected_list = db_get_item_by_id(default_list,table='lists')

        box.add(choose_from_lists(self.select_list, default_list))

        box.add(Gtk.Box(border_width=10)) #spacer
        
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL
        )

        self.add_button("Save", 1)
        
        self.add_button("Save & Start", 2)
        
        self.set_default_response(2)

        self.show_all()
        self.connect("response", self.on_response)


    def select_list(self, widget = None, l = None):
        if widget.get_active():
            self.selected_list = l


    def on_response(self, widget, response):
        list_menus =self.app.list_menus
        menu_tasks = self.app.menu_tasks
        # print("Cool!",response, self.selected_list,self.task_label_entry)

        if response == 1 or response == 2:

            task_label = self.task_label_entry.get_text().strip()

            if not task_label:
                error_notice("Please Enter a name before saving new task")
                return False

            parent_list = self.selected_list
            todolist_conf = conf.user['todolists'][parent_list['todolist']]
            try:

                conf.file_watch_ignores[todolist_conf['id']] = True
                task = conf.todo_connectors[todolist_conf['type']].add_new_task(todolist_conf,parent_list,task_label)
                del conf.file_watch_ignores[todolist_conf['id']]

                dbg('connector add task response',task)

                # add it to the database 
                db_set_item(task)

                # add it to the menu 
                menu_tasks[task['id']] = Gtk.MenuItem.new_with_label(task['label'])
                menu_tasks[task['id']].connect("activate", self.app.start_task, task)
                list_menus[task['parent_id']].append(menu_tasks[task['id']])

                if response == 2:
                    self.app.start_task(None, task)

                    try:
                        self.app.taskwindow.destroy()
                    except Exception as e:
                        print("Error trying to remove taskwindow",e)
                    
                else:
                    try:
                        self.app.taskwindow.task_search()
                    except Exception as e:
                        print("Error trying to update taskwindow",e)

                    
            except Exception as e:

                if conf.debug_level > 1:
                    raise e
                
                error_notice('Error adding tasks',"Adding "+ task_label+" to "+todolist_conf['label']+" had a serious failure",e )

            

        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel button clicked")
 
        del self.app.new_task_dialog
        self.destroy()

