import sys
import tkinter as tk
from os.path import splitext, basename
import time

DEBUG = True
unsaved_changes_exist = False
conv_file_ending = ".conv.json"

SALOME_IDENTIFIERS = {
        102 : "Lines",
        203 : "Triangles",
        204 : "Quadrilateral",
        304 : "Tetrahedrals"
        
}


ELEMENTS = {
  "0_Generic" : {
      2 : [
          ],
      3 : ["Element2D3N"
          ],
      4 : ["Element3D4N"
          ]
  },
  "1_Fluid" : {
      2 : [
          ],
      3 : [
          "Element2D3N"
          ],
      4 : [
          "Elemen3D4N"
          ]
  },
  "2_Structure" : {
      2 : ["CrBeamElement3D2N",
          "CrLinearBeamElement3D2N"
          ],
      3 : ["PreStressMembraneElement3D3N",
          "ShellThinElementCorotational3D3N",
          "ShellThickElementCorotational3D3N"
          ],
      4 : ["PreStressMembraneElement3D4N",
          "ShellThinElementCorotational3D4N",
          "ShellThickElementCorotational3D4N"
          ]
  }
}
  

CONDITIONS = {
  "0_Generic" : {
      2 : [
          ],
      3 : [
          ],
      4 : [
          ]
  },
  "1_Fluid" : {
      2 : ["WallCondition2D2N"
          ],
      3 : [
          "WallCondition3D3N"
          ],
      4 : [
          ]
  },
  "2_Structure" : {
      2 : [
          ],
      3 : [
          ],
      4 : ["SurfaceLoadCondition3D4N",
          ]
  }
}


# Functions related to Window
def BringWindowToFront(window):
    window.lift()
    window.attributes('-topmost', 1)
    window.after_idle(window.attributes,'-topmost',False) # TODO check under Windows


def MaximizeWindow(window):
    # TODO check which one works for MacOS
    if (GetOS() == "linux"):
        window.attributes('-zoomed', True)
    else:   
        window.state('zoomed')


def CloseWindow(window, master):
    window.destroy()
    if master is not None:
        master.SetChildWindowIsClosed()


# Functions related to Files
def GetFilePathOpen(FileType):
    file_path = ""
    if (FileType == "dat"):
        file_path = tk.filedialog.askopenfilename(title="Open file",filetypes=[("salome mesh","*.dat")])
    elif (FileType == conv_file_ending):
        file_path = tk.filedialog.askopenfilename(title="Open file",filetypes=[("converter files","*" + conv_file_ending)])
        # file_path = tk.filedialog.askopenfilename(initialdir='/home/philippb', title="Open file",filetypes=[("converter files","*" + conv_file_ending)])
    else:
        print("Unsupported FileType") # TODO make messagebox

    return file_path


def GetFilePathSave(FileType):
    file_path = ""
    if (FileType == "mdpa"):
        file_path = tk.filedialog.asksaveasfilename(title="Select file",
                                                    filetypes=[("mdpa files","*.mdpa")])
        if file_path: # check if a file path was read (i.e. if the file-selection was NOT aborted)
            if not file_path.endswith(".mdpa"):
                file_path += ".mdpa"
    else:
        print("Unsupported FileType") # TODO make messagebox

    return file_path


def GetFileName(FilePath):
    return splitext(basename(FilePath))[0]


# Other Functions
def GetOS():
    os_name = "unknown"

    os_platform = sys.platform

    if (os_platform.startswith("linux")):
        os_name = "linux"
    elif (os_platform == ("win32" or "cygwin")):
        os_name = "windows"
    elif (os_platform == "darwin"):
        os_name = "macos"

    return os_name


def GetEntityType(SalomeIdentifier):
    pre_string = "Unknown"
    if (SalomeIdentifier in SALOME_IDENTIFIERS):
        pre_string = SALOME_IDENTIFIERS[SalomeIdentifier]

    return str(SalomeIdentifier) + "_" + pre_string


def GetNumberOfNodes(String):
    return int(String[1:3])


def GetDebugFlag():
    return DEBUG

def GetTreeItem(tree, event):
    return tree.identify('item', event.x, event.y)
  


class GeometricEntitySalome:
    def __init__(self, salome_ID, salome_identifier, node_list):
        self.salome_ID = salome_ID
        self.salome_identifier = salome_identifier
        self.node_list = node_list
        
    def GetNodeList(self):
        return self.node_list


