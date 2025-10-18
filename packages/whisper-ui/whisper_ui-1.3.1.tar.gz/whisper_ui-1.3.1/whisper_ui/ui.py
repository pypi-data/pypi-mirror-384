import os
import sys
import re
import glob
import time
import threading
from functools import partial
import warnings
import tkinter as tk
from tkinter import *
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename, askdirectory
from tkinterdnd2 import TkinterDnD, DND_ALL

import ssl
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import faster_whisper

from whisper_ui.whisper_funcs import AVAILABLE_MODELS, ModelInterface
from whisper_ui.handle_prefs import set_option, check_model, USER_PREFS, AVAILABLE_LANGUAGES

if 'None' not in AVAILABLE_LANGUAGES:
    AVAILABLE_LANGUAGES = ['None'] + AVAILABLE_LANGUAGES

warnings.filterwarnings('ignore')

app = None
mi = None
switch_model = False
TABS = 2

WINDOWS_FFMPEG_LINK = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-lgpl.zip'
LINUX_FFMPEG_LINK = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-lgpl.tar.xz'
LINUX_ARM_FFMPEG_LINK = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-lgpl.tar.xz'
MAC_FFMPEG_LINK = 'https://evermeet.cx/ffmpeg/getrelease/zip'

def check_ffmpeg(log=True):
    try:
        os.system('ffmpeg -version')
    except:
        if log:
            print(f'ffmpeg not found.')
        return False
    if log:
        print('ffmpeg found.')
    return True

def ffmpeg_download():
    if not check_ffmpeg(False):
        result = messagebox.askokcancel(
            'Confirm ffmpeg download',
            f'Would you like to download and install ffmpeg?'
        )
        if result:
            print(f'Downloading ffmpeg...')
            
            # if windows
            if os.name == 'nt':
                # download zip to downloads
                os.system(f'start {WINDOWS_FFMPEG_LINK}')
                # extract to C:\Program Files\ffmpeg
                os.system('powershell.exe Expand-Archive -Path "$env:USERPROFILE\Downloads\ffmpeg-master-latest-win64-lgpl.zip" -DestinationPath "C:\Program Files"')
                # add to path
                os.system('setx path "%path%;C:\Program Files\ffmpeg\bin"')
            # if linux
            elif os.name == 'posix':
                # download tar to downloads
                os.system(f'wget {LINUX_FFMPEG_LINK} -O ~/Downloads/ffmpeg.tar.xz')
                # extract to /usr/local/bin
                os.system('tar -xf ~/Downloads/ffmpeg.tar.xz -C /usr/local/bin')
                # add to path
                os.system('echo "export PATH=$PATH:/usr/local/bin/ffmpeg" >> ~/.bashrc')
            # if mac
            elif os.name == 'mac':
                # download zip to downloads
                os.system(f'open {MAC_FFMPEG_LINK}')
                # extract to /usr/local/bin
                os.system('unzip ~/Downloads/ffmpeg-master-latest-win64-lgpl.zip -d /usr/local/bin')
                # add to path
                os.system('echo "export PATH=$PATH:/usr/local/bin/ffmpeg" >> ~/.bash_profile')
            
            print(f'Downloaded ffmpeg successfully. Reloading window...\n')
            time.sleep(1)
            reload()
        else:
            print(f'Download canceled.\n')
    else:
        print(f'ffmpeg already downloaded.\n')

def raw(text: str) -> str:
    text = text.replace('\\t', '\t')
    return text

def unraw(text: str) -> str:
    text = text.replace('\t', '\\t')
    return text

def save_template_options(entries):
    (text_template_entry,
    text_insertion_symbol_entry,
    segmentation_template_entry,
    segment_insertion_symbol_entry,
    start_time_insertion_symbol_entry,
    end_time_insertion_symbol_entry) = entries
    
    print('Template options saved.\n')
    set_option('text_template', raw(text_template_entry.get()), False)
    set_option('text_insertion_symbol', raw(text_insertion_symbol_entry.get()))
    set_option('segmentation_template', raw(segmentation_template_entry.get()), False)
    set_option('segment_insertion_symbol', raw(segment_insertion_symbol_entry.get()), False)
    set_option('start_time_insertion_symbol', raw(start_time_insertion_symbol_entry.get()), False)
    set_option('end_time_insertion_symbol', raw(end_time_insertion_symbol_entry.get()))
    
