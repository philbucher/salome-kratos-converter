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

# Python imports
import tkinter as tk
from tkinter import messagebox
#from tkinter import filedialog
from tkinter import ttk
import logging
try: # ujson is much faster in file saving and a bit faster in file opening. Install in Ubuntu with: "sudo apt-get install python3-ujson"
    import ujson as json
    logging.info("Using ujson-module")
except ImportError:
    import json
    logging.info("Using json-module")
import time

# Project imports
import converter_utilities as utils


class BaseWindow(): # This is the base class for all window classes
    def __init__(self, window, window_title, master=None):
        self.window = window
        self.child_window_open = False
        self.window.protocol('WM_DELETE_WINDOW', self.CloseWindow) # Overwrite the closing behavior
        self.window.wm_title(window_title)
        utils.BringWindowToFront(self.window)
        
        self.is_root = False
        if master is None:
            self.is_root = True
        self.master = master

        if not self.is_root:        
            self.master.SetChildWindowIsOpen()
            
        self.window.bind("<Escape>", lambda event: self.CloseWindow())


    def GetWindow(self):
        return self.window


    def CloseWindow(self):
        utils.CloseWindow(self.window, self.master)


    def SetChildWindowIsOpen(self):
        self.child_window_open = True
    

    def SetChildWindowIsClosed(self):
        self.child_window_open = False


    def PlotCmdOutput(self, String, color):
        self.master.PlotCmdOutput(String, color)
        utils.BringWindowToFront(self.window)


    def OpenChildWindow(self, child_create_function, args=None):
        if self.child_window_open:
            self.PlotCmdOutput("Only one window can be open at a time", "red")
            try:
                utils.BringWindowToFront(self.child_window_object.GetWindow())
            except:
                self.PlotCmdOutput("Couldn't bring existing window to the front", "red")
        else:
            if args is None:
                self.child_window_object = child_create_function()
            else:
                self.child_window_object = child_create_function(args)



