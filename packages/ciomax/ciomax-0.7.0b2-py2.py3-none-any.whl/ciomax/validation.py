import os


from ciocore.validator import Validator

from pymxs import runtime as rt
from ciomax import const as k

LEGACY_MAPS_MODE = 1


class ValidateSceneExists(Validator):
    def run(self, _):
        filepath = rt.maxFilePath + rt.maxFileName
        if not filepath:
            self.add_error(
                "This file has never been saved. Please give it a name and try again."
            )


class ValidateChunkSize(Validator):
    def run(self, _):
        original_chunk_size = self._submitter.configuration_tab.section(
            "FramesSection"
        ).chunk_size_component.field.value()
        resolved_chunk_size = self._submitter.configuration_tab.section(
            "InfoSection"
        ).resolved_chunk_size_component.field.value()

        capped = original_chunk_size != resolved_chunk_size

        if capped:
            self.add_notice(
                "The number of frames per task has been automatically adjusted from {} to {} in order to bring the total number of tasks to below {}. If you have a critical deadline and need each frame to run on a single instance, please contact Conductor customer support.".format(
                    original_chunk_size, resolved_chunk_size, k.MAX_TASKS
                )
            )
        else:
            if resolved_chunk_size > 1:
                msg = "Chunk-size is the number of frames per task and is currently set to {}.".format(
                    resolved_chunk_size
                )
                msg += "This means your render may take longer than necessary. "
                msg += "We recommend setting chunk size to 1, unless each frame render time is short compared to the time it takes to load the scene"
                self.add_notice(msg)


class ValidateUploadDaemon(Validator):
    def run(self, _):
        advanced_section = self._submitter.configuration_tab.section("AdvancedSection")

        context = self._submitter.get_context()

        conductor_executable = os.path.join(context["conductor"], "bin", "conductor")

        use_daemon = advanced_section.use_daemon_checkbox.isChecked()
        if use_daemon:
            msg = "This submission expects an uploader daemon to be running.\n"
            msg += 'After you press submit you can open a command prompt and enter: "{}" uploader'.format(
                conductor_executable
            )

            location = advanced_section.location_component.field.text()
            if location:
                msg = "This submission expects an uploader daemon to be running and set to a specific location tag.\n"
                msg += 'After you press submit you can open a command prompt and type: "{}" uploader --location {}'.format(
                    conductor_executable, location
                )

            self.add_notice(msg)


class ValidateNoArnoldLegacyMapSupport(Validator):
    def run(self, _):
        render_scope = self._submitter.render_scope
        if render_scope.__class__.__name__ == "ArnoldRenderScope":
            warning = "Legacy map mode is not supported for Arnold standalone The compatibility option will be set to Arnold Compliant for the submission."
            try:
                # NOTE: This property changed name in some version of Arnold, so we try both.
                if rt.renderers.current.legacy_3ds_max_map_support:
                    self.add_warning(warning)
            except AttributeError:
                try:
                    if rt.renderers.current.compatibility_mode == LEGACY_MAPS_MODE:
                        self.add_warning(warning)
                except AttributeError:
                    pass


class ValidateInstanceType(Validator):
    """Block submission if there are no instance types.

    This validation will likely never run since it's now impossible to choose software for which
    there are no instance types.
    """

    def run(self, _):
        section = self._submitter.configuration_tab.section("ServiceSection")

        if not section._get_current_instance_type_name():
            self.add_error(
                "No instance types available for the selected render mode and software choice."
            )


class ValidateSoftware(Validator):
    """Block submission if there's no valid software with which to render'.

    Thic can happen if the account has an orchestrator that doesn't provide machines that can handle
    the renderer in the selected render mode. Example, 3ds max native ART renderer with a linux only
    orchestrator.
    """

    def run(self, _):
        section = self._submitter.configuration_tab.section("ServiceSection")
        if not section.software_component.combobox.currentText().strip():
            self.add_error(
                "No software available for the selected render mode and available instance types."
            )


# Implement more validators here
####################################
####################################


def run(dialog):
    validators = [plugin(dialog) for plugin in Validator.plugins()]

    for validator in validators:
        validator.run(None)

    errors = list(set.union(*[validator.errors for validator in validators]))
    warnings = list(set.union(*[validator.warnings for validator in validators]))
    notices = list(set.union(*[validator.notices for validator in validators]))
    return errors, warnings, notices