def open_template_options():
    win = tk.Toplevel()
    win.wm_title('Template formatting options')
    temp_frame = Frame(win)
    temp_frame.pack(fill=X, expand=False, pady=4, padx=30)

    w = 400 # width for the Tk root
    h = 400 # height for the Tk root
    # get screen width and height
    ws = win.winfo_screenwidth() # width of the screen
    hs = win.winfo_screenheight() # height of the screen
    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2) - 80
    # set the dimensions of the screen
    # and where it is placed
    win.geometry('%dx%d+%d+%d' % (w, h, x, y))
    win.resizable(True, True)
    
    
    text_template_label = Label(
        temp_frame,
        text = "Template for full transcript (.txt file):"
    )
    text_template_entry = Entry(
        temp_frame,
        width=20
    )
    text_template_entry.insert(0, unraw(USER_PREFS['text_template']))
    text_template_label.pack(pady=4)
    text_template_entry.pack(fill=X, expand=True, pady=4)

    
    text_insertion_symbol_label = Label(
        temp_frame,
        text = "Symbol to replace with full transcript (.txt file):"
    )
    text_insertion_symbol_entry = Entry(
        temp_frame,
        width=20
    )
    text_insertion_symbol_entry.insert(0, unraw(USER_PREFS['text_insertion_symbol']))
    text_insertion_symbol_label.pack(pady=4)
    text_insertion_symbol_entry.pack(fill=X, expand=True, pady=4)
    
    
    segmentation_template_label = Label(
        temp_frame,
        text = "Template for each segment (each line in .seg file):"
    )
    segmentation_template_entry = Entry(
        temp_frame,
        width=20
    )
    segmentation_template_entry.insert(0, unraw(USER_PREFS['segmentation_template']))
    segmentation_template_label.pack(pady=4)
    segmentation_template_entry.pack(fill=X, expand=True, pady=4)
    
    
    segment_insertion_symbol_label = Label(
        temp_frame,
        text = "Symbol to replace with segment text in each line (.seg file):"
    )
    segment_insertion_symbol_entry = Entry(
        temp_frame,
        width=20
    )
    segment_insertion_symbol_entry.insert(0, unraw(USER_PREFS['segment_insertion_symbol']))
    segment_insertion_symbol_label.pack(pady=4)
    segment_insertion_symbol_entry.pack(fill=X, expand=True, pady=4)
    
    
    start_time_insertion_symbol_label = Label(
        temp_frame,
        text = "Symbol to replace with start time in each line (.seg file):"
    )
    start_time_insertion_symbol_entry = Entry(
        temp_frame,
        width=20
    )
    start_time_insertion_symbol_entry.insert(0, unraw(USER_PREFS['start_time_insertion_symbol']))
    start_time_insertion_symbol_label.pack(pady=4)
    start_time_insertion_symbol_entry.pack(fill=X, expand=True, pady=4)
    
    
    end_time_insertion_symbol_label = Label(
        temp_frame,
        text = "Symbol to replace with end time in each line (.seg file):"
    )
    end_time_insertion_symbol_entry = Entry(
        temp_frame,
        width=20
    )
    end_time_insertion_symbol_entry.insert(0, unraw(USER_PREFS['end_time_insertion_symbol']))
    end_time_insertion_symbol_label.pack(pady=4)
    end_time_insertion_symbol_entry.pack(fill=X, expand=True, pady=4)
    
    buttons_frame = Frame(win)
    buttons_frame.pack(fill=X, expand=True, pady=4, padx=4)
    entries = (
        text_template_entry,
        text_insertion_symbol_entry,
        segmentation_template_entry,
        segment_insertion_symbol_entry,
        start_time_insertion_symbol_entry,
        end_time_insertion_symbol_entry
    )
    ok_button = Button(buttons_frame, text='Save', command=partial(save_template_options, entries))
    ok_button.pack(padx=26, pady=4, side=RIGHT, expand=True, fill=X)
    close_button = Button(buttons_frame, text='Close', command=win.destroy)
    close_button.pack(padx=26, pady=4, side=RIGHT, expand=True, fill=X)
    
