from ciomax import QtGui

from ciomax.sections.collapsible_section import CollapsibleSection
from ciomax.components.combo_box_grp_2 import DualComboBoxGrp
from ciomax.components.combo_box_grp import ComboBoxGrp
from ciomax.components.checkbox_grp import CheckboxGrp
from ciocore import data as coredata
from ciomax import const as k
from ciocore.hardware_set import HardwareSet

INVALID_INSTANCE_TYPE = "INVALID INSTANCE TYPE"

class ServiceSection(CollapsibleSection):
    ORDER = 5

    def __init__(self, dialog):
        """
        Combo box. Renderer

        """
        super(ServiceSection, self).__init__(dialog, "Service")
        self.software_component = ComboBoxGrp(label="Software")

        self.instance_type_component = DualComboBoxGrp(
            direction="row", label="Instance Type", width1=70
        )
        self.preemptible_component = CheckboxGrp(
            label="Preemptible (Spot)", checkboxes=1
        )

        self.content_layout.addWidget(self.software_component)
        self.content_layout.addWidget(self.instance_type_component)
        self.content_layout.addWidget(self.preemptible_component)

        self.configure_software_combo_box()
        self.set_instance_type_model()
        self.configure_signals()

    def configure_signals(self):
        """Write to store when values change"""

        self.software_component.combobox.currentTextChanged.connect(
            self.on_software_change
        )

        self.instance_type_component.combobox_content.currentTextChanged.connect(
            self.on_instance_type_change
        )

        self.preemptible_component.checkboxes[0].clicked.connect(
            self.on_preemptible_change
        )

    def on_software_change(self, value):
        value = self.software_component.combobox.currentText()
        self.dialog.store.set_renderer_version(value)
        advanced_section = self.dialog.configuration_tab.section("AdvancedSection")
        advanced_section.on_renderer_change()
        self.set_instance_type_model()

    def on_instance_type_change(self, value):
        instance_type = self._get_current_instance_type_name()
        self.dialog.store.set_instance_type(instance_type)

    def on_preemptible_change(self, value):
        self.dialog.store.set_preemptible(value > 0)

    def populate_from_store(self):
        super(ServiceSection, self).populate_from_store()

        store = self.dialog.store
        path = store.renderer_version()
        path = self.dialog.render_scope.closest_version(path)
        self.software_component.set_by_text(path)

        self.instance_type_component.set_by_text(store.instance_type(), column=1)
        self.preemptible_component.checkboxes[0].setChecked(store.preemptible())

    def configure_software_combo_box(self):
        paths = self.dialog.render_scope.package_paths

        model = QtGui.QStandardItemModel()
        for path in paths:
            model.appendRow(QtGui.QStandardItem(path))
        self.software_component.set_model(model)

    def set_instance_type_model(self):
        """
        Populate the instance_types pair of combo boxes.
        """
        path = self.dialog.store.renderer_version()

        instance_type = self.dialog.store.instance_type()

        path = self.dialog.render_scope.closest_version(path)

        operating_system = "linux"
        if path:
            operating_system = path.split(" ")[-1] 
        qtmodel = self.get_instance_types_qtmodel(operating_system)
        self.instance_type_component.set_model(qtmodel)
        self.instance_type_component.set_by_text(instance_type, column=1)

        provider = coredata.data()["instance_types"].provider
        if provider == "cw":
            self.preemptible_component.checkboxes[0].setChecked(False)
            self.preemptible_component.hide()
            self.dialog.store.set_preemptible(False)
        else:
            self.preemptible_component.show()
        return True

    def resolve(self, _, **kwargs):
        """
        Return software IDs.
        """
        if not coredata.valid():
            return {}
        is_cw = coredata.data()["instance_types"].provider == "cw"
        tree_data = coredata.data()["software"]

        paths = self.get_all_software_paths()
        package_ids = []
        for path in paths:
            package = tree_data.find_by_path(path)
            if package:
                package_ids.append(package["package_id"])

        return {
            "software_package_ids": package_ids,
            "instance_type":  self._get_current_instance_type_name(),
            "preemptible": False if is_cw else self.preemptible_component.checkboxes[0].isChecked()
        }

    def get_all_software_paths(self):
        return self.dialog.render_scope.all_software_paths(
            self.software_component.combobox.currentText()
        )


    def _get_current_instance_type_name(self):
        data = self.instance_type_component.get_current_data()
        if data and data["content"] and len(data["content"]) > 1 and data["content"][1]:
            return data["content"][1]
        return INVALID_INSTANCE_TYPE
    
    def get_current_instance_type(self):
        name = self._get_current_instance_type_name()
        instance_type = coredata.data()["instance_types"].find(name)
        return instance_type
    
    @staticmethod
    def get_instance_types_qtmodel(operating_system):
        """
        Return a QStandardItemModel of the instance types.

        The model is populated from the coredata HardwareSet. It represents instance types arranged by categories.
        """
        hardware = unconnected_hardware()
        if (
            coredata.valid()
            and coredata.data().get("instance_types")
            and coredata.data().get("instance_types").categories
        ):
            hardware = coredata.data().get("instance_types")

        category_labels = [category["label"] for category in hardware.categories]

        model = QtGui.QStandardItemModel()
        for category_label in category_labels:
            item = QtGui.QStandardItem(category_label)
            category = hardware.find_category(category_label)
            if not category:
                continue
            for entry in category["content"]:
                if entry["operating_system"] != operating_system:
                    continue
                item.appendRow(
                    (
                        QtGui.QStandardItem(entry["description"]),
                        QtGui.QStandardItem(entry["name"]),
                    )
                )
            model.appendRow(item)
        return model


def unconnected_hardware():
    """Return a HardwareSet with a single entry.

    This entry is not connected to any instance type.
    """
    return HardwareSet(
        [
            {
                "cores": 0,
                "memory": 0,
                "description": k.NOT_CONNECTED,
                "name": k.NOT_CONNECTED,
                "operating_system": "linux",
            }
        ]
    )
