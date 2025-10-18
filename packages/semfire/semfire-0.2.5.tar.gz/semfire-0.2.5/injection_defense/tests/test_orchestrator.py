import os
import sys
import json
import unittest
from unittest import mock

import scripts.orchestrator as orchestrator

class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self._orig_argv = sys.argv.copy()
        self._orig_env = os.environ.copy()

    def tearDown(self):
        sys.argv = self._orig_argv
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_usage_no_args(self):
        sys.argv = ['orchestrator.py']
        os.environ['OPENAI_API_KEY'] = 'dummy'
        with self.assertRaises(SystemExit) as cm:
            orchestrator.main()
        self.assertIn('Usage: orchestrator.py', str(cm.exception))

    def test_missing_api_key(self):
        sys.argv = ['orchestrator.py', 'prompt']
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        with self.assertRaises(SystemExit) as cm:
            orchestrator.main()
        self.assertEqual(str(cm.exception), 'Error: OPENAI_API_KEY not set')

    def test_invalid_json_response(self):
        sys.argv = ['orchestrator.py', 'prompt']
        os.environ['OPENAI_API_KEY'] = 'dummy'
        mock_resp = mock.Mock()
        mock_resp.choices = [mock.Mock(message=mock.Mock(content='not a json'))]
        with mock.patch('scripts.orchestrator.openai.ChatCompletion.create', return_value=mock_resp):
            with self.assertRaises(SystemExit) as cm:
                orchestrator.main()
            self.assertIn('Failed to parse JSON', str(cm.exception))

    def test_valid_response_prints_plan(self):
        sys.argv = ['orchestrator.py', 'compute 2 plus 3']
        os.environ['OPENAI_API_KEY'] = 'dummy'
        plan = {"action": "add", "args": {"a": 2, "b": 3}}
        content = json.dumps(plan)
        mock_resp = mock.Mock()
        mock_resp.choices = [mock.Mock(message=mock.Mock(content=content))]
        with mock.patch('scripts.orchestrator.openai.ChatCompletion.create', return_value=mock_resp):
            with mock.patch('builtins.print') as mock_print:
                orchestrator.main()
                mock_print.assert_called_once_with(json.dumps(plan))

if __name__ == '__main__':
    unittest.main()