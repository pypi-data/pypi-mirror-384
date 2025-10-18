"""
RenderScope

We need to support different submission methods based on the renderer chosen in Render Setup.
* vray - we can submit with vray-standalone on Linux, or with Max on Windows. 
* arnold - we can submit with arnold-for-maya (kick) on Linux, or with Max on Windows.
* all other renderers - we submit with Max on Windows.

A RenderScope encapsulates all the information for one of the above options.
It knows for example the version, the appropriate render commands, the presubmission scripts.
Since the submitter is a modal dialog, we know that the renderer will not change.
"""

from pymxs import runtime as rt
from ciocore import data as coredata

from ciomax import const as k


# The Key is the MaxToA version and the value is the remote installed mtoa version.
MAX_TO_MAYA_ARNOLD_MAP = {
    "4.1.2.1": "maya-io 2020.SP4 linux/arnold-maya 4.1.1.1 linux",  # Arnold 6.1.0.1
    "4.2.0.55": "maya-io 2020.SP4 linux/arnold-maya 4.1.1.1 linux",  # Arnold 6.1.0.1
    "4.2.2.20": "maya-io 2020.SP4 linux/arnold-maya 4.1.1.1 linux",  # Arnold 6.1.0.1
    "4.3.0.78": "maya-io 2020.SP4 linux/arnold-maya 4.2.0.0 linux",  # Arnold 6.2.0.0
    "4.3.1.20": "maya-io 2020.SP4 linux/arnold-maya 4.2.1.0 linux",  # Arnold 6.2.0.1
    "4.3.2.46": "maya-io 2022.SP0 linux/arnold-maya 4.2.3.0 linux",  # Arnold 6.2.1.0
    "4.3.3.21": "maya-io 2022.SP0 linux/arnold-maya 4.2.3.0 linux",  # Arnold 6.2.1.1
    "5.0.0.93": "maya-io 2022.SP0 linux/arnold-maya 5.0.0.1 linux",  # Arnold 7.0.0.0
    "5.0.3.3": "maya-io 2022.SP0 linux/arnold-maya 5.0.0.3 linux",  # Arnold 7.0.0.2
    "5.0.4.4": "maya-io 2022.SP0 linux/arnold-maya 5.0.0.4 linux",  # Arnold 7.0.0.3
    "5.2.0.0": "maya-io 2022.SP0 linux/arnold-maya 5.1.1.1 linux",  # Arnold 7.1.1.0
    "5.4.2.6": "maya-io 2023.SP3 linux/arnold-maya 5.2.1.1 linux",  # Arnold 7.1.3.2
    "5.5.2.11": "maya-io 2023.SP3 linux/arnold-maya 5.2.2.3 linux",  # Arnold 7.1.4.4
    "5.6.5.2": "maya-io 2024.SP1 linux/arnold-maya 5.3.3.1 linux",  # Arnold 7.2.4.1
}


VALID_MAYA_ARNOLD_VERSIONS = list(
    set(
        [
            MAX_TO_MAYA_ARNOLD_MAP[maxtoa_version]
            for maxtoa_version in MAX_TO_MAYA_ARNOLD_MAP
        ]
    )
)

LAST_MAYA_ARNOLD_VERSION = sorted(VALID_MAYA_ARNOLD_VERSIONS)[-1]


