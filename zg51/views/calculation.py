from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QComboBox, QGroupBox, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QCheckBox, QSpinBox,
                               QDoubleSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog
from models import ZarzadcaDanych, Produkt
from utils import waliduj_kod


class CalculationWidget(QWidget):
    def __init__(self, zarzadca: ZarzadcaDanych):
        super().__init__()
        self.zarzadca = zarzadca
        self.produkt = None
        self.ostatni_wpis_id = None
        self._setup_ui()
        self.refresh_groups()
        self.grupa_combo.currentIndexChanged.connect(self._odswiez_tabele_metrow)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Sekcja danych produktu ---
        form_group = QGroupBox("Dane produktu")
        form_layout = QFormLayout(form_group)

        self.kod_input = QLineEdit()
        self.kod_input.setPlaceholderText("xxx-xxxx-xxx")
        form_layout.addRow("Kod produktu:", self.kod_input)

        self.grupa_combo = QComboBox()
        form_layout.addRow("Grupa:", self.grupa_combo)

        self.przedzial_combo = QComboBox()
        self.przedzial_combo.addItems(self.zarzadca.przedzialy)
        form_layout.addRow("Przedział wielkości:", self.przedzial_combo)

        main_layout.addWidget(form_group)

        # --- Sekcja metrów zgrzewania i wymuszenia pracowników ---
        self.metry_group = QGroupBox("Metry zgrzewania dla metod")
        metry_layout = QVBoxLayout(self.metry_group)
        self.metry_table = QTableWidget()
        self.metry_table.setColumnCount(4)
        self.metry_table.setHorizontalHeaderLabels(["Metoda", "Metry (mtr)", "Wymuś pracowników", "Liczba"])
        self.metry_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        metry_layout.addWidget(self.metry_table)
        main_layout.addWidget(self.metry_group)

        # --- Przyciski akcji ---
        btn_layout = QHBoxLayout()
        self.oblicz_btn = QPushButton("Oblicz czas")
        self.oblicz_btn.clicked.connect(self.oblicz)
        btn_layout.addWidget(self.oblicz_btn)

        self.waliduj_btn = QPushButton("Waliduj z czasem produkcji")
        self.waliduj_btn.clicked.connect(self.waliduj)
        self.waliduj_btn.setEnabled(False)
        btn_layout.addWidget(self.waliduj_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # --- Sekcja wyników ---
        self.wyniki_group = QGroupBox("Wyniki obliczeń")
        wyniki_layout = QVBoxLayout(self.wyniki_group)

        self.wyniki_text = QLabel()
        self.wyniki_text.setAlignment(Qt.AlignTop)
        self.wyniki_text.setWordWrap(True)
        wyniki_layout.addWidget(self.wyniki_text)

        main_layout.addWidget(self.wyniki_group)

    def refresh_groups(self):
        """Odświeża listę grup w combobox."""
        self.grupa_combo.clear()
        for grupa in self.zarzadca.grupy:
            self.grupa_combo.addItem(grupa.nazwa, grupa)
        self._odswiez_tabele_metrow()

    def _odswiez_tabele_metrow(self):
        """Wypełnia tabelę metrów na podstawie wybranej grupy."""
        grupa = self.grupa_combo.currentData()
        if not grupa:
            self.metry_table.setRowCount(0)
            return

        self.metry_table.setRowCount(len(grupa.metody))
        for i, metoda in enumerate(grupa.metody):
            # Nazwa metody
            self.metry_table.setItem(i, 0, QTableWidgetItem(metoda.nazwa))

            # SpinBox dla metrów z jednostką "mtr"
            spin_metry = QDoubleSpinBox()
            spin_metry.setRange(0, 10000)
            spin_metry.setDecimals(2)
            spin_metry.setSuffix(" mtr")
            self.metry_table.setCellWidget(i, 1, spin_metry)

            # CheckBox "Wymuś pracowników"
            chk_wymus = QCheckBox()
            self.metry_table.setCellWidget(i, 2, chk_wymus)

            # SpinBox dla liczby pracowników (domyślnie wyłączony)
            spin_prac = QSpinBox()
            spin_prac.setRange(1, 10)
            spin_prac.setEnabled(False)
            self.metry_table.setCellWidget(i, 3, spin_prac)

            # Połączenie: włączenie/wyłączenie spinBoxa pracowników
            chk_wymus.toggled.connect(spin_prac.setEnabled)

    def oblicz(self):
        """Główna metoda obliczeniowa."""
        kod = self.kod_input.text().strip()
        if not waliduj_kod(kod):
            QMessageBox.warning(self, "Błąd", "Nieprawidłowy format kodu produktu. Wymagany format: xxx-xxxx-xxx (same cyfry).")
            return

        grupa = self.grupa_combo.currentData()
        if not grupa:
            QMessageBox.warning(self, "Błąd", "Wybierz grupę produktów.")
            return

        przedzial = self.przedzial_combo.currentText()

        # Tworzymy obiekt produktu
        produkt = Produkt(kod, grupa, przedzial)

        # Zbieramy metry i ewentualne wymuszenia
        for i, metoda in enumerate(grupa.metody):
            spin_metry = self.metry_table.cellWidget(i, 1)
            metry = spin_metry.value()
            if metry > 0:
                produkt.metry_zgrzewania[metoda.nazwa] = metry

                chk_wymus = self.metry_table.cellWidget(i, 2)
                if chk_wymus.isChecked():
                    spin_prac = self.metry_table.cellWidget(i, 3)
                    produkt.wymuszeni_pracownicy[metoda.nazwa] = spin_prac.value()

        if not produkt.metry_zgrzewania:
            QMessageBox.warning(self, "Błąd", "Wprowadź przynajmniej jeden metraż dla metody.")
            return

        # Obliczenia
        produkt.oblicz_czasy()
        self.produkt = produkt
        self._wyswietl_wyniki(produkt)

        # --- Zapis do bazy danych ---
        metry_dict = produkt.metry_zgrzewania
        czas_total = produkt.oblicz_calkowity_czas()
        self.ostatni_wpis_id = self.zarzadca.baza.dodaj_wpis(
            kod=produkt.kod,
            grupa=produkt.grupa.nazwa,
            przedzial=produkt.przedzial,
            metry_dict=metry_dict,
            czas_total=czas_total,
            czas_produkcji=None
        )
        # ---------------------------

        self.waliduj_btn.setEnabled(True)

    def _wyswietl_wyniki(self, produkt: Produkt):
        """Wyświetla szczegółowe wyniki w etykiecie."""
        czas_calkowity = produkt.oblicz_calkowity_czas()
        text = f"<b>Kod produktu:</b> {produkt.kod}<br>"
        text += f"<b>Grupa:</b> {produkt.grupa.nazwa}<br>"
        text += f"<b>Przedział wielkości:</b> {produkt.przedzial}<br><br>"
        text += "<b>Szczegółowe obliczenia:</b><br>"

        for nazwa, wynik in produkt.wyniki.items():
            text += f"<hr><b>{nazwa}</b><br>"
            text += f"&nbsp;&nbsp;Metry: {wynik['metry']:.2f} mtr<br>"
            text += f"&nbsp;&nbsp;Czas na metr: {wynik['czas_na_metr']:.2f} min<br>"
            text += f"&nbsp;&nbsp;Liczba pracowników: {wynik['pracownicy']} {'(wymuszeni)' if wynik['czy_wymuszeni'] else ''}<br>"
            text += f"&nbsp;&nbsp;Czas całkowity: {wynik['czas_calkowity']:.2f} min<br>"

        text += f"<hr><b>CAŁKOWITY CZAS ZGRZEWANIA: {czas_calkowity:.2f} min</b>"
        self.wyniki_text.setText(text)

    def waliduj(self):
        """Walidacja obliczonego czasu z rzeczywistym czasem produkcji."""
        if not self.produkt:
            return

        czas, ok = QInputDialog.getDouble(self, "Walidacja", "Podaj czas z produkcji (w minutach):",
                                          decimals=2, minValue=0)
        if ok:
            self.produkt.czas_produkcji = czas
            odchylenie = self.produkt.oblicz_odchylenie()
            if odchylenie is not None and self.ostatni_wpis_id:
                self.zarzadca.baza.aktualizuj_czas_produkcji(self.ostatni_wpis_id, czas, odchylenie)
            if odchylenie is not None:
                msg = f"Czas obliczony: {self.produkt.oblicz_calkowity_czas():.2f} min\n"
                msg += f"Czas z produkcji: {czas:.2f} min\n"
                msg += f"Odchylenie: {odchylenie:+.2f}%\n\n"
                if abs(odchylenie) <= 10:
                    msg += "Status: W normie (odchylenie ≤ 10%)"
                elif abs(odchylenie) <= 20:
                    msg += "Status: Dopuszczalne (odchylenie ≤ 20%)"
                else:
                    msg += "Status: Poza normą (odchylenie > 20%)"
                QMessageBox.information(self, "Wynik walidacji", msg)

    def wypelnij_z_historii(self, dane):
        """Wypełnia formularz danymi z rekordu historii."""
        self.kod_input.setText(dane['kod'])

        # Ustaw grupę
        nazwa_grupy = dane['grupa']
        for i in range(self.grupa_combo.count()):
            if self.grupa_combo.itemText(i) == nazwa_grupy:
                self.grupa_combo.setCurrentIndex(i)
                break

        # Ustaw przedział
        index_przedzial = self.przedzial_combo.findText(dane['przedzial'])
        if index_przedzial >= 0:
            self.przedzial_combo.setCurrentIndex(index_przedzial)

        # Odśwież tabelę metrów (po zmianie grupy)
        self._odswiez_tabele_metrow()

        # Wypełnij metry
        grupa = self.grupa_combo.currentData()
        if grupa:
            metraze = dane.get('metraze', {})
            for i, metoda in enumerate(grupa.metody):
                if metoda.nazwa in metraze:
                    metry = metraze[metoda.nazwa]
                    if metry > 0:
                        spin = self.metry_table.cellWidget(i, 1)
                        spin.setValue(metry)