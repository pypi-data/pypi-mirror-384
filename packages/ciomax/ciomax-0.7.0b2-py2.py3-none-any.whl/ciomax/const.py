import os
import pymxs

VERSION = "dev.999"
PLUGIN_DIR = os.path.dirname(__file__)
try:
    with open(os.path.join(PLUGIN_DIR, "VERSION")) as version_file:
        VERSION = version_file.read().strip()
except BaseException:
    pass

MAX_VERSION = pymxs.runtime.maxVersion()
MAX_VERSION_MAJOR = int(MAX_VERSION[7])

RIGHT_COLUMN_WIDTH = 100
RIGHT_COLUMN_WIDTH_PLUS = 105
WINDOWS = "windows"
LINUX = "linux"


VRAY_STANDALONE_PREFIX = "v-ray-standalone"
ARNOLD_MAYA_PREFIX = "arnold-maya"
MAX_PREFIX = "3dsmax-io"
ARNOLD_MAX_PREFIX = "arnold-3dsmax"
VRAY_MAX_PREFIX = "v-ray-3dsmax"
NOT_CONNECTED = "NOT CONNECTED"
NOT_SAVED = "UNTITLED"
MAX_TASKS = int(os.environ.get("CONDUCTOR_MAX_TASKS", 800))
