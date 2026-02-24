from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QComboBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QHeaderView, QSpinBox,
                               QDoubleSpinBox, QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt
from models import ZarzadcaDanych, MetodaZgrzewania
from typing import Dict, Tuple


class AddGroupDialog(QDialog):
    """Dialog dodawania/edycji grupy."""
    def __init__(self, zarzadca: ZarzadcaDanych, parent=None,
                 edytuj: bool = False, stara_nazwa: str = ""):
        super().__init__(parent)
        self.zarzadca = zarzadca
        self.edytuj = edytuj
        self.stara_nazwa = stara_nazwa
        self.setWindowTitle("Edytuj grupę" if edytuj else "Dodaj grupę")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.nazwa_input = QLineEdit()
        if self.edytuj:
            self.nazwa_input.setText(self.stara_nazwa)
        form.addRow("Nazwa grupy:", self.nazwa_input)
        layout.addLayout(form)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def nazwa_grupy(self) -> str:
        return self.nazwa_input.text().strip()


class AddMethodDialog(QDialog):
    """Dialog dodawania metody do grupy."""
    def __init__(self, zarzadca: ZarzadcaDanych, indeks_grupy: int, parent=None):
        super().__init__(parent)
        self.zarzadca = zarzadca
        self.indeks_grupy = indeks_grupy
        self.setWindowTitle("Dodaj metodę")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.metoda_combo = QComboBox()
        # Lista wszystkich dostępnych metod
        grupa = self.zarzadca.grupy[self.indeks_grupy]
        istniejace = {m.nazwa for m in grupa.metody}
        for nazwa in grupa.domyslne_metody:
            if nazwa not in istniejace:
                self.metoda_combo.addItem(nazwa)
        form.addRow("Wybierz metodę:", self.metoda_combo)
        layout.addLayout(form)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Ok).setEnabled(self.metoda_combo.count() > 0)
        self.metoda_combo.currentTextChanged.connect(
            lambda: button_box.button(QDialogButtonBox.Ok).setEnabled(bool(self.metoda_combo.currentText()))
)
        layout.addWidget(button_box)

    def wybrana_metoda(self) -> str:
        return self.metoda_combo.currentText()


class EditMethodDialog(QDialog):
    """Dialog edycji ustawień czasowych metody."""
    def __init__(self, metoda: MetodaZgrzewania, przedzialy: list, parent=None):
        super().__init__(parent)
        self.metoda = metoda
        self.przedzialy = przedzialy
        self.setWindowTitle(f"Edycja metody: {metoda.nazwa}")
        self.resize(500, 300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel(f"<b>{self.metoda.nazwa}</b>")
        layout.addWidget(label)

        # Tabela z przedziałami
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Przedział", "Liczba pracowników", "Czas na metr (min)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table.setRowCount(len(self.przedzialy))
        for i, przedzial in enumerate(self.przedzialy):
            pracownicy, czas = self.metoda.pobierz_czas(przedzial)

            item_przedzial = QTableWidgetItem(przedzial)
            item_przedzial.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, item_przedzial)

            spin_prac = QSpinBox()
            spin_prac.setRange(1, 20)
            spin_prac.setValue(pracownicy)
            self.table.setCellWidget(i, 1, spin_prac)

            spin_czas = QDoubleSpinBox()
            spin_czas.setRange(0, 100)
            spin_czas.setDecimals(2)
            spin_czas.setValue(czas)
            self.table.setCellWidget(i, 2, spin_czas)

        layout.addWidget(self.table)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def pobierz_czasy(self) -> Dict[str, Tuple[int, float]]:
        """Zwraca słownik przedział -> (pracownicy, czas)"""
        czasy = {}
        for i, przedzial in enumerate(self.przedzialy):
            prac = self.table.cellWidget(i, 1).value()
            czas = self.table.cellWidget(i, 2).value()
            czasy[przedzial] = (prac, czas)
        return czasy