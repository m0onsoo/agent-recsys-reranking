import subprocess
import sys
import unittest


class RuntimeDependencyTests(unittest.TestCase):
    def test_cli_import_does_not_load_torch_or_recbole(self):
        code = (
            "import sys; import agent_reranking.cli; "
            "assert 'torch' not in sys.modules; "
            "assert not any(name == 'recbole' or name.startswith('recbole.') "
            "for name in sys.modules)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
