import sqlite3
import pandas as pd
from datetime import datetime

class BazaDanych:
    """Klasa zarządzająca relacyjną bazą SQLite z historią obliczeń."""
    def __init__(self, db_path="historia.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Tworzy tabele, jeśli nie istnieją."""
        with sqlite3.connect(self.db_path) as conn:
            # Główna tabela obliczeń
            conn.execute("""
                CREATE TABLE IF NOT EXISTS obliczenia (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kod TEXT NOT NULL,
                    data TEXT NOT NULL,
                    grupa TEXT NOT NULL,
                    przedzial TEXT NOT NULL,
                    czas_total REAL NOT NULL,
                    czas_produkcji REAL,
                    odchylenie REAL
                )
            """)
            # Tabela metraży – osobne wiersze dla każdej metody
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metry_obliczenia (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    obliczenie_id INTEGER NOT NULL,
                    metoda TEXT NOT NULL,
                    metry REAL NOT NULL,
                    FOREIGN KEY (obliczenie_id) REFERENCES obliczenia(id) ON DELETE CASCADE
                )
            """)
            # Indeks dla szybszego wyszukiwania
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metry_obliczenie ON metry_obliczenia(obliczenie_id)")

    def dodaj_wpis(self, kod, grupa, przedzial, metry_dict, czas_total, czas_produkcji=None):
        """
        metry_dict: słownik {nazwa_metody: metry} dla metod, które mają metraż > 0
        Zwraca ID nowego wpisu.
        """
        data = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO obliczenia (kod, data, grupa, przedzial, czas_total, czas_produkcji, odchylenie)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (kod, data, grupa, przedzial, czas_total, czas_produkcji, None))
            obliczenie_id = cursor.lastrowid

            # Dodaj metraże
            for metoda, metry in metry_dict.items():
                if metry > 0:
                    conn.execute("""
                        INSERT INTO metry_obliczenia (obliczenie_id, metoda, metry)
                        VALUES (?, ?, ?)
                    """, (obliczenie_id, metoda, metry))

            return obliczenie_id

    def aktualizuj_czas_produkcji(self, wpis_id, czas_produkcji, odchylenie):
        """Aktualizuje czas produkcji i odchylenie dla istniejącego wpisu."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE obliczenia 
                SET czas_produkcji = ?, odchylenie = ?
                WHERE id = ?
            """, (czas_produkcji, odchylenie, wpis_id))

    def usun_wpis(self, wpis_id):
        """Usuwa wpis o podanym ID (kaskadowo usuwa też metraże)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM obliczenia WHERE id = ?", (wpis_id,))
            return cursor.rowcount > 0

    def pobierz_wszystkie(self):
        """
        Zwraca listę wpisów z dołączonymi metrażami.
        Każdy wpis to słownik zawierający pola z tabeli obliczenia oraz
        dodatkowo słownik 'metraze' z metrażami dla poszczególnych metod.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Pobierz główne dane
            cursor = conn.execute("SELECT * FROM obliczenia ORDER BY data DESC")
            rows = [dict(row) for row in cursor.fetchall()]

            # Dla każdego wpisu dołącz metraże
            for row in rows:
                cursor_metry = conn.execute(
                    "SELECT metoda, metry FROM metry_obliczenia WHERE obliczenie_id = ?",
                    (row['id'],)
                )
                metraze = {m['metoda']: m['metry'] for m in cursor_metry.fetchall()}
                row['metraze'] = metraze

            return rows

    def export_do_excel(self, sciezka):
        """
        Eksportuje wszystkie dane do pliku Excel.
        Tworzy arkusz z głównymi danymi i arkusz z metrażami.
        """
        dane = self.pobierz_wszystkie()
        if not dane:
            return False

        # Przygotuj DataFrame dla głównych danych
        df_glowne = pd.DataFrame([{
            'ID': r['id'],
            'Kod': r['kod'],
            'Data': r['data'],
            'Grupa': r['grupa'],
            'Przedział': r['przedzial'],
            'Czas total [min]': r['czas_total'],
            'Czas produkcji [min]': r['czas_produkcji'] if r['czas_produkcji'] is not None else '',
            'Odchylenie [%]': r['odchylenie'] if r['odchylenie'] is not None else ''
        } for r in dane])

        # Przygotuj DataFrame dla metraży (w formacie "szerokim" – metody w kolumnach)
        # Najpierw zbierz wszystkie unikalne metody
        wszystkie_metody = set()
        for r in dane:
            wszystkie_metody.update(r['metraze'].keys())
        wszystkie_metody = sorted(wszystkie_metody)

        # Stwórz wiersze dla każdego ID z wartościami metraży
        metry_data = []
        for r in dane:
            wiersz = {'ID': r['id']}
            for metoda in wszystkie_metody:
                wiersz[metoda] = r['metraze'].get(metoda, 0.0)
            metry_data.append(wiersz)

        df_metry = pd.DataFrame(metry_data)

        # Zapisz do Excela z dwoma arkuszami
        with pd.ExcelWriter(sciezka, engine='openpyxl') as writer:
            df_glowne.to_excel(writer, sheet_name='Podsumowanie', index=False)
            df_metry.to_excel(writer, sheet_name='Metry', index=False)

        return True