import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import conf
import utils
from utils import *


class SessionEditDialog(Gtk.Dialog):

    def __init__(self, widget=None, parent=None, target_session=None):

        
        if isinstance(parent,Gtk.Window):
            self.parent_window = parent
            if isinstance(parent.app,Gtk.Application):
                self.app = parent.app
            else:
                error_notice("Error: SessionEditDialog called out of application context")

        elif isinstance(parent,Gtk.Application):
            # if called from main class
            self.parent_window = None
            self.app = parent
        else:
            error_notice("Error: SessionEditDialog called out of application context")

        if  target_session:
            self.s = target_session


        else:
            error_notice("Error: SessionEditDialog called without session data")

        print(' SessionEditDialog target_session',target_session)

        self.s['task'] = db_get_item_by_id(self.s['task_id'])
        # Used to identify and remove old session 
        self.session_id = {
            'extended_label':self.s['extended_label'], 'start_time': self.s['start_time']
            }

        super().__init__(title="Edit "+self.s['extended_label']+" Session", transient_for=self.parent_window, flags=0)
        self.set_position(position=1) # doesn't work on wayland
        self.set_default_size(300,300)
        self.set_border_width(15)

        box = self.get_content_area()


        # label = Gtk.Label()
        # label.set_markup("<b>"+self.s['extended_label']+"</b> ")
        # box.add(label)

        menubar = Gtk.MenuBar()
        self.menu_bar_item = Gtk.MenuItem(label=self.s['extended_label']+" (change)")
        menubar.append(self.menu_bar_item)
        change_task_menu = Gtk.Menu()
        self.menu_bar_item.set_submenu(change_task_menu)

        utils.add_todos_to_menu(change_task_menu, {}, {}, self.change_task,True)
        
        box.add(menubar)

        box.add(Gtk.Box(border_width=10)) #spacer
        
        # start_time 
        start_time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        start_time_box.add(Gtk.Label(label='Start: '+self.s['start_time']))

        self.start_time_entry = Gtk.Entry()
        self.start_time_entry.set_text(str(self.s['start_time']))

        # TODO: Fancy (idiotic?) idiot-proof  inputs, Forget it ... for now

        # self.cal = gtk.Calendar()
        # self.cal.set_display_options(gtk.CALENDAR_SHOW_HEADING|gtk.CALENDAR_SHOW_DAY_NAMES)
        # start_time_box.add(self.cal)
        # start_date = self.s['start_time'][:10]
        # start_hours = self.s['start_time'][11:13]
        # start_minutes = self.s['start_time'][14:16]
        # hours_adjustment = Gtk.Adjustment(value=(utils.force_number(start_hours)),
        #     lower=00,
        #     upper=66,
        #     step_increment=1,
        #     page_increment=5,
        #     page_size=0)
        # self.hours_input = Gtk.SpinButton(adjustment=hours_adjustment) 
        # start_time_box.add(self.hours_inputhours_input)
        
        start_time_box.add(self.start_time_entry)
        box.add(start_time_box) 

        # Duration 
        duration_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        duration_box.add(Gtk.Label(label='Duration (in Minutes)'))
        
        adjustment = Gtk.Adjustment(value=(utils.force_number(self.s['duration']) / 60),
            lower=0,
            upper=9999,
            step_increment=1,
            page_increment=5,
            page_size=0)

        self.duration_input = Gtk.SpinButton(adjustment=adjustment) 

        duration_box.add(self.duration_input)

        box.add(duration_box) 


        box.add(Gtk.Box(border_width=10)) #spacer

        box.add(Gtk.Label(label='Notes'))

        self.notes_text_buffer = Gtk.TextBuffer()
        if 'notes' in self.s and  self.s['notes'] :
            self.notes_text_buffer.set_text(self.s['notes'])

        self.notes = Gtk.TextView(buffer=self.notes_text_buffer)
        self.notes.set_size_request(300,150)
        box.add(self.notes)

        box.add(Gtk.Box(border_width=10)) #spacer

        self.add_button("Cancel", 1)

        self.add_button("Delete", 2)

        self.add_button("Save", 3)

                
        self.set_default_response(3)

        self.show_all()
        self.connect("response", self.on_response)



    def change_task(self, widget = None, t = None):

        print('initial session ',self.s)

        self.s['extended_label'] = extended_label(t)
        self.s['task_id'] = t['id']
        self.s['parent_id'] = t['parent_id']
        self.s['todolist'] = t['todolist']
        self.s['task'] = t

        print('updated session',self.s)

        self.menu_bar_item.set_label(self.s['extended_label'])


    def on_response(self, widget, response):
        
        print("on_response",response, " session", self.s)


        if response == 2:
            db_query("DELETE FROM sessions WHERE extended_label = ? AND start_time = ? LIMIT 1",(self.session_id['extended_label'],self.session_id['start_time']))

            error_notice('Session Deleted','')
        
        if response == 3:

            if self.notes_text_buffer.get_modified():
            
                start, end = self.notes_text_buffer.get_bounds()
                self.s['notes'] = self.notes_text_buffer.get_text(start, end,False)

            # validate start_time
            if validate_start_time_str(self.start_time_entry.get_text()):
                self.s['start_time'] = self.start_time_entry.get_text()
            else:
                return False

            self.s['duration'] = (self.duration_input.get_value_as_int() * 60)

            print("(Modified) self.s", self.s)

            
            prepared_session = {
                'start_time' : str(self.s['start_time']),
                'duration': round(self.s['duration']),
                'task_id': str(self.s['task_id']),
                'parent_id': str(self.s['parent_id']),
                'todolist': str(self.s['todolist']),
                'extended_label': str(self.s['extended_label']),
                'timetracker': str(self.s['timetracker']),
                'notes': str(self.s['notes']),
            }


            db_query("DELETE FROM sessions WHERE extended_label = ? AND start_time = ? LIMIT 1",(self.session_id['extended_label'],self.session_id['start_time']))

            db_query("INSERT INTO sessions(start_time, duration, task_id, parent_id, todolist, extended_label,timetracker, notes) VALUES(:start_time, :duration, :task_id, :parent_id, :todolist, :extended_label, :timetracker, :notes )",prepared_session)

            reindex(self.s['task'])

        # del self.app.session_edit_dialog
        self.destroy()