class RenderScope(object):
    """
    RenderScope base class.
    """

    __magic_shield = object()

    @classmethod
    def get(cls):
        """Factory which will create render-options based on the chosen render setup."""

        name = str(rt.renderers.current).split(":")[0]

        if name.startswith("V_Ray_GPU"):
            return VrayGPURenderScope(cls.__magic_shield, name)
        elif name.startswith("V_Ray"):
            return VraySWRenderScope(cls.__magic_shield, name)
        elif name == "Arnold":
            return ArnoldRenderScope(cls.__magic_shield, name)
        else:
            return NativeRenderScope(cls.__magic_shield, name)

    def __init__(self, _shield, name):
        assert (
            _shield == RenderScope.__magic_shield
        ), "RenderScope must be created with RenderScope.get()"

        self.package_paths = self.get_render_package_paths()

        self.templates = {
            "max": {
                "command": '3dsmaxcmd.exe -v 5 -workPath "<project>" -frames <start>-<end> -outputName "<destination>/<scenenamex>.<output_ext>" "<scenedir>/<timestamp>_<scenenamex>.max" ',
                "script": '"<conductor>/ciomax/scripts/save_max_scene.py" "<scenedir>/<timestamp>_<scenenamex>"',
            },
            "maxio": {
                "command": '3dsmaxcmdio.exe -v 5 -workPath "<project>" -frames <start>-<end> -outputName "<destination>/<scenenamex>.<output_ext>" "<scenedir>/<timestamp>_<scenenamex>.max" ',
                "script": '"<conductor>/ciomax/scripts/save_max_scene.py" "<scenedir>/<timestamp>_<scenenamex>"',
            }
        }

        self._name = name
        self.version = self.get_version()

    def __str__(self):
        return str(self._name)

    def get_render_package_paths(self):
        raise NotImplementedError

    @staticmethod
    def get_version():
        raise NotImplementedError

    def closest_version(self, partial_path):
        raise NotImplementedError

    def operating_systems(self, partial_path):
        raise NotImplementedError

    def set_render_packages(self):
        raise NotImplementedError

    def get_script_template(self, path):
        if path.split(" ")[-1] == "windows":
            return self.templates["max"]["script"]
        return self.templates["standalone"]["script"]

    def get_task_template(self, path):
        if path.split(" ")[-1] == "windows":
            if k.MAX_VERSION_MAJOR == 2023 or k.MAX_VERSION_MAJOR >= 2025:
                return self.templates["max"]["command"]
            return self.templates["maxio"]["command"]
        return self.templates["standalone"]["command"]

    def all_software_paths(self, path):
        path = path.split("(")[0].strip()
        result = []
        while True:
            result.append(path)
            parts = path.partition("/")
            if not parts[1]:
                return result
            path = parts[0]

    @staticmethod
    def get_compatible_software_paths():
        """Find software for which there are compatible instance types.

        Returns:
            A list of software "paths" such as:
                3dsmax 2021/arnold-max 5.0.0.0
                3dsmax 2021/vray-max 4.3.4
        """
        return coredata.data()["software"].to_path_list() if coredata.valid() else []


class VraySWRenderScope(RenderScope):
    def __init__(self, _shield, name):
        super(VraySWRenderScope, self).__init__(_shield, name)

        self.templates["standalone"] = {
            "command": 'vray -display=0 -verboseLevel=4 -sceneFile="<posix project>/vray/<timestamp>_<scenenamex>.vrscene"  -remapPathFile="<posix project>/vray/<timestamp>_<scenenamex>.xml"   -imgFile="<posix destination>/<scenenamex>.<output_ext>" -frames=<start>-<end>',
            "script": '"<conductor>/ciomax/scripts/export_vray.py" "<project>/vray/<timestamp>_<scenenamex>"',
        }

    @staticmethod
    def get_render_package_paths():
        """
        The user can render with Max, or with Vray Standalone
        """
        version_year = str(rt.maxVersion()[7])
        path_list = RenderScope.get_compatible_software_paths()

        max_vray_paths = [
            p
            for p in path_list
            if k.VRAY_MAX_PREFIX in p and p.split(" ")[1].startswith(version_year)
        ]

        max_vray_paths = sorted(list(set(max_vray_paths)))
        vray_standalone_paths = [
            p for p in path_list if p.startswith(k.VRAY_STANDALONE_PREFIX)
        ]
        vray_standalone_paths = sorted(list(set(vray_standalone_paths)))

        return max_vray_paths + vray_standalone_paths

    @staticmethod
    def get_version():
        parts = rt.vrayVersion()[0].split(".")
        version = ".".join(parts + ["0"] * (4 - len(parts)))
        return "v-ray-standalone {}".format(version)

    def closest_version(self, partial_path):
        """Try to get an exact match from the list of full versions.

        Otherwise try to determine if it was set to a standalone vray, and if so, see if it matches
        the current version.
        """
        if not self.package_paths:
            return None
        if partial_path and partial_path in self.package_paths:
            return partial_path

        if partial_path.startswith("v-ray"):
            if self.version in self.package_paths:
                return self.version
            return self.package_paths[-1].split("/")[-1]
        elif partial_path in self.package_paths:
            return partial_path
        else:
            result = next(
                (p for p in self.package_paths if p.startswith(k.MAX_PREFIX)), None
            )
            return result


