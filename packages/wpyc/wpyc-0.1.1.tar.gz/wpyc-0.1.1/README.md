# WPYC

Write Python code object to .pyc file.

```
from wpyc import write_pyc

code = compile(f"print('Hello, World!')", "<string>", "exec")

code_bytes = marshal.dumps(code)

write_pyc(code_bytes, "output.pyc")
```
