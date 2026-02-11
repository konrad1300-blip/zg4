import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union


class MetodaZgrzewania:
    """Klasa reprezentująca metodę zgrzewania z jej ustawieniami czasowymi"""
    def __init__(self, nazwa: str):
        self.nazwa = nazwa
        self.czasy: Dict[str, Dict[str, Union[int, float]]] = {}
        self.domyslne_czasy = {
            "HF Duży (ZEMAT)": {
                "do 2m2": (1, 2.0),
                "od 2 do 20m2": (1, 3.0),
                "od 20 do 60m2": (2, 2.0),
                "powyżej 60m2": (3, 3.0)
            },
            "HF Mały (WOLDAN)": {
                "do 2m2": (1, 2.0),
                "od 2 do 20m2": (1, 3.0),
                "od 20 do 60m2": (2, 2.0),
                "powyżej 60m2": (3, 3.0)
            },
            "Gorące Powietrze (MILLER)": {
                "do 2m2": (1, 1.5),
                "od 2 do 20m2": (2, 1.5),
                "od 20 do 60m2": (3, 1.5),
                "powyżej 60m2": (4, 2.0)
            },
            "Gorące Powietrze (Ręcznie)": {
                "do 2m2": (1, 3.0),
                "od 2 do 20m2": (1, 5.0),
                "od 20 do 60m2": (2, 4.0),
                "powyżej 60m2": (3, 5.0)
            },
            "Gorące Powietrze (Zgrzewarka jezdna)": {
                "do 2m2": (1, 1.5),
                "od 2 do 20m2": (2, 2.0),
                "od 20 do 60m2": (3, 3.0),
                "powyżej 60m2": (4, 4.0)
            },
            "Gorące Powietrze (ASATECH)": {
                "do 2m2": (1, 1.5),
                "od 2 do 20m2": (2, 2.0),
                "od 20 do 60m2": (3, 3.0),
                "powyżej 60m2": (4, 4.0)
            },
            "Gorący Klin (SEAMTEC)": {
                "do 2m2": (1, 1.5),
                "od 2 do 20m2": (2, 1.5),
                "od 20 do 60m2": (3, 1.5),
                "powyżej 60m2": (4, 2.0)
            }
        }
        if nazwa in self.domyslne_czasy:
            self.czasy = {k: {"pracownicy": v[0], "czas": v[1]}
                         for k, v in self.domyslne_czasy[nazwa].items()}

    def ustaw_czas(self, przedzial: str, pracownicy: int, czas: float):
        self.czasy[przedzial] = {"pracownicy": pracownicy, "czas": czas}

    def pobierz_czas(self, przedzial: str) -> Tuple[int, float]:
        if przedzial in self.czasy:
            return (self.czasy[przedzial]["pracownicy"], self.czasy[przedzial]["czas"])
        return (1, 0.0)

    def to_dict(self) -> dict:
        return {
            "nazwa": self.nazwa,
            "czasy": self.czasy
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MetodaZgrzewania':
        metoda = cls(data["nazwa"])
        metoda.czasy = data["czasy"]
        return metoda


class Grupa:
    """Klasa reprezentująca grupę produktów z metodami zgrzewania"""
    def __init__(self, nazwa: str):
        self.nazwa = nazwa
        self.metody: List[MetodaZgrzewania] = []
        self.domyslne_metody = [
            "HF Duży (ZEMAT)",
            "HF Mały (WOLDAN)",
            "Gorące Powietrze (MILLER)",
            "Gorące Powietrze (Ręcznie)",
            "Gorące Powietrze (Zgrzewarka jezdna)",
            "Gorące Powietrze (ASATECH)",
            "Gorący Klin (SEAMTEC)"
        ]

    def dodaj_metode(self, metoda: MetodaZgrzewania):
        self.metody.append(metoda)

    def usun_metode(self, indeks: int):
        if 0 <= indeks < len(self.metody):
            self.metody.pop(indeks)

    def to_dict(self) -> dict:
        return {
            "nazwa": self.nazwa,
            "metody": [m.to_dict() for m in self.metody]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Grupa':
        grupa = cls(data["nazwa"])
        for metoda_data in data["metody"]:
            grupa.dodaj_metode(MetodaZgrzewania.from_dict(metoda_data))
        return grupa


class Produkt:
    """Klasa reprezentująca produkt do obliczeń"""
    def __init__(self, kod: str, grupa: Grupa, przedzial: str):
        self.kod = kod
        self.grupa = grupa
        self.przedzial = przedzial
        self.metry_zgrzewania: Dict[str, float] = {}
        self.wymuszeni_pracownicy: Dict[str, int] = {}
        self.czas_produkcji: Optional[float] = None
        self.wyniki: Dict[str, Dict] = {}

    def oblicz_czasy(self):
        self.wyniki = {}
        for metoda in self.grupa.metody:
            if metoda.nazwa in self.metry_zgrzewania:
                metry = self.metry_zgrzewania[metoda.nazwa]
                pracownicy, czas_na_metr = metoda.pobierz_czas(self.przedzial)
                if metoda.nazwa in self.wymuszeni_pracownicy:
                    pracownicy = self.wymuszeni_pracownicy[metoda.nazwa]
                czas_calkowity = metry * czas_na_metr * pracownicy
                self.wyniki[metoda.nazwa] = {
                    "metry": metry,
                    "czas_na_metr": czas_na_metr,
                    "pracownicy": pracownicy,
                    "czas_calkowity": czas_calkowity,
                    "czy_wymuszeni": metoda.nazwa in self.wymuszeni_pracownicy
                }

    def oblicz_calkowity_czas(self) -> float:
        return sum(w["czas_calkowity"] for w in self.wyniki.values())

    def oblicz_odchylenie(self) -> Optional[float]:
        if self.czas_produkcji is not None:
            czas_obliczony = self.oblicz_calkowity_czas()
            if czas_obliczony > 0:
                return ((self.czas_produkcji - czas_obliczony) / czas_obliczony) * 100
        return None


class ZarzadcaDanych:
    """Główny zarządca danych – wczytuje, zapisuje i modyfikuje grupy."""
    def __init__(self, plik_danych: str = "dane_zgrzewania.json"):
        self.plik_danych = plik_danych
        self.grupy: List[Grupa] = []
        self.przedzialy = ["do 2m2", "od 2 do 20m2", "od 20 do 60m2", "powyżej 60m2"]
        self._wczytaj()

    def _wczytaj(self):
        if os.path.exists(self.plik_danych):
            try:
                with open(self.plik_danych, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.grupy = [Grupa.from_dict(g) for g in data.get("grupy", [])]
            except Exception:
                self._utworz_domyslne()
        else:
            self._utworz_domyslne()

    def _utworz_domyslne(self):
        grupy_nazwy = ["Koła", "Box", "Płachty", "Nieregularne Drobne", "Nieregularne Duże"]
        for nazwa in grupy_nazwy:
            grupa = Grupa(nazwa)
            for m_nazwa in grupa.domyslne_metody:
                grupa.dodaj_metode(MetodaZgrzewania(m_nazwa))
            self.grupy.append(grupa)

    def zapisz(self):
        data = {
            "grupy": [g.to_dict() for g in self.grupy],
            "data_zapisu": datetime.now().isoformat()
        }
        with open(self.plik_danych, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- Zarządzanie grupami ---
    def dodaj_grupe(self, nazwa: str) -> bool:
        if any(g.nazwa.lower() == nazwa.lower() for g in self.grupy):
            return False
        self.grupy.append(Grupa(nazwa))
        self.zapisz()
        return True

    def usun_grupe(self, indeks: int) -> bool:
        if 0 <= indeks < len(self.grupy):
            self.grupy.pop(indeks)
            self.zapisz()
            return True
        return False

    def edytuj_grupe(self, indeks: int, nowa_nazwa: str) -> bool:
        if 0 <= indeks < len(self.grupy) and not any(g.nazwa.lower() == nowa_nazwa.lower() for g in self.grupy if g != self.grupy[indeks]):
            self.grupy[indeks].nazwa = nowa_nazwa
            self.zapisz()
            return True
        return False

    # --- Zarządzanie metodami w grupie ---
    def dodaj_metode_do_grupy(self, indeks_grupy: int, nazwa_metody: str) -> bool:
        if 0 <= indeks_grupy < len(self.grupy):
            grupa = self.grupy[indeks_grupy]
            if any(m.nazwa == nazwa_metody for m in grupa.metody):
                return False
            grupa.dodaj_metode(MetodaZgrzewania(nazwa_metody))
            self.zapisz()
            return True
        return False

    def usun_metode_z_grupy(self, indeks_grupy: int, indeks_metody: int) -> bool:
        if 0 <= indeks_grupy < len(self.grupy):
            grupa = self.grupy[indeks_grupy]
            if 0 <= indeks_metody < len(grupa.metody):
                grupa.usun_metode(indeks_metody)
                self.zapisz()
                return True
        return False

    def edytuj_metode_w_grupie(self, indeks_grupy: int, indeks_metody: int,
                               nowe_czasy: Dict[str, Tuple[int, float]]) -> bool:
        if 0 <= indeks_grupy < len(self.grupy):
            grupa = self.grupy[indeks_grupy]
            if 0 <= indeks_metody < len(grupa.metody):
                metoda = grupa.metody[indeks_metody]
                for przedzial, (prac, czas) in nowe_czasy.items():
                    metoda.ustaw_czas(przedzial, prac, czas)
                self.zapisz()
                return True
        return False