def toggle_txt():
    global app
    app.txt_var.set(not USER_PREFS['do_text'])
    set_option('do_text', not USER_PREFS['do_text'])
    
def toggle_seg():
    global app
    app.seg_var.set(not USER_PREFS['do_segmentation'])
    set_option('do_segmentation', not USER_PREFS['do_segmentation'])
    
def toggle_json():
    global app
    app.json_var.set(not USER_PREFS['do_json'])
    set_option('do_json', not USER_PREFS['do_json'])

def toggle_gpu():
    global app
    global mi
    app.gpu_var.set(not USER_PREFS['use_gpu'])
    set_option('use_gpu', not USER_PREFS['use_gpu'])
    if mi is not None:
        mi.update_device(True)

def toggle_translate():
    global app
    app.translate_var.set(not USER_PREFS['do_translate'])
    set_option('do_translate', not USER_PREFS['do_translate'])

def toggle_use_textgrid():
    global app
    app.textgrid_var.set(not USER_PREFS['use_textgrid'])
    set_option('use_textgrid', not USER_PREFS['use_textgrid'])

def file_choose_wrapper():
    global app
    app.glob_path_entry.delete(0, len(app.glob_path_entry.get()))
    app.glob_path_entry.insert(0, os.path.normpath(askopenfilename()))
    
def dir_choose_wrapper():
    global app
    app.glob_path_entry.delete(0, len(app.glob_path_entry.get()))
    app.glob_path_entry.insert(
        0,
        os.path.normpath(os.path.join(askdirectory(),'*'))
    )
    
def output_dir_choose_wrapper():
    global app
    app.output_dir_entry.delete(0, len(app.output_dir_entry.get()))
    app.output_dir_entry.insert(
        0,
        os.path.normpath(askdirectory())
    )
    set_output_dir_wrapper()
    
def paths_wrapper():
    print(f'Clicking "Transcribe" will process:')
    if ';' in app.glob_path_entry.get():
        paths = app.glob_path_entry.get().split(';')
    else:
        paths = glob.glob(app.glob_path_entry.get())

    if USER_PREFS['use_textgrid']:
        for path in paths:
            print(f'\t{os.path.normpath(path)}')
            path_no_ext = os.path.splitext(path)[0]
            if os.path.exists(path_no_ext + '.TextGrid'):
                print(f'\t{os.path.normpath(path_no_ext + '.TextGrid')}')
            elif os.path.exists(path_no_ext + '.textgrid'):
                print(f'\t{os.path.normpath(path_no_ext + '.textgrid')}')
            else:
                print(f'\tWarning: Could not find a matching textgrid file.')
    else:
        for path in paths:
            print(f'\t{os.path.normpath(path)}')

    print()

def transcribe_wrapper():
    global app
    global mi
    global switch_model
    set_output_dir_wrapper(log=False)
    
    if mi is None:
        mi = ModelInterface()
        
    text = app.glob_path_entry.get()    
    
    if ';' in text:
        files = text.split(';')
    else:
        files = glob.glob(text)
    
    mi.transcribe(files, switch_model)
    
def set_output_dir_wrapper(log=True):
    global app
    new_value = app.output_dir_entry.get()
    set_option('output_dir', new_value)
    p = os.path.normpath(os.path.abspath(new_value))
    if log:
        print(f'Outputs will be written to "{p}".\n')
    
def model_select_wrapper(event):
    global app
    global switch_model
    new_value = app.model_clicked.get()
    if USER_PREFS['model'] != new_value:
        switch_model = True
    else:
        switch_model = False
    set_option('model', new_value)
    print(f'Using model "{new_value}".\n')
    
def language_select_wrapper(event):
    global app
    new_value = app.language_clicked.get()
    set_option('language', new_value)
    if new_value == 'None':
        print(f'Detecting language automatically.\n')
    else:
        print(f'Assuming language "{new_value}."\n')
    