class VrayGPURenderScope(VraySWRenderScope):
    def __init__(self, _shield, name):
        super(VrayGPURenderScope, self).__init__(_shield, name)


class ArnoldRenderScope(RenderScope):
    def __init__(self, _shield, name):
        super(ArnoldRenderScope, self).__init__(_shield, name)

        self.templates["standalone"] = {
            "command": 'kick -i "<posix project>/ass/<timestamp>/<scenenamex>.<pad start 4>.ass" -dw -dp -v 5 -o "<posix destination>/<scenenamex>.<pad start 4>.<output_ext>"',
            "script": '"<conductor>/ciomax/scripts/export_ass.py" "<project>/ass/<timestamp>/<scenenamex>."',
        }

    @staticmethod
    def get_render_package_paths():
        """
        The user can render with Max, or with Arnold for Maya
        """
        path_list = RenderScope.get_compatible_software_paths()

        version_year = str(rt.maxVersion()[7])
        max_arnold_paths = [
            p
            for p in path_list
            if k.ARNOLD_MAX_PREFIX in p and p.split(" ")[1].startswith(version_year)
        ]
        max_arnold_paths = sorted(list(set(max_arnold_paths)))

        arnold_standalone_paths = [
            p.split("/")[-1] for p in path_list if p in VALID_MAYA_ARNOLD_VERSIONS
        ]
        arnold_standalone_paths = sorted(list(set(arnold_standalone_paths)))

        return max_arnold_paths + arnold_standalone_paths

    def all_software_paths(self, path):
        if not path.startswith(k.ARNOLD_MAYA_PREFIX):
            return super(ArnoldRenderScope, self).all_software_paths(path)
        path = path.split("(")[0].strip()
        # will be array of length 1
        return [p for p in VALID_MAYA_ARNOLD_VERSIONS if p.endswith(path)]

    @staticmethod
    def get_version():
        parts = rt.getFileVersion("maxtoa.dlr").split("\t")[0].split(",")
        version = ".".join(parts + ["0"] * (4 - len(parts)))
        return MAX_TO_MAYA_ARNOLD_MAP.get(version, LAST_MAYA_ARNOLD_VERSION)

    def closest_version(self, partial_path):
        """Try to get an exact match from the list of full versions.

        Otherwise try to determine if it was set to a maya, and if so, see if it matches
        the current version.

        arnold-maya 5.1.1.1 linux
        arnold-maya 5.2.1.1 linux
        arnold-maya 5.2.2.3 linux
        arnold-maya 5.3.3.1 linux
        """
        if not self.package_paths:
            return None
        if not partial_path:
            return self.package_paths[-1]
        found = partial_path and partial_path in (
            p.split("/")[-1] for p in self.package_paths
        )
        if found:
            return partial_path

        if partial_path.startswith("arnold"):
            if self.version in self.package_paths:
                result = self.version
            else:
                result = self.package_paths[-1]
            return result.split("/")[-1]
        elif partial_path in self.package_paths:
            return partial_path
        else:
            result = next(
                (p for p in self.package_paths if p.startswith(k.MAX_PREFIX)), None
            )
            return result


class NativeRenderScope(RenderScope):
    # OPERATING_SYSTEMS = ["windows"]
    def __init__(self, _shield, name):
        super(NativeRenderScope, self).__init__(_shield, name)

        msg = "UNABLE TO RENDER {} ON THIS ACCOUNT".format(name)
        self.templates["standalone"] = {
            "command": "{}".format(msg),
            "script": "{}".format(msg),
        }

    @staticmethod
    def get_render_package_paths():
        """
        The user can render with Max
        """
        path_list = RenderScope.get_compatible_software_paths()
        version_year = str(rt.maxVersion()[7])
        max_paths = [
            p
            for p in path_list
            if p.startswith(k.MAX_PREFIX)
            and p.split(" ")[1].startswith(version_year)
            and not "/" in p
        ]
        return sorted(list(set(max_paths)))

    @staticmethod
    def get_version():
        return "max 0.0.0.0"

    def closest_version(self, partial_path):
        """Try to get an exact match from the list of full versions."""
        if not self.package_paths:
            return None

        found = partial_path and partial_path in (
            p.split("/")[-1] for p in self.package_paths
        )
        if not partial_path:
            return self.package_paths[-1]
        if found:
            return partial_path

        # For now, return the first version of Max
        return self.package_paths[0]
