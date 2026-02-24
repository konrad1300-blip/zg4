import sqlite3
import pandas as pd
from datetime import datetime

# Lista metod (oryginalne nazwy)
METODY_ORIGINAL = [
    "HF Duży (ZEMAT)",
    "HF Mały (WOLDAN)",
    "Gorące Powietrze (MILLER)",
    "Gorące Powietrze (Ręcznie)",
    "Gorące Powietrze (Zgrzewarka jezdna)",
    "Gorące Powietrze (ASATECH)",
    "Gorący Klin (SEAMTEC)"
]

# Mapowanie na bezpieczne nazwy kolumn (bez polskich znaków i spacji)
def nazwa_kolumny(oryginalna):
    return (oryginalna
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("ą", "a")
            .replace("ć", "c")
            .replace("ę", "e")
            .replace("ł", "l")
            .replace("ń", "n")
            .replace("ó", "o")
            .replace("ś", "s")
            .replace("ź", "z")
            .replace("ż", "z")
            .replace("Ł", "L")
            .replace("Ó", "O")
    )

KOLUMNY_METR = {orig: nazwa_kolumny(orig) for orig in METODY_ORIGINAL}
BEZPIECZNE_NAZWY = list(KOLUMNY_METR.values())

class BazaDanych:
    """Klasa zarządzająca bazą SQLite z historią obliczeń."""
    def __init__(self, db_path="historia.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            kolumny_metry = ",\n                ".join([f'"{bezp}" REAL' for bezp in BEZPIECZNE_NAZWY])
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS obliczenia (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kod TEXT NOT NULL,
                    data TEXT NOT NULL,
                    grupa TEXT NOT NULL,
                    przedzial TEXT NOT NULL,
                    czas_total REAL NOT NULL,
                    czas_produkcji REAL,
                    odchylenie REAL,
                    {kolumny_metry}
                )
            """)

    def dodaj_wpis(self, kod, grupa, przedzial, metry_dict, czas_total, czas_produkcji=None):
        """
        metry_dict: słownik {oryginalna_nazwa_metody: metry} dla metod, które mają metraż > 0
        """
        data = datetime.now().isoformat()
        # Wartości dla kolumn metrażu (w kolejności METODY_ORIGINAL)
        values = [kod, data, grupa, przedzial, czas_total, czas_produkcji, None]
        for orig in METODY_ORIGINAL:
            values.append(metry_dict.get(orig, 0.0))
        
        placeholders = ','.join(['?'] * len(values))
        kolumny = ['kod', 'data', 'grupa', 'przedzial', 'czas_total', 'czas_produkcji', 'odchylenie'] + BEZPIECZNE_NAZWY
        kolumny_sql = ', '.join(f'"{k}"' for k in kolumny)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"""
                INSERT INTO obliczenia ({kolumny_sql})
                VALUES ({placeholders})
            """, values)
            return cursor.lastrowid

    def aktualizuj_czas_produkcji(self, wpis_id, czas_produkcji, odchylenie):
        """Aktualizuje czas produkcji i zapisuje odchylenie."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE obliczenia 
                SET czas_produkcji = ?, odchylenie = ?
                WHERE id = ?
            """, (czas_produkcji, odchylenie, wpis_id))

    def usun_wpis(self, wpis_id):
        """Usuwa wpis o podanym ID z bazy danych."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM obliczenia WHERE id = ?", (wpis_id,))
            return cursor.rowcount > 0

    def pobierz_wszystkie(self):
        """Zwraca listę wszystkich wpisów (jako słowniki) posortowaną malejąco według daty.
           Klucze słownika to oryginalne nazwy metod (dla wygody)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM obliczenia ORDER BY data DESC")
            rows = [dict(row) for row in cursor.fetchall()]
            # Dodajemy wpisy z oryginalnymi nazwami (dla łatwiejszego dostępu)
            for row in rows:
                for orig, bezp in KOLUMNY_METR.items():
                    # Jeśli kolumna istnieje w bazie, przepisz, w przeciwnym razie 0.0
                    row[orig] = row.get(bezp, 0.0)
            return rows

    def export_do_excel(self, sciezka):
        """Eksportuje wszystkie dane do pliku Excel (format .xlsx)."""
        dane = self.pobierz_wszystkie()
        if not dane:
            return False
        df = pd.DataFrame(dane)
        # Usuwamy bezpieczne kolumny, zostawiamy oryginalne
        kolumny_do_usuniecia = BEZPIECZNE_NAZWY
        df.drop(columns=kolumny_do_usuniecia, inplace=True, errors='ignore')
        # Zmieniamy nazwę kolumny odchylenie na "Odchylenie [%]"
        df.rename(columns={'odchylenie': 'Odchylenie [%]'}, inplace=True)
        df.to_excel(sciezka, index=False, engine='openpyxl')
        return True