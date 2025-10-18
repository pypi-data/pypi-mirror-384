"""
Presubmission script to export max scene files.

To write your own presubmission script, use this as a jumping off point and
consult the Conductor Max reference documentation.
https://docs.conductortech.com/reference/max/#pre-submission-script
"""


import os

from pymxs import runtime as rt
from ciopath.gpath import Path
from ciomax.scripts import export_utils 

def main(dialog, *args):
    """
    Export assets needed for a max render.

    Return an object containing the list of payload amendments.

    args

    """

    fn = os.path.splitext(args[0])[0]

    export_max_scene(dialog, fn)

    for new_file in _get_amendment_paths(*args):
        found = export_utils.wait_for_file(new_file)
        if not found:
            raise ValueError("File not found: {}".format(new_file))
        else:
            print("File found: {}".format(new_file))

    return amendments(dialog, *args)

def amendments(dialog, *args):
    """
    Return payload amendments only.
    """

    return {"upload_paths": list(_get_amendment_paths(*args)) }

def export_max_scene(dialog, max_scene_prefix):
    camera_name = dialog.configuration_tab.section(
        "GeneralSection"
    ).camera_component.combobox.currentText()
    print("Set the current view to look through camera: {}", format(camera_name))

    rt.viewport.setCamera(rt.getNodeByName(camera_name))

    print("Ensure directory is available for max scene file")
    _ensure_directory_for(max_scene_prefix)

    print("Closing render setup window if open...")
    if rt.renderSceneDialog.isOpen():
        rt.renderSceneDialog.close()

    print("Exporting max scene file")

    rt.saveMaxFile(max_scene_prefix, clearNeedSaveFlag=False, useNewFile=False)

    print("Completed max scene export..")

    return "{}.max".format(max_scene_prefix)

def _ensure_directory_for(path):
    """Ensure that the parent directory of `path` exists"""
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)

def _get_amendment_paths(*args):
    max_scene_name = "{}.max".format(os.path.splitext(args[0])[0])
    mxp_file = Path(rt.pathConfig.getCurrentProjectFolderPath()).fslash()
    return max_scene_name, mxp_file