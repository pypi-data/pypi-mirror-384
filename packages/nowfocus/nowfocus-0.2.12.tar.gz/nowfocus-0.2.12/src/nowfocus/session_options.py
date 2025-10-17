import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import conf
import utils
from utils import *


class SessionOptionsDialog(Gtk.Dialog):

    def __init__(self, parent=None, input_data = None):

        
        if isinstance(parent,Gtk.Window):
            self.parent_window = parent
            if isinstance(parent,Gtk.Application):
                self.app = parent.app
            else:
                error_notice("Error: Session called out of application context")

        elif isinstance(parent,Gtk.Application):
            # if called from main class
            self.parent_window = None
            self.app = parent
        else:
            error_notice("Error: SessionOptionsDialog called out of application context")

        session = self.app.session

        super().__init__(title="Modify Current Session", transient_for=self.parent_window, flags=0)
        self.set_position(position=1) # doesn't work on wayland
        self.set_default_size(300,300)
        self.set_border_width(15)

        box = self.get_content_area()

        print(' SessionOptionsDialog input_data',input_data)

        # label = Gtk.Label()
        # label.set_markup("<b>"+session['extended_label']+"</b> ")
        # box.add(label)

        menubar = Gtk.MenuBar()
        self.menu_bar_item = Gtk.MenuItem(label=session['label']+" (change)")
        menubar.append(self.menu_bar_item)
        change_task_menu = Gtk.Menu()
        self.menu_bar_item.set_submenu(change_task_menu)

        utils.add_todos_to_menu(change_task_menu, {}, {}, self.change_task,True)
        
        box.add(menubar)

        box.add(Gtk.Box(border_width=10)) #spacer

        duration_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        duration_box.add(Gtk.Label(label='Duration (in Minutes)'))
        
        adjustment = Gtk.Adjustment(value=(utils.force_number(session['duration']) / 60),
            lower=0,
            upper=9999,
            step_increment=1,
            page_increment=5,
            page_size=0)

        self.duration_input = Gtk.SpinButton(adjustment=adjustment) 

        duration_box.add(self.duration_input)

        box.add(duration_box) #spacer
        box.add(Gtk.Box(border_width=10)) #spacer

        box.add(Gtk.Label(label='Notes'))

        self.notes_text_buffer = Gtk.TextBuffer()
        if 'notes' in session:
            self.notes_text_buffer.set_text(session['notes'])

        self.notes = Gtk.TextView(buffer=self.notes_text_buffer)
        self.notes.set_size_request(300,150)
        box.add(self.notes)

        box.add(Gtk.Box(border_width=10)) #spacer

        self.mark_done = Gtk.CheckButton(label="Mark Done")

        box.add(self.mark_done)

        self.add_button("Cancel", 1)

        self.add_button("Modify", 2)

        self.add_button("Finish", 3)
                
        self.set_default_response(3)

        self.show_all()
        self.connect("response", self.on_response)


    def change_task(self, widget = None, t = None):
        session = self.app.session

        print('Hot-swap current task (initial) session',session)
        session['label'] = t['label']
        session['extended_label'] = extended_label(t)
        session['id'] = t['id']
        session['parent_id'] = t['parent_id']
        session['parent_label'] = t['parent_label']
        session['task'] = t
        print('updated session',session)

        self.menu_bar_item.set_label(session['label'])


    def on_response(self, widget, response):
        
        session = self.app.session

        print("on_response",response, "original session", session)


        if response == 1:
            self.app.stop_task(None,'cancel')
            
        elif response > 1:

            if self.notes_text_buffer.get_modified():
            
                start, end = self.notes_text_buffer.get_bounds()
                session['notes'] = self.notes_text_buffer.get_text(start, end,False)

            print("(Modified) session", session)

            if response == 2:
                # move session [start_time] to set duration for 'continue' option 
                print('initial start_time', session['start_time'],'timedelta')

                session['start_time'] = now() - timedelta(seconds = (self.duration_input.get_value_as_int() * 60))

                print(' start_time + ', session['start_time'])

            # Or change session[duration] value  to reflect dropped / afk session 
            if response == 3:
                # Create custom end time
                custom_end_time = session['start_time'] + timedelta(seconds = (self.duration_input.get_value_as_int() * 60))

                # session['duration'] = (self.duration_input.get_value_as_int() * 60)
                
                if self.mark_done.get_active():
                    self.app.stop_task(None,'mark_done',custom_end_time)
                else:
                    self.app.stop_task(None,'save',custom_end_time)

        del self.app.session_options_dialog
        self.destroy()














