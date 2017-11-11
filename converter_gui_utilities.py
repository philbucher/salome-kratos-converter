'''
  ___   _   _    ___  __  __ ___    _  _____    _ _____ ___  ___  
 / __| /_\ | |  / _ \|  \/  | __|__| |/ / _ \  /_\_   _/ _ \/ __| 
 \__ \/ _ \| |_| (_) | |\/| | _|___| ' <|   / / _ \| || (_) \__ \ 
 |___/_/ \_\____\___/|_|  |_|___|  |_|\_\_|_\/_/ \_\_| \___/|___/ 
  / __|___ _ ___ _____ _ _| |_ ___ _ _                            
 | (__/ _ \ ' \ V / -_) '_|  _/ -_) '_|                           
  \___\___/_||_\_/\___|_|  \__\___|_|                             
                                                                  

Salome to Kratos Converter
Converts *.dat files that contain mesh information to *.mdpa file to be used as input for Kratos Multiphysics.
Author: Philipp Bucher
Chair of Structural Analysis
June 2017
Intended for non-commercial use in research
'''

### TODO list ###
# sort selection window by entities (nodes, elements, conditions)

VERSION = 1.1
PREV_USED_DIR = "."

# Python imports
import sys
import tkinter as tk
from tkinter import filedialog
from os.path import splitext, basename, dirname, isfile, isdir

# Project imports
import global_utilities as global_utils


conv_scheme_file_ending = ".conv.scheme.json"
conv_project_file_ending = ".conv.proj.json"



# Functions related to Window
def BringWindowToFront(window):
    window.lift()
    window.attributes('-topmost', 1)
    window.focus_force() # Forcing the focus on the window, seems to be not the nicest solution but it works
    window.after_idle(window.attributes,'-topmost',False) # TODO check under Windows


def MaximizeWindow(window):
    # TODO check which one works for MacOS
    if (global_utils.GetOS() == "linux"):
        window.attributes('-zoomed', True)
    else:   
        window.state('zoomed')


def CloseWindow(window, master):
    window.destroy()
    if master is not None:
        master.SetChildWindowIsClosed()


# Functions related to Files
def GetFilePathOpen(FileType, name=""):
    file_path = ""
    valid_file = False
    if name is not "":
        name = " for: " + name

    initial_directory = GetInitialDirectory()
        
    if (FileType == "dat"):
        file_path = tk.filedialog.askopenfilename(initialdir=initial_directory, title="Open file" + name,filetypes=[("salome mesh","*.dat")])
    elif (FileType == conv_project_file_ending):
        file_path = tk.filedialog.askopenfilename(initialdir=initial_directory, title="Open file" + name,filetypes=[("converter files","*" + conv_project_file_ending)])
    elif (FileType == conv_scheme_file_ending):
        file_path = tk.filedialog.askopenfilename(initialdir=initial_directory, title="Open file" + name,filetypes=[("converter files","*" + conv_scheme_file_ending)])
    else:
        print("Unsupported FileType") # TODO make messagebox
    
    if file_path not in ["", ()]: # () is the output of a cancelled file open dialog
        valid_file = FileExists(file_path)
        global_utils.LogDebug("File Path: " + file_path)
        if valid_file:
            SetInitialDirectory(file_path)
    
    return file_path, valid_file


def FileExists(file_path):
    return isfile(file_path)


def GetFilePathSave(FileType):
    file_path = ""

    initial_directory = GetInitialDirectory()

    if (FileType == "mdpa"):
        file_path = tk.filedialog.asksaveasfilename(initialdir=initial_directory, title="Select file",
                                                    filetypes=[("mdpa files","*.mdpa")])
        if file_path: # check if a file path was read (i.e. if the file-selection was NOT aborted)
            if not file_path.endswith(".mdpa"):
                file_path += ".mdpa"
            SetInitialDirectory(file_path)
    else:
        print("Unsupported FileType") # TODO make messagebox

    return file_path


def GetFileName(FilePath):
    return splitext(basename(FilePath))[0]


def GetInitialDirectory():
    global PREV_USED_DIR
    if not isdir(PREV_USED_DIR): # Assign the default in case the directory does not exist (any more)
        PREV_USED_DIR = "."

    return PREV_USED_DIR


def SetInitialDirectory(FilePath):
    global PREV_USED_DIR
    PREV_USED_DIR = dirname(FilePath)


def PrintLogo():
    print('''  ___   _   _    ___  __  __ ___    _  _____    _ _____ ___  ___  
 / __| /_\ | |  / _ \|  \/  | __|__| |/ / _ \  /_\_   _/ _ \/ __| 
 \__ \/ _ \| |_| (_) | |\/| | _|___| ' <|   / / _ \| || (_) \__ \ 
 |___/_/ \_\____\___/|_|  |_|___|  |_|\_\_|_\/_/ \_\_| \___/|___/ 
  / __|___ _ ___ _____ _ _| |_ ___ _ _                            
 | (__/ _ \ ' \ V / -_) '_|  _/ -_) '_|                           
  \___\___/_||_\_/\___|_|  \__\___|_|  ''')
    print("   VERSION", VERSION)

