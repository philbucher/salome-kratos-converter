# this file contains the GUI stuff
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import json

import converter_utilities as utils
import converter_file_parser as parser


import matplotlib
matplotlib.use('TkAgg')

# from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

from mpl_toolkits.mplot3d import  axes3d,Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np

# TODO sort selection window by entities (nodes, elements, conditions)
# TODO add geometrical information to the Kratos entities
# TODO initial directories
# TODO bind escape to closing the window (aka cancel)


class BaseWindow(): # This is the base class for all window classes
    def __init__(self, window, window_title, master=None):
        self.window = window
        self.child_window_open = False
        self.window.protocol('WM_DELETE_WINDOW', self.CloseWindow)
        self.window.wm_title(window_title)
        utils.BringWindowToFront(self.window)
        
        self.is_root = False
        if master is None:
            self.is_root = True
        self.master = master

        if not self.is_root:        
            self.master.SetChildWindowIsOpen()


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



class GUIObject(BaseWindow):
    def __init__(self, root_window, model_part): # Constructor
        super().__init__(root_window, "SALOME Kratos Converter")

        if(utils.GetDebugFlag):
            print("Gui Constructor")

        self.model_part = model_part        

        utils.MaximizeWindow(self.window)
        self._SetMenuBar()
        self._SetToolBar()
        self._SetTree()
        # self.CreateTreeContextMenu()
        
        self.save_file_path = ""

        self.child_window_open = False

        self.window.bind("<Control-n>", lambda event: self._NewProject())
        self.window.bind("<Control-o>", lambda event: self._OpenConverterProject())
        self.window.bind("<Control-w>", lambda event: self._CloseProject())
        self.window.bind("<Control-s>", lambda event: self._SaveConverterProject(False))
        self.window.bind("<Control-Shift-S>", lambda event: self._SaveConverterProject(True))
        
        self.window.bind("<Control-r>", lambda event: self.CreateReadMainMeshWindow())

        self._Initialize()


    def _Initialize(self):
        self.model_part.Reset()
        self.tree.delete(*self.tree.get_children())
        self.save_file_path = ""


    def _ResetGUI(self):
        self._Initialize()


    def GetModelPart(self):
        return self.model_part


    def _SetMenuBar(self):
        menubar = tk.Menu(self.window)
                     
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self._NewProject)
        filemenu.add_command(label="Open", command=self._OpenConverterProject)
        filemenu.add_command(label="Save", command=lambda: self._SaveConverterProject(False))
        filemenu.add_command(label="Save as...", command=lambda: self._SaveConverterProject(True))
        filemenu.add_command(label="Close", command=self._CloseProject)
        filemenu.add_separator()
        filemenu.add_command(label="Export Converter Scheme", command=self._ExportConverterScheme)
        filemenu.add_command(label="Import Converter Scheme", command=self._ImportConverterScheme)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.CloseWindow)
        menubar.add_cascade(label="Project", menu=filemenu)
        
        # editmenu = tk.Menu(menubar, tearoff=0)
        # editmenu.add_command(label="Undo", command=self.donothing)
        # editmenu.add_separator()
        # editmenu.add_command(label="Cut", command=self.donothing)
        # editmenu.add_command(label="Copy", command=self.donothing)
        # editmenu.add_command(label="Paste", command=self.donothing)
        # editmenu.add_command(label="Delete", command=self.donothing)
        # editmenu.add_command(label="Select All", command=self.donothing)
        # menubar.add_cascade(label="Edit", menu=editmenu)
        
        helpmenu = tk.Menu(menubar, tearoff=0)
        # helpmenu.add_command(label="Help Index", command=self.donothing)
        helpmenu.add_command(label="About...", command=self.ShowAboutInfo)
        menubar.add_cascade(label="Help", menu=helpmenu)
        
        self.window.config(menu=menubar)
        

    def _SetToolBar(self):
        # create a toolbar
        toolbar = tk.Frame(self.window, bd=1, relief=tk.RAISED)
        toolbar2 = tk.Frame(self.window, bd=1, relief=tk.RAISED)

        b = tk.Button(toolbar, text="Read Mesh", width=14, command=lambda: self.OpenChildWindow(self.CreateReadMainMeshWindow))
        b.pack(side=tk.LEFT, padx=2, pady=2)

        b = tk.Button(toolbar, text="Write MDPA", width=14, command=self.WriteMPDAFile)
        b.pack(side=tk.LEFT, padx=2, pady=2)

        # b = tk.Button(toolbar, text="Read MDPA", width=14, command=print("Nothing"))
        # b.pack(side=tk.LEFT, padx=2, pady=2)

        # b = tk.Button(toolbar, text="Output PostFile", width=14, command=self.CreatePlot)
        # b.pack(side=tk.LEFT, padx=2, pady=2)

        # b = tk.Button(toolbar, text="Create Plot", width=14, command=self.CreatePlot)
        # b.pack(side=tk.LEFT, padx=2, pady=2)

        toolbar.pack(side=tk.TOP, fill=tk.X)


        self.output_str = tk.StringVar()

        label = tk.Label(toolbar2, text="Output:")
        label.pack(side=tk.LEFT, padx=2, pady=2)
        self.entry_output=tk.Entry(toolbar2, textvariable=self.output_str)
        self.entry_output.pack(side=tk.LEFT, expand=1, fill=tk.X)

        toolbar2.pack(side=tk.TOP, fill=tk.X)
    
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


    def _SetTree(self):
        self.tree = ttk.Treeview(self.window, show='tree')

        # self.tree.bind("<Button-3>", self.ShowTreeContextMenu) # show the context menu when rightclicked
        # self.tree.bind("<Double-1>", self.EditDblClickedTreeItem)
        self.tree.tag_bind("Mesh", "<Double-1>", lambda event : self.EditTreeItem(utils.GetTreeItem(self.tree, event)))
        self.tree.tag_bind("Mesh", "<Delete>", self.DeleteTreeItems)

        self.tree.pack(side=tk.LEFT, fill=tk.Y)


    def CreatePlot(self):

        if self.model_part.GetMeshRead():
            fig = plt.figure()
            
            canvas = FigureCanvasTkAgg(fig, master=self.window)
            canvas.show()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            canvas._tkcanvas.pack(side =tk.TOP, fill=tk.BOTH, expand=1)

            ax = Axes3D(fig)

            num_nodes, x_coords, y_coords, z_coords = self.main_mesh.GetNodeCoords()

            ax.scatter(x_coords, y_coords, z_coords)

            ax.set_xlabel('X-Direction')
            ax.set_ylabel('Y-Direction')
            ax.set_zlabel('Z-Direction')

            # Test for plotting triangles and quads
            x = [0.0, 0.1, 0.2]
            y = [0.0, 0.5, 0.0]
            z = [0.0, 0.0, 0.0]

            xx = np.array([[0,1],[0,1]])
            yy = np.array([[0,0],[1,1]])
            zz = np.array([[1,2],[3,4]])

            # surf = ax.plot_surface(xx, yy, zz, cmap=cm.coolwarm,
            #            linewidth=0, antialiased=False)
            # ax.plot_trisurf(x, y, z, linewidth=0.2, antialiased=True)
            
        else:
            self.PlotCmdOutput("Please read Main Mesh first", "red")


    # def EditDblClickedTreeItem(self, event):
    #     item = self.tree.identify('item',event.x,event.y)
    #     print("you clicked on", self.tree.item(item,"text"))
    #     print(self.tree.item(item,"values"))
    #     print(len(self.tree.item(item,"values")))
    #     print(self.tree.item(item,"values")[2])
    #     uuu = self.tree.item(item,"values")[2]
    #     if isinstance(uuu, dict):
    #         print("true")
    #     else:
    #         print("false")
    #     json_acceptable_string = uuu.replace("'", "\"")
    #     print(json_acceptable_string)
    #     #print(uuu["ttt"])
    #     uuu2 = json.loads(json_acceptable_string)
    #     print("dict", uuu2)
    #     if isinstance(uuu2, dict):
    #         print("true")
    #     else:
    #         print("false")
    #     self.CreateEditWindow(item)
    #     print(uuu2["ttt"])
    #     print(uuu2["Element"])

       
    def EditTreeItem(self, item):
        self.OpenChildWindow(self.CreateReadMainMeshWindowEditItem, item)


    def CreateReadMainMeshWindowEditItem(self, item):
        # item = self.tree_output.identify('item', event.x, event.y)
        smp_name = self.tree.item(item,"text")
        return ReadMeshWindow(self, smp_name) #Is only called if Item has tag "modifyable"
    

    def DeleteTreeItems(self, event):
        smp_to_remove = []
        for item in self.tree.selection():
            smp_to_remove.append(self.tree.item(item,"text")) # Identify SubModelParts by name
            self.tree.delete(item)

        if len(self.tree.get_children(self.main_tree_item)) == 0: # Everything is deleted, reset ModelPart
            self.tree.delete(self.main_tree_item)
            self.model_part.Reset()
            self.PlotCmdOutput("ModelPart resetted", "orange")
        else:
            for smp in smp_to_remove:
                self.model_part.RemoveSubmodelPart(smp)


        print("deleted item")


    def ShowTreeContextMenu(self, event):
        self.tree_context_menu.post(event.x_root, event.y_root)


    def CreateTreeContextMenu(self):
        self.tree_context_menu = tk.Menu(self.window, tearoff=0)
        self.tree_context_menu.add_command(label="Edit", command=self.EditSelectedTreeItem)
        self.tree_context_menu.add_command(label="Delete", command=self.DeleteTreeItems)


    def CreateReadMainMeshWindow(self):
        return ReadMeshWindow(self)


    def CloseWindow(self):
        if (utils.unsaved_changes_exist):
            result = messagebox.askquestion("Warning", "Unsaved changes exist, exit anyway?", icon='warning')
            if result == 'yes':
                self.CloseMainWindow()
        else:
            self.CloseMainWindow()        


    def CloseMainWindow(self):
        self.window.quit() # needed to end the GUI with the plot
        self.window.destroy()


    def ShowAboutInfo(self):
        messagebox.showinfo("Information", "Salome2Kratos Converter\n" +
                                    "Author: Philipp Bucher\n" +
                                    "Version: 1.0")
    
    def _NewProject(self):
        # TODO check for unsaved changes and stuff
        if self.child_window_open:
            self.PlotCmdOutput("Close child windows first", "red")
        else:
            self._ResetGUI()
            self.PlotCmdOutput("New project initialized", "orange")

    def _CloseProject(self):
        # TODO check for unsaved changes and stuff
        if self.child_window_open:
            self.PlotCmdOutput("Close child windows first", "red")
        else:
            self._ResetGUI()
            self.PlotCmdOutput("Closed project", "orange")


    def _OpenConverterProject(self):
        file_path = utils.GetFilePathOpen(utils.conv_project_file_ending)
  
        if file_path:
            serialized_model_part_dict = {}
            with open(file_path, "r") as json_file:
                serialized_model_part_dict = json.load(json_file)

            self.model_part.Deserialize(serialized_model_part_dict)

            self.UpdateMeshTree()


    def _SaveConverterProject(self, save_as):
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
            serialized_model_part_dict = self.model_part.Serialize()
            with open(self.save_file_path, "w") as save_file:
                json.dump(serialized_model_part_dict, save_file)
                #json.dump(serialized_model_part_dict, save_file, sort_keys = True, indent = 4) # Do this only for debugging, file size is much larger!
            
            self.PlotCmdOutput("Saved the file", "green")
            utils.unsaved_changes_exist = False


    def _ImportConverterScheme(self):
        file_path = utils.GetFilePathOpen(utils.conv_scheme_file_ending)

        if file_path:
            json_dict = {}
            with open(file_path, "r") as json_file:
                json_dict = json.load(json_file)

            self.UpdateMeshTree(json_dict)


    def _ExportConverterScheme(self):
        input_save_file_path = tk.filedialog.asksaveasfilename(title="Select file",
                                    filetypes=[("converter files","*" + utils.conv_scheme_file_ending)])
        if input_save_file_path:
            if not input_save_file_path.endswith(utils.conv_scheme_file_ending):
                input_save_file_path += utils.conv_scheme_file_ending

            model_part_dict = self.model_part.AssembleMeshInfoDict()
            with open(input_save_file_path, "w") as save_file:
                json.dump(model_part_dict, save_file, sort_keys = True, indent = 4)
            
            self.PlotCmdOutput("Saved the file", "green")
            utils.unsaved_changes_exist = False


    def UpdateMeshTree(self, tree_items_dict=None):
        if not tree_items_dict:
            tree_items_dict = self.model_part.AssembleMeshInfoDict()
        self.tree.delete(*self.tree.get_children())
        if len(tree_items_dict) > 0:
            self.main_tree_item = self.tree.insert("", "end", text="Main Mesh", open=True)
            for item in sorted(tree_items_dict.keys()):
                item_values = tree_items_dict[item]
                self.tree.insert(self.main_tree_item, "end", text=item, values=item_values, tag="Mesh")


    def WriteMPDAFile(self):
        if self.model_part.GetMeshRead(): # Only write output if a main mesh was read
            writing_successful = False
            mdpa_file_path = utils.GetFilePathSave("mdpa")
            if mdpa_file_path:
                with open(mdpa_file_path,"w") as mdpa_file:
                    writing_successful = self.model_part.WriteMesh(mdpa_file)

            if writing_successful:
                self.PlotCmdOutput("Mesh was written successfully!", "green")
            else:
                self.PlotCmdOutput("An error occured while writing the mesh", "red")

        else:
            self.PlotCmdOutput("Please Read a Main Mesh First!", "red")


    ####### Temp functions, to be removed
    def donothing(self):
        filewin = tk.Toplevel(self.window)
        button = tk.Button(filewin, text="Do nothing button")
        button.pack()
        
    def donothing2(self, event):
        filewin = tk.Toplevel(self.window)
        strr = "clicked at " +  str(event.x) + "   " + str(event.y)
        button = tk.Button(filewin, text=strr)
        button.pack()




