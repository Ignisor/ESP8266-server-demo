import esp; esp.osdebug(None)

import gc

from utils import wifi
from utils.pins import LED, ON

wifi.toggle_wifi(False)
wifi.toggle_hotspot(True)

LED.value(ON)

gc.collect()
