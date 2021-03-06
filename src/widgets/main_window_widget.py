from PyQt5.QtWidgets import QAction, QCompleter, QMainWindow, QTabWidget, QStatusBar, QVBoxLayout
from metadata.molecule_meta import MoleculeMeta
from widgets.about_widget import AboutWidget
from widgets.config_editor_widget import ConfigEditorWidget
from widgets.cross_section_fetch_widget import CrossSectionFetchWidget
from widgets.fetch_widget import FetchWidget
from widgets.graphing.graphing_widget import *
from widgets.molecule_info_widget import MoleculeInfoWidget
from widgets.select_widget import SelectWidget
from widgets.view_widget import ViewWidget
from windows.molecule_info_window import MoleculeInfoWindow
import webbrowser

class MainWindowWidget(QMainWindow):
    """
    The main window contains most of the functionality. This includes the Edit widget,
    Fetch widget, Select widget, and
    graphing widget.
    """

    MAIN_WINDOW_WIDGET_INSTANCE = None

    def __init__(self, parent):
        """
        Instantiates all of the widgets for each of the individual tabs
        """
        QMainWindow.__init__(self)

        if MainWindowWidget.MAIN_WINDOW_WIDGET_INSTANCE is not None:
            raise Exception("Only one instance of the MainWindowGui should be created")

        MainWindowWidget.MAIN_WINDOW_WIDGET_INSTANCE = self

        self.setWindowIcon(program_icon())

        self.parent = parent
        self.workers = []

        self.tab_widget: QTabWidget = None

        # Containers
        self.fetch_tab: QWidget = None
        self.cross_section_tab: QWidget = None
        self.fetch_container: QVBoxLayout = None
        self.cross_section_fetch_widget: QVBoxLayout = None

        # Elements in 'Molecules' tab
        self.molecule_container: QVBoxLayout = None
        self.molecules_popout_button: QPushButton = None
        self.molecules_current_molecule: QComboBox = None
        self.molecule_info = None

        self.completer = None

        # Elements in 'Graphing' tab
        self.graphing_tab: QWidget = None
        self.graphing_container: QVBoxLayout = None

        # Other stuff..
        self.config_action: QAction = None
        self.about_hapiest_action: QAction = None
        self.statusbar: QStatusBar = None
        self.help_manual: QAction = None

        self.config_window = None
        self.about_window = None

        offline_text = 'HAPPIEST is currently offline. Data fetching is disabled, ' \
                       'but you can still use the graph tab.'
        self.fetch_offline_label = QLabel(offline_text)
        self.cross_section_offline_label = QLabel(offline_text)
        self.fetch_offline_label.setStyleSheet("color : red")
        self.cross_section_offline_label.setStyleSheet("color : red")

        # All of the gui elements get loaded and initialized by loading the ui file
        uic.loadUi('layouts/main_window.ui', self)

        self.setWindowTitle("hapiest - {}".format(VERSION_STRING))

        self.config_action.triggered.connect(self.__on_config_action)
        self.about_hapiest_action.triggered.connect(self.__on_about_action)

        self.fetch_widget = FetchWidget(self)
        if not Config.online:
            self.fetch_container.addWidget(self.fetch_offline_label)
        self.fetch_container.addWidget(self.fetch_widget)

        self.graphing_widget: QWidget = GraphingWidget(self)
        self.graphing_container.addWidget(self.graphing_widget)

        self.cross_section_fetch_widget = CrossSectionFetchWidget(self)
        if not Config.online:
            self.cross_section_container.addWidget(self.cross_section_offline_label)
        self.cross_section_container.addWidget(self.cross_section_fetch_widget)

        self.populate_table_lists()
        self.populate_molecule_list()

        # Initially display a molecule in the molecule widget
        self.__on_molecules_current_text_changed()
        self.molecules_current_molecule.currentTextChanged.connect(
        self.__on_molecules_current_text_changed)
        self.molecules_popout_button.clicked.connect(self.__on_molecules_popout_button)

        self.workers = []

        self.status_bar_label: QWidget = QtWidgets.QLabel("Ready")
        self.statusbar.addWidget(self.status_bar_label)

        self.help_manual.triggered.connect(self.open_manual)

        self.setWindowTitle("hapiest - {}".format(VERSION_STRING))

        if not Config.online:
            self.fetch_tab.setDisabled(True)
            self.cross_section_tab.setDisabled(True)
            self.setWindowTitle("hapiest - OFFLINE")

        # Display the GUI since we're done configuring it
        self.show()

    def closeEvent(self, event):
        if self.config_window:
            self.config_window.close()
        if self.about_window:
            self.about_window.close()
        for widget in list(GraphDisplayWidget.graph_windows.values()):
            widget.close()
        for widget in list(SelectWidget.instances):
            widget.close()
        for widget in list(ViewWidget.instances):
            widget.close()
        QMainWindow.closeEvent(self, event)

    def remove_worker_by_jid(self, jid: int):
        """
        *Params : int jid (job id), the method terminates a worker thread based on a given job id.*
        """
        for worker in self.workers:
            if worker.job_id == jid:
                worker.safe_exit()
                break

    def __on_config_action(self, *_args):
        # if self.config_window:
        #     self.config_window.close()
        self.config_window = ConfigEditorWidget(None)
        self.config_window.show()

    def __on_about_action(self, *_args):
        # if self.about_window:
        #     self.about_window.close()
        self.about_window = AboutWidget(None)
        self.about_window.show()

    def __on_molecules_current_text_changed(self, *_args):
        molecule = MoleculeMeta(self.molecules_current_molecule.currentText())
        if not molecule.is_populated():
            return

        if self.molecule_info is not None:
            for i in reversed(range(self.molecule_container.count())):
                self.molecule_container.itemAt(i).widget().setParent(None)
        self.molecule_info = MoleculeInfoWidget(self.molecules_current_molecule.currentText(), self)
        self.molecule_container.addWidget(self.molecule_info)

    def __on_molecules_popout_button(self):
        new_window = MoleculeInfoWindow(self.parent,
                                        self.molecules_current_molecule.currentText())
        new_window.gui.show()
        self.parent.add_child_window(new_window)

    def populate_molecule_list(self):
        """
        Extract the name of each molocule that hapi has data on and add it to the molecule list.
        """
        # Make sure that molecule meta has had it's static members initialized initialized.
        self.molecules_current_molecule.addItems(MoleculeMeta.all_names_sorted_by_hitran_id())
        self.completer: QCompleter = QCompleter(MoleculeMeta.all_aliases(), self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.molecules_current_molecule.setEditable(True)
        self.molecules_current_molecule.setCompleter(self.completer)

    def populate_table_lists(self, data_names=None):
        """
        *This method initializes the default table values for the fetch tab and the edit tab.*
        """
        if data_names == None:
            data_names = list(get_all_data_names())
        non_xsc_data = list(data for data in data_names if not data.endswith(".xsc"))

        # self.view_widget.table_name.clear()
        # self.view_widget.table_name.addItems(data_names)
        # self.select_widget.table_name.clear()
        # self.select_widget.table_name.addItems(data_names)

        # cross sections can only be graphed, not modified or transformed using select.
        ViewWidget.set_table_names(non_xsc_data)
        SelectWidget.set_table_names(non_xsc_data)

        self.graphing_widget.data_name.clear()
        self.graphing_widget.data_name.addItems(data_names)

    def open_manual(self):
        webbrowser.open_new(r'docs/manual.pdf')