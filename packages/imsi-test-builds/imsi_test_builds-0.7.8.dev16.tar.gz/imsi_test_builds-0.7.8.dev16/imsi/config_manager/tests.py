import unittest
from unittest.mock import Mock
from config_manager import (
    Experiment, Model, Machine, JsonConfigDatabase,
    MachineFactory, Configuration, ConfigManager
)

class TestExperiment(unittest.TestCase):
    def test_experiment_creation(self):
        parameters = {'param1': 1, 'param2': 2}
        exp = Experiment(name='test_exp', parameters=parameters)
        self.assertEqual(exp.name, 'test_exp')
        self.assertEqual(exp.parameters, parameters)

class TestModel(unittest.TestCase):
    def test_model_creation(self):
        parameters = {'param1': 1, 'param2': 2}
        model = Model(name='test_model', parameters=parameters)
        self.assertEqual(model.name, 'test_model')
        self.assertEqual(model.parameters, parameters)

class TestMachine(unittest.TestCase):
    def test_machine_creation(self):
        parameters = {'param1': 1, 'param2': 2}
        machine = Machine(name='test_machine', parameters=parameters)
        self.assertEqual(machine.name, 'test_machine')
        self.assertEqual(machine.parameters, parameters)

class TestJsonConfigDatabase(unittest.TestCase):
    def setUp(self):
        self.mock_combine_configs = Mock(return_value={'mock_config': {'param1': 1}})

    def test_load_config(self):
        with unittest.mock.patch('config_manager.combine_json_configs', self.mock_combine_configs):
            json_db = JsonConfigDatabase(imsi_config_path='/mock/path')
            self.assertEqual(json_db.database, {'mock_config': {'param1': 1}})

    # Add more tests for other methods as needed

#class TestMachineFactory(unittest.TestCase):
#    # Write tests for create_from_database, get_machine_name_from_hostname, find_matching_machine, get_hostname
#
#class TestConfiguration(unittest.TestCase):
#    # Write tests for __init__
#
#class TestConfigManager(unittest.TestCase):
#    # Write tests for __init__, create_configuration, create_experiment, create_model, create_machine

if __name__ == '__main__':
    unittest.main()
