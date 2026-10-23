import contextlib
import io
import runpy
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parents[1] / "wwara-repeaterbook"
TOKEN = "SYNTHETIC-TEST-TOKEN"


class TokenNotPrintedTest(unittest.TestCase):
    def test_token_not_in_output(self):
        output = io.StringIO()
        with (
            mock.patch.dict("os.environ", {"RB_TOKEN": TOKEN}),
            mock.patch(
                "urllib.request.urlopen",
                side_effect=lambda request: io.BytesIO(b'{"results": []}'),
            ) as urlopen,
            mock.patch("wwara.database.coordinations", return_value=[]),
            contextlib.redirect_stdout(output),
            contextlib.redirect_stderr(output),
        ):
            runpy.run_path(SCRIPT)
        self.assertEqual(urlopen.call_args.args[0].get_header("X-rb-app-token"), TOKEN)
        self.assertNotIn(TOKEN, output.getvalue())


if __name__ == "__main__":
    unittest.main()
