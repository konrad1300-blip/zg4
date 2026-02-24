from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTableWidget,
                               QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
                               QHBoxLayout)
from PySide6.QtCore import Signal


class HistoriaWidget(QWidget):
    """Widget wyświetlający historię obliczeń z możliwością eksportu do Excela i usuwania."""
    rekordWybrany = Signal(dict)

    def __init__(self, zarzadca):
        super().__init__()
        self.zarzadca = zarzadca
        self.dane = []
        self._setup_ui()
        self.odswiez()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Kod", "Data", "Grupa", "Przedział", "Czas total [min]", "Czas produkcji [min]", "Odchylenie [%]"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_export = QPushButton("Eksportuj do Excela")
        btn_export.clicked.connect(self.export_excel)
        btn_layout.addWidget(btn_export)

        btn_usun = QPushButton("Usuń zaznaczony rekord")
        btn_usun.clicked.connect(self.usun_rekord)
        btn_layout.addWidget(btn_usun)

        btn_odswiez = QPushButton("Odśwież")
        btn_odswiez.clicked.connect(self.odswiez)
        btn_layout.addWidget(btn_odswiez)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def odswiez(self):
        """Odświeża tabelę danymi z bazy."""
        try:
            self.dane = self.zarzadca.baza.pobierz_wszystkie()
        except Exception as e:
            QMessageBox.critical(self, "Błąd bazy", f"Nie można pobrać danych: {e}")
            self.dane = []

        self.table.setRowCount(len(self.dane))
        for i, row in enumerate(self.dane):
            self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(row['kod']))
            self.table.setItem(i, 2, QTableWidgetItem(row['data']))
            self.table.setItem(i, 3, QTableWidgetItem(row['grupa']))
            self.table.setItem(i, 4, QTableWidgetItem(row['przedzial']))
            self.table.setItem(i, 5, QTableWidgetItem(f"{row['czas_total']:.2f}"))
            czas_prod = row['czas_produkcji']
            self.table.setItem(i, 6, QTableWidgetItem(f"{czas_prod:.2f}" if czas_prod is not None else ""))
            odch = row['odchylenie']
            self.table.setItem(i, 7, QTableWidgetItem(f"{odch:.2f}" if odch is not None else ""))

    def _on_item_double_clicked(self, item):
        row = item.row()
        if 0 <= row < len(self.dane):
            self.rekordWybrany.emit(self.dane[row])

    def usun_rekord(self):
        """Usuwa zaznaczony wiersz z bazy danych."""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Uwaga", "Zaznacz wiersz do usunięcia.")
            return

        item_id = self.table.item(current_row, 0)
        if not item_id:
            return
        rekord_id = int(item_id.text())

        odp = QMessageBox.question(self, "Potwierdzenie",
                                   f"Czy na pewno usunąć rekord o ID {rekord_id}?",
                                   QMessageBox.Yes | QMessageBox.No)
        if odp != QMessageBox.Yes:
            return

        try:
            if self.zarzadca.baza.usun_wpis(rekord_id):
                QMessageBox.information(self, "Sukces", f"Rekord {rekord_id} został usunięty.")
                self.odswiez()
            else:
                QMessageBox.warning(self, "Błąd", "Nie udało się usunąć rekordu.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd bazy", f"Wystąpił błąd podczas usuwania: {e}")

    def export_excel(self):
        """Wywołuje okno wyboru pliku i eksportuje dane do Excela."""
        sciezka, _ = QFileDialog.getSaveFileName(self, "Zapisz jako Excel", "", "Excel files (*.xlsx)")
        if sciezka:
            try:
                if self.zarzadca.baza.export_do_excel(sciezka):
                    QMessageBox.information(self, "Sukces", f"Dane wyeksportowane do {sciezka}")
                else:
                    QMessageBox.warning(self, "Błąd", "Brak danych do eksportu.")
            except Exception as e:
                QMessageBox.critical(self, "Błąd eksportu", f"Nie można zapisać pliku: {e}")