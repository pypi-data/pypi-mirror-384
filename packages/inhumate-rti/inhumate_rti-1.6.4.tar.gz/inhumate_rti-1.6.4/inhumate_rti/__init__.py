__version__ = "1.6.4"

from . import proto
from . import constants
from . import channel
from . import capability
from .rticlient import RTIClient
Client = RTIClient
from .rtiruntimecontrol import RTIRuntimeControl
RuntimeControl = RTIRuntimeControl
from .rticommand import RTICommand
Command = RTICommand
