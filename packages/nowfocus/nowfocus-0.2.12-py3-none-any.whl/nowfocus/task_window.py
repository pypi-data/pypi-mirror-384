import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import conf
import utils
from utils import *

from settings import EditAddTargetDialog, EditTaskCommandDialog

class TaskWindow(Gtk.Window):
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path("styles.css")
    style_context = Gtk.StyleContext()
    style_context.add_provider_for_screen(
        Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    _instance = None
    
    def __init__(self,app,passed_data=None):

        if TaskWindow._instance:
            try:
                if TaskWindow._instance.taskEntry.get_text():
                    # Present existing window if there is anything in task entry
                    TaskWindow._instance.present()
                    self = TaskWindow._instance
                    self.recreate_header()
                    self.show_all()
                    return None

                    
                TaskWindow._instance.destroy() # get rid of old window instance 
                # TaskWindow._instance.present()
                # return None
            except Exception as e:
                dbg("TaskWindow._instance exception",e,s='taskwindow')

        TaskWindow._instance = self

        Gtk.Window.__init__(self, title=conf.app_name)

        self.set_default_size(900,900)
        self.modifyer_keys = {
            'control': False,
            'shift': False,
            'alt': False,
        }

        self.search_cache_refresh_time = now().strftime("%Y-%m-%d %H:%M:%S")
        self.search_cache = {}
        self.task_rclick_menu = Gtk.Popover()
        self.task_rclick_menu.set_name('task_rclick_menu')

        self.num_initial_tasks = 25

        self.app = app
        session = app.session
        self.set_name("TaskWindow") # set css id

        if conf.user['open_task_window_fullscreen']:
            self.fullscreen()
            self.get_style_context().add_class("large")

        # self.present() # try to focus the window
        # self.focus_force() # try to focus the window

        self.shown_tasks = {}
        
        self.set_border_width(20)
        self.set_position(position=1) # Works on x11 but not wayland (ubuntu 22.04)

        self.accel_group = Gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        box = Gtk.VBox(spacing=10)
        box.set_halign(Gtk.Align.CENTER)
        # box.set_valign(Gtk.Align.CENTER)
        
        self.add(box)

        self.header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15, border_width=10)

        # self.header.set_halign(Gtk.Align.CENTER)

        box.pack_start(self.header,False, False, 0)

        self.recreate_header()

        self.tick_timer = GLib.timeout_add_seconds(1, self.tick)

        self.task_entry_overlay = Gtk.Overlay()

        # Large fuzzy task input
        self.taskEntry = Gtk.Entry() 
        self.taskEntry.set_name("FuzzyTask") # set css id
        # self.taskEntry.set_width_chars(59)
        self.taskEntry.set_max_width_chars(79)

        self.taskEntry.set_placeholder_text("Find Task [Ctrl+F]")
        self.taskEntry.set_property("tooltip-text", "Find Task [Ctrl+F], press Enter to start work on the first task in the list")

        self.task_entry_overlay.add(self.taskEntry)

        box.pack_start(self.task_entry_overlay,False, False, 0)

        self.taskEntry.grab_focus()

        if passed_data:
            dbg('taskwindow passed_data',passed_data,s='taskwindow')
            if 'afk_time' in passed_data:

                last_active_time = datetime.now() - timedelta(seconds=passed_data['afk_time'])

                last_active_str = time.strftime('%H:%M', last_active_time.timetuple())

                afk_label = Gtk.Label()
                afk_label.set_markup("<b>Inactive Since "+" "+str(last_active_str) +"</b>")
                self.header.add(afk_label)

                pause_then_button = Gtk.Button(label="Finish Then")

                pause_then_button.connect("clicked", self.pause_then, last_active_time)
                self.header.add(pause_then_button)

            if 'task' in passed_data:
                self.taskEntry.set_text(passed_data['task']['label'])
        


        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(self.scrolled_window, True, True, 0)
        self.scrolled_window.set_size_request(-1, 350) 

        self.scrolled_window.connect('scroll-event', self.on_scroll) # This doesn't catch scrollbar moves
        self.scrolled_window.connect('edge-reached', self.on_scroll) # This is a little late and may not fire if the list is short?

        self.tasks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        self.tasks_box.set_halign(Gtk.Align.START)

        self.scrolled_window.add(self.tasks_box)

        self.total_duration_label = Gtk.Label()
        self.total_duration_label.set_margin_end(12)
        self.total_duration_label.set_halign(Gtk.Align.END)
        self.task_entry_overlay.add_overlay(self.total_duration_label)

        # Cool but captures the up/down selection  

        # self.timesheet_to_button = Gtk.Button()
        # self.timesheet_to_button.set_relief(Gtk.ReliefStyle.NONE)
        # self.timesheet_to_button.add(self.total_duration_label)

        # # self.timesheet_to_button.set_halign(Gtk.Align.END)
        # # self.task_entry_overlay.add_overlay(self.timesheet_to_button)
        # self.timesheet_to_button.connect("clicked",self.timesheet_to_clipboard)
        # self.timesheet_to_button.set_name("Footer")
        # self.timesheet_to_button.set_property("tooltip-text","Click to copy CSV timesheet to clipboard")
        # box.pack_start(self.timesheet_to_button,False, False, 0)


        self.buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self.buttons_box.set_halign(Gtk.Align.CENTER)
        self.buttons_box.set_name("Footer")

        box.pack_start(self.buttons_box,False, False, 0)

        self.settings_button = Gtk.Button(label="Settings")
        self.settings_button.connect("clicked",self.app.open_settings_window)
        self.buttons_box.add(self.settings_button)

        self.refresh_button = Gtk.Button(label="Refresh")
        self.refresh_button.set_property("tooltip-text","Reload all todolists (Ctrl + R)")
        self.refresh_button.connect("clicked",self.app.async_refresh)
        self.buttons_box.add(self.refresh_button)

        # Todolist openables
        for id, todo in conf.user['todolists'].items():
            if todo['status']:
                try:
                    openable = conf.todo_connectors[todo['type']].launch
                    openable_button = Gtk.Button(label=GLib.markup_escape_text(todo['label']))
                    openable_button.connect("clicked", lambda button_widget,todo=todo, openable=openable: openable(todo))
                    openable_button.set_property("tooltip-text","Open (new) "+GLib.markup_escape_text(todo['label']))
                    self.buttons_box.add(openable_button)

                except Exception as e:
                    dbg("error adding todo connector open() to task window ",e, s='taskwindow')

        self.new_task_button = Gtk.Button(label="New Task")
        self.new_task_button.set_property("tooltip-text","Add a new task (Ctrl + N)")
        self.new_task_button.connect("clicked",self.open_new_task_dialog)
        self.buttons_box.add(self.new_task_button)

        self.show_all()

        key, mod = Gtk.accelerator_parse('<Control>n')
        self.new_task_button.add_accelerator("clicked", self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)

        key, mod = Gtk.accelerator_parse('<Control>r')
        self.refresh_button.add_accelerator("clicked", self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)        

        self.connect("key-press-event", self.key_press)
        self.connect('key-release-event', self.key_release)
        self.connect("window-state-event", self.on_window_state_event)

        self.taskEntry.connect("changed",self.task_search)
        
        self.refresh_search_cache()
        self.connect("destroy", self.on_destroy)

        
    def on_destroy(self, widget= None):
        TaskWindow._instance = None
        print("¡Adios Task Window!")

    def on_scroll(self, w = None, e = None):

        # print("scroll event", e)
        
        if self.lazy_loadable_tasks:
            print('Tasks to lazy load ', len(self.lazy_loadable_tasks))
            for id, t in self.lazy_loadable_tasks.items():
                self.add_task_to_list(t)
            self.tasks_box.show_all()

            self.lazy_loadable_tasks = {}


    def refresh_search_cache(self,w = None):
        self.search_cache = {}
        self.search_cache_refresh_time = now().strftime("%Y-%m-%d %H:%M:%S")
        self.task_search(self.taskEntry)


    def open_new_task_dialog(self,w = None):
        passed_data = {"label":self.taskEntry.get_text()}
        self.app.open_new_task_dialog(self, passed_data)


    def tick(self):

        self.session_time.set_label(sec_to_time(self.app.session['duration']))
        if self.app.session['label'] != self.header_task:
            self.recreate_header() 
        
        if utils.taskindex_updated_time() > self.search_cache_refresh_time:
            # print("taskindex was updated,  utils.taskindex_updated_time()", utils.taskindex_updated_time(), 'self.search_cache_refresh_time',self.search_cache_refresh_time)
            self.refresh_search_cache()
        # else:
        #     print("taskindex was not updated",current_data_version)

        return True # This continues the timer


    def recreate_header(self,widget = None):
        self.header.foreach(lambda child: child.destroy()) 
        self.header_task = self.app.session['label']

        self.set_title(conf.app_name +"ing on "+self.header_task+"!")

        self.session_time = Gtk.Label(sec_to_time(self.app.session['duration']))

        if self.app.is_running == True: 

            self.session_label = Gtk.Button(label=self.header_task)
            self.session_label.set_relief(Gtk.ReliefStyle.NONE)
            self.session_label.connect("clicked", self.app.open_session_options_dialog)
            self.session_label.set_property("tooltip-text", "Edit session")

            self.header.pack_start(self.session_label, False, False, 0)
            self.header.pack_start(self.session_time, False, False, 0)


            # Header notes field
            # Herumph. So much work (and it even works!) but... never used. and UGLY!  :( 
            # self.notes_text_buffer = Gtk.TextBuffer()
            # if 'notes' in self.app.session:
            #     self.notes_text_buffer.set_text(self.app.session['notes'])
            # self.notes_text_buffer.connect("changed", self.on_notes_changed)
            # self.notes = Gtk.TextView(buffer=self.notes_text_buffer)
            # self.notes.set_size_request(300,25)
            # self.header.add(self.notes)


            # Padding
            self.header.pack_start(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15, border_width=10),True, True, 0)

            pause_button = Gtk.Button()
            pause_button.set_image(Gtk.Image.new_from_file(os.path.abspath('icon/pause.png')))
            pause_button.connect("clicked", self.app.stop_task)
            pause_button.connect("clicked", self.recreate_header)

            pause_button.connect("clicked", self.refresh_search_cache) 
            pause_button.set_property("tooltip-text", "Pause Task (Ctrl + P)")
            pause_button.set_relief(Gtk.ReliefStyle.NONE)
            self.header.add(pause_button)

            done_button = Gtk.Button()
            done_button.set_image(Gtk.Image.new_from_file(os.path.abspath('icon/mark-done.png')))
            done_button.set_property("tooltip-text", "Mark Task Done (Ctrl + D)")
            done_button.connect("clicked", self.app.stop_task,'mark_done')
            done_button.connect("clicked", self.recreate_header)
            done_button.connect("clicked", self.refresh_search_cache) # doesn't work, probably because it happens before stop_task 
            done_button.set_relief(Gtk.ReliefStyle.NONE)
            self.header.add(done_button)


            cancel_button = Gtk.Button()
            cancel_button.set_image(Gtk.Image.new_from_file(os.path.abspath('icon/cancel.png'))) 
            cancel_button.connect("clicked", self.app.stop_task,"cancel")
            cancel_button.connect("clicked", self.recreate_header)
            cancel_button.set_property("tooltip-text", "Discard timer (Ctrl + X)")
            cancel_button.set_relief(Gtk.ReliefStyle.NONE)
            self.header.add(cancel_button)

            key, mod = Gtk.accelerator_parse('<Control>p')
            pause_button.add_accelerator("clicked", self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)

            key, mod = Gtk.accelerator_parse('<Control>x')
            cancel_button.add_accelerator("clicked", self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)

            key, mod = Gtk.accelerator_parse('<Control>d')
            done_button.add_accelerator("clicked", self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)                

        else:
            lines = conf.user['prompts'].split("\n")
            p = lines.pop(0)
            lines.append(p)
            conf.user['prompts'] = "\n".join(lines)

            
            # self.header.set_orientation(Gtk.Orientation.VERTICAL)

            self.header.pack_start(Gtk.Box(), True, True, 0) # Spacer

            self.the_question = Gtk.Label(p)
            self.the_question.set_name("RelevantQuestion")
            self.header.add(self.the_question)
            # self.header.pack_start(self.the_question, True, True, 0)

            if (int(self.app.session['duration']) / 60) > conf.user['randomness_interrupt_interval']:
                self.header.add(self.session_time)

            self.header.pack_end(Gtk.Box(), True, True, 0) # Spacer
            

        self.header.show_all()

        try:
            self.taskEntry.grab_focus()
        except Exception: 
            pass
        
    def on_notes_changed(self,buffer):
       notes = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
       self.app.session['notes'] = notes
       print(self.app.session['notes'])


    def pause_then(self, widget = None, last_active_time = None):
        self.app.stop_task(None,"save",last_active_time)
        self.recreate_header()
        self.refresh_search_cache()


    def task_search(self,widget):

        self.tasks_box.foreach(lambda child: child.destroy()) 
        self.tasks_box.show_all()
        self.shown_tasks.clear()

        self.search_term = i = widget.get_text()

        # utils.dbg({"task search":i},s='taskwindow')
        if i in self.search_cache:
            tasks = self.search_cache[i]
        else:
            tasks = utils.taskindex_search(i)
            self.search_cache[i] = tasks

        total_duration = 0
        self.lazy_loadable_tasks = {}

        if tasks:
            count = 0
            for id, t in tasks.items():
                count = count + 1
                if 'duration' in t and t['duration']:
                    total_duration += int(t['duration'])

                if count < self.num_initial_tasks:
                    self.add_task_to_list(t)
                else:
                    self.lazy_loadable_tasks[id] = t

            self.tasks_box.show_all()

        self.total_duration_label.set_markup('<b>'+str(round(total_duration / 60 / 60,1))+'</b> hrs\n'+conf.user['hours_search_timeframe'] )



    def add_task_to_list(self,t):

        try:
            search_str = self.search_term
            utils.dbg("add_task_to_list "+ str(t['extended_label']), "status",t['status'], s='taskwindow',l=3)

            # self.shown_tasks[t['id']] = Gtk.Button() # Works but does not accept popovers
            self.shown_tasks[t['id']] = Gtk.MenuButton(popover=self.task_rclick_menu) 
            self.shown_tasks[t['id']].set_halign(Gtk.Align.START)
            self.shown_tasks[t['id']].set_hexpand(True)

            label = Gtk.Label()

            # button_context = self.shown_tasks[t['id']].get_style_context().add_class("large")
            extended_label = GLib.markup_escape_text(t['extended_label'],)
            
            if len(search_str) > 1:
                
                # fts5 match highlighting, not that good because it highlights the whole word rather than the matching part...
                # extended_label = extended_label.replace('[[',"<b>").replace(']]',"</b>")

                extended_label = extended_label.replace(search_str,"<b>"+search_str+"</b>")
                extended_label = extended_label.replace(search_str.capitalize(),"<b>"+search_str.capitalize()+"</b>") # Cheesy
            
            if "duration" in t and t['duration']:
                extended_label += " ("+sec_to_time(t['duration'])+")"

            if t['id'] in conf.user['task_commands'] and conf.user['task_commands'][t['id']]['status']:
                extended_label += " ["+GLib.markup_escape_text(conf.user['task_commands'][t['id']]['command'])+"]"

            if t['priority']:
                extended_label = str(t['priority']) +" "+ extended_label

            if not t['status']:
                # utils.dbg("add strikethrough to done task "+t['extended_label'],l=3,s="taskwindow")
                # button_context.add_class("done")
                label.set_markup('<s>'+extended_label+'</s>')

            elif t['priority'] > 0:
                label.set_name('priorityTask')
                label.set_markup(extended_label)
            else:
                label.set_markup(extended_label)

            self.shown_tasks[t['id']].add(label)

            # self.shown_tasks[t['id']].set_size_request(955, -1)
            self.shown_tasks[t['id']].connect("button-release-event", self.select_task, t['id'])
            self.shown_tasks[t['id']].connect("activate", self.select_task, None, t['id']) 
            self.shown_tasks[t['id']].set_relief(Gtk.ReliefStyle.NONE)
            self.tasks_box.add(self.shown_tasks[t['id']])
            self.tasks_box.show_all()


        except Exception as e:
            utils.dbg("Error adding task to list"+ str(t['extended_label']), t, e, l=0, s='taskwindow')


    def select_task(self,widget,event=None,tid=None):
        print("select_task task id",tid)
        t = utils.db_get_item_by_id(tid)
        # print('event',event)
        # print("select_task self.modifyer_keys", self.modifyer_keys)

        if self.modifyer_keys['control'] or event and event.button == 3:  # Right-click (button 3)  or control click context menu popover
            
            popover = self.task_rclick_menu
            widget.set_popover(popover)

            popover.foreach(lambda child: child.destroy()) 

            vbox = Gtk.Box(spacing=0, orientation=Gtk.Orientation.VERTICAL)
            vbox.set_border_width(5)
            
            # Open todo
            w = Gtk.Button(label="Open in "+conf.user['todolists'][t['todolist']]['label'])
            w.set_halign(Gtk.Align.START)
            w.set_relief(Gtk.ReliefStyle.NONE)
            w.connect('clicked',utils.open_todo,t)
            vbox.pack_start(w, True, True, 5)

            # mark_done
            w = Gtk.Button(label="Mark done")
            w.set_halign(Gtk.Align.START)
            w.set_relief(Gtk.ReliefStyle.NONE)
            w.connect('clicked',self.app.mark_done,t)
            vbox.pack_start(w, True, True, 5)

            # Reassign session/randomness to be on this task, 
            w = Gtk.Button(label="Reassign last "+ str(round((self.app.session['duration'] / 60),1))+" minutes to this task" )
            w.set_halign(Gtk.Align.START)
            w.set_relief(Gtk.ReliefStyle.NONE)
            w.connect('clicked',self.app.start_task,t,True)
            vbox.pack_start(w, True, True, 5)

            # show/edit targets
            ttt_data = utils.get_time_target_data(t) 
            if ttt_data:
                w = Gtk.Button(label="Edit Target:"+str(ttt_data['type'])+ " "+str(round(ttt_data['value']))+" minutes per "+str(round(ttt_data['within_value']))+" "+str(ttt_data['within_unit'])+"  ("+str(round(utils.check_time_target(t)))+" minutes remaining)")
            else:
                w = Gtk.Button(label="Set Time Target")
            w.set_halign(Gtk.Align.START)
            w.set_relief(Gtk.ReliefStyle.NONE)
            w.connect('clicked', lambda button_widget: EditAddTargetDialog(self,'tasks', t['id']))
            vbox.pack_start(w, True, True, 5)


            # show/edit commands
            if t['id'] in conf.user['task_commands']:
                command_data = conf.user['task_commands'][t['id']]
                if not command_data['status']:
                    disabled = "(disabled)"
                else:
                    disabled = ""

                w = Gtk.Button(label="Edit Command: '"+command_data['command']+"' "+disabled+"")
            else:
                w = Gtk.Button(label="Add Task Command")

            w.set_halign(Gtk.Align.START)
            w.set_relief(Gtk.ReliefStyle.NONE)
            w.connect('clicked', lambda button_widget: EditTaskCommandDialog(None, self, t['id']))
            vbox.pack_start(w, True, True, 5)


            # get_times, Ugly 
            # for key, val in utils.get_times(t).items():
            #     vbox.pack_start(Gtk.Label(key+": "+val), True, True, 5)

            popover.add(vbox)
            popover.set_position(Gtk.PositionType.BOTTOM)
            popover.show_all()

            return

        if self.modifyer_keys['shift']:
            print('transfer session')
            self.app.start_task(None,t,True) 
        elif self.modifyer_keys['alt']:
            print('open_todo')
            utils.open_todo(None,t)
        else:
            self.app.start_task(None,t) 

        self.destroy()


    def timesheet_to_clipboard(self,widget = None):

        search_term = self.taskEntry.get_text()
        tasks = self.search_cache[search_term]

        print("timesheet for "+search_term, len(tasks))
        dbg("timesheet for "+search_term, len(tasks),l=1,s='taskwindow')

        o = '"Project","Task","Hours"\n'  
        total_hours = 0

        for t_id, t in tasks.items():
            if t['duration']:

                t_data = utils.db_get_item_by_id(t_id)
                rounded_hours = round(force_number(t['duration']) / 60 / 60, 3)
                total_hours += rounded_hours

                o +=  '"'+str(t_data['parent_label'])+'","'+str(t_data['label'])+'","'+str(rounded_hours)+'"\n'
        

        o +=  ", Total,"+str(total_hours)+"\n"

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(o, -1)
        clipboard.store()
        error_notice("Timesheet for '"+search_term+"' copied to clipboard")


    def toggle_fullscreen(self):

        if self.__is_fullscreen:
            self.unfullscreen()
            self.get_style_context().remove_class("large")
            conf.user['open_task_window_fullscreen'] = False

        else:
            self.fullscreen()
            self.get_style_context().add_class("large")
            conf.user['open_task_window_fullscreen'] = True

        utils.save_user_settings()


    def key_release(self, widget, event):
        key = Gdk.keyval_name(event.keyval)
        # utils.dbg("key_release",key,s="taskwindow",l=1)
        # utils.dbg("key_release event.state",event.state,s="taskwindow",l=1)
        if (event.state & Gdk.ModifierType.CONTROL_MASK):
            self.modifyer_keys['control'] = False
        if (event.state & Gdk.ModifierType.SHIFT_MASK):
            self.modifyer_keys['shift'] = False        
        if (event.state & Gdk.ModifierType.MOD1_MASK):
            self.modifyer_keys['alt'] = False
        
        
        # print("modifyer_keys",self.modifyer_keys)


    def key_press(self, widget, event):

        key = Gdk.keyval_name(event.keyval)
        # utils.dbg("key_press",key,s="taskwindow",l=1)
        # utils.dbg("key_press event.state",event.state,s="taskwindow",l=1)
        # utils.dbg("key_press_event",event,s="taskwindow",l=1)
        # utils.dbg("ModifierType is CONTROL_MASK",Gdk.ModifierType.CONTROL_MASK,s="taskwindow",l=3)
        
        if (event.state & Gdk.ModifierType.CONTROL_MASK) or key == 'Control_L':
            self.modifyer_keys['control'] = True        
        if (event.state & Gdk.ModifierType.SHIFT_MASK) or key == 'Shift_L':
            self.modifyer_keys['shift'] = True        
        if (event.state & Gdk.ModifierType.MOD1_MASK) or key == 'Alt_L':
            self.modifyer_keys['alt'] = True

        # print("modifyer_keys", self.modifyer_keys)


        if key == "F11":
            self.toggle_fullscreen()
        elif key == "Escape":
            self.destroy()
        elif key in ['l','f'] and (event.state & Gdk.ModifierType.CONTROL_MASK) and not self.taskEntry.is_focus():
            self.taskEntry.grab_focus()

        elif key == "Return":
            # print('self.get_focus()',self.get_focus())
            # print('self.tasks_box.get_children()[1]',self.tasks_box.get_children()[1])
            if self.taskEntry.is_focus():
                # print("self.taskEntry has focus, do the thing")
                if self.shown_tasks:
                    self.tasks_box.get_children()[0].emit('activate')
                else:
                    self.new_task_button.emit('clicked')
            
            elif self.shown_tasks and self.get_focus() in self.tasks_box.get_children():
                # print("Return pressed on shown task select it",self.get_focus())
                self.get_focus().emit('activate')


    def on_window_state_event(self, widget, event):
        self.__is_fullscreen = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)