# This class is the main WIndow of the GUI
class GUIObject(BaseWindow): # This is the main Window
    def __init__(self, root_window, model_part): # Constructor
        super().__init__(root_window, "SALOME Kratos Converter")

        logging.info("Initializing Main Window")

        self.model_part = model_part        

        utils.MaximizeWindow(self.window)
        
        self._InitializeWidgets()
        
        self.child_window_open = False

        self.window.bind("<Control-n>", lambda event: self._NewProject())
        self.window.bind("<Control-o>", lambda event: self._OpenConverterProject())
        self.window.bind("<Control-s>", lambda event: self._SaveConverterProject(False))
        self.window.bind("<Control-Shift-S>", lambda event: self._SaveConverterProject(True))
        self.window.unbind("<Escape>") # Overwritting the base class behaviour
        
        self.window.bind("<Control-r>", lambda event: self._CreateReadMainMeshWindow())
        self.window.bind("<Control-i>", lambda event: self._ImportConverterScheme())
        self.window.bind("<Control-e>", lambda event: self._ExportConverterScheme())

        self._Initialize()
        
        
    def _InitializeWidgets(self):
        self._SetMenuBar()
        self._SetToolBar()
        self._SetTree()


    def _SetMenuBar(self):
        menubar = tk.Menu(self.window)
                     
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self._NewProject)
        filemenu.add_command(label="Open", command=self._OpenConverterProject)
        filemenu.add_command(label="Save", command=lambda: self._SaveConverterProject(False))
        filemenu.add_command(label="Save as...", command=lambda: self._SaveConverterProject(True))
        filemenu.add_separator()
        filemenu.add_command(label="Import Converter Scheme", command=self._ImportConverterScheme)
        filemenu.add_command(label="Export Converter Scheme", command=self._ExportConverterScheme)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.CloseWindow)
        menubar.add_cascade(label="Project", menu=filemenu)
        
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About...", command=self._ShowAboutInfo)
        menubar.add_cascade(label="Help", menu=helpmenu)
        
        self.window.config(menu=menubar)
        

    def _SetToolBar(self):
        # Create a toolbar
        toolbar = tk.Frame(self.window, bd=1, relief=tk.RAISED)
        toolbar_output = tk.Frame(self.window, bd=1, relief=tk.RAISED)

        b = tk.Button(toolbar, text="Read Mesh", width=14, command=lambda: self.OpenChildWindow(self._CreateReadMainMeshWindow))
        b.pack(side=tk.LEFT, padx=2, pady=2)

        b = tk.Button(toolbar, text="Write MDPA", width=14, command=self._WriteMPDAFile)
        b.pack(side=tk.LEFT, padx=2, pady=2)

        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Creating the filed for Output-Plotting
        self.output_str = tk.StringVar()

        label = tk.Label(toolbar_output, text="Output:")
        label.pack(side=tk.LEFT, padx=2, pady=2)
        self.entry_output=tk.Entry(toolbar_output, textvariable=self.output_str)
        self.entry_output.pack(side=tk.LEFT, expand=1, fill=tk.X)

        toolbar_output.pack(side=tk.TOP, fill=tk.X)


    def _SetTree(self):
        self.tree = ttk.Treeview(self.window, show='tree')
        self.tree.tag_bind("Mesh", "<Double-1>", lambda event : self._EditTreeItem(utils.GetTreeItem(self.tree, event)))
        self.tree.tag_bind("Mesh", "<Delete>", self._DeleteTreeItems)

        self.tree.pack(side=tk.LEFT, fill=tk.Y)
        

    def _Initialize(self):
        self.model_part.Reset()
        self.tree.delete(*self.tree.get_children())
        self.save_file_path = ""
        self.unsaved_changes_exist = False


    def _ResetGUI(self):
        logging.info("Resetted the GUI")
        self._Initialize()


    def GetModelPart(self):
        return self.model_part
    
    
    def SetUnsavedChangesExist(self):
        self.unsaved_changes_exist = True
    
    
    def PlotCmdOutput(self, String, color):
        utils.BringWindowToFront(self.window)
        current_color = self.entry_output.cget("background")
        self.output_str.set(String)
        for i in range(3):
            self.window.after(200, self._ResetColor(color))
            self.window.after(200, self._ResetColor(current_color))


    def _ResetColor(self, Color):
        self.entry_output.config(background=Color)
        self.window.update()

    
    def CloseWindow(self): # override
        if (self.unsaved_changes_exist):
            result = messagebox.askquestion("Warning", "Unsaved changes exist, exit anyway?", icon='warning')
            if result == 'yes':
                self._CloseMainWindow()
        else:
            self._CloseMainWindow()        


    def _CloseMainWindow(self):
        logging.info("Closing the Main Window")
        self.window.quit() # needed to end the GUI with the plot
        self.window.destroy()


    def _ShowAboutInfo(self):
        messagebox.showinfo("Information", "Salome-Kratos Converter\n" +
                                    "Author: Philipp Bucher\n" +
                                    "Website: https://github.com/philbucher/salome-kratos-converter\n" +
                                    "Version: " + str(utils.VERSION))

    def _NewProject(self):
        # TODO check for unsaved changes and stuff
        if self.child_window_open:
            self.PlotCmdOutput("Close child windows first", "red")
        else:
            self._ResetGUI()
            self.PlotCmdOutput("New project initialized", "orange")


    def _OpenConverterProject(self):
        self._ResetGUI()
        file_path, valid_file = utils.GetFilePathOpen(utils.conv_project_file_ending)
        utils.BringWindowToFront(self.window)
  
        if valid_file:
            serialized_model_part_dict = {}
            try:
                start_time = time.time()
                with open(file_path, "r") as json_file:
                    serialized_model_part_dict = json.load(json_file)

                self.model_part.Deserialize(serialized_model_part_dict)
                self.UpdateMeshTree()
                utils.LogTiming("Open Project", start_time)
                self.PlotCmdOutput("Opened the project", "green")
                logging.info("Opened Project")
            except:
                self.PlotCmdOutput("Opening project from file \"{}\" failed".format(file_path), "red")


    def _SaveConverterProject(self, save_as):
        if len(self.tree.get_children()) == 0:
            self.PlotCmdOutput("Nothing to be saved", "red")
        else:
            if (self.save_file_path == "" or save_as):
                input_save_file_path = tk.filedialog.asksaveasfilename(title="Select file",
                                         filetypes=[("converter files","*" + utils.conv_project_file_ending)])
                
                if input_save_file_path: # A file path was returned
                    if not input_save_file_path.endswith(utils.conv_project_file_ending):
                        input_save_file_path += utils.conv_project_file_ending
    
                    self.save_file_path = input_save_file_path
            
            if self.save_file_path == "":
                self.PlotCmdOutput("File was not saved", "red")
            else:
                start_time = time.time()
                serialized_model_part_dict = self.model_part.Serialize()
                
                # Add general information to file                
                serialized_model_part_dict.update({"general" : utils.GetGeneralInfoDict()})
                
                with open(self.save_file_path, "w") as save_file:
                    if utils.DEBUG:
                        # Do this only for debugging, file size is much larger!   
                        json.dump(serialized_model_part_dict, save_file, sort_keys = True, indent = 4) 
                    else:
                        json.dump(serialized_model_part_dict, save_file)
                
                utils.LogTiming("Save Project", start_time)
                self.PlotCmdOutput("Saved the project", "green")
                self.unsaved_changes_exist = False
                logging.info("Saved Project")


    def _ImportConverterScheme(self):
        self._ResetGUI()
        file_path, valid_file = utils.GetFilePathOpen(utils.conv_scheme_file_ending)
        utils.BringWindowToFront(self.window)

        if valid_file:
            json_dict = {}
            try:
                with open(file_path, "r") as json_file:
                    json_dict = json.load(json_file)
                    if json_dict == {}:
                        self.PlotCmdOutput("Nothing imported", "red")
                    else:
                        corrected_json = {}
                        for file_name in json_dict.keys():
                            if file_name != "general":
                                corrected_json.update({file_name : utils.CorrectMeshDict(json_dict[file_name])})
                    
                        self.OpenChildWindow(self._CreateFileSelectionWindow, corrected_json)
            except:
                self.PlotCmdOutput("Opening scheme from file \"{}\" failed".format(file_path), "red")


    def _ExportConverterScheme(self):
        if len(self.tree.get_children()) == 0:
            self.PlotCmdOutput("Nothing to be exported", "red")
        else:
            input_save_file_path = tk.filedialog.asksaveasfilename(title="Select file",
                                        filetypes=[("converter files","*" + utils.conv_scheme_file_ending)])
            if input_save_file_path:
                if not input_save_file_path.endswith(utils.conv_scheme_file_ending):
                    input_save_file_path += utils.conv_scheme_file_ending
    
                model_part_dict = self.model_part.AssembleMeshInfoDict()
                
                # Add general information to file                
                model_part_dict.update({"general" : utils.GetGeneralInfoDict()})
                
                with open(input_save_file_path, "w") as save_file:
                    json.dump(model_part_dict, save_file, sort_keys = True, indent = 4)
                
                self.PlotCmdOutput("Exported the file", "green")


    def _CreateFileSelectionWindow(self, json_dict):
        return FileSelectionWindow(self, json_dict)

        
    def _CreateReadMainMeshWindow(self):
        return ReadMeshWindow(self)
    
        
    def _EditTreeItem(self, item):
        self.OpenChildWindow(self._CreateReadMainMeshWindowEditItem, item)


    def _CreateReadMainMeshWindowEditItem(self, item):
        smp_name = self.tree.item(item,"text")
        return ReadMeshWindow(self, smp_name) #Is only called if Item has tag "modifyable"
    

    def _DeleteTreeItems(self, event):
        smp_to_remove = []
        for item in self.tree.selection():
            smp_name = self.tree.item(item,"text")
            smp_to_remove.append(smp_name) # Identify SubModelParts by name
            self.tree.delete(item)
            logging.info("Deleted SubModelPart: " + smp_name)

        if len(self.tree.get_children(self.main_tree_item)) == 0: # Everything is deleted, reset ModelPart
            self.tree.delete(self.main_tree_item)
            self.model_part.Reset()
            self.unsaved_changes_exist = False
            self.PlotCmdOutput("ModelPart resetted", "orange")
            logging.info("ModelPart resetted")
        else:
            for smp_name in smp_to_remove:
                self.model_part.RemoveSubmodelPart(smp_name)


    def _WriteMPDAFile(self):
        if self.model_part.GetMeshRead(): # Only write output if a main mesh was read
            writing_successful = False
            mdpa_file_path = utils.GetFilePathSave("mdpa")
            if mdpa_file_path:
                with open(mdpa_file_path,"w") as mdpa_file:
                    writing_successful = self.model_part.WriteMesh(mdpa_file)

            if writing_successful:
                self.PlotCmdOutput("MDPA-file was written successfully!", "green")
            else:
                self.PlotCmdOutput("An error occured while writing the mesh", "red")

        else:
            self.PlotCmdOutput("Please Read a Main Mesh First!", "red")
            
    
    # This function is called from the Child
    def UpdateMeshTree(self, tree_items_dict=None):
        if not tree_items_dict:
            tree_items_dict = self.model_part.AssembleMeshInfoDict()
        self.tree.delete(*self.tree.get_children())
        if len(tree_items_dict) > 0:
            self.main_tree_item = self.tree.insert("", "end", text="Main Mesh", open=True)
            for item in sorted(tree_items_dict.keys()):
                item_values = tree_items_dict[item]
                self.tree.insert(self.main_tree_item, "end", text=item, values=item_values, tag="Mesh")



