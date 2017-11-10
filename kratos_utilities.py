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
import time

# Project imports
import global_utilities as global_utils

class KratosEntity:
    def __init__(self, salome_entity, name, property_ID):
        self.is_node = False
        if isinstance(salome_entity, int):
            self.is_node = True

        self.origin_entity = salome_entity # int for Node, GeometricEntitySalome for Element/Condition
        self.name = name        
        self.new_ID = -1
        self.property_ID = property_ID
    

    def GetID(self):
        if self.new_ID == -1:
            raise Exception("No new ID has been assiged")
        return self.new_ID
    

    def GetWriteLine(self, ID, format_str, space):
        self.new_ID = ID
        # "0" is the Property Placeholder
        line = format_str.format(str(self.new_ID), str(self.property_ID))

        if self.is_node:
            line += space + str(self.origin_entity)
        else:
            for node in self.origin_entity.GetNodeList():
                line += space + str(node)
                
            if global_utils.GetDebug():
                line += " // " + str(self.origin_entity.GetID()) # add the origin ID
        
        return line
        
        
    
class Element(KratosEntity):
    def __init__(self, salome_entity, name, property_ID):
        super().__init__(salome_entity, name, property_ID)
        
        
        
class Condition(KratosEntity):
    def __init__(self, salome_entity, name, property_ID):
        super().__init__(salome_entity, name, property_ID)
        
        
        
