import os
import marshal

from wpyc import write_pyc

from io import StringIO
import sys


class StdoutCapture(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout


def test_wpyc_can_reexec():
    message = "Hello from pyc!"
    code = compile(f"print('{message}')", "<string>", "exec")
    code_bytes = marshal.dumps(code)

    test_file = "test.pyc"

    write_pyc(code_bytes, test_file)

    code_output = []
    with open(test_file, "rb") as f:
        _ = f.read(16)  # Discard .pyc header
        code_obj = marshal.load(f)
        with StdoutCapture() as output:
            exec(code_obj)
            code_output = output
    assert message == code_output[0]

    os.remove(test_file)