class Node:
    def __init__(self, origin_ID, coord_x, coord_y, coord_z):
        self.origin_ID = origin_ID
        self.X = coord_x
        self.y = coord_y
        self.z = coord_z
        
        
class GeometricalObject:
    def __init__(self, salome_entity, name):
        self.origin_entity = salome_entity
        self.name = name        
        self.new_ID = -1
    
    def GetID(self):
        if self.new_ID == -1:
            raise Exception("No new ID has been assiged")
        return self.new_ID
    
    def GetWriteLine(self, ID):
        self.new_ID = ID
        # "0" is the Property Placeholder
        line = str(self.new_ID) + "\t0"
        for node in self.origin_entity.GetNodeList():
            line += "\t" + str(node)
        
        return line
        
        
class Element(GeometricalObject):
    def __init__(self, salome_entity, name):
        super().__init__(salome_entity, name)
        
        
class Condition(GeometricalObject):
    def __init__(self, salome_entity, name):
        super().__init__(salome_entity, name)
        
        
class MainModelPart:
    def __init__(self):
        self._Initialize()
        
    def _Initialize(self):
        self.sub_model_parts = {}
        self._InitializeMesh()
        self.mesh_read = False
        self.precision = 12 # Same as in Kratos ("/kratos/includes/gid_io.h")
        
        
    def _InitializeMesh(self):
        self.nodes = {} # ID : [Coord_X, Coord_Y, Coord_Z]
        self.elements = {} # Name : [List]
        self.conditions = {} # Name : [List]
        self.node_counter = 1
        self.element_counter = 1
        self.condition_counter = 1
    
    def GetMeshRead(self):
        return self.mesh_read
    
    def GetSubModelPart(self, smp_name):
        if smp_name in self.sub_model_parts:
            return self.sub_model_parts[smp_name]