def download_model(model_name):
    global TABS
    global app
    TABS = 0
    if not check_model(model_name):
        result = messagebox.askokcancel(
            'Confirm model download',
            f'Would you like to download {model_name}?'
        )
        if result:
            print(f'Downloading model {model_name}...')
            
            # Define the download function to run in thread
            def do_download():
                try:
                    faster_whisper.download_model(model_name)
                    print(f'Downloaded model {model_name} successfully. Reloading window...\n')
                    time.sleep(1)
                    # Use after() to safely call reload from main thread
                    app.root.after(0, reload)  # assuming 'root' is your Tk root window
                except Exception as e:
                    print(f'Error downloading model: {e}\n')
                finally:
                    global TABS
                    TABS = 2
            
            # Start download in background thread
            thread = threading.Thread(target=do_download, daemon=True)
            thread.start()
        else:
            print(f'Download canceled.\n')
            TABS = 2
    else:
        print(f'Model {model_name} already downloaded.\n')
        TABS = 2

def reload():
    global app
    app.destroy()
    app = MainGUI()
    app.mainloop()

def drop_file(event):
    global app
    raw_data = event.data.strip()

    # Extract file paths: Matches either {wrapped path} or plain paths
    files = re.findall(r'(\{.*?\})', raw_data)
    
    # remove each match from the raw data
    for file in files:
        raw_data = raw_data.replace(file, '')
        
    # split on whitespace - default .split() handles multiple spaces/trailing spaces
    files += raw_data.split()
    
    final_files = []
    for i in range(len(files)):
        files[i] = files[i].replace('{', '').replace('}', '').strip()
        if files[i]:
            final_files.append(files[i])
    
    for file in files:
        assert os.path.exists(file), f'File {file} does not exist.'

    # Convert to a semicolon-separated string
    formatted_paths = ";".join(files)

    # Update the entry field
    app.glob_path_entry.delete(0, len(app.glob_path_entry.get()))
    app.glob_path_entry.insert(0, formatted_paths)

class PrintLogger(object):  # create file like object

    def __init__(self, textbox: ScrolledText):  # pass reference to text widget
        self.textbox = textbox  # keep ref
        self.textbox.configure(state="disabled")

    def write(self, text):
        global TABS
        if not text:  # Skip empty strings
            return
            
        self.textbox.configure(state="normal")

        if '\r' in text:
            # Handle carriage return - delete current line and replace
            self.textbox.delete("end-1c linestart", "end-1c")
            # Remove the \r from the text before inserting
            text = '\t' * TABS + text.replace('\r', '')
        
        self.textbox.insert("end", text)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
        self.textbox.update()
        
    def clear(self):
        self.textbox.configure(state='normal')
        self.textbox.delete('1.0', tk.END)
        self.textbox.configure(state='disabled')

    def flush(self):  # needed for file like object
        self.textbox.update()

    def isatty(self):  # ADD THIS METHOD
        return True
    


