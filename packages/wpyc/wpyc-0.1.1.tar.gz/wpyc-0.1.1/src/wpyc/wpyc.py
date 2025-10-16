import struct
import importlib.util


def write_pyc(code_bytes: bytes, output_path, magic_number=importlib.util.MAGIC_NUMBER):
    """
    Write marshalled code bytes to a .pyc file.

    Args:
        code_bytes: Bytes object from marshal.dumps(code_object)
        output_path: Path to output .pyc file
    """
    with open(output_path, "wb") as f:
        _ = f.write(magic_number)
        _ = f.write(struct.pack("<I", 0))
        _ = f.write(struct.pack("<I", 0))
        _ = f.write(struct.pack("<I", 0))
        _ = f.write(code_bytes)
