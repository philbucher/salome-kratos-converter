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

READABLE_MDPA = True

class KratosEntity:
    def __init__(self, origin_entity, name, property_ID):
        self.origin_entity = origin_entity
        self.name = name
        self.property_ID = property_ID
        self.new_ID = -1
        self.is_added_already = False

    def __str__(self):
        stringbuf = "Name: " + self.name
        stringbuf += "; PropID: " + str(self.property_ID)
        stringbuf += "; NewId: " + str(self.new_ID)
        '''
        if self.is_node:
            stringbuf += "; OriginEntity: " + str(self.origin_entity)
        else:
            stringbuf += "; OriginEntity: " + str(self.origin_entity)
        '''
        stringbuf += "; OriginEntity: " + str(self.origin_entity)

        return stringbuf

    __repr__ = __str__

    def __eq__(self, Other):
        if self.origin_entity != Other.origin_entity:
            return False
        if self.name != Other.name:
            return False
        if self.property_ID != Other.property_ID:
            return False
        return True

    def SetIsAdded(self):
        self.is_added_already = True

    def IsAddedAlready(self):
        return self.is_added_already

    def ResetWritingInfo(self):
        self.new_ID = -1
        self.is_added_already = False

    def SetID(self, new_id):
        self.new_ID = new_id

    def GetID(self):
        if self.new_ID == -1:
            raise RuntimeError("No new ID has been assiged")
        return self.new_ID

    def GetNodeList(self):
        return self.origin_entity.GetNodeList()

    def HasEntityData(self):
        return self.origin_entity.HasEntityData()

    def GetEntityData(self):
        return self.origin_entity.GetEntityData()



class Element(KratosEntity):
    def __init__(self, origin_entity, name, property_ID):
        super().__init__(origin_entity, name, property_ID)

    def __str__(self):
        return "Element | " + super().__str__()

    __repr__ = __str__



class Condition(KratosEntity):
    def __init__(self, origin_entity, name, property_ID):
        super().__init__(origin_entity, name, property_ID)

    def __str__(self):
        return "Condition | " + super().__str__()

    __repr__ = __str__



