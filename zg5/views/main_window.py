from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PySide6.QtGui import QAction
from models import ZarzadcaDanych
from views.group_management import GroupManagementWidget
from views.calculation import CalculationWidget
from views.history import HistoriaWidget


class MainWindow(QMainWindow):
    def __init__(self, zarzadca: ZarzadcaDanych):
        super().__init__()
        self.zarzadca = zarzadca
        self.setWindowTitle("Program do obliczania czasów zgrzewania")
        self.resize(900, 700)

        # Stylizacja
        self._apply_styles()

        # Centralny widget z zakładkami
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tworzenie widoków
        self.group_widget = GroupManagementWidget(self.zarzadca)
        self.calc_widget = CalculationWidget(self.zarzadca)
        self.history_widget = HistoriaWidget(self.zarzadca)

        self.tabs.addTab(self.group_widget, "Zarządzanie grupami")
        self.tabs.addTab(self.calc_widget, "Obliczanie czasu")
        self.tabs.addTab(self.history_widget, "Historia obliczeń")

        # Menu
        self._create_menu()

        # Połączenia
        self.group_widget.data_changed.connect(self.on_data_changed)
        self.history_widget.rekordWybrany.connect(self.on_rekord_wybrany)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #c0c0c0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2a5c8a;
            }
            QPushButton {
                background-color: #2a5c8a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1e4a6f;
            }
            QPushButton:pressed {
                background-color: #123a5a;
            }
            QPushButton:disabled {
                background-color: #a0a0a0;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 5px;
                background-color: #ffffff;
                selection-background-color: #2a5c8a;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #2a5c8a;
            }
            QTableWidget {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                background-color: #ffffff;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                padding: 6px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
                color: #2a5c8a;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                background-color: #f5f5f5;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #f5f5f5;
                border-bottom: 2px solid #2a5c8a;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #d0d0d0;
            }
            QLabel {
                color: #333333;
            }
        """)

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

    def on_rekord_wybrany(self, dane):
        """Przechodzi do zakładki obliczeń i wypełnia formularz danymi z historii."""
        self.tabs.setCurrentIndex(1)  # przejdź do zakładki "Obliczanie czasu"
        self.calc_widget.wypelnij_z_historii(dane)

    def show_about(self):
        QMessageBox.about(self, "O programie",
                          "Program do obliczania czasów zgrzewania\n"
                          "Wersja 4.0 (GUI PySide6)\n"
                          "Autor: Konrad Piaskowski\n"
                          "Luty 2026")