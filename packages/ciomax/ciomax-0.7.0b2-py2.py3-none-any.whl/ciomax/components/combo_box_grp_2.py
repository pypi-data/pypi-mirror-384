from ciomax import QtWidgets
from ciomax.components import widgets
from ciomax import const as k


class ComboBoxGrp(QtWidgets.QWidget):
    """Single combo box containing model rows."""

    def __init__(self, **kwargs):
        super(ComboBoxGrp, self).__init__()
        self.scale_factor = self.logicalDpiX() / 96.0
        
        self.model = None
        tooltip = kwargs.get("tooltip")

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(widgets.FormLabel(kwargs.get("label", ""), tooltip))

        self.combobox = QtWidgets.QComboBox()

        layout.addWidget(self.combobox)
        layout.addSpacing(k.RIGHT_COLUMN_WIDTH_PLUS * self.scale_factor)

    def set_by_text(self, text, column=0, default=0):
        """set to the row where column contains the given text."""
        for row in range(self.model.rowCount()):
            if self.model.item(row, column).text() == text:
                self.combobox.setCurrentIndex(row)
                return
        self.combobox.setCurrentIndex(default)

    def set_model(self, model):
        self.model = model
        self.combobox.setModel(self.model)


class DualComboBoxGrp(QtWidgets.QWidget):
    """Combo box pair.

    The model is a tree of depth 2, and where the child combo box is
    maintained to always contain the children of the model item selected in the
    first combo box.

    Think of the model as a tree of categories and content.

    There are two ways to layout the two widgets:
    1. direction="row" - the two combo boxes are placed side by side next to a single label.
    2. direction="column" - the two combo boxes are placed one above the other, each with their own label.
    """

    def __init__(self, **kwargs):
        super(DualComboBoxGrp, self).__init__()

        self.model = None
        self.combobox_category = None
        self.combobox_content = None
        tooltip = kwargs.get("tooltip")
        scale_factor = self.logicalDpiX() / 96.0

        if kwargs.get("direction") == "row":
            layout = QtWidgets.QHBoxLayout()
            self.setLayout(layout)

            layout.addWidget(widgets.FormLabel(kwargs.get("label", ""), tooltip))
            self.combobox_category = QtWidgets.QComboBox()
            self.combobox_content = QtWidgets.QComboBox()

            layout.addWidget(self.combobox_category)
            layout.addWidget(self.combobox_content)
            self.combobox_category.setFixedWidth(kwargs.get("width1", 70))
            layout.addSpacing(k.RIGHT_COLUMN_WIDTH_PLUS * scale_factor)
        else:
            layout = QtWidgets.QVBoxLayout()
            self.setLayout(layout)

            row1 = ComboBoxGrp(label=kwargs.get("label1", ""))
            row2 = ComboBoxGrp(label=kwargs.get("label2", ""))

            self.combobox_category = row1.combobox
            self.combobox_content = row2.combobox

            layout.addWidget(row1)
            layout.addWidget(row2)

        self.combobox_category.currentIndexChanged.connect(self.category_changed)

    def set_model(self, model):
        """
        Set the model for both combo boxes.

        Set the content (child) combo box first because the category (parent)
        has a change event that will trigger on the initial set_model.
        """
        self.model = model
        self.combobox_content.setModel(self.model)
        self.combobox_category.setModel(self.model)
        self.combobox_content.setRootModelIndex(self.model.index(0, 0))
        self.combobox_category.setCurrentIndex(0)
        self.combobox_content.setCurrentIndex(0)

    def category_changed(self, index):
        """Change left-box and set right-box to the first in the list."""
        if not self.model:
            return
        self.set_by_indices(index, 0)

    def set_by_indices(self, i, j):
        self.combobox_category.setCurrentIndex(i)
        model_index = self.model.index(i, 0)
        self.combobox_content.setRootModelIndex(model_index)
        self.combobox_content.setCurrentIndex(j)

    def set_by_text(self, text, column=0, default=(0, 0)):
        if not self.model:
            return

        for root_row in range(self.model.rowCount()):
            root_item = self.model.item(root_row)
            for row in range(root_item.rowCount()):
                item_text = root_item.child(row, column).text()

                if item_text == text:
                    self.set_by_indices(root_row, row)
                    return

        self.set_by_indices(default[0], default[1])

    def get_current_data(self):
        result = {"category": "", "content": []}
        cat_index = self.combobox_category.currentIndex()

        cat_item = self.model.item(cat_index)
        result["category"] = self.model.item(cat_index, 0).text()
        columns = cat_item.columnCount()

        content_index = self.combobox_content.currentIndex()
        for i in range(columns):
            result["content"].append(cat_item.child(content_index, i).text())

        return result
