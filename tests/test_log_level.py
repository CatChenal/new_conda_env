# test_log_level.py

import os
import sys
from pathlib import Path
from logging import getLogger

import unittest
from unittest import mock, TestCase
from new_conda_env import envir


########## WIP ##########

mocker = MagicMock()
"""
@mock.patch('library.library.Library.query_fun')
def test_get_response(self, mock_query_fun):
    mock_query_fun.return_value = {
        'text': 'Hi',
        'entities': 'value'
        }
    }
    response = MockBotter.get_response()
    self.assertIsNotNone(response)
    
@mock.patch('new_conda_env.envir.CondaEnvir.create_new_env_yaml')
def test_get_response(self, mock_create_new_env_yaml):
    mock_create_new_env_yaml.return_value = Path().home()
    response = MockBotter.get_response()
    self.assertIsNotNone(response)    
"""

class CondaEnvirTestCase(unittest.TestCase):

    def test_create_class_call_method(self):
        # Create a mock to return for MyClass.
        m = mock.MagicMock()
        # Patch my_method's return value.
        m.create_new_env_yaml() = mock.Mock(return_value=Path().home())

        # Patch MyClass. Here, we could use autospec=True for more
        # complex classes.
        with patch('tmp.my_module.MyClass', return_value=m) as p:
            value = my_module.create_class_call_method()

        # Method should be called once.
        p.assert_called_once()
        # In the original my_method, we would get a return value of 1.
        # However, if we successfully patched it, we'll get a return
        # value of 2.
        self.assertEqual(value, 2)


if __name__ == '__main__':
    unittest.main()