class MainModelPart:
    def __init__(self):
        self.__Initialize()


    def __Initialize(self):
        self.sub_model_parts = {}
        self.mesh_read = False


    def GetMeshRead(self):
        return self.mesh_read


    def GetSubModelPart(self, smp_name):
        if smp_name in self.sub_model_parts:
            return self.sub_model_parts[smp_name]


    def Reset(self):
        self.__Initialize()


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
        if smp_name in self.sub_model_parts.keys():
            raise NameError("SubModelPart \"" + smp_name + "\" exists already!")

        self.sub_model_parts[smp_name] = MeshSubmodelPart()
        self.sub_model_parts[smp_name].FillWithEntities(smp_info_dict, mesh_dict, nodes_read, geom_entities_read)

        self.mesh_read = True


    def UpdateMesh(self, old_smp_name, smp_info_dict, mesh_dict):
        new_smp_name = smp_info_dict["smp_name"]
        if old_smp_name not in self.sub_model_parts.keys():
            raise NameError("SubModelPart \"" + old_smp_name + "\" does not exist!")
        self.sub_model_parts[new_smp_name] = self.sub_model_parts.pop(old_smp_name) # Update the key

        self.sub_model_parts[new_smp_name].Update(smp_info_dict, mesh_dict)


    def RemoveSubmodelPart(self, name_smp):
        self.sub_model_parts.pop(name_smp, None)


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


    def GetTreeItems(self):
        return sorted(self.sub_model_parts.keys()) # return sorted bcs it is also sorted in the json format!


    def WriteMesh(self, mdpa_file_name, info_text=""):
        try:
            if mdpa_file_name.endswith('.mdpa'):
                mdpa_file_name = mdpa_file_name[:-5]
            import KratosMultiphysics
            import KratosMultiphysics.FluidDynamicsApplication
            import KratosMultiphysics.StructuralMechanicsApplication

            model_part = KratosMultiphysics.ModelPart()

            self.__AssembleMesh(model_part)

            file = open(mdpa_file_name + ".mdpa","w")
            self.__WriteModelPartInfo(model_part, file, info_text)
            file.close()

            # using append bcs some info was written beforehand
            model_part_io = KratosMultiphysics.ReorderConsecutiveModelPartIO(mdpa_file_name,
                                                                             KratosMultiphysics.IO.APPEND)
            model_part_io.WriteModelPart(model_part)

            return True

        except ImportError:
            global_utils.LogError("Loading Kratos failed!")
            return False


    def __WriteModelPartInfo(self, model_part,
                             open_file, info_text=""):
        '''
        Writing some information about the ModelPart to the mdpa file
        '''
        import time
        localtime = time.asctime( time.localtime(time.time()) )
        open_file.write("// File created on " + localtime + "\n")
        if info_text != "":
            open_file.write("// " + info_text + "\n")
        open_file.write("// Mesh Information:\n")
        open_file.write("// Number of Nodes: " + str(model_part.NumberOfNodes()) + "\n")
        open_file.write("// Number of Elements: " + str(model_part.NumberOfElements()) + "\n")
        open_file.write("// Number of Conditions: " + str(model_part.NumberOfConditions()) + "\n")
        open_file.write("// Number of SubModelParts: " + str(model_part.NumberOfSubModelParts()) + "\n")
        for smp in model_part.SubModelParts: # TODO sort
            open_file.write("// SubModelPart " + smp.Name + "\n")
            open_file.write("//   Number of Nodes: " + str(smp.NumberOfNodes()) + "\n")
            open_file.write("//   Number of Elements: " + str(smp.NumberOfElements()) + "\n")
            open_file.write("//   Number of Conditions: " + str(smp.NumberOfConditions()) + "\n")
        open_file.write("\n")


    def __AssembleMesh(self, model_part):
        all_nodes = {}
        all_elements = {}
        all_conditions = {}

        for smp_name, smp in self.sub_model_parts.items():
            smp.Assemble()
            smp_nodes, smp_elements, smp_conditions = smp.GetMesh()
            self.__AssembleNodes(smp_nodes, all_nodes)
            self.__AssembleGeometricEntities(smp_elements,   all_elements)
            self.__AssembleGeometricEntities(smp_conditions, all_conditions)

        self.__AddNodes(all_nodes, model_part)
        self.__AddGeometricEntities(all_elements, model_part, "Element")
        self.__AddGeometricEntities(all_conditions, model_part, "Condition")

        for smp_name, smp in self.sub_model_parts.items():
            self.__AddSubModelPart(smp_name, smp, model_part)


    def __AssembleNodes(self, smp_nodes, all_nodes):
        for node_ID in smp_nodes.keys():
            if node_ID in all_nodes.keys():
                existing_node_coords = all_nodes[node_ID][0]
                if existing_node_coords != smp_nodes[node_ID][0]:
                    err_msg =  'Node with ID" ' + str(node_ID) + '" already exists with different coordinates!\n'
                    err_msg += 'Existing Cooridnates: ' + str(existing_node_coords) + '\n'
                    err_msg += 'New Coordinates: ' + str(smp_nodes[node_ID])
                    raise RuntimeError(err_msg)
            else:
                all_nodes[node_ID] = smp_nodes[node_ID]


    def __AddNodes(self, all_nodes, model_part):
        for node_ID in sorted(all_nodes.keys()):
            this_node = all_nodes[node_ID]
            node_coords = this_node[0]
            n_x = node_coords[0]
            n_y = node_coords[1]
            n_z = node_coords[2]
            kratos_node = model_part.CreateNewNode(node_ID, n_x, n_y, n_z) # Id, X, Y, Z

            nodal_data = this_node[1]
            if len(nodal_data) > 0: # NodalData to write is present
                for var, value in nodal_data.items():
                    variable = KratosMultiphysics.KratosGlobals.GetVariable(var)
                    kratos_node.SetSolutionStepValue(variable,0,value)


    def __AssembleGeometricEntities(self, smp_entities, all_entities):
        id_index = sum([len(val) for val in all_entities.values()]) + 1
        for entity_name in sorted(smp_entities.keys()):
            entities = smp_entities[entity_name]

            if entity_name not in all_entities.keys():
                all_entities[entity_name] = []

            for entity in entities:
                if not entity.IsAddedAlready():
                    all_entities[entity_name].append(entity)
                    entity.SetID(id_index)
                    entity.SetIsAdded()
                    id_index += 1


    def __AddGeometricEntities(self, all_entities, model_part, entity_type):
        if entity_type == "Element":
            fct_ptr = model_part.CreateNewElement
        elif entity_type == "Condition":
            fct_ptr = model_part.CreateNewCondition
        else:
            raise Exception("Wrong entity type")

        prop = model_part.GetProperties()[0]

        for entity_name, entities in all_entities.items():
            for entity in entities:
                entity_id = entity.GetID()
                entity_nodes = entity.GetNodeList()

                kratos_entity = fct_ptr(entity_name, entity_id, entity_nodes, prop)

                if entity.HasEntityData():
                    for var, value in entity.GetEntityData().items():
                        variable = KratosMultiphysics.KratosGlobals.GetVariable(var)
                        kratos_entity.SetValue(variable,0,value)


    def __AddSubModelPart(self, smp_name, smp, model_part):
        kratos_smp = model_part.CreateSubModelPart(smp_name)

        kratos_smp.AddNodes(smp.GetNodeIds())
        kratos_smp.AddElements(smp.GetElementIds())
        kratos_smp.AddConditions(smp.GetConditionIds())


