import os
from pathlib import Path

__version__ = "1.0.1"

_package_dir = Path(__file__).parent
_m6_library_path = _package_dir / "m6_library"
_moret_xml_lib_path = _m6_library_path / "MORET_XML_LIB"

os.environ["MORET_XML_LIB_PATH"] = str(_moret_xml_lib_path)

try:
    from .m6geo import *
except ImportError:
    pass