#        else:
#            raise Exception("SubModelPart " + smp_name + " does not exist!")
    

    def Reset(self):
        self._Initialize()
    
    
    def FileExists(self, file_name):
        # TODO check against path, name, or both? Or even allow it with a warning?
        file_exists = False
        
        if file_name in self.sub_model_parts.keys():
            file_exists = True
            
        return file_exists
    
    
    def AssembleJSONDict(self):
        mp_dict = {}
        
        for smp_name in self.sub_model_parts.keys():
            mp_dict[smp_name] = self.sub_model_parts[smp_name].GetDictionary()
        
        return mp_dict
        
        
    def AddMesh(self, tree_selection, nodes_read, geom_entities_read, file_name):
        smp_dict = {}

        for child in tree_selection.get_children():
            if (tree_selection.tag_has("Element", child)):
                item_values = tree_selection.item(child,"values")
                element_name = item_values[0]
                salome_identifier = int(item_values[1].split("_")[0])
                
                self.AddEntryToDict(smp_dict, salome_identifier, "Element", element_name)

            if (tree_selection.tag_has("Condition", child)):
                item_values = tree_selection.item(child,"values")
                condition_name = item_values[0]
                salome_identifier = int(item_values[1].split("_")[0])
                
                self.AddEntryToDict(smp_dict, salome_identifier, "Condition", condition_name)

        self.sub_model_parts[file_name] = MeshSubmodelPart(file_name, smp_dict, nodes_read, geom_entities_read)
        
        self.mesh_read = True
        
    
    def RemoveSubmodelPart(self, name_smp):
        self.sub_model_parts.pop(name_smp, None)

        self._Assemble() # Update the ModelPart
        
                
    def _Assemble(self):
        # TODO Check if this was done before! (same for the submodelparts)
        self._InitializeMesh()
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.Assemble()
            smp_nodes, smp_elements, smp_conditions = smp.GetMesh()
            self._AddNodes(smp_nodes)
            self._AddElements(smp_elements)
            self._AddConditions(smp_conditions)
        

    def _AddNodes(self, smp_nodes):
        for node_ID in smp_nodes.keys():
            if node_ID in self.nodes.keys():
                existing_node_coords = self.nodes[node_ID]
                print("Double Check")
                if existing_node_coords != smp_nodes[node_ID]:
                    raise Exception("Node with ID", node_ID, "already exists with different coordinates!")
            else:
                self.nodes[node_ID] = smp_nodes[node_ID]
        
        
    def _AddElements(self, smp_elements):
        for element_name in sorted(smp_elements.keys()):
            if element_name not in self.elements.keys():
                self.elements[element_name] = []
                                
            self.elements[element_name].extend(smp_elements[element_name])
            
            
    def _AddConditions(self, smp_conditions):
        for condition_name in sorted(smp_conditions.keys()):
            if condition_name not in self.conditions.keys():
                self.conditions[condition_name] = []
                                
            self.conditions[condition_name].extend(smp_conditions[condition_name])
            
    
    def AddEntryToDict(self, json_dict, salome_identifier, entity_type, entity_name):
        if salome_identifier not in json_dict:
            json_dict[salome_identifier] = {}
            
        if entity_type not in json_dict[salome_identifier]:
            json_dict[salome_identifier][entity_type] = []
                
        json_dict[salome_identifier][entity_type].append(entity_name)
        
        
    def GetTreeItems(self):
        return sorted(self.sub_model_parts.keys()) # return sorted bcs it is also sorted in the json format!
            
    
    def _NumberOfNodes(self):
        return len(self.nodes)

    def _NumberOfElements(self):
        return sum([len(val) for val in self.elements.values()])

    def _NumberOfConditions(self):
        return sum([len(val) for val in self.conditions.values()])
    
    def WriteMesh(self, file, write_submodelparts):
        self._Assemble() # TODO only do this if sth has changed
        # Write Header
        self._WriteMeshInfo(file)
        file.write("\nBegin ModelPartData\n//  VARIABLE_NAME value\nEnd ModelPartData\n\n")
        file.write("Begin Properties 0\nEnd Properties\n\n")
        
        # Write Nodes
        self._WriteNodes(file)
        
        # Write Elements
        self._WriteElements(file)
        
        # Write Conditions
        self._WriteConditions(file)
        
        # Write SubModelParts
        if write_submodelparts:
            for smp_name in sorted(self.sub_model_parts.keys()):
                smp = self.sub_model_parts[smp_name]
                smp.WriteMesh(file)
                
        return True
            
            
    def _WriteNodes(self, file):
        file.write("Begin Nodes\n")
        for ID in sorted(list(self.nodes.keys())):
            coords = self.nodes[ID]
            
            coords = [round(coords[0], self.precision), 
                      round(coords[1], self.precision), 
                      round(coords[2], self.precision)]
            
            # TODO improve this, somehow take into account the max number
            line_new = ('{:<5}  {:>20}  {:>20}  {:>20}'.format(str(ID), str(coords[0]), str(coords[1]), str(coords[2]))) + "\n"
            
            # line = str(ID) + "\t" + str(coords[0]) + "\t" + str(coords[1]) + "\t" + str(coords[2]) + "\n"
            # file.write(line)

            file.write(line_new)
        
        file.write("End Nodes\n\n")
        
        
    def _WriteElements(self, file):
        for name in sorted(list(self.elements.keys())):
            file.write("Begin Elements " + name + "\n")
            elements_by_name = self.elements[name]
            for elem in elements_by_name:
                file.write(elem.GetWriteLine(self.element_counter) + "\n")
                self.element_counter += 1
            
            file.write("End Elements // " + name + "\n\n")
        
        
    def _WriteConditions(self, file):
        for name in sorted(list(self.conditions.keys())):
            file.write("Begin Conditions " + name + "\n")
            condition_by_name = self.conditions[name]
            for cond in condition_by_name:
                file.write(cond.GetWriteLine(self.condition_counter) + "\n")
                self.condition_counter += 1
            
            file.write("End Conditions // " + name + "\n\n")
    
    def _WriteMeshInfo(self, file):
        localtime = time.asctime( time.localtime(time.time()) )
        file.write("// File created on " + localtime + " with SALOME-Kratos Converter\n")
        file.write("// Mesh Information:\n")
        file.write("// Number of Nodes: " + str(self._NumberOfNodes()) + "\n")
        file.write("// Number of Elements: " + str(self._NumberOfElements()) + "\n")
        file.write("// Number of Conditions: " + str(self._NumberOfConditions()) + "\n")

        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.WriteMeshInfo(file)