class ReadMeshWindow(BaseWindow):
    def __init__(self, master, smp_name=None):
        window = tk.Toplevel(master.GetWindow())
        super().__init__(window, "Read Mesh", master)
        
        self.file_parsed = False
        self.edited_mesh = False
        self.old_smp_name = ""
        
        ### Row 1 ###
        # Button for reading the Mesh
        tk.Button(self.window, text="Read Mesh File", width=20, command=self.ReadAndParseMeshFile).grid(
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
        self.tree_input.tag_bind("clickable", "<Double-1>", lambda event : self.OpenChildWindow(self.CreateEntrySelectionWindow, event))

        # Tree with entities that will be cretated
        self.tree_output = ttk.Treeview(self.window)
        self.tree_output["columns"]=("col_entity_name", "col_origin_entity")
        self.tree_output.heading("#0", text="Entity Type")
        self.tree_output.heading("col_entity_name", text="Entity Name")
        self.tree_output.heading("col_origin_entity", text="Origin Entity")
        self.tree_output.grid(row=6, sticky=tk.E, column=1, padx=15, pady=(0,15))
        self.tree_output.tag_configure("Element", foreground="blue")
        self.tree_output.tag_configure("Condition", foreground="red")
        self.tree_output.tag_bind("modifyable", "<Double-1>", lambda event : self.EditTreeOutputItem(
                                                                              utils.GetTreeItem(self.tree_output, event)))
        self.tree_output.tag_bind("modifyable", "<Delete>", self.DeleteTreeOutputItem)

        # self.tree_input.bind("<Double-1>", self.CreateEntrySelectionWindow)
        # self.tree_output.tag_bind("modifyable", "<Return>", self.EditSelectedTreeItem)
        # self.CreateTreeContextMenu()
        # self.tree_output.tag_bind("modifyable", "<Button-3>", self.ShowTreeContextMenu) # show the context menu when rightclicked
        #self.tree_input.tag_bind("Node", "<Double-1>", lambda event : self.CreateEntrySelectionWindowNode(event))
        #self.FillTree(tree, nodes, geom_entities)
        
        ### Row 7 ###
        # Buttons for Canceling and Saving
        tk.Button(self.window, text="Cancel", width=20, command=self.CloseWindow).grid(
                row=7, column=0, pady=(0,15))

        tk.Button(self.window, text="Save and Close", width=20, command=self.SaveAndCloseWindow).grid(
                row=7, column=1, pady=(0,15))
        
        # In case an existing mesh is edited:
        if smp_name: # This means that an existing mesh is edited
            smp = self.master.GetModelPart().GetSubModelPart(smp_name)
            smp_info_dict = smp.GetInfoDict()
            self.FillInputTree(smp.GetGeomEntites())
            self.FillOutputTree(smp.GetMeshInfoDict())
            self.edited_mesh = True
            self.old_smp_name = smp_name
            self.smp_name_var.set(smp_name)
            self.smp_path_var.set(smp_info_dict["smp_file_path"])
            self.write_smp_var.set(smp_info_dict["write_smp"])
            
            self.file_name = smp_info_dict["smp_file_name"]
            self.file_path = smp_info_dict["smp_file_path"]

        
    def ReadAndParseMeshFile(self):
        file_path = utils.GetFilePathOpen("dat")
        utils.BringWindowToFront(self.window)

        if file_path: # check if file exists
            self.tree_input.delete(*self.tree_input.get_children())
            self.tree_output.delete(*self.tree_output.get_children())

            file_name = utils.GetFileName(file_path)
            
            if self.master.GetModelPart().FileExists(file_name):
                self.PlotCmdOutput("File was already read!", "red")
            else:
                self.nodes_read, self.geom_entities_read = parser.ReadAndParseFile(file_path)
                self.FillInputTree(self.geom_entities_read)
                # TODO check if num_node > 0!
                self.file_parsed = True
                
                self.file_name = file_name
                self.file_path = file_path
                
                self.smp_name_var.set(file_name)
                self.smp_path_var.set(file_path)
            

    def CreateDictionaryFromParsedEntities(self, geom_entities):
        dictionary = {}
        sorted_keys = sorted(list(geom_entities.keys()))#, key = lambda x: x.split("_")[1]) # Sort keys based on identifier

        for key in sorted_keys:
            label = utils.GetEntityType(key)
            self.tree_input.insert("", "end", text=label, tags="clickable")
        return dictionary


    def FillInputTree(self, geom_entities_read):
        self.tree_input.delete(*self.tree_input.get_children())
        self.tree_output.delete(*self.tree_output.get_children())
        
        self.tree_input.insert("", "end", text="Nodes")
        self.tree_output.insert("", "end", text="Nodes", tags="Node")

        # Keys are in format identifier_name
        if geom_entities_read: # check if geom entities are present
            sorted_keys = sorted(list(geom_entities_read.keys()))#, key = lambda x: x.split("_")[1]) # Sort keys based on identifier

            for key in sorted_keys:
                label = utils.GetEntityType(key)
                self.tree_input.insert("", "end", text=label, tags="clickable")
            
            
    def FillOutputTree(self, smp_dict):
        for salome_ID in sorted(smp_dict.keys()):
            for entity_type in sorted(smp_dict[salome_ID].keys()):
                for entity_name in sorted(smp_dict[salome_ID][entity_type]):
                    item_values = (entity_name, salome_ID)
                    
                    self.InsertTreeOutputItem(entity_type, item_values)

    
    def CreateEntrySelectionWindow(self, event):
        item = self.tree_input.identify('item', event.x, event.y)
        origin_entity = self.tree_input.item(item,"text")
        return EntrySelectionWindow(self, origin_entity) #Is only called if Item has tag "clickable"


    def CreateEntrySelectionWindowEditItem(self, item):
        # item = self.tree_output.identify('item', event.x, event.y)
        entity_type = self.tree_output.item(item,"text")
        entity_name = self.tree_output.item(item,"values")[0]
        origin_entity = self.tree_output.item(item,"values")[1]
        return EntrySelectionWindow(self, origin_entity, [entity_type, entity_name, item]) #Is only called if Item has tag "modifyable"
    

    def EditTreeOutputItem(self, item):
        self.OpenChildWindow(self.CreateEntrySelectionWindowEditItem, item)


    # this was used with the context menu
    # def EditSelectedTreeItem(self):
    #     if (len(self.tree_output.selection()) != 1):
    #         print("Select One item")
    #     else:
    #         self.EditTreeOutputItem(self.tree_output.selection())


    def donothing(self):
        filewin = tk.Toplevel(self.master)
        button = tk.Button(filewin, text="Do nothing button")
        button.pack()


    def CreateTreeOutputItem(self, OriginEntity, EntityTypeID, EntityName, item_iid):
        entity_type = ""
        if EntityTypeID == 1: # Element
            entity_type = "Element"
        elif EntityTypeID == 2: # Condition
            entity_type = "Condition"
        else:
            self.PlotCmdOutput("Wrong EntityTypeID", "red")

        item_values = (EntityName, OriginEntity)
        
        # Check for uniqueness of the entry that should be created
        identical_entry_found = False
        for tree_item in self.tree_output.get_children():
            if self.tree_output.item(tree_item,"text") == entity_type:
                if self.tree_output.item(tree_item,"values") == item_values:
                    identical_entry_found = True
                    break # Exit the loop, an identical entry was found, no need to check the other items
        
        # Insert / modify the value, in case it does not  exist yet
        if identical_entry_found:
            self.PlotCmdOutput("This entry exists already!", "red")
        else:
            self.InsertTreeOutputItem(entity_type, item_values, item_iid)


    def InsertTreeOutputItem(self, entity_type, item_values, item_iid=None):
        if item_iid is None: # Inserting a new item
            item_iid = self.tree_output.insert("", "end")
                
        self.tree_output.item(item_iid, text=entity_type, values=item_values, tag=(entity_type, "modifyable"))


    def DeleteTreeOutputItem(self, event):
        for item in self.tree_output.selection():
            if self.tree_output.tag_has("modifyable", item):
                self.tree_output.delete(item)



    # def ShowTreeContextMenu(self, event):
    #     for item in self.tree_output.selection():
    #         self.tree_output.selection_remove(item)

    #     self.tree_context_menu.post(event.x_root, event.y_root)


    # def CreateTreeContextMenu(self):
    #     self.tree_context_menu = tk.Menu(self.window, tearoff=0)
    #     self.tree_context_menu.add_command(label="Edit", command=self.EditSelectedTreeItem)
    #     self.tree_context_menu.add_command(label="Delete", command=self.DeleteTreeItems)


    def ValidateInput(self):
        valid_input = True

        if not self.smp_name_var.get():
            valid_input = False
            self.PlotCmdOutput("Please enter a SubModelPart Name", "red")
        else:
            if not isinstance(self.smp_name_var.get(), str):
                valid_input = False
                self.PlotCmdOutput("SubModelPart name is not valid", "red")
            if self.old_smp_name != self.smp_name_var.get():
                if self.master.GetModelPart().FileExists(self.smp_name_var.get()):
                    self.PlotCmdOutput("SubModelPart name exists already!", "red")
                    valid_input = False

        return valid_input

    def SaveAndCloseWindow(self):
        if self.ValidateInput():
            smp_info_dict = {}
            smp_info_dict["smp_name"] = self.smp_name_var.get()
            smp_info_dict["smp_file_name"] = self.file_name
            smp_info_dict["smp_file_path"] = self.file_path
            smp_info_dict["write_smp"] = self.write_smp_var.get()

            if self.file_parsed and self.edited_mesh: # A mesh was edited but then re-read (overwritten)
                self.master.GetModelPart().RemoveSubmodelPart(self.old_smp_name)
                self.master.GetModelPart().AddMesh(smp_info_dict, self.tree_output, self.nodes_read, self.geom_entities_read)

            if self.file_parsed and not self.edited_mesh: # A mesh was read
                self.master.GetModelPart().AddMesh(smp_info_dict, self.tree_output, self.nodes_read, self.geom_entities_read)
        
            elif not self.file_parsed and self.edited_mesh: # A mesh was edited
                self.master.GetModelPart().UpdateMesh(self.old_smp_name, smp_info_dict, self.tree_output)
        
            self.master.UpdateMeshTree()

            self.CloseWindow()
    


class EntrySelectionWindow(BaseWindow):
    def __init__(self, master, origin_entity, arguments=[]):
        window = tk.Toplevel(master.GetWindow())
        super().__init__(window, "Select Type of Entity", master)
        
        self.origin_entity = origin_entity
        self.InitializeWidgets()

        self.item_iid = None

        if len(arguments) == 3:
            self.SetWidgetEntries(arguments[0], arguments[1])
            self.item_iid = arguments[2]

    
    def InitializeWidgets(self):
        label_string = "Select Entity for: " + self.origin_entity
        tk.Label(self.window, text=label_string,
            justify = tk.LEFT, relief=tk.RAISED,
            padx = 20).grid(row=0, column=0, columnspan=2, sticky=tk.W+tk.E)

        tk.Label(self.window, text="""Choose an entity type:""",
            justify = tk.LEFT,
            padx = 20).grid(row=1, column=0, columnspan=2)
        
        # Variable for RadioButtons
        self.rb_var = tk.IntVar()
        self.rb_var.set(1) # Choose "Element" as default
        self.entity_name = tk.StringVar()

        radio_button_1 = tk.Radiobutton(self.window, 
                    text="Element",
                    padx = 20, 
                    variable=self.rb_var, 
                    value=1,
                    command=lambda: self.entity_name.set(""))
        radio_button_2 = tk.Radiobutton(self.window, 
                    text="Condition",
                    padx = 20, 
                    variable=self.rb_var, 
                    value=2,
                    command=lambda: self.entity_name.set(""))
        
        radio_button_1.grid(sticky = tk.W, row=2, column=0, columnspan=2)
        radio_button_2.grid(sticky = tk.W, row=3, column=0, columnspan=2)
    
        
        tk.Label(self.window, text="""Name of Entity:""",
            justify = tk.LEFT,
            padx = 20).grid(row=4, column=0, columnspan=2)
        entry_name=tk.Entry(self.window, textvariable=self.entity_name)
        entry_name.grid(row=5, column=0, columnspan=2, sticky=tk.W+tk.E)
        b = tk.Button(self.window, text="...", command=lambda: self.OpenChildWindow(self.CreateKratosEntitySelectionWindow))
        b.grid(row=5, column=2)

        b = tk.Button(self.window, text="Cancel", width=14, command=self.CloseWindow)
        b.grid(row=8, column=0)

        b = tk.Button(self.window, text="Save and Close", width=14, command=self.SaveAndCloseWindow)
        b.grid(row=8, column=1)


    def SetWidgetEntries(self, entity_type, entity_name):
        if entity_type == "Element":
            self.rb_var.set(1)
        elif entity_type == "Condition":
            self.rb_var.set(2)
        else: # TODO test
            self.rb_var.set(0)
        
        self.entity_name.set(entity_name)


    def CreateKratosEntitySelectionWindow(self):
        return KratosEntitySelectionWindow(self, self.entity_name, self.GetSelection(), utils.GetNumberOfNodes(self.origin_entity))

    
    def GetSelection(self):
        if self.rb_var.get() == 1:
            return utils.ELEMENTS
        else:
            return utils.CONDITIONS


    def ValidateInput(self):
        valid_input = True

        if not self.entity_name.get():
            valid_input = False
            self.PlotCmdOutput("Please enter an Entity Name", "red")
        else:
            if not isinstance(self.entity_name.get(), str):
                valid_input = False
                self.PlotCmdOutput("Entity name is not valid", "red")

        return valid_input


    def SaveAndCloseWindow(self):
        if self.ValidateInput():
              # pass stuff to Master
              self.master.CreateTreeOutputItem(self.origin_entity,     # Original Entity Name (From Salome)
                                               self.rb_var.get(),      # Element of Condition
                                               self.entity_name.get(), # Name of Entity
                                               self.item_iid) 
              self.CloseWindow()



class KratosEntitySelectionWindow(BaseWindow):
    def __init__(self, master, StringVariable, Selection, NumNodes):
        window = tk.Toplevel(master.GetWindow())
        super().__init__(window, "Select Entity", master)
        
        self.string_var = StringVariable
        self.num_nodes = NumNodes

        self.tree = ttk.Treeview(self.window, show='tree', selectmode='browse')
        self.tree.tag_bind("clickable", "<Double-1>", lambda event : self.SetName(event))

        keys_selection = sorted(list(Selection.keys()))

        for key in keys_selection:
            top_item = self.tree.insert("", "end", text=key)
            values = Selection[key]
            if self.num_nodes in values:
                for entry in values[self.num_nodes]:
                    self.tree.insert(top_item, "end", text=entry, tag="clickable")

        self.tree.pack(fill=tk.BOTH, expand=1)

        b = tk.Button(self.window, text="Cancel", command=self.CloseWindow)
        b.pack(fill = tk.X)


    def SetName(self,event):
        item = self.tree.identify('item', event.x, event.y)
        entity = self.tree.item(item,"text")
        self.string_var.set(entity)
        self.CloseWindow()