# This class provides functionalities for reading meshes
class ReadMeshWindow(BaseWindow):
    def __init__(self, master, smp_name=None):
        window = tk.Toplevel(master.GetWindow())
        super().__init__(window, "Read Mesh", master)
        
        self.file_parsed = False
        self.edited_mesh = False
        self.old_smp_name = ""
        
        self._InitializeWidgets()
        
        # In case an existing mesh is edited:
        if smp_name: # This means that an existing mesh is edited
            smp = self.master.GetModelPart().GetSubModelPart(smp_name)
            smp_info_dict = smp.GetInfoDict()
            self._FillInputTree(smp.GetGeomEntites())
            mesh_dict = smp.GetMeshInfoDict()
            self._FillOutputTree(mesh_dict["entity_creation"])
            self.edited_mesh = True
            self.old_smp_name = smp_name
            self.smp_name_var.set(smp_name)
            self.smp_path_var.set(smp_info_dict["smp_file_path"])
            self.write_smp_var.set(mesh_dict["write_smp"])
            
            self.file_name = smp_info_dict["smp_file_name"]
            self.file_path = smp_info_dict["smp_file_path"]

        
    def _InitializeWidgets(self):
        ### Row 1 ###
        # Button for reading the Mesh
        tk.Button(self.window, text="Read Mesh File", width=20, command=self._ReadAndParseMeshFile).grid(
                row=1, column=0, pady=15)

        # CheckBox for selecting if a SubModelPart should be written or not
        self.write_smp_var = tk.IntVar()
        self.write_smp_var.set(1) # Choose to write SubModelPart to file by default
        tk.Checkbutton(self.window, text="Write SubModelPart", variable=self.write_smp_var).grid(
                row=1, column=1, sticky=tk.W)
        
        ### Row 2 ###
        # Label for name of SubModelPart
        tk.Label(self.window, text="Name SubModelPart",justify = tk.LEFT, width=20).grid(
                row=2, column=0, sticky=tk.W+tk.E)
        
        # Entry field for name of SubModelPart
        self.smp_name_var = tk.StringVar()
        tk.Entry(self.window, textvariable=self.smp_name_var).grid(
                row=2, column=1, sticky=tk.W+tk.E)

        ### Row 3 ###
        # Label for file-path of SubModelPart
        tk.Label(self.window, text="Path to SubModelPart",
            justify = tk.LEFT, width=20).grid(row=3, column=0, sticky=tk.W+tk.E)
        # Label for file-path of SubModelPart
        self.smp_path_var = tk.StringVar()
        tk.Label(self.window, textvariable=self.smp_path_var, anchor=tk.W, relief=tk.GROOVE).grid(row=3, column=1, sticky=tk.W+tk.E)
        
        ### Row 4 ###
        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).grid(
                row=4, pady=15, columnspan=2, sticky=tk.W+tk.E)
        
        ### Row 5 ###
        # Labels for tree
        tk.Label(self.window, text="Read Entities:").grid(row=5, column=0)
        tk.Label(self.window, text="Entities to be written to MDPA:").grid(row=5, column=1)
        
        ### Row 6 ###
        # Tree with read entities
        self.tree_input = ttk.Treeview(self.window, show='tree', selectmode='none')
        self.tree_input.grid(row=6, sticky=tk.W, column=0, padx=15, pady=(0,15))
        self.tree_input.tag_bind("clickable", "<Double-1>", lambda event : self.OpenChildWindow(self._CreateEntrySelectionWindow, event))

        # Tree with entities that will be cretated
        self.tree_output = ttk.Treeview(self.window)
        self.tree_output["columns"]=("col_entity_name", "col_property_ID", "col_origin_entity")
        self.tree_output.heading("#0", text="Entity Type")
        self.tree_output.heading("col_entity_name", text="Entity Name")
        self.tree_output.heading("col_property_ID", text="Property ID")
        self.tree_output.heading("col_origin_entity", text="Origin Entity")
        self.tree_output.column("col_entity_name", anchor=tk.W, width=300)
        self.tree_output.column("col_property_ID", anchor=tk.CENTER)
        self.tree_output.column("col_origin_entity", anchor=tk.CENTER)
        self.tree_output.grid(row=6, sticky=tk.E, column=1, padx=15, pady=(0,15))
        self.tree_output.tag_configure("Element", foreground="blue")
        self.tree_output.tag_configure("Condition", foreground="red")
        self.tree_output.tag_bind("modifyable", "<Double-1>", lambda event : self._EditTreeOutputItem(
                                                                              utils.GetTreeItem(self.tree_output, event)))
        self.tree_output.tag_bind("modifyable", "<Delete>", self._DeleteTreeOutputItem)
        
        ### Row 7 ###
        # Buttons for Canceling and Saving
        tk.Button(self.window, text="Cancel", width=20, command=self.CloseWindow).grid(
                row=7, column=0, pady=(0,15))

        tk.Button(self.window, text="Save and Close", width=20, command=self._SaveAndCloseWindow).grid(
                row=7, column=1, pady=(0,15))
        
        
    def _ReadAndParseMeshFile(self):
        file_path, valid_file = utils.GetFilePathOpen("dat")
        utils.BringWindowToFront(self.window)

        if valid_file: # check if file exists
            self.tree_input.delete(*self.tree_input.get_children())
            self.tree_output.delete(*self.tree_output.get_children())

            file_name = utils.GetFileName(file_path)

            valid_file, self.nodes_read, self.geom_entities_read = utils.ReadAndParseFile(file_path)
            if valid_file:
                self._FillInputTree(self.geom_entities_read)
                self.file_parsed = True
                
                self.file_name = file_name
                self.file_path = file_path
                
                self.smp_name_var.set(file_name)
                self.smp_path_var.set(file_path)
            else:
                self.PlotCmdOutput("File is not valid", "red")
            

    def _FillInputTree(self, geom_entities_read):
        self.tree_input.delete(*self.tree_input.get_children())
        self.tree_output.delete(*self.tree_output.get_children())
        
        self.tree_input.insert("", "end", text="Nodes", values=utils.NODE_IDENTIFIER, tags="clickable")
        self.tree_output.insert("", "end", text="Nodes", tags="Node")

        # Keys are in format identifier_name
        if geom_entities_read: # check if geom entities are present
            sorted_keys = sorted(list(geom_entities_read.keys()))

            for salome_identifier in sorted_keys:
                label = utils.GetEntityType(salome_identifier)
                self.tree_input.insert("", "end", text=label, value=salome_identifier, tags="clickable")
            
            
    def _FillOutputTree(self, smp_dict):
        for salome_ID in sorted(smp_dict.keys()):
            for entity_type in sorted(smp_dict[salome_ID].keys()):
                entity_dict = smp_dict[salome_ID][entity_type]
                entity_list = entity_dict.keys()
                
                for entity_name in sorted(entity_list):
                    property_ID = entity_dict[entity_name]
                    item_values = (entity_name, property_ID, utils.GetEntityType(salome_ID))
                    
                    self._InsertTreeOutputItem(entity_type, item_values)
                        

    def _EditTreeOutputItem(self, item):
        self.OpenChildWindow(self._CreateEntrySelectionWindowEditItem, item)


    def _InsertTreeOutputItem(self, entity_type, item_values, item_iid=None):
        if item_iid is None: # Inserting a new item
            item_iid = self.tree_output.insert("", "end")
                
        self.tree_output.item(item_iid, text=entity_type, values=item_values, tag=(entity_type, "modifyable"))


    def _DeleteTreeOutputItem(self, event):
        for item in self.tree_output.selection():
            if self.tree_output.tag_has("modifyable", item):
                self.tree_output.delete(item)


    # Create Child Window
    def _CreateEntrySelectionWindow(self, event): # TODO use utils function
        item = self.tree_input.identify('item', event.x, event.y)
        salome_identifier = int(self.tree_input.item(item,"values")[0])
        return EntrySelectionWindow(self, salome_identifier) # Is only called if Item has tag "clickable"


    # Create Child Window
    def _CreateEntrySelectionWindowEditItem(self, item):
        entity_type = self.tree_output.item(item,"text")
        entity_name = self.tree_output.item(item,"values")[0]
        property_ID = self.tree_output.item(item,"values")[1]
        origin_entity = self.tree_output.item(item,"values")[2]
        salome_identifier = utils.GetSalomeIdentifier(origin_entity)
        return EntrySelectionWindow(self, salome_identifier, [entity_type, entity_name, property_ID, item]) #Is only called if Item has tag "modifyable"


    def _ValidateInput(self):
        valid_input = True

        if not self.smp_name_var.get():
            valid_input = False
            self.PlotCmdOutput("Please enter a SubModelPart Name", "red")
        else:
            if not isinstance(self.smp_name_var.get(), str):
                valid_input = False
                self.PlotCmdOutput("SubModelPart name is not valid", "red")
                
            if self.old_smp_name != self.smp_name_var.get():
                if self.master.GetModelPart().SubModelPartNameExists(self.smp_name_var.get()):
                    self.PlotCmdOutput("SubModelPart name exists already!", "red")
                    valid_input = False

            if not self.edited_mesh:
                if (self.master.GetModelPart().FileNameExists(self.file_name) or 
                    self.master.GetModelPart().FilePathExists(self.file_path)):
                    result = messagebox.askquestion("Warning", "This file might have been read already, continue?", icon='warning')
                    if result == 'no':
                        valid_input = False
                        utils.BringWindowToFront(self.window)

        return valid_input


    def _SaveAndCloseWindow(self):
        if self._ValidateInput():
            smp_info_dict = {}
            smp_info_dict["smp_name"] = self.smp_name_var.get()
            smp_info_dict["smp_file_name"] = self.file_name
            smp_info_dict["smp_file_path"] = self.file_path
            
            mesh_dict = utils.GetDictFromTree(self.tree_output)
            mesh_dict["write_smp"] = self.write_smp_var.get()

            if self.file_parsed and self.edited_mesh: # A mesh was edited but then re-read (overwritten)
                self.master.GetModelPart().RemoveSubmodelPart(self.old_smp_name)
                self.master.GetModelPart().AddMesh(smp_info_dict, mesh_dict, self.nodes_read, self.geom_entities_read)

            if self.file_parsed and not self.edited_mesh: # A mesh was read
                self.master.GetModelPart().AddMesh(smp_info_dict, mesh_dict, self.nodes_read, self.geom_entities_read)
        
            elif not self.file_parsed and self.edited_mesh: # A mesh was edited
                self.master.GetModelPart().UpdateMesh(self.old_smp_name, smp_info_dict, mesh_dict)
        
            self.master.UpdateMeshTree()
            
            self.master.SetUnsavedChangesExist()

            self.CloseWindow()
            
            
    # This function is called from the Child
    def CreateTreeOutputItem(self, origin_entity, entity_type_ID, entity_name, property_ID, item_iid):
        entity_type = ""
        if entity_type_ID == 1: # Element
            entity_type = "Element"
        elif entity_type_ID == 2: # Condition
            entity_type = "Condition"
        else:
            self.PlotCmdOutput("Wrong EntityTypeID", "red")

        item_values = (entity_name, property_ID, origin_entity)
        
        # Check for uniqueness of the entry that should be created
        identical_entry_found = False
        for tree_item in self.tree_output.get_children():
            if self.tree_output.item(tree_item,"text") == entity_type:
                if tree_item != item_iid: # Don't check myself
                    if (self.tree_output.item(tree_item,"values")[0] == entity_name and
                        self.tree_output.item(tree_item,"values")[2] == origin_entity):
                        # Property ID is not checked!!!
                        identical_entry_found = True
                        break # Exit the loop, an identical entry was found, no need to check the other items
        
        # Insert / modify the value, in case it does not  exist yet
        if identical_entry_found:
            self.PlotCmdOutput("This entry exists already!", "red")
        else:
            self._InsertTreeOutputItem(entity_type, item_values, item_iid)
    