class MainGUI(TkinterDnD.Tk):

    def __init__(self):
        TkinterDnD.Tk.__init__(self)
        # window

        self.version = '1.3.1'

        self.title(f"Whisper User Interface v.{self.version}")
        w = 1067 # width for the Tk root
        h = 600 # height for the Tk root
        # get screen width and height
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen
        # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2) - 40
        # set the dimensions of the screen
        # and where it is placed
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.resizable(True, True)
        
        
        # menu
        self.menu = Menu(self)
        
        self.file_menu = Menu(self.menu, tearoff=False)
        self.file_menu.add_command(label='Open file', command=file_choose_wrapper)
        self.file_menu.add_command(label='Open audio directory', command=dir_choose_wrapper)
        self.file_menu.add_command(label='Choose output directory', command=output_dir_choose_wrapper)
        
        self.models_menu = Menu(self.menu, tearoff=False)
        for model_name in AVAILABLE_MODELS:
            if check_model(model_name):
                self.models_menu.add_command(
                    label=model_name + ' ✓',
                    command=partial(download_model, model_name)
                )
            else:
                self.models_menu.add_command(
                    label=model_name + ' ⤓',
                    command=partial(download_model, model_name)
                )
                
        self.debug_menu = Menu(self.menu, tearoff=False)
        self.debug_menu.add_command(label='Reload window', command=reload)
        
        self.deps_menu = Menu(self.menu, tearoff=False)
        self.deps_menu.add_command(
            label='Check for ffmpeg',
            command=check_ffmpeg
        )
        self.deps_menu.add_command(
            label='Install ffmpeg',
            command=ffmpeg_download
        )
        
        self.menu.add_cascade(label='File', menu=self.file_menu)
        self.menu.add_cascade(label='Download models', menu=self.models_menu)
        self.menu.add_cascade(label='Debug', menu=self.debug_menu)
        self.menu.add_cascade(label='Dependencies', menu=self.deps_menu)
        self.config(menu=self.menu)
        
        
        
        # frames
        self.root = Frame(self)
        self.root.pack(padx=4, pady=4)
        
        
        
        # log console
        self.log_console_frame = Frame(self)
        self.log_widget = ScrolledText(
            self.log_console_frame,
            height=4,
            width=20,
            font=("consolas", "10", "normal")
        )
        self.logger = PrintLogger(self.log_widget)
        sys.stdout = self.logger
        sys.stderr = self.logger
        self.clear_log_button = Button(
            self.log_console_frame,
            text = "Clear output",
            fg = "black",
            command = self.logger.clear
        )
        self.log_console_frame.pack(fill=BOTH, expand=True)
        self.log_widget.pack(fill=BOTH, expand=True)
        self.clear_log_button.pack(pady=4)
        
        
        
        # file path entry
        self.file_path_entry_frame = Frame(self)
        self.glob_path_desc = Label(
            self.file_path_entry_frame,
            text = "File path(s) to transcribe (type, drag, or File > Open): "
        )
        self.glob_path_entry = Entry(
            self.file_path_entry_frame,
            width=20
        )
        self.glob_path_entry.drop_target_register(DND_ALL)
        self.glob_path_entry.dnd_bind("<<Drop>>", lambda event: drop_file(event))
        self.glob_path_entry.insert(0, os.path.join('test_audio', '*.m4a'))
        self.transcribe_button = Button(
            self.file_path_entry_frame,
            text = "Transcribe",
            fg = "red",
            command = transcribe_wrapper
        )
        # list file paths in glob
        self.list_files_button = Button(
            self.file_path_entry_frame,
            text = "List files",
            fg = "black",
            command = paths_wrapper
        )
        self.file_path_entry_frame.pack(pady=4, fill=X, expand=False)
        self.glob_path_desc.pack(padx=4, side=LEFT)
        self.glob_path_entry.pack(padx=4, side=LEFT, fill=X, expand=True)
        self.list_files_button.pack(side=LEFT, padx=4)
        self.transcribe_button.pack(side=LEFT, padx=4)
        
        
        
        # edit output_dir
        self.output_dir_frame = Frame(self)
        self.output_dir_desc = Label(
            self.output_dir_frame,
            text = "Change output directory:"
        )
        self.output_dir_entry = Entry(
            self.output_dir_frame,
            width=20
        )
        self.output_dir_entry.insert(0, USER_PREFS['output_dir'])
        self.set_output_dir_button = Button(
            self.output_dir_frame,
            text = "Set output directory",
            fg = "black",
            command = set_output_dir_wrapper
        )
        self.output_dir_frame.pack(pady=4, fill=X, expand=False)
        self.output_dir_desc.pack(side=LEFT, padx=4)
        self.output_dir_entry.pack(side=LEFT, padx=4, fill=X, expand=True)
        self.set_output_dir_button.pack(side=LEFT, padx=4)
        
        
        
        # output options
        self.output_options_frame = Frame(self)
        self.txt_var = BooleanVar()
        self.do_txt_tickbox = Checkbutton(
            self.output_options_frame,
            variable=self.txt_var,
            text = "Output plain transcript txt?",
            command = toggle_txt
        )
        if USER_PREFS['do_text']:
            self.txt_var.set(True)
            self.do_txt_tickbox.select()
        self.seg_var = BooleanVar()
        self.do_seg_tickbox = Checkbutton(
            self.output_options_frame,
            variable=self.seg_var,
            text = "Output segmentation file?",
            command = toggle_seg
        )
        if USER_PREFS['do_segmentation']:
            self.seg_var.set(True)
            self.do_seg_tickbox.select()
        self.json_var = BooleanVar()
        self.do_json_tickbox = Checkbutton(
            self.output_options_frame,
            variable=self.json_var,
            text = "Output full JSON output?",
            command = toggle_json
        )
        if USER_PREFS['do_json']:
            self.json_var.set(True)
            self.do_json_tickbox.select()
        self.gpu_var = BooleanVar()
        self.use_gpu_tickbox = Checkbutton(
            self.output_options_frame,
            variable=self.gpu_var,
            text = "Use GPU?",
            command = toggle_gpu
        )
        if USER_PREFS['use_gpu']:
            self.gpu_var.set(True)
            self.use_gpu_tickbox.select()
        self.textgrid_var = BooleanVar()
        self.use_textgrid_tickbox = Checkbutton(
            self.output_options_frame,
            variable=self.textgrid_var,
            text = "Use TextGrid?",
            command = toggle_use_textgrid
        )
        if USER_PREFS['use_textgrid']:
            self.textgrid_var.set(True)
            self.use_textgrid_tickbox.select()
        self.template_options_button = Button(
            self.output_options_frame,
            text = "Template formatting options...",
            fg = "black",
            command = open_template_options
        )
        self.output_options_frame.pack(pady=4)
        self.do_txt_tickbox.pack(side=LEFT, padx=4)
        self.do_seg_tickbox.pack(side=LEFT, padx=4)
        self.do_json_tickbox.pack(side=LEFT, padx=4)
        self.use_gpu_tickbox.pack(side=LEFT, padx=4)
        self.use_textgrid_tickbox.pack(side=LEFT, padx=4)
        self.template_options_button.pack(side=LEFT, padx=4)
        
        
        
        # select model and language
        self.select_model_language_frame = Frame(self)
        self.model_clicked = StringVar()
        self.model_clicked.set(USER_PREFS['model'])
        self.select_model_desc = Label(
            self.select_model_language_frame,
            text = 'Currently selected Whisper model:'
        )
        self.select_model_entry = ttk.Combobox(
            self.select_model_language_frame,
            textvariable=self.model_clicked,
            values=AVAILABLE_MODELS
        )
        self.select_model_entry.current(AVAILABLE_MODELS.index(USER_PREFS['model']))
        self.select_model_entry['state'] = 'readonly'
        self.select_model_entry.bind(
            '<<ComboboxSelected>>', model_select_wrapper
        )
        self.language_clicked = StringVar()
        self.language_clicked.set(USER_PREFS['language'])
        self.select_language_desc = Label(
            self.select_model_language_frame,
            text = 'Currently selected Whisper language:'
        )
        self.select_language_entry = ttk.Combobox(
            self.select_model_language_frame,
            textvariable=self.language_clicked,
            values=AVAILABLE_LANGUAGES
        )
        self.select_language_entry.current(AVAILABLE_LANGUAGES.index(USER_PREFS['language']))
        self.select_language_entry['state'] = 'readonly'
        self.select_language_entry.bind(
            '<<ComboboxSelected>>', language_select_wrapper
        )
        self.translate_var = BooleanVar()
        self.do_translate_tickbox = Checkbutton(
            self.select_model_language_frame,
            text = "Translate to English?",
            command = toggle_translate
        )
        if USER_PREFS['do_translate']:
            self.translate_var.set(True)
            self.do_translate_tickbox.select()
        self.select_model_language_frame.pack(pady=4)
        self.select_model_desc.pack(side=LEFT, padx=4)
        self.select_model_entry.pack(side=LEFT, padx=4)
        self.select_language_desc.pack(side=LEFT, padx=4)
        self.select_language_entry.pack(side=LEFT, padx=4)
        self.do_translate_tickbox.pack(side=LEFT, padx=4)
        
        


def main():
    # breakpoint()
    global app
    app = MainGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
