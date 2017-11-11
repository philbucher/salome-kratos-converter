import unittest
import sys
sys.path.insert(0, '../')
import kratos_utilities as kratos_utils
import global_utilities as global_utils


class TestKratosEntity(unittest.TestCase):

    def _test_GetID(self, class2test):
        obj2test = class2test(
            salome_entity=203, name="SomeName", property_ID=5)

        with self.assertRaises(Exception):
            obj2test.GetID()

    def _test_GetWriteLineNode(self, class2test):
        """
        Here the KratosEntity is a "Node", sine it is not constructed with a Geometrical Entity
        """
        obj2test = class2test(
            salome_entity=1, name="SomeOtherName", property_ID=2)
        write_line = obj2test.GetWriteLine(
            ID=85, format_str='{} {}', space=" ")

        expected = "85 2 1"

        self.assertEqual(expected, write_line)

    def _test_GetWriteLineGeomEntity(self, class2test):
        """
        Here the KratosEntity is an "Element" or "Condition", sine it is constructed with a Geometrical Entity
        """
        geom_entity = global_utils.GeometricEntitySalome(35, 102, [1,5,9])
        obj2test = class2test(
            salome_entity=geom_entity, name="SomeOtherName", property_ID=2)
        write_line = obj2test.GetWriteLine(
            ID=85, format_str='{} {}', space=" ")

        if global_utils.GetDebug():
            expected = "85 2 1 5 9 // 35"
        else:
            expected = "85 2 1 5 9"
        
        self.assertEqual(expected, write_line)

    def _execute_entity_tests(self, class2test):
        self._test_GetID(class2test)
        self._test_GetWriteLineNode(class2test)
        self._test_GetWriteLineGeomEntity(class2test)

    def test_KratosEntity(self):
        class2test = kratos_utils.KratosEntity # "Class-Pointer"

        self._execute_entity_tests(class2test)

    def test_Element(self):
        class2test = kratos_utils.Element # "Class-Pointer"

        self._execute_entity_tests(class2test)

    def test_Condition(self):
        class2test = kratos_utils.Condition  # "Class-Pointer"

        self._execute_entity_tests(class2test)



    def test_MainModelPart(self):
        obj2test = kratos_utils.MainModelPart()

        serialized_obj = obj2test.Serialize()
        self.assertEqual({}, serialized_obj)

    def test_MeshSubmodelPart(self):
        obj2test = kratos_utils.MeshSubmodelPart()
        

if __name__ == '__main__':
    unittest.main()
