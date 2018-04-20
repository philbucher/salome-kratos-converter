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
        if self.is_node:
            stringbuf += "; OriginEntity: " + str(self.origin_entity)
        else:
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
        return self.origin_entity.GetEntityData()

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
        self._Initialize()


    def _Initialize(self):
        self.sub_model_parts = {}
        self.mesh_read = False


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
        for smp in model_part.SubModelParts:
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
        self.is_properly_initialized = False
        self.is_assembled = False


    def _Initialize(self):
        self.nodes = {}
        self.elements = {}
        self.conditions = {}


    def FillWithEntities(self, smp_info_dict, mesh_dict, nodes_read, geom_entities_read):
        self.smp_info_dict = smp_info_dict
        self.mesh_dict = mesh_dict
        self.nodes_read = nodes_read
        self.geom_entities_read = geom_entities_read
        self._Initialize()
        self.is_properly_initialized = True


    def Update(self, smp_info_dict, mesh_dict):
        if self.is_properly_initialized:
            self.smp_info_dict = smp_info_dict
            self.mesh_dict = mesh_dict
            self.is_assembled = False
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")


    def Serialize(self):
        if self.is_properly_initialized:
            global_utils.LogDebug("Serializing " + self.smp_info_dict["smp_name"])
            serialized_smp = {}

            serialized_smp["submodelpart_information"] = self.smp_info_dict
            serialized_smp["mesh_information"] = self.mesh_dict
            serialized_smp["nodes_read"] = self._SerializeNodesRead()
            serialized_smp["geom_entities_read"] = self._SerializeGeomEntitiesRead()

            return {self.smp_info_dict["smp_name"] : serialized_smp}
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")


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
            raise RuntimeError("\"submodelpart_information\" is not in serialized SubModelPart!")

        if not "mesh_information" in serialized_smp:
            raise RuntimeError("\"mesh_information\" is not in serialized SubModelPart!")

        mesh_dict = global_utils.CorrectMeshDict(serialized_smp["mesh_information"])

        return serialized_smp["submodelpart_information"], mesh_dict


    def _DeserializeNodesRead(self, serialized_nodes_read):
        return global_utils.DictKeyToInt(serialized_nodes_read) # Nodes don't need deserialization


    def _DeserializeGeomEntitiesRead(self, serialized_geom_entities_read):
        deserialized_geom_entities_read = {}

        for serialized_entity in serialized_geom_entities_read:
            geom_entity = global_utils.GeometricEntity.Deserialize(serialized_entity)

            geometry_identifier = geom_entity.GetGeometryIdentifier()

            if geometry_identifier not in deserialized_geom_entities_read.keys(): # geom entities with this identifier are already existing # TODO don't I have to use .key() here?
                deserialized_geom_entities_read[geometry_identifier] = []

            deserialized_geom_entities_read[geometry_identifier].append(geom_entity)

        return deserialized_geom_entities_read


    def GetGeomEntites(self):
        return self.geom_entities_read

    def GetNodeIds(self):
        if self.is_properly_initialized:
            if self.is_assembled:
                return list(self.nodes.keys())
            else:
                raise RuntimeError("MeshSubmodelPart was not assembled!")
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")

    def GetElementIds(self):
        return self.__GetGeometricEntityIds(self.elements)


    def GetConditionIds(self):
        return self.__GetGeometricEntityIds(self.conditions)


    def __GetGeometricEntityIds(self, entities):
        if self.is_properly_initialized:
            if self.is_assembled:
                entity_ids = []
                for entities_per_name in entities.values():
                    for entity in entities_per_name:
                        entity_ids.append(entity.GetID())

                return sorted(entity_ids)
            else:
                raise RuntimeError("MeshSubmodelPart was not assembled!")
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")


    def Assemble(self):
        if self.is_properly_initialized:
            # This function creates the Kratos entities from the read entities
            # that are defined in it's dictionary
            self._AddNodes()
            self._AddElements()
            self._AddConditions()

            self.is_assembled = True
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")


    def _AddNodes(self):
        self.nodes = self.nodes_read


    def _AddElements(self):
        self.elements.clear()

        for geometry_identifier in self.mesh_dict["entity_creation"].keys():
            if geometry_identifier == global_utils.NODE_IDENTIFIER:
                entities = self._CreateGeometricEntitiesFromNodes(self.nodes)
            else:
                entities = self.geom_entities_read[geometry_identifier]

            if "Element" in self.mesh_dict["entity_creation"][geometry_identifier]:
                element_dict = self.mesh_dict["entity_creation"][geometry_identifier]["Element"]
                element_list = element_dict.keys()
                for element_name in sorted(element_list):
                    if element_name not in self.elements:
                        self.elements[element_name] = []

                    property_ID = element_dict[element_name]

                    for entity in entities:
                        elem = entity.GetChildObject(element_name, Element, property_ID)
                        self.elements[element_name].append(elem)


    def _AddConditions(self):
        self.conditions.clear()

        for geometry_identifier in self.mesh_dict["entity_creation"].keys():
            if geometry_identifier == global_utils.NODE_IDENTIFIER:
                entities = self._CreateGeometricEntitiesFromNodes(self.nodes)
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


    def _CreateGeometricEntitiesFromNodes(self, nodes):
        geom_entities = []

        for node_id, node_data in nodes.items():
            nodal_data = node_data[1]
            geom_entities.append(global_utils.GeometricEntity(-1,
                                                              global_utils.NODE_IDENTIFIER,
                                                              [node_id],
                                                              nodal_data))

        return geom_entities

    def GetMesh(self):
        if self.is_properly_initialized:
            if self.is_assembled:
                return self.nodes, self.elements, self.conditions
            else:
                raise RuntimeError("MeshSubmodelPart was not assembled!")
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")

    def GetInfoDict(self):
        if self.is_properly_initialized:
            return self.smp_info_dict
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")

    def GetMeshInfoDict(self):
        if self.is_properly_initialized:
            return self.mesh_dict
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")

    def GetFileName(self):
        if self.is_properly_initialized:
            return self.smp_info_dict["smp_file_name"]
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")

    def GetFilePath(self):
        if self.is_properly_initialized:
            return self.smp_info_dict["smp_file_path"]
        else:
            raise RuntimeError("MeshSubmodelPart is not properly initialized!")