class MeshSubmodelPart:
    def __init__(self, file_name, dictionary, nodes_read, geom_entities_read):
        self.file_name = file_name
        self.dictionary = dictionary
        self.nodes_read = nodes_read
        self.geom_entities_read = geom_entities_read
        self.dict_used_for_assembly = None
        self.Initialize()
        
        
    def Initialize(self):
        self.nodes = {}
        self.elements = {}
        self.conditions = {}
        
        
    def GetName(self):
        return self.file_name
    
    def GetGeomEntites(self):
        return self.geom_entities_read
    
    
    def Assemble(self):
        # This function creates the Kratos entities from the read entities  
        # that are defined in it's dictionary
        if self.dict_used_for_assembly != self.dictionary:
        
            self.dict_used_for_assembly = self.dictionary
            
            self._AddNodes()
            self._AddElements()
            self._AddConditions()
        
    
    def _AddNodes(self):
        for line in self.nodes_read:
            words = line.split()
            salome_ID = int(words[0])
            coords = [float(words[1]), float(words[2]), float(words[3])] # X, Y, Z
            if salome_ID in self.nodes:
                raise Exception("Node with ID", salome_ID, "already exists!")
            else:
                self.nodes[salome_ID] = coords
        
        
    def _AddElements(self):
        for salome_identifier in self.dictionary.keys():
            geom_entities = self.geom_entities_read[salome_identifier]
            
            if "Element" in self.dictionary[salome_identifier]:
                element_list = self.dictionary[salome_identifier]["Element"]
                for element_name in element_list:
                    if element_name not in self.elements:
                        self.elements[element_name] = []
                        
                    for entity in geom_entities:
                        self.elements[element_name].append(Element(entity, element_name))
        
        
    def _AddConditions(self):
        for salome_identifier in self.dictionary.keys():
            geom_entities = self.geom_entities_read[salome_identifier]
            
            if "Condition" in self.dictionary[salome_identifier]:
                condition_list = self.dictionary[salome_identifier]["Condition"]
                for condition_name in condition_list:
                    if condition_name not in self.conditions:
                        self.conditions[condition_name] = []
                        
                    for entity in geom_entities:
                        self.conditions[condition_name].append(Condition(entity, condition_name))        
    
    def GetMesh(self):
        return self.nodes, self.elements, self.conditions
    
    def GetDictionary(self):
        return self.dictionary

    def _NumberOfNodes(self):
        return len(self.nodes)

    def _NumberOfElements(self):
        return sum([len(val) for val in self.elements.values()])

    def _NumberOfConditions(self):
        return sum([len(val) for val in self.conditions.values()])
    
    
    def WriteMesh(self, file):
        # Write Header
        file.write("Begin SubModelPart " + self.file_name + "\n")
        
        # Write Nodes
        self._WriteNodes(file)
        
        # Write Elements
        self._WriteElements(file)
        
        # Write Conditions
        self._WriteConditions(file)
        
        file.write("End SubModelPart // " + self.file_name + "\n\n")
        
            
    def _WriteNodes(self, file):
        file.write("\tBegin SubModelPartNodes\n")
        for ID in sorted(self.nodes.keys()):
            file.write("\t\t" + str(ID) + "\n")
        
        file.write("\tEnd SubModelPartNodes\n\n")
        
        
    def _WriteElements(self, file):
        file.write("\tBegin SubModelPartElements \n")
        
        for element_name in sorted(self.elements.keys()):
            for elem in self.elements[element_name]:
                file.write("\t\t" + str(elem.GetID()) + "\n")
            
        file.write("\tEnd SubModelPartElements \n\n")
        
        
    def _WriteConditions(self, file):
        file.write("\tBegin SubModelPartConditions \n")
        
        for condition_name in sorted(self.conditions.keys()):
            for cond in self.conditions[condition_name]:
                file.write("\t\t" + str(cond.GetID()) + "\n")
            
        file.write("\tEnd SubModelPartConditions \n\n")

    def WriteMeshInfo(self, file):
        file.write("// SubModelPart " + self.file_name + "\n")
        file.write("//   Number of Nodes: " + str(self._NumberOfNodes()) + "\n")
        file.write("//   Number of Elements: " + str(self._NumberOfElements()) + "\n")
        file.write("//   Number of Conditions: " + str(self._NumberOfConditions()) + "\n")