# This class provides a window where one can select what Kratos entities
# one wants to create from Salome entities
class EntrySelectionWindow(BaseWindow):
    def __init__(self, master, salome_identifier, arguments=[]):
        window = tk.Toplevel(master.GetWindow())
        super().__init__(window, "Select Type of Entity", master)
        
        self.salome_identifier = salome_identifier
        self._InitializeWidgets()

        self.item_iid = None

        if len(arguments) > 0: # This is executed if an existing entity is modified
            self._SetWidgetEntries(arguments[0], arguments[1], arguments[2])
            self.item_iid = arguments[3]

    
    def _InitializeWidgets(self):
        label_string = "Select Entity for: " + utils.GetEntityType(self.salome_identifier)
        tk.Label(self.window, text=label_string,
            justify = tk.LEFT, relief=tk.GROOVE,
            padx = 20).grid(row=0, column=0, columnspan=3, sticky=tk.W+tk.E)

        tk.Label(self.window, text="""Choose an entity type:""",
            justify = tk.LEFT,
            padx = 20, relief=tk.GROOVE).grid(row=1, column=0, columnspan=2)
        
        # Variable for RadioButtons
        self.rb_var = tk.IntVar()
        self.rb_var.set(1) # Choose "Element" as default
        self.entity_name = tk.StringVar()
        self.property_ID = tk.StringVar()
        self.property_ID.set("0") # Default Property ID is 0

        radio_button_1 = tk.Radiobutton(self.window, 
                    text="Element",
                    padx = 20, 
                    variable=self.rb_var, 
                    value=1,
                    command=self._ResetWidgetEntries)
        radio_button_2 = tk.Radiobutton(self.window, 
                    text="Condition",
                    padx = 20, 
                    variable=self.rb_var, 
                    value=2,
                    command=self._ResetWidgetEntries)
        
        radio_button_1.grid(sticky = tk.W, row=2, column=0, columnspan=2)
        radio_button_2.grid(sticky = tk.W, row=3, column=0, columnspan=2)
    
        ttk.Separator(self.window, orient=tk.HORIZONTAL).grid(
                    row=4, pady=15, columnspan=3, sticky=tk.W+tk.E)
        
        tk.Label(self.window, text="""Name of Entity:""",
            justify = tk.LEFT,
            padx = 20, relief=tk.GROOVE).grid(row=5, column=0, columnspan=2)
        tk.Entry(self.window, textvariable=self.entity_name).grid(row=6, column=0, columnspan=2, sticky=tk.W+tk.E)
        tk.Button(self.window, text="...", command=lambda: self.OpenChildWindow(self._CreateKratosEntitySelectionWindow)).grid(row=6, column=2)
        
        ttk.Separator(self.window, orient=tk.HORIZONTAL).grid(
                    row=7, pady=15, columnspan=3, sticky=tk.W+tk.E)        
        
        tk.Label(self.window, text="""Property ID:""", justify = tk.LEFT,
            padx = 20, relief=tk.GROOVE).grid(row=8, column=0, pady=(0,15))
        tk.Entry(self.window, textvariable=self.property_ID).grid(row=8, column=1, pady=(0,15))

        b = tk.Button(self.window, text="Cancel", width=14, command=self.CloseWindow)
        b.grid(row=9, column=0)

        b = tk.Button(self.window, text="Save and Close", width=14, command=self._SaveAndCloseWindow)
        b.grid(row=9, column=1)


    def _SetWidgetEntries(self, entity_type, entity_name, property_ID):
        if entity_type == "Element":
            self.rb_var.set(1)
        elif entity_type == "Condition":
            self.rb_var.set(2)
        else: # TODO test
            self.rb_var.set(0)
        
        self.entity_name.set(entity_name)
        
        self.property_ID.set(property_ID)


    def _ResetWidgetEntries(self):
        self.entity_name.set("")
        self.property_ID.set("0")

    
    def _GetSelection(self):
        if self.rb_var.get() == 1:
            return utils.ELEMENTS
        else:
            return utils.CONDITIONS


    # Create Child Window
    def _CreateKratosEntitySelectionWindow(self):
        return KratosEntitySelectionWindow(self, self.entity_name, self._GetSelection(), self.salome_identifier)


    def _ValidateInput(self):
        valid_input = True

        # Check Entity Name
        if not self.entity_name.get(): # Field is empty
            valid_input = False
            self.PlotCmdOutput("Please enter an Entity Name", "red")
        else:
            if not isinstance(self.entity_name.get(), str):
                valid_input = False
                self.PlotCmdOutput("Entity name is not valid", "red")
                
        # Check Property ID
        if not self.property_ID.get(): # Field is empty
            valid_input = False
            self.PlotCmdOutput("Please enter a Property ID", "red")
        else:
            prop_ID_entry_str = self.property_ID.get()
            if prop_ID_entry_str.isdigit():
                try:
                    property_ID = int(prop_ID_entry_str)
                    if property_ID < 0:
                        valid_input = False
                        self.PlotCmdOutput("Property ID must be > 0", "red")
                except:
                    self.PlotCmdOutput("Property ID is not valid, int-conversion failed", "red")
            else:
                valid_input = False
                self.PlotCmdOutput("Property ID is not valid, it has to be an int", "red")

        return valid_input


    def _SaveAndCloseWindow(self):
        if self._ValidateInput():
              # pass stuff to Master
              self.master.CreateTreeOutputItem(utils.GetEntityType(self.salome_identifier),     # Original Entity Name (From Salome)
                                               self.rb_var.get(),      # Element of Condition
                                               self.entity_name.get(), # Name of Entity
                                               int(self.property_ID.get()), # Property ID
                                               self.item_iid)          # Tree item iid, if existing
              self.CloseWindow()



