import sys
import json
import unittest
from unittest import mock

import scripts.executor as executor

class TestExecutor(unittest.TestCase):
    def setUp(self):
        self._orig_argv = sys.argv.copy()

    def tearDown(self):
        sys.argv = self._orig_argv

    def test_usage_no_args(self):
        sys.argv = ['executor.py']
        with self.assertRaises(SystemExit) as cm:
            executor.main()
        self.assertIn('Usage: executor.py', str(cm.exception))

    def test_invalid_json(self):
        sys.argv = ['executor.py', 'not a json']
        with self.assertRaises(SystemExit) as cm:
            executor.main()
        self.assertIn('Invalid JSON plan', str(cm.exception))

    def test_unknown_action(self):
        plan = {"action": "subtract", "args": {"a": 1, "b": 2}}
        sys.argv = ['executor.py', json.dumps(plan)]
        with self.assertRaises(SystemExit) as cm:
            executor.main()
        self.assertIn('Unknown action: subtract', str(cm.exception))

    def test_add(self):
        plan = {"action": "add", "args": {"a": 4, "b": 5}}
        sys.argv = ['executor.py', json.dumps(plan)]
        with mock.patch('builtins.print') as mock_print:
            executor.main()
            mock_print.assert_called_once_with(9)

    def test_multiply(self):
        plan = {"action": "multiply", "args": {"a": 6, "b": 7}}
        sys.argv = ['executor.py', json.dumps(plan)]
        with mock.patch('builtins.print') as mock_print:
            executor.main()
            mock_print.assert_called_once_with(42)

if __name__ == '__main__':
    unittest.main()