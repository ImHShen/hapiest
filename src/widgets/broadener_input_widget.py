from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox, QSpacerItem, QSizePolicy, \
    QDoubleSpinBox, QComboBox, QPushButton, QVBoxLayout, QScrollArea


class BroadenerItemWidget(QWidget):

    def __init__(self, broadener: str):
        QWidget.__init__(self)

        self.broadener = broadener

        self.selected = QCheckBox()
        self.name = QLabel(broadener)
        self.hspacer = QSpacerItem(1, 1, hPolicy = QSizePolicy.Expanding)

        # Spin box with two decimal places, constant size, range from 0 to 1
        self.proportion = QDoubleSpinBox()
        self.proportion.setDecimals(2)
        self.proportion.setRange(0.0, 1.0)
        self.proportion.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.selected)
        self.hlayout.addWidget(self.name)
        self.hlayout.addSpacerItem(self.hspacer)
        self.hlayout.addWidget(self.proportion)

        self.setLayout(self.hlayout)


class BroadenerInputWidget(QWidget):

    BROADENERS = {"b1", "b2", "b3", "b4", "b5", "b6", "b7S"}

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.selected_broadener = QComboBox()
        self.selected_broadener.addItems(BroadenerInputWidget.BROADENERS)

        self.add_broadener = QPushButton()
        self.add_broadener.setText("Add Broadener")
        self.add_broadener.pressed.connect(self.__on_add_broadener_pressed)

        self.remove_checked = QPushButton()
        self.remove_checked.setText("Remove Checked")
        self.remove_checked.pressed.connect(self.__on_remove_checked_pressed)

        self.added_broadener_names = set()
        self.broadener_items = {}

        self.broadener_item_layout = QVBoxLayout()
        self.broadener_items_container = QWidget()
        self.broadener_items_container.setLayout(self.broadener_item_layout)

        self.controls_layout = QHBoxLayout()
        self.controls_layout.addWidget(self.selected_broadener)
        self.controls_layout.addWidget(self.add_broadener)
        self.controls_layout.addWidget(self.remove_checked)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.broadener_items_container)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.controls_layout)
        self.main_layout.addWidget(self.scroll_area)
        self.setLayout(self.main_layout)

        self.update_widgets()

    def update_widgets(self):
        # Removes all items from broadener_item_layout, and adds the ones that are in
        # added_broadener_names. Then updates selected_broadener to only contain the names
        # of broadeners that have not yet been added

        while True:
            a = self.broadener_item_layout.takeAt(0)
            if a is None:
                break
            a.widget().hide()

        for name in self.added_broadener_names:
            if name not in self.broadener_items:
                self.broadener_items[name] = BroadenerItemWidget(name)

            self.broadener_items[name].show()
            self.broadener_item_layout.addWidget(self.broadener_items[name])

        self.selected_broadener.clear()
        self.selected_broadener.addItems(
                list(BroadenerInputWidget.BROADENERS.difference(self.added_broadener_names)))

        if len(self.selected_broadener) == 0:
            self.add_broadener.setDisabled(True)
        else:
            self.add_broadener.setEnabled(True)

        if len(self.added_broadener_names) == 0:
            self.remove_checked.setDisabled(True)
        else:
            self.remove_checked.setEnabled(True)

    def as_hapi_parameter(self):
        raise Exception("You forgot to do this")

    def __on_add_broadener_pressed(self, *_args):
        if len(self.selected_broadener) == 0:
            return

        self.added_broadener_names.add(self.selected_broadener.currentText())
        self.update_widgets()

    def __on_remove_checked_pressed(self, *_args):
        for broadener_item in self.broadener_items.values():
            if broadener_item.selected.isChecked() \
                    and broadener_item.broadener in self.added_broadener_names:
                self.added_broadener_names.remove(broadener_item.broadener)

        self.update_widgets()