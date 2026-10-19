import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

from agentglass.cli import main


class CLITests(unittest.TestCase):
    def test_demo_inspect_validate_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.jsonl"
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["demo", "--output", str(path)]), 0)
            self.assertTrue(path.exists())
            self.assertIn("No external model", output.getvalue())
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["validate", str(path)]), 0)
                self.assertEqual(main(["inspect", str(path)]), 0)
                self.assertEqual(main(["summary", str(path)]), 0)


if __name__ == "__main__":
    unittest.main()