class MeshSubmodelPart:
    def __init__(self):
        """Constructor of the MeshSubModelPart
        Sets some internal variables
        """
        self.is_properly_initialized = False
        self.is_assembled = False


    def __InitializeMesh(self):
        """This function initializes the member variables for the mesh
        """
        self.nodes = {}
        self.elements = {}
        self.conditions = {}


    def FillWithEntities(self, smp_info_dict, mesh_dict, nodes_read, geom_entities_read):
        """This function fills the MeshSubModelPart with entities
        This function has to be called before other operations such
        as assembling can be performed
        """
        self.__ValidateSMPInfoDict(smp_info_dict)
        self.smp_info_dict = smp_info_dict

        self.__ValidateMeshDict(mesh_dict)
        self.mesh_dict = mesh_dict

        self.nodes_read = nodes_read
        self.geom_entities_read = geom_entities_read
        self.is_properly_initialized = True


    def Update(self, smp_info_dict, mesh_dict):
        """This function updates the MeshSubModelPart
        E.g. if different Elements/Conditions should
        be created from the Geometric Entities
        """
        self.__CheckIsProperlyInitialized()

        self.__ValidateSMPInfoDict(smp_info_dict)
        self.smp_info_dict = smp_info_dict

        self.__ValidateMeshDict(mesh_dict)
        self.mesh_dict = mesh_dict

        self.is_assembled = False


    def __ValidateSMPInfoDict(self, smp_info_dict):
        """This function adds missing information to the
        dictionary based on default values.
        It mimics the "ValidateAndAssignDefaults" function in Kratos
        """
        default_smp_info_dict = {
            "smp_name"      : "PLEASE_SPECIFY_SUBMODELPART_NAME",
            "smp_file_name" : "default",
            "smp_file_path" : "default"
        }

        for k,v in default_smp_info_dict.items():
            if k not in smp_info_dict:
                smp_info_dict[k] = v # Assigning the default value


    def __ValidateMeshDict(self, mesh_dict):
        """This function adds missing information to the
        dictionary based on default values.
        It mimics the "ValidateAndAssignDefaults" function in Kratos
        """
        default_mesh_dict = {
            "entity_creation" : {},
            "write_smp"       : True
        }

        for k,v in default_mesh_dict.items():
            if k not in mesh_dict:
                mesh_dict[k] = v # Assigning the default value


    def Assemble(self):
        """This function assembles the entities in the MeshSubModelPart
        After this operation the Object is ready to write it's
        entities to an mdpa file
        """
        self.__CheckIsProperlyInitialized()
        self.__InitializeMesh()

        # This function creates the Kratos entities from the read entities
        # that are defined in it's dictionary
        self.__AddNodes()
        self.__AddElements()
        self.__AddConditions()

        self.is_assembled = True


    def __AddNodes(self):
        self.nodes = self.nodes_read


    def __AddElements(self):
        self.elements.clear()

        for geometry_identifier in self.mesh_dict["entity_creation"].keys():
            if geometry_identifier == global_utils.NODE_IDENTIFIER:
                entities = self.__CreateGeometricEntitiesFromNodes(self.nodes)
            else:
                entities = self.geom_entities_read[geometry_identifier]

            if "Element" in self.mesh_dict["entity_creation"][geometry_identifier]:
                element_dict = self.mesh_dict["entity_creation"][geometry_identifier]["Element"]
                element_list = element_dict.keys()
                for element_name in sorted(element_list):
                    if element_name not in self.elements:
                        self.elements[element_name] = []
                    print(element_dict)
                    property_ID = element_dict[element_name]

                    for entity in entities:
                        elem = entity.GetChildObject(element_name, Element, property_ID)
                        self.elements[element_name].append(elem)


    def __AddConditions(self):
        self.conditions.clear()

        for geometry_identifier in self.mesh_dict["entity_creation"].keys():
            if geometry_identifier == global_utils.NODE_IDENTIFIER:
                entities = self.__CreateGeometricEntitiesFromNodes(self.nodes)
            else:
                entities = self.geom_entities_read[geometry_identifier]

            if "Condition" in self.mesh_dict["entity_creation"][geometry_identifier]:
                condition_dict = self.mesh_dict["entity_creation"][geometry_identifier]["Condition"]
                condition_list = condition_dict.keys()
                for condition_name in sorted(condition_list):
                    if condition_name not in self.conditions:
                        self.conditions[condition_name] = []

                    property_ID = condition_dict[condition_name]

                    for entity in entities:
                        cond = entity.GetChildObject(condition_name, Condition, property_ID)
                        self.conditions[condition_name].append(cond)


    def __CreateGeometricEntitiesFromNodes(self, nodes):
        geom_entities = []

        for node_id, node_data in nodes.items():
            nodal_data = node_data[1]
            geom_entities.append(global_utils.GeometricEntity(-1,
                                                              global_utils.NODE_IDENTIFIER,
                                                              [node_id],
                                                              nodal_data))

        return geom_entities

    def GetMesh(self):
        self.__CheckIsAssembled()
        return self.nodes, self.elements, self.conditions

    def GetGeomEntites(self): # TODO still needed?
        return self.geom_entities_read

    def GetInfoDict(self):
        self.__CheckIsProperlyInitialized()
        return self.smp_info_dict

    def GetMeshInfoDict(self):
        self.__CheckIsProperlyInitialized()
        return self.mesh_dict

    def GetFileName(self):
        self.__CheckIsProperlyInitialized()
        return self.smp_info_dict["smp_file_name"]

    def GetFilePath(self):
        self.__CheckIsProperlyInitialized()
        return self.smp_info_dict["smp_file_path"]

    def NumberOfNodes(self):
        """Returns the number of Nodes in this SubModelPart
        """
        self.__CheckIsAssembled()
        return len(self.nodes)

    def NumberOfElements(self):
        """Returns the number of Elements in this SubModelPart
        """
        self.__CheckIsAssembled()
        return sum([len(val) for val in self.elements.values()])

    def NumberOfConditions(self):
        """Returns the number of Conditions in this SubModelPart
        """
        self.__CheckIsAssembled()
        return sum([len(val) for val in self.conditions.values()])

    def WriteMesh(self, file):
        """This function writes the SubModelPart to the
        mdpa-file (If wanted).
        """
        self.__CheckIsAssembled()

        # Write Header
        if self.mesh_dict["write_smp"]:
            smp_name = self.smp_info_dict["smp_name"]
            file.write("Begin SubModelPart " + smp_name + "\n")

            space = ""
            if READABLE_MDPA:
                space = "\t"

            self.__WriteNodes(file, space)
            self.__WriteElements(file, space)
            self.__WriteConditions(file, space)

            file.write("End SubModelPart // " + smp_name + "\n\n")


    def __WriteNodes(self, file, space):
        """This function write the SubModelPartNodes to the
        mdpa-file.
        Note that these are only the Ids of the Nodes
        """
        self.__CheckIsAssembled()

        file.write(space + "Begin SubModelPartNodes\n")

        for ID in sorted(self.nodes.keys()):
            file.write(space + space + str(ID) + "\n")

        file.write(space + "End SubModelPartNodes\n")


    def __WriteElements(self, file, space):
        """This function write the SubModelPartElements to the
        mdpa-file.
        """
        self.__WriteEntityIds(file, space, "Elements", self.elements)


    def __WriteConditions(self, file, space):
        """This functin write the SubModelPartConditions to the
        mdpa-file.
        """
        self.__WriteEntityIds(file, space, "Conditions", self.conditions)


    def __WriteEntityIds(self, file, space, entity_type_name, entities):
        """This function writes the Ids of the entities to the
        mdpa file.
        Note that these are only the Ids of the entities
        """
        self.__CheckIsAssembled()

        smp_entities_name = "SubModelPart" + entity_type_name

        file.write(space + "Begin " + smp_entities_name + "\n")

        for entity_name in sorted(entities.keys()):
            for entity in entities[entity_name]:
                file.write(space + space + str(entity.GetID()) + "\n")

        file.write(space + "End " + smp_entities_name + "\n")


    def WriteMeshInfo(self, file):
        """This function is called by the parent class to write info about this
        SubModelPart to the header of the mdpa-file
        """
        self.__CheckIsAssembled()
        if self.mesh_dict["write_smp"]:
            file.write("// SubModelPart " + self.smp_info_dict["smp_name"] + "\n")
            file.write("//   Number of Nodes: " + str(self.NumberOfNodes()) + "\n")
            file.write("//   Number of Elements: " + str(self.NumberOfElements()) + "\n")
            file.write("//   Number of Conditions: " + str(self.NumberOfConditions()) + "\n")


    def __CheckIsAssembled(self):
        """This function checks if the MeshSubModelPart has been assembled
        It is used internally to ensure that the MeshSubModelPart is assembled
        """
        self.__CheckIsProperlyInitialized()
        if not self.is_assembled:
            raise RuntimeError("MeshSubmodelPart was not assembled!")


    def __CheckIsProperlyInitialized(self):
        """This function checks if the MeshSubModelPart has been properly initialized
        It is used internally to ensure that the MeshSubModelPart is properly initialized
        """
        if not self.is_properly_initialized:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")

    ##############################################
    ##### Functions related to Serialization #####
    ##############################################
    def Serialize(self):
        self.__CheckIsProperlyInitialized()

        global_utils.LogDebug("Serializing " + self.smp_info_dict["smp_name"])
        serialized_smp = {}

        serialized_smp["submodelpart_information"] = self.smp_info_dict
        serialized_smp["mesh_information"] = self.mesh_dict
        serialized_smp["nodes_read"] = self.__SerializeNodesRead()
        serialized_smp["geom_entities_read"] = self.__SerializeGeomEntitiesRead()

        return {self.smp_info_dict["smp_name"] : serialized_smp}


    def __SerializeNodesRead(self):
        self.__AddNodes() # Update the internal information
        return self.nodes


    def __SerializeGeomEntitiesRead(self):
        serialized_geom_entities = []

        for salome_ID in self.geom_entities_read:
            for entity in self.geom_entities_read[salome_ID]:
                serialized_geom_entities.append(entity.Serialize())

        return serialized_geom_entities


    def Deserialize(self, smp_name, serialized_smp):
        smp_info_dict, mesh_dict = self.__DeserializeDictionary(serialized_smp)

        nodes_read = {}
        geom_entities_read = {}
        if "nodes_read" in serialized_smp:
            nodes_read  = self.__DeserializeNodesRead(serialized_smp["nodes_read"])
            if "geom_entities_read" in serialized_smp: # Geometric Entities can only exist if there are nodes!
                geom_entities_read = self.__DeserializeGeomEntitiesRead(serialized_smp["geom_entities_read"])

        self.FillWithEntities(smp_info_dict, mesh_dict, nodes_read, geom_entities_read)

        global_utils.LogDebug("Deserialized " + smp_name)


    def __DeserializeDictionary(self, serialized_smp):
        # concert the keys to strings (has to be done bcs json converts ints to string)
        if not "submodelpart_information" in serialized_smp:
            raise RuntimeError("\"submodelpart_information\" is not in serialized SubModelPart!")

        if not "mesh_information" in serialized_smp:
            raise RuntimeError("\"mesh_information\" is not in serialized SubModelPart!")

        mesh_dict = global_utils.CorrectMeshDict(serialized_smp["mesh_information"])

        return serialized_smp["submodelpart_information"], mesh_dict


    def __DeserializeNodesRead(self, serialized_nodes_read):
        return global_utils.DictKeyToInt(serialized_nodes_read) # Nodes don't need deserialization


    def __DeserializeGeomEntitiesRead(self, serialized_geom_entities_read):
        deserialized_geom_entities_read = {}

        for serialized_entity in serialized_geom_entities_read:
            geom_entity = global_utils.GeometricEntity.Deserialize(serialized_entity)

            geometry_identifier = geom_entity.GetGeometryIdentifier()

            if geometry_identifier not in deserialized_geom_entities_read.keys(): # geom entities with this identifier are already existing # TODO don't I have to use .key() here?
                deserialized_geom_entities_read[geometry_identifier] = []

            deserialized_geom_entities_read[geometry_identifier].append(geom_entity)

        return deserialized_geom_entities_read