class MainModelPart:
    def __init__(self):
        self._Initialize()
        
    def _Initialize(self):
        self.sub_model_parts = {}
        self._InitializeMesh()
        self.mesh_read = False
        self.precision = 12 # Same as in Kratos ("/kratos/includes/gid_io.h")
        self.num_spaces = 3 # number of spaces in mdpa btw numbers
        
        
    def _InitializeMesh(self):
        self.nodes = {} # ID : [Coord_X, Coord_Y, Coord_Z]
        self.elements = {} # Name : [List]
        self.conditions = {} # Name : [List]
        self.node_counter = 1
        self.element_counter = 1
        self.condition_counter = 1
        # Variables for optimizing the size of the mdpa file
        self.max_node_coord_x = 0
        self.max_node_coord_y = 0
        self.max_node_coord_z = 0
    
    
    def GetMeshRead(self):
        return self.mesh_read
    
    
    def GetSubModelPart(self, smp_name):
        if smp_name in self.sub_model_parts:
            return self.sub_model_parts[smp_name]
    

    def Reset(self):
        self._Initialize()
    
    
    def SubModelPartNameExists(self, smp_name):
        smp_exists = False
        
        if smp_name in self.sub_model_parts.keys():
            smp_exists = True
            
        return smp_exists

    def FileNameExists(self, file_name):
        file_name_exists = False
        for smp in self.sub_model_parts.values():
            if file_name == smp.GetFileName():
                file_name_exists = True
                
        return file_name_exists

    def FilePathExists(self, file_path):
        file_path_exists = False
        for smp in self.sub_model_parts.values():
            if file_path == smp.GetFilePath():
                file_path_exists = True
                
        return file_path_exists
    
    
    def AssembleMeshInfoDict(self):
        mp_dict = {}
        
        for smp_name in self.sub_model_parts.keys():
            mp_dict[smp_name] = self.sub_model_parts[smp_name].GetMeshInfoDict()
        
        return mp_dict
        
        
    def AddMesh(self, smp_info_dict, mesh_dict, nodes_read, geom_entities_read):
        smp_name = smp_info_dict["smp_name"]
        self.sub_model_parts[smp_name] = MeshSubmodelPart()
        self.sub_model_parts[smp_name].FillWithEntities(smp_info_dict, mesh_dict, nodes_read, geom_entities_read)
        
        self.mesh_read = True

    def UpdateMesh(self, old_smp_name, smp_info_dict, mesh_dict):
        new_smp_name = smp_info_dict["smp_name"]
        self.sub_model_parts[new_smp_name] = self.sub_model_parts.pop(old_smp_name) # Update the key
        
        self.sub_model_parts[new_smp_name].Update(smp_info_dict, mesh_dict)

    
    def RemoveSubmodelPart(self, name_smp):
        self.sub_model_parts.pop(name_smp, None)

        self._Assemble() # Update the ModelPart


    def Serialize(self):
        # This function serializes the ModelPart such that it can be saved in a json file
        global_utils.LogDebug("Serializing ModelPart")
        serialized_dict = {}
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            serialized_dict.update(smp.Serialize())

        return serialized_dict

        
    def Deserialize(self, serialized_dict):
        # This function constructs a modelpart from a serialized dictionary
        self.Reset()

        for smp_name in sorted(serialized_dict.keys()):
            if smp_name != "general":
                self.sub_model_parts[smp_name] = MeshSubmodelPart()
                self.sub_model_parts[smp_name].Deserialize(smp_name, serialized_dict[smp_name])
        
        self.mesh_read = True

        global_utils.LogDebug("Deserialized ModelPart")


    def _Assemble(self):
        # TODO Check if this was done before! (same for the submodelparts)
        start_time = time.time()
        global_utils.LogInfo("Assembling Mesh")
        self._InitializeMesh()
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.Assemble()
            smp_nodes, smp_elements, smp_conditions = smp.GetMesh()
            self._AddNodes(smp_nodes)
            self._AddElements(smp_name, smp_elements)
            self._AddConditions(smp_name, smp_conditions)
        
        global_utils.LogTiming("Mesh assembling time", start_time)
        

    def _AddNodes(self, smp_nodes):
        for node_ID in smp_nodes.keys():
            if node_ID in self.nodes.keys():
                existing_node_coords = self.nodes[node_ID]
                if existing_node_coords != smp_nodes[node_ID]:
                    raise Exception("Node with ID", node_ID, "already exists with different coordinates!")
            else:
                self.nodes[node_ID] = smp_nodes[node_ID]
                if global_utils.GetReadableMDPA():
                    if smp_nodes[node_ID][0] > self.max_node_coord_x: self.max_node_coord_x = smp_nodes[node_ID][0]
                    if smp_nodes[node_ID][1] > self.max_node_coord_y: self.max_node_coord_y = smp_nodes[node_ID][1]
                    if smp_nodes[node_ID][2] > self.max_node_coord_z: self.max_node_coord_z = smp_nodes[node_ID][2]
        
        
    def _AddElements(self, smp_name, smp_elements):
        self.elements[smp_name] = smp_elements
            
            
    def _AddConditions(self, smp_name, smp_conditions):
        self.conditions[smp_name] = smp_conditions
        
        
    def GetTreeItems(self):
        return sorted(self.sub_model_parts.keys()) # return sorted bcs it is also sorted in the json format!
            
    
    def _NumberOfNodes(self):
        return len(self.nodes)


    def _NumberOfElements(self):
        num_elements = 0
        for smp in self.sub_model_parts.values():
            num_elements += smp.NumberOfElements()
        return num_elements


    def _NumberOfConditions(self):
        num_conditions = 0
        for smp in self.sub_model_parts.values():
            num_conditions += smp.NumberOfConditions()
        return num_conditions
    

    def WriteMesh(self, file):
        self._Assemble() # TODO only do this if sth has changed
        
        start_time = time.time()
        global_utils.LogInfo("Writing Mesh")

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
        for smp_name in sorted(self.sub_model_parts.keys()):
            smp = self.sub_model_parts[smp_name]
            smp.WriteMesh(file)
        
        global_utils.LogTiming("Mesh writing time", start_time)
                
        return True
            
            
    def _WriteNodes(self, file):
        file.write("Begin Nodes\n")

        if global_utils.GetReadableMDPA():
            max_ID = max(self.nodes.keys())
            global_utils.LogDebug("Max Node ID: " + str(max_ID))

            spaces_coords_x = '{:>' + str(len(str(int(self.max_node_coord_x))) + self.precision + self.num_spaces) + '} '
            spaces_coords_y = '{:>' + str(len(str(int(self.max_node_coord_y))) + self.precision + self.num_spaces) + '} '
            spaces_coords_z = '{:>' + str(len(str(int(self.max_node_coord_z))) + self.precision + self.num_spaces) + '} '
            format_str = '{:>' + str(len(str(max_ID))) + '} ' + spaces_coords_x + spaces_coords_y + spaces_coords_z
        else:
            format_str = '{} {} {} {}'
            
        global_utils.LogDebug("Node Format String: " + str(format_str))

        for ID in sorted(list(self.nodes.keys())):
            coords = self.nodes[ID]

            coords = [round(coords[0], self.precision), 
                      round(coords[1], self.precision), 
                      round(coords[2], self.precision)]
            
            line = format_str.format(str(ID), coords[0], str(coords[1]), str(coords[2])) + "\n"

            file.write(line)
        
        file.write("End Nodes\n\n")
        
        
    def _WriteElements(self, file):
        if global_utils.GetReadableMDPA():
            num_elements = self._NumberOfElements()
            format_str = '{:>' + str(len(str(num_elements))) + '} {:>' + str(self.num_spaces) + '}'
            space = "\t"
        else:
            format_str = '{} {}'
            space = " "

        global_utils.LogDebug("Element Format String: " + str(format_str))

        for smp_name in sorted(list(self.elements.keys())):
            for element_name in sorted(list(self.elements[smp_name])):

                file.write("Begin Elements " + element_name + " // " + smp_name + "\n")
                elements_by_name = self.elements[smp_name][element_name]
                for elem in elements_by_name:
                    file.write(elem.GetWriteLine(self.element_counter, format_str, space) + "\n")
                    self.element_counter += 1
                
                file.write("End Elements // " + element_name + "\n\n")        
        
        
    def _WriteConditions(self, file):
        if global_utils.GetReadableMDPA():
            num_conditions = self._NumberOfConditions()
            format_str = '{:>' + str(len(str(num_conditions))) + '} {:>' + str(self.num_spaces) + '}'
            space = "\t"
        else:
            format_str = '{} {}'
            space = " "

        global_utils.LogDebug("Condition Format String: " + str(format_str))

        for smp_name in sorted(list(self.conditions.keys())):
            for condition_name in sorted(list(self.conditions[smp_name])):

                file.write("Begin Conditions " + condition_name + " // " + smp_name + "\n")
                conditions_by_name = self.conditions[smp_name][condition_name]
                for cond in conditions_by_name:
                    file.write(cond.GetWriteLine(self.condition_counter, format_str, space) + "\n")
                    self.condition_counter += 1
                
                file.write("End Conditions // " + condition_name + "\n\n")
    

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
    def __init__(self): # TODO is this needed?
        pass
        
        
    def Initialize(self):
        self.nodes = {}
        self.elements = {}
        self.conditions = {}


    def FillWithEntities(self, smp_info_dict, mesh_dict, nodes_read, geom_entities_read):
        self.smp_info_dict = smp_info_dict
        self.mesh_dict = mesh_dict
        self.nodes_read = nodes_read
        self.geom_entities_read = geom_entities_read
        self.smp_info_dict_used_for_assembly = None
        self.mesh_dict_used_for_assembly = None
        self.Initialize()
        

    def Update(self, smp_info_dict, mesh_dict):
        self.smp_info_dict = smp_info_dict
        self.mesh_dict = mesh_dict


    def Serialize(self):
        global_utils.LogDebug("Serializing " + self.smp_info_dict["smp_name"])
        serialized_smp = {}

        serialized_smp["submodelpart_information"] = self.smp_info_dict
        serialized_smp["mesh_information"] = self.mesh_dict
        serialized_smp["nodes_read"] = self._SerializeNodesRead()
        serialized_smp["geom_entities_read"] = self._SerializeGeomEntitiesRead()

        return {self.smp_info_dict["smp_name"] : serialized_smp}


    def _SerializeNodesRead(self):
        self._AddNodes() # Update the internal information
        
        return self.nodes


    def _SerializeGeomEntitiesRead(self):
        serialized_geom_entities = []
        
        for salome_ID in self.geom_entities_read:
            for entity in self.geom_entities_read[salome_ID]:
                serialized_geom_entities.append(entity.Serialize())
            
        return serialized_geom_entities


    def Deserialize(self, smp_name, serialized_smp):
        smp_info_dict, mesh_dict = self._DeserializeDictionary(serialized_smp)

        nodes_read = {}
        geom_entities_read = {}
        if "nodes_read" in serialized_smp:
            nodes_read  = self._DeserializeNodesRead(serialized_smp["nodes_read"])
            if "geom_entities_read" in serialized_smp: # Geometric Entities can only exist if there are nodes!
                geom_entities_read = self._DeserializeGeomEntitiesRead(serialized_smp["geom_entities_read"])

        self.FillWithEntities(smp_info_dict, mesh_dict, nodes_read, geom_entities_read)

        global_utils.LogDebug("Deserialized " + smp_name)


    def _DeserializeDictionary(self, serialized_smp):
        # concert the keys to strings (has to be done bcs json converts ints to string)
        if not "submodelpart_information" in serialized_smp:
            raise Exception("\"submodelpart_information\" is not in serialized SubModelPart!")

        if not "mesh_information" in serialized_smp:
            raise Exception("\"mesh_information\" is not in serialized SubModelPart!")
        
        mesh_dict = global_utils.CorrectMeshDict(serialized_smp["mesh_information"])

        return serialized_smp["submodelpart_information"], mesh_dict

    
    def _DeserializeNodesRead(self, serialized_nodes_read):
        return global_utils.DictKeyToInt(serialized_nodes_read) # Nodes don't need deserialization


    def _DeserializeGeomEntitiesRead(self, serialized_geom_entities_read):
        deserialized_geom_entities_read = {}
        
        for serialized_entity in serialized_geom_entities_read:
            # serialized_entity = [self.salome_ID, self.salome_identifier, self.node_list]
            salome_ID         = serialized_entity[0]
            salome_identifier = serialized_entity[1]
            node_list         = serialized_entity[2]
    
            geom_entity = global_utils.GeometricEntitySalome(salome_ID, salome_identifier, node_list)
            
            if salome_identifier not in deserialized_geom_entities_read: # geom entities with this identifier are already existing # TODO don't I have to use .key() here?
                deserialized_geom_entities_read[salome_identifier] = []

            deserialized_geom_entities_read[salome_identifier].append(geom_entity)
        
        return deserialized_geom_entities_read        
        
    
    def GetGeomEntites(self):
        return self.geom_entities_read
    
    
    def Assemble(self):
        # This function creates the Kratos entities from the read entities  
        # that are defined in it's dictionary
        if (self.mesh_dict_used_for_assembly != self.mesh_dict and
            self.smp_info_dict_used_for_assembly != self.smp_info_dict):
        
            self.smp_info_dict_used_for_assembly = self.smp_info_dict
            self.mesh_dict_used_for_assembly = self.mesh_dict
            
            self._AddNodes()
            self._AddElements()
            self._AddConditions()
        
    
    def _AddNodes(self):
        self.nodes = self.nodes_read 
        
        
    def _AddElements(self):
        self.elements.clear()

        for salome_identifier in self.mesh_dict["entity_creation"].keys():
            if salome_identifier == global_utils.NODE_IDENTIFIER:
                entities = self.nodes
            else:
                entities = self.geom_entities_read[salome_identifier]
                
            if "Element" in self.mesh_dict["entity_creation"][salome_identifier]:
                element_dict = self.mesh_dict["entity_creation"][salome_identifier]["Element"]
                element_list = element_dict.keys()
                for element_name in sorted(element_list):
                    if element_name not in self.elements:
                        self.elements[element_name] = []
                    
                    property_ID = element_dict[element_name]
            
                    for entity in entities: # Node IDs or GeometricEntities
                        self.elements[element_name].append(Element(entity, element_name, property_ID))
        
        
    def _AddConditions(self):
        self.conditions.clear()

        for salome_identifier in self.mesh_dict["entity_creation"].keys():
            if salome_identifier == global_utils.NODE_IDENTIFIER:
                entities = self.nodes
            else:
                entities = self.geom_entities_read[salome_identifier]
            
            if "Condition" in self.mesh_dict["entity_creation"][salome_identifier]:
                condition_dict = self.mesh_dict["entity_creation"][salome_identifier]["Condition"]
                condition_list = condition_dict.keys()
                for condition_name in sorted(condition_list):
                    if condition_name not in self.conditions:
                        self.conditions[condition_name] = []
                    
                    property_ID = condition_dict[condition_name]
                        
                    for entity in entities: # Node IDs or GeometricEntities
                        self.conditions[condition_name].append(Condition(entity, condition_name, property_ID))        
    
    def GetMesh(self):
        return self.nodes, self.elements, self.conditions
    
    def GetInfoDict(self):
        return self.smp_info_dict
    
    def GetMeshInfoDict(self):
        return self.mesh_dict

    def NumberOfNodes(self):
        return len(self.nodes)

    def NumberOfElements(self):
        return sum([len(val) for val in self.elements.values()])

    def NumberOfConditions(self):
        return sum([len(val) for val in self.conditions.values()])

    def GetFileName(self):
        return self.smp_info_dict["smp_file_name"]
    
    def GetFilePath(self):
        return self.smp_info_dict["smp_file_path"]

    
    def WriteMesh(self, file):
        # Write Header
        if self.mesh_dict["write_smp"]:
            smp_name = self.smp_info_dict["smp_name"]
            file.write("Begin SubModelPart " + smp_name + "\n")
            
            space = ""
            if global_utils.GetReadableMDPA():
                space = "\t"

            # Write Nodes
            self._WriteNodes(file, space)
            
            # Write Elements
            self._WriteElements(file, space)
            
            # Write Conditions
            self._WriteConditions(file, space)
            
            file.write("End SubModelPart // " + smp_name + "\n\n")
        
            
    def _WriteNodes(self, file, space):
        file.write(space + "Begin SubModelPartNodes\n")

        for ID in sorted(self.nodes.keys()):
            file.write(space + space + str(ID) + "\n")
        
        file.write(space + "End SubModelPartNodes\n")
        
        
    def _WriteElements(self, file, space):
        file.write(space + "Begin SubModelPartElements \n")
        
        for element_name in sorted(self.elements.keys()):
            for elem in self.elements[element_name]:
                file.write(space + space + str(elem.GetID()) + "\n")
            
        file.write(space + "End SubModelPartElements \n")
        
        
    def _WriteConditions(self, file, space):
        file.write(space + "Begin SubModelPartConditions \n")
        
        for condition_name in sorted(self.conditions.keys()):
            for cond in self.conditions[condition_name]:
                file.write(space + space + str(cond.GetID()) + "\n")
            
        file.write(space + "End SubModelPartConditions \n")


    def WriteMeshInfo(self, file):
        if self.mesh_dict["write_smp"]: 
            file.write("// SubModelPart " + self.smp_info_dict["smp_name"] + "\n")
            file.write("//   Number of Nodes: " + str(self.NumberOfNodes()) + "\n")
            file.write("//   Number of Elements: " + str(self.NumberOfElements()) + "\n")
            file.write("//   Number of Conditions: " + str(self.NumberOfConditions()) + "\n")