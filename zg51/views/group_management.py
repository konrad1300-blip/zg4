from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QListWidget, QListWidgetItem, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMessageBox,
                               QAbstractItemView, QGroupBox, QLabel)
from PySide6.QtCore import Signal
from models import ZarzadcaDanych, Grupa
from views.dialogs import AddGroupDialog, AddMethodDialog, EditMethodDialog
from PySide6.QtCore import Signal, Qt


class GroupManagementWidget(QWidget):
    data_changed = Signal()

    def __init__(self, zarzadca: ZarzadcaDanych):
        super().__init__()
        self.zarzadca = zarzadca
        self.aktualna_grupa = None
        self._setup_ui()
        self._odswiez_liste_grup()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # --- Lewy panel: lista grup ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Grupy:"))
        self.lista_grup = QListWidget()
        self.lista_grup.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lista_grup.currentRowChanged.connect(self._wybrano_grupe)
        left_layout.addWidget(self.lista_grup)

        btn_dodaj_grupe = QPushButton("Dodaj grupę")
        btn_dodaj_grupe.clicked.connect(self._dodaj_grupe)
        left_layout.addWidget(btn_dodaj_grupe)

        btn_usun_grupe = QPushButton("Usuń grupę")
        btn_usun_grupe.clicked.connect(self._usun_grupe)
        left_layout.addWidget(btn_usun_grupe)

        btn_edytuj_grupe = QPushButton("Edytuj nazwę grupy")
        btn_edytuj_grupe.clicked.connect(self._edytuj_grupe)
        left_layout.addWidget(btn_edytuj_grupe)

        left_layout.addStretch()

        # --- Prawy panel: szczegóły grupy (metody) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("Metody w grupie:"))
        self.tabela_metod = QTableWidget()
        self.tabela_metod.setColumnCount(6)
        self.tabela_metod.setHorizontalHeaderLabels(
            ["Lp.", "Metoda", "Przedział", "Pracownicy", "Czas na metr (min)", "Akcje"])
        self.tabela_metod.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_metod.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela_metod.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.tabela_metod)

        btn_dodaj_metode = QPushButton("Dodaj metodę do grupy")
        btn_dodaj_metode.clicked.connect(self._dodaj_metode)
        right_layout.addWidget(btn_dodaj_metode)

        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

    def _odswiez_liste_grup(self):
        self.lista_grup.clear()
        for grupa in self.zarzadca.grupy:
            item = QListWidgetItem(grupa.nazwa)
            item.setData(Qt.UserRole, grupa)  # przechowujemy referencję do obiektu
            self.lista_grup.addItem(item)

    def _wybrano_grupe(self, row: int):
        if row >= 0:
            item = self.lista_grup.item(row)
            self.aktualna_grupa = item.data(Qt.UserRole)
            self._pokaz_metody()
        else:
            self.aktualna_grupa = None
            self.tabela_metod.setRowCount(0)

    def _pokaz_metody(self):
        if not self.aktualna_grupa:
            return
        grupa = self.aktualna_grupa
        self.tabela_metod.setRowCount(0)

        for i, metoda in enumerate(grupa.metody):
            for j, przedzial in enumerate(self.zarzadca.przedzialy):
                row = self.tabela_metod.rowCount()
                self.tabela_metod.insertRow(row)
                pracownicy, czas = metoda.pobierz_czas(przedzial)

                if j == 0:
                    lp_item = QTableWidgetItem(str(i + 1))
                else:
                    lp_item = QTableWidgetItem("")
                self.tabela_metod.setItem(row, 0, lp_item)

                self.tabela_metod.setItem(row, 1, QTableWidgetItem(metoda.nazwa if j == 0 else ""))
                self.tabela_metod.setItem(row, 2, QTableWidgetItem(przedzial))
                self.tabela_metod.setItem(row, 3, QTableWidgetItem(str(pracownicy)))
                self.tabela_metod.setItem(row, 4, QTableWidgetItem(f"{czas:.2f}"))

                if j == 0:
                    btn_edit = QPushButton("Edytuj")
                    btn_edit.clicked.connect(lambda checked, idx=i: self._edytuj_metode(idx))
                    self.tabela_metod.setCellWidget(row, 5, btn_edit)

    # --- Akcje na grupach ---
    def _dodaj_grupe(self):
        dialog = AddGroupDialog(self.zarzadca, self)
        if dialog.exec():
            nazwa = dialog.nazwa_grupy()
            if self.zarzadca.dodaj_grupe(nazwa):
                self._odswiez_liste_grup()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "Błąd", "Grupa o tej nazwie już istnieje.")

    def _usun_grupe(self):
        row = self.lista_grup.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Wybierz grupę do usunięcia.")
            return
        item = self.lista_grup.item(row)
        grupa = item.data(Qt.UserRole)
        odp = QMessageBox.question(self, "Potwierdzenie",
                                   f"Czy na pewno usunąć grupę '{grupa.nazwa}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if odp == QMessageBox.Yes:
            # Znajdź indeks grupy na liście (może się zmienić, ale używamy referencji)
            indeks = self.zarzadca.grupy.index(grupa)
            self.zarzadca.usun_grupe(indeks)
            self._odswiez_liste_grup()
            self.data_changed.emit()

    def _edytuj_grupe(self):
        row = self.lista_grup.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Wybierz grupę do edycji.")
            return
        item = self.lista_grup.item(row)
        grupa = item.data(Qt.UserRole)
        stara_nazwa = grupa.nazwa
        dialog = AddGroupDialog(self.zarzadca, self, edytuj=True, stara_nazwa=stara_nazwa)
        if dialog.exec():
            nowa_nazwa = dialog.nazwa_grupy()
            indeks = self.zarzadca.grupy.index(grupa)
            if self.zarzadca.edytuj_grupe(indeks, nowa_nazwa):
                self._odswiez_liste_grup()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "Błąd", "Nie można zmienić nazwy – grupa o podanej nazwie już istnieje.")

    # --- Akcje na metodach ---
    def _dodaj_metode(self):
        if not self.aktualna_grupa:
            QMessageBox.information(self, "Info", "Najpierw wybierz grupę.")
            return
        indeks_grupy = self.zarzadca.grupy.index(self.aktualna_grupa)
        dialog = AddMethodDialog(self.zarzadca, indeks_grupy, self)
        if dialog.exec():
            nazwa_metody = dialog.wybrana_metoda()
            if self.zarzadca.dodaj_metode_do_grupy(indeks_grupy, nazwa_metody):
                self._pokaz_metody()
                self.data_changed.emit()
            else:
                QMessageBox.warning(self, "Błąd", "Metoda już istnieje w tej grupie.")

    def _usun_metode(self, indeks_metody: int):
        if not self.aktualna_grupa:
            return
        indeks_grupy = self.zarzadca.grupy.index(self.aktualna_grupa)
        metoda = self.aktualna_grupa.metody[indeks_metody]
        odp = QMessageBox.question(self, "Potwierdzenie",
                                   f"Czy na pewno usunąć metodę '{metoda.nazwa}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if odp == QMessageBox.Yes:
            self.zarzadca.usun_metode_z_grupy(indeks_grupy, indeks_metody)
            self._pokaz_metody()
            self.data_changed.emit()

    def _edytuj_metode(self, indeks_metody: int):
        if not self.aktualna_grupa:
            return
        indeks_grupy = self.zarzadca.grupy.index(self.aktualna_grupa)
        metoda = self.aktualna_grupa.metody[indeks_metody]
        dialog = EditMethodDialog(metoda, self.zarzadca.przedzialy, self)
        if dialog.exec():
            nowe_czasy = dialog.pobierz_czasy()
            self.zarzadca.edytuj_metode_w_grupie(indeks_grupy, indeks_metody, nowe_czasy)
            self._pokaz_metody()
            self.data_changed.emit()