# This Class creates a window from which Kratos Entities can be selected
class KratosEntitySelectionWindow(BaseWindow):
    def __init__(self, master, string_var, selection, num_nodes):
        window = tk.Toplevel(master.GetWindow())
        super().__init__(window, "Select Entity", master)
        
        self.string_var = string_var
        self.num_nodes = num_nodes
        self._InitializeWidgets(selection)


    def _InitializeWidgets(self, selection):
        self.tree = ttk.Treeview(self.window, show='tree', selectmode='browse')
        self.tree.tag_bind("clickable", "<Double-1>", lambda event : self._SetName(event))

        keys_selection = sorted(list(selection.keys()))

        for key in keys_selection:
            top_item = self.tree.insert("", "end", text=key)
            values = selection[key]
            if self.num_nodes in values:
                for entry in values[self.num_nodes]:
                    self.tree.insert(top_item, "end", text=entry, tag="clickable")

        self.tree.pack(fill=tk.BOTH, expand=1)

        b = tk.Button(self.window, text="Cancel", command=self.CloseWindow)
        b.pack(fill = tk.X)


    def _SetName(self, event):
        item = utils.GetTreeItem(self.tree, event)
        entity = self.tree.item(item,"text")
        self.string_var.set(entity)
        self.CloseWindow()
        
        

