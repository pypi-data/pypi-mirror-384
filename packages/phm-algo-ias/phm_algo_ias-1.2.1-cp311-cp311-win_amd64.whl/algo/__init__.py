__version__ = '0.0.2'

from . import HI
from . import RUL
# print('pythonds was called')

try:
    from ._version import version as __version__
except Exception:  # 後備（理論上不太會用到）
    __version__ = "0.0.0"
