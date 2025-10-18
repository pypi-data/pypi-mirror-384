from ciocore import data as coredata
from ciomax.sections.collapsible_section import CollapsibleSection
from ciomax.components.key_value_grp import KeyValueGrpList
from ciocore.package_environment import PackageEnvironment
from ciopath.gpath import Path
from pymxs import runtime as rt


class EnvironmentSection(CollapsibleSection):
    ORDER = 60

    def __init__(self, dialog):
        super(EnvironmentSection, self).__init__(dialog, "Extra Environment")

        self.component = KeyValueGrpList(checkbox_label="Excl", key_label="Name")
        self.content_layout.addWidget(self.component)
        self.configure_signals()

    def configure_signals(self):
        """Write to store when values change"""
        self.component.edited.connect(self.on_edited)

    def on_edited(self):
        self.dialog.store.set_extra_environment(self.component.entries())

    def get_entries(self, expander):
        return [
            {
                "name": x[0],
                "value": expander.evaluate(x[1]),
                "merge_policy": "exclusive" if x[2] else "append",
            }
            for x in self.component.entries()
        ]

    def populate_from_store(self):
        super(EnvironmentSection, self).populate_from_store()

        store = self.dialog.store
        self.component.set_entries(store.extra_environment())

    def resolve(self, expander, **kwargs):
        """
        Compose the environment submission sub-object.

        Consists of:
            package = Environment provided by the package (Arnold / Vray etc.)
            CONDUCTOR_PATHHELPER = We currently handle all path remapping.
            self.get_entries() = stuff from this UI
            amendments = Stuff from presubmission script.
        """
        amendments = kwargs.get("amendments", {}).get("environment", [])

        if not coredata.valid():
            return {}
        service_section = self.dialog.configuration_tab.section("ServiceSection")
        platform = service_section.get_current_instance_type().get("operating_system")

        tree_data = coredata.data()["software"]
        paths = service_section.get_all_software_paths()
        env = PackageEnvironment(platform=platform)
        for path in paths:
            package = tree_data.find_by_path(path)
            env.extend(package)

        env.extend(amendments)

        try:
            project = Path(rt.pathConfig.getCurrentProjectFolder()).fslash()
            env.extend(
                [
                    {
                        "merge_policy": "exclusive",
                        "name": "ADSK_3DSMAX_PROJECT_FOLDER_DIR",
                        "value": project,
                    }
                ]
            )
        except Exception as e:
            print("Error getting project folder path: {}".format(e))

        env.extend(self.get_entries(expander))

        return {"environment": dict(env)}