# This class provides a window for selecting files for the imported Converter-Scheme
class FileSelectionWindow(BaseWindow):
    def __init__(self, master, json_dict):
        window = tk.Toplevel(master.GetWindow())
        super().__init__(window, "Select Files", master)
        self.json_dict = json_dict
        self.file_names = sorted(json_dict.keys())
        self.num_files = len(self.file_names)
        self.entry_fields = []
        
        self._InitializeWidgets()

    
    def _InitializeWidgets(self):
        tk.Label(self.window, text="""File list:""",
            justify = tk.LEFT,
            padx = 20, relief=tk.GROOVE).grid(row=1, column=0, columnspan=3)
        
        for i in range(self.num_files):
            row_counter = i+2
            tk.Label(self.window, text=self.file_names[i], justify = tk.LEFT,
                     padx = 20, relief=tk.GROOVE).grid(row=row_counter, column=0, sticky=tk.W+tk.E)
            
            self.entry_fields.append(tk.Entry(self.window, width=120))
            self.entry_fields[i].grid(row=row_counter, column=1, sticky=tk.W+tk.E)
            
            tk.Button(self.window, text="...", command=lambda i=i: self._SetFilePath(self.entry_fields[i], self.file_names[i])).grid(row=row_counter, column=2)

        tk.Button(self.window, text="Cancel", width=14, command=self.CloseWindow).grid(row=self.num_files+2, column=0)
        tk.Button(self.window, text="Save and Close", width=14, command=self._SaveAndCloseWindow).grid(row=self.num_files+2, column=1)


    def _SetFilePath(self, entry_field, origin_file_name):
        file_path, valid_file = utils.GetFilePathOpen("dat", origin_file_name)
        
        if valid_file:
            entry_field.delete(0,"end")
            entry_field.insert(0, file_path)
        
        utils.BringWindowToFront(self.window)


    def _ValidateInput(self):
        valid_input = True
        
        counter = 0
        for entry_field in self.entry_fields:
            file_name = self.file_names[counter]
            if not entry_field.get():
                valid_input = False
                self.PlotCmdOutput("Please select a file for \"" + file_name + "\"", "red")
                break # Input is not valid, no need to check the other entry fields
            else:
                if not utils.FileExists(entry_field.get()):
                    valid_input = False
                    self.PlotCmdOutput("Path for \"" + file_name + "\" is not valid", "red")
            counter += 1

        return valid_input


    def _SaveAndCloseWindow(self):
        if self._ValidateInput():
            # pass stuff to Master
            all_files_valid = True
            for file_name, entry_field in zip(self.file_names, self.entry_fields):
                file_path = entry_field.get()
                valid_file, nodes_read, geom_entities_read = utils.ReadAndParseFile(file_path)
                if valid_file:  
                    smp_info_dict = {}
                    smp_info_dict["smp_name"] = file_name
                    smp_info_dict["smp_file_name"] = file_name
                    smp_info_dict["smp_file_path"] = file_path
                    
                    self.master.GetModelPart().AddMesh(smp_info_dict, self.json_dict[file_name], nodes_read, geom_entities_read)
                else:
                    self.master.GetModelPart().Reset()
                    all_files_valid = False
                    self.PlotCmdOutput("File for \"{}\" is not valid".format(file_name), "red")
                    break # no need to check the other files

            if all_files_valid:  
                self.master.UpdateMeshTree(self.json_dict)
                self.CloseWindow()