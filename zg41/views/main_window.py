from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PySide6.QtGui import QAction
from models import ZarzadcaDanych
from views.group_management import GroupManagementWidget
from views.calculation import CalculationWidget


class MainWindow(QMainWindow):
    def __init__(self, zarzadca: ZarzadcaDanych):
        super().__init__()
        self.zarzadca = zarzadca
        self.setWindowTitle("Program do obliczania czasów zgrzewania")
        self.resize(900, 700)

        # Centralny widget z zakładkami
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tworzenie widoków
        self.group_widget = GroupManagementWidget(self.zarzadca)
        self.calc_widget = CalculationWidget(self.zarzadca)

        self.tabs.addTab(self.group_widget, "Zarządzanie grupami")
        self.tabs.addTab(self.calc_widget, "Obliczanie czasu")

        # Menu
        self._create_menu()

        # Połączenie sygnałów odświeżania
        self.group_widget.data_changed.connect(self.on_data_changed)

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Plik")
        save_action = QAction("Zapisz dane", self)
        save_action.triggered.connect(self.zarzadca.zapisz)
        file_menu.addAction(save_action)

        exit_action = QAction("Zakończ", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("Pomoc")
        about_action = QAction("O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def on_data_changed(self):
        """Odświeża widget obliczeń po zmianie danych w grupach."""
        self.calc_widget.refresh_groups()

    def show_about(self):
        QMessageBox.about(self, "O programie",
                          "Program do obliczania czasów zgrzewania\n"
                          "Wersja 4.0 (GUI PySide6)\n"
                          "Autor: Konrad Piaskowski\n"
                          "Luty 2026")