from ciomax import QtGui
from ciomax.sections.collapsible_section import CollapsibleSection
from ciomax.components.text_field_grp import TextFieldGrp
from ciomax.components.combo_box_grp import ComboBoxGrp


from ciocore import data as coredata
from pymxs import runtime as rt
from ciopath.gpath import Path


class GeneralSection(CollapsibleSection):
    ORDER = 10

    def __init__(self, dialog):
        super(GeneralSection, self).__init__(dialog, "General")

        self.title_component = TextFieldGrp(
            label="Job Title",
            tooltip="The title that appears in the Conductor web dashboard on the jobs page.",
        )

        self.project_component = ComboBoxGrp(label="Conductor Project")

        self.destination_component = TextFieldGrp(
            label="Destination",
            directory=True,
            placeholder="Path where renders are saved to",
        )

        self.camera_component = ComboBoxGrp(label="Camera")

        self.content_layout.addWidget(self.title_component)
        self.content_layout.addWidget(self.project_component)

        self.content_layout.addWidget(self.destination_component)
        self.content_layout.addWidget(self.camera_component)

        self.set_project_model()
        self.set_camera_model()
        self.configure_signals()

    def set_project_model(self):
        if not coredata.valid():
            return False

        model = QtGui.QStandardItemModel()
        for project in coredata.data()["projects"] or []:
            model.appendRow(QtGui.QStandardItem(project))
        self.project_component.set_model(model)

        return True

    def set_camera_model(self):
        cam_names = [c.name for c in rt.cameras]
        model = QtGui.QStandardItemModel()
        for cam_name in cam_names or []:
            model.appendRow(QtGui.QStandardItem(cam_name))
        self.camera_component.set_model(model)
        return True

    def configure_signals(self):
        """Write to store when values change"""
        self.title_component.field.editingFinished.connect(self.on_title_change)

        self.project_component.combobox.currentTextChanged.connect(
            self.on_project_change
        )

        self.camera_component.combobox.currentTextChanged.connect(self.on_camera_change)

        self.destination_component.field.editingFinished.connect(
            self.on_destination_change
        )

        self.destination_component.button.clicked.connect(self.on_destination_change)

    def on_title_change(self):
        self.dialog.store.set_title(self.title_component.field.text())

    def on_project_change(self, value):
        self.dialog.store.set_project(value)

    def on_camera_change(self, value):
        self.dialog.store.set_camera(value)

    def on_destination_change(self):
        path = self.destination_component.field.text()
        if path:
            path = Path(path).fslash()
        self.dialog.store.set_destination(path)
        self.destination_component.field.setText(path)

    def populate_from_store(self):
        super(GeneralSection, self).populate_from_store()

        store = self.dialog.store
        self.title_component.field.setText(store.title())
        self.destination_component.field.setText(store.destination())
        self.project_component.set_by_text(store.project())
        self.camera_component.set_by_text(store.camera())

    def resolve(self, expander, **kwargs):
        return {
            "job_title": expander.evaluate(self.title_component.field.text()),
            "output_path": expander.evaluate(self.destination_component.field.text()),
            "project": self.project_component.combobox.currentText(),
        }
