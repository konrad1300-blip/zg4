# Program do obliczania czasów zgrzewania z podziałem na metody
# Autor: Konrad Piaskowski
# Wersja 4.0
# Piła luty 2026

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

class MetodaZgrzewania:
    """Klasa reprezentująca metodę zgrzewania z jej ustawieniami czasowymi"""
    def __init__(self, nazwa: str):
        self.nazwa = nazwa
        self.czasy: Dict[str, Dict[str, Union[int, float]]] = {}  # {przedzial: {"pracownicy": int, "czas": float}}
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
        
        # Ustaw domyślne czasy jeśli metoda istnieje w domyślnych
        if nazwa in self.domyslne_czasy:
            self.czasy = {k: {"pracownicy": v[0], "czas": v[1]} 
                         for k, v in self.domyslne_czasy[nazwa].items()}
    
    def ustaw_czas(self, przedzial: str, pracownicy: int, czas: float):
        """Ustawia czas dla danego przedziału wielkości"""
        self.czasy[przedzial] = {"pracownicy": pracownicy, "czas": czas}
    
    def pobierz_czas(self, przedzial: str) -> Tuple[int, float]:
        """Pobiera ustawienia czasu dla danego przedziału"""
        if przedzial in self.czasy:
            return (self.czasy[przedzial]["pracownicy"], self.czasy[przedzial]["czas"])
        return (1, 0.0)  # Domyślne wartości
    
    def to_dict(self) -> dict:
        """Konwertuje obiekt do słownika"""
        return {
            "nazwa": self.nazwa,
            "czasy": self.czasy
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MetodaZgrzewania':
        """Tworzy obiekt ze słownika"""
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
        """Dodaje metodę zgrzewania do grupy"""
        self.metody.append(metoda)
    
    def usun_metode(self, indeks: int):
        """Usuwa metodę z grupy"""
        if 0 <= indeks < len(self.metody):
            self.metody.pop(indeks)
    
    def edytuj_metode(self, indeks: int, nowa_nazwa: str = None, 
                      nowe_czasy: Dict[str, Tuple[int, float]] = None):
        """Edytuje metodę w grupie"""
        if 0 <= indeks < len(self.metody):
            if nowa_nazwa:
                self.metody[indeks].nazwa = nowa_nazwa
            if nowe_czasy:
                for przedzial, (pracownicy, czas) in nowe_czasy.items():
                    self.metody[indeks].ustaw_czas(przedzial, pracownicy, czas)
    
    def to_dict(self) -> dict:
        """Konwertuje obiekt do słownika"""
        return {
            "nazwa": self.nazwa,
            "metody": [metoda.to_dict() for metoda in self.metody]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Grupa':
        """Tworzy obiekt ze słownika"""
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
        # Słownik do przechowywania metrów zgrzewania dla każdej metody
        self.metry_zgrzewania: Dict[str, float] = {}
        # Słownik do przechowywania wymuszonej liczby pracowników
        self.wymuszeni_pracownicy: Dict[str, int] = {}
        self.czas_produkcji: Optional[float] = None
        self.wyniki: Dict[str, Dict] = {}
    
    def oblicz_czasy(self):
        """Oblicza czasy dla wszystkich metod"""
        self.wyniki = {}
        
        for metoda in self.grupa.metody:
            if metoda.nazwa in self.metry_zgrzewania:
                metry = self.metry_zgrzewania[metoda.nazwa]
                pracownicy, czas_na_metr = metoda.pobierz_czas(self.przedzial)
                
                # Sprawdź czy wymuszono liczbę pracowników
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
        """Oblicza całkowity czas zgrzewania"""
        return sum(wynik["czas_calkowity"] for wynik in self.wyniki.values())
    
    def oblicz_odchylenie(self) -> Optional[float]:
        """Oblicza odchylenie od czasu produkcji"""
        if self.czas_produkcji is not None:
            czas_obliczony = self.oblicz_calkowity_czas()
            if czas_obliczony > 0:
                return ((self.czas_produkcji - czas_obliczony) / czas_obliczony) * 100
        return None


class ProgramZgrzewania:
    """Główna klasa programu"""
    def __init__(self):
        self.grupy: List[Grupa] = []
        self.przedzialy = ["do 2m2", "od 2 do 20m2", "od 20 do 60m2", "powyżej 60m2"]
        self.plik_danych = "dane_zgrzewania.json"
        self.wczytaj_dane()
    
    def wczytaj_dane(self):
        """Wczytuje dane z pliku JSON"""
        if os.path.exists(self.plik_danych):
            try:
                with open(self.plik_danych, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.grupy = [Grupa.from_dict(grupa_data) for grupa_data in data.get("grupy", [])]
            except Exception as e:
                print(f"Błąd wczytywania danych: {e}")
                self.utworz_domyslne_grupy()
        else:
            self.utworz_domyslne_grupy()
    
    def zapisz_dane(self):
        """Zapisuje dane do pliku JSON"""
        try:
            data = {
                "grupy": [grupa.to_dict() for grupa in self.grupy],
                "data_zapisu": datetime.now().isoformat()
            }
            with open(self.plik_danych, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Błąd zapisywania danych: {e}")
    
    def utworz_domyslne_grupy(self):
        """Tworzy domyślne grupy produktów"""
        grupy_nazwy = ["Koła", "Box", "Płachty", "Nieregularne Drobne", "Nieregularne Duże"]
        
        for nazwa_grupy in grupy_nazwy:
            grupa = Grupa(nazwa_grupy)
            
            # Dodaj domyślne metody do każdej grupy
            for nazwa_metody in grupa.domyslne_metody:
                metoda = MetodaZgrzewania(nazwa_metody)
                grupa.dodaj_metode(metoda)
            
            self.grupy.append(grupa)
    
    def pokaz_menu(self):
        """Wyświetla główne menu programu"""
        print("\n" + "="*50)
        print("PROGRAM DO OBLICZANIA CZASÓW ZGRZEWANIA")
        print("Autor: Konrad Piaskowski")
        print("Wersja 4.0 - Luty 2026")
        print("="*50)
        print("\nGŁÓWNE MENU:")
        print("1. Zarządzanie grupami")
        print("2. Oblicz czas zgrzewania dla produktu")
        print("3. Pokaż wszystkie grupy i metody")
        print("4. Zapisz dane")
        print("5. Zakończ program")
    
    def zarzadzaj_grupami(self):
        """Menu zarządzania grupami"""
        while True:
            print("\n--- ZARZĄDZANIE GRUPAMI ---")
            print("1. Pokaż wszystkie grupy")
            print("2. Dodaj nową grupę")
            print("3. Usuń grupę")
            print("4. Edytuj grupę")
            print("5. Wróć do głównego menu")
            
            wybor = input("\nWybierz opcję (1-5): ")
            
            if wybor == "1":
                self.pokaz_grupy()
            elif wybor == "2":
                self.dodaj_grupe()
            elif wybor == "3":
                self.usun_grupe()
            elif wybor == "4":
                self.edytuj_grupe()
            elif wybor == "5":
                break
            else:
                print("Nieprawidłowy wybór!")
    
    def pokaz_grupy(self):
        """Wyświetla wszystkie grupy"""
        if not self.grupy:
            print("\nBrak grup!")
            return
        
        print("\n--- LISTA GRUP ---")
        for i, grupa in enumerate(self.grupy, 1):
            print(f"\n{i}. {grupa.nazwa}:")
            for j, metoda in enumerate(grupa.metody, 1):
                print(f"   {j}. {metoda.nazwa}")
                for przedzial in self.przedzialy:
                    pracownicy, czas = metoda.pobierz_czas(przedzial)
                    print(f"      {przedzial}: {pracownicy} osoba/y * {czas} min")
    
    def dodaj_grupe(self):
        """Dodaje nową grupę"""
        nazwa = input("\nPodaj nazwę nowej grupy: ")
        
        # Sprawdź czy grupa już istnieje
        for grupa in self.grupy:
            if grupa.nazwa.lower() == nazwa.lower():
                print("Grupa o tej nazwie już istnieje!")
                return
        
        nowa_grupa = Grupa(nazwa)
        
        # Dodaj metody do nowej grupy
        print("\nDostępne metody zgrzewania:")
        metody_lista = [
            "HF Duży (ZEMAT)",
            "HF Mały (WOLDAN)",
            "Gorące Powietrze (MILLER)",
            "Gorące Powietrze (Ręcznie)",
            "Gorące Powietrze (Zgrzewarka jezdna)",
            "Gorące Powietrze (ASATECH)",
            "Gorący Klin (SEAMTEC)"
        ]
        
        for i, metoda_nazwa in enumerate(metody_lista, 1):
            print(f"{i}. {metoda_nazwa}")
        
        print("\nWybierz metody do dodania (np. 1,3,5 lub 'wszystkie'):")
        wybor = input("Wybierz: ")
        
        if wybor.lower() == 'wszystkie':
            for metoda_nazwa in metody_lista:
                metoda = MetodaZgrzewania(metoda_nazwa)
                nowa_grupa.dodaj_metode(metoda)
        else:
            try:
                wybrane = [int(x.strip()) for x in wybor.split(',')]
                for numer in wybrane:
                    if 1 <= numer <= len(metody_lista):
                        metoda = MetodaZgrzewania(metody_lista[numer-1])
                        nowa_grupa.dodaj_metode(metoda)
            except ValueError:
                print("Nieprawidłowy format!")
                return
        
        self.grupy.append(nowa_grupa)
        print(f"\nGrupa '{nazwa}' została dodana!")
    
    def usun_grupe(self):
        """Usuwa grupę"""
        if not self.grupy:
            print("\nBrak grup do usunięcia!")
            return
        
        self.pokaz_grupy()
        try:
            numer = int(input("\nPodaj numer grupy do usunięcia: "))
            if 1 <= numer <= len(self.grupy):
                usunieta_grupa = self.grupy.pop(numer-1)
                print(f"\nGrupa '{usunieta_grupa.nazwa}' została usunięta!")
            else:
                print("Nieprawidłowy numer grupy!")
        except ValueError:
            print("Nieprawidłowa wartość!")
    
    def edytuj_grupe(self):
        """Edytuje istniejącą grupę"""
        if not self.grupy:
            print("\nBrak grup do edycji!")
            return
        
        self.pokaz_grupy()
        try:
            numer = int(input("\nPodaj numer grupy do edycji: "))
            if 1 <= numer <= len(self.grupy):
                grupa = self.grupy[numer-1]
                self.menu_edycji_grupy(grupa)
            else:
                print("Nieprawidłowy numer grupy!")
        except ValueError:
            print("Nieprawidłowa wartość!")
    
    def menu_edycji_grupy(self, grupa: Grupa):
        """Menu edycji pojedynczej grupy"""
        while True:
            print(f"\n--- EDYCJA GRUPY: {grupa.nazwa} ---")
            print("1. Pokaż metody w grupie")
            print("2. Dodaj metodę do grupie")
            print("3. Usuń metodę z grupy")
            print("4. Edytuj metodę w grupie")
            print("5. Wróć do poprzedniego menu")
            
            wybor = input("\nWybierz opcję (1-5): ")
            
            if wybor == "1":
                print(f"\nMetody w grupie '{grupa.nazwa}':")
                for i, metoda in enumerate(grupa.metody, 1):
                    print(f"{i}. {metoda.nazwa}")
                    for przedzial in self.przedzialy:
                        pracownicy, czas = metoda.pobierz_czas(przedzial)
                        print(f"   {przedzial}: {pracownicy} osoba/y * {czas} min")
            
            elif wybor == "2":
                self.dodaj_metode_do_grupy(grupa)
            
            elif wybor == "3":
                self.usun_metode_z_grupy(grupa)
            
            elif wybor == "4":
                self.edytuj_metode_w_grupie(grupa)
            
            elif wybor == "5":
                break
    
    def dodaj_metode_do_grupy(self, grupa: Grupa):
        """Dodaje metodę do grupy"""
        print("\nDostępne metody zgrzewania:")
        metody_lista = [
            "HF Duży (ZEMAT)",
            "HF Mały (WOLDAN)",
            "Gorące Powietrze (MILLER)",
            "Gorące Powietrze (Ręcznie)",
            "Gorące Powietrze (Zgrzewarka jezdna)",
            "Gorące Powietrze (ASATECH)",
            "Gorący Klin (SEAMTEC)"
        ]
        
        for i, metoda_nazwa in enumerate(metody_lista, 1):
            print(f"{i}. {metoda_nazwa}")
        
        try:
            numer = int(input("\nWybierz numer metody do dodania: "))
            if 1 <= numer <= len(metody_lista):
                nazwa_metody = metody_lista[numer-1]
                
                # Sprawdź czy metoda już istnieje w grupie
                for metoda in grupa.metody:
                    if metoda.nazwa == nazwa_metody:
                        print("Ta metoda już istnieje w grupie!")
                        return
                
                nowa_metoda = MetodaZgrzewania(nazwa_metody)
                grupa.dodaj_metode(nowa_metoda)
                print(f"\nMetoda '{nazwa_metody}' została dodana do grupy!")
            else:
                print("Nieprawidłowy numer metody!")
        except ValueError:
            print("Nieprawidłowa wartość!")
    
    def usun_metode_z_grupy(self, grupa: Grupa):
        """Usuwa metodę z grupy"""
        if not grupa.metody:
            print("\nBrak metod w grupie!")
            return
        
        print(f"\nMetody w grupie '{grupa.nazwa}':")
        for i, metoda in enumerate(grupa.metody, 1):
            print(f"{i}. {metoda.nazwa}")
        
        try:
            numer = int(input("\nWybierz numer metody do usunięcia: "))
            if 1 <= numer <= len(grupa.metody):
                usunieta_metoda = grupa.metody[numer-1]
                grupa.usun_metode(numer-1)
                print(f"\nMetoda '{usunieta_metoda.nazwa}' została usunięta!")
            else:
                print("Nieprawidłowy numer metody!")
        except ValueError:
            print("Nieprawidłowa wartość!")
    
    def edytuj_metode_w_grupie(self, grupa: Grupa):
        """Edytuje metodę w grupie"""
        if not grupa.metody:
            print("\nBrak metod w grupie!")
            return
        
        print(f"\nMetody w grupie '{grupa.nazwa}':")
        for i, metoda in enumerate(grupa.metody, 1):
            print(f"{i}. {metoda.nazwa}")
        
        try:
            numer = int(input("\nWybierz numer metody do edycji: "))
            if 1 <= numer <= len(grupa.metody):
                metoda = grupa.metody[numer-1]
                self.edytuj_ustawienia_metody(metoda)
            else:
                print("Nieprawidłowy numer metody!")
        except ValueError:
            print("Nieprawidłowa wartość!")
    
    def edytuj_ustawienia_metody(self, metoda: MetodaZgrzewania):
        """Edytuje ustawienia czasowe metody"""
        while True:
            print(f"\n--- EDYCJA METODY: {metoda.nazwa} ---")
            print("Aktualne ustawienia:")
            
            for przedzial in self.przedzialy:
                pracownicy, czas = metoda.pobierz_czas(przedzial)
                print(f"   {przedzial}: {pracownicy} osoba/y * {czas} min")
            
            print("\n1. Edytuj czas dla przedziału")
            print("2. Wróć do poprzedniego menu")
            
            wybor = input("\nWybierz opcję (1-2): ")
            
            if wybor == "1":
                print("\nDostępne przedziały:")
                for i, przedzial in enumerate(self.przedzialy, 1):
                    print(f"{i}. {przedzial}")
                
                try:
                    numer_przedzialu = int(input("\nWybierz numer przedziału: "))
                    if 1 <= numer_przedzialu <= len(self.przedzialy):
                        przedzial = self.przedzialy[numer_przedzialu-1]
                        
                        aktualni_pracownicy, aktualny_czas = metoda.pobierz_czas(przedzial)
                        print(f"\nAktualne ustawienia dla '{przedzial}':")
                        print(f"Liczba pracowników: {aktualni_pracownicy}")
                        print(f"Czas na metr: {aktualny_czas} min")
                        
                        try:
                            nowi_pracownicy = int(input("\nPodaj nową liczbę pracowników: "))
                            nowy_czas = float(input("Podaj nowy czas na metr (w minutach): "))
                            
                            metoda.ustaw_czas(przedzial, nowi_pracownicy, nowy_czas)
                            print("\nUstawienia zostały zaktualizowane!")
                        except ValueError:
                            print("Nieprawidłowa wartość!")
                    else:
                        print("Nieprawidłowy numer przedziału!")
                except ValueError:
                    print("Nieprawidłowa wartość!")
            
            elif wybor == "2":
                break
    
    def oblicz_czas_produktu(self):
        """Główna funkcja obliczania czasu dla produktu"""
        print("\n--- OBLICZANIE CZASU ZGRZEWANIA DLA PRODUKTU ---")
        
        # 1. Wprowadzenie kodu produktu
        while True:
            kod = input("\nPodaj kod produktu (format: xxx-xxxx-xxx, same cyfry): ")
            if self.waliduj_kod(kod):
                break
            else:
                print("Nieprawidłowy format kodu! Wprowadź w formacie xxx-xxxx-xxx (same cyfry).")
        
        # 2. Wybór grupy
        if not self.grupy:
            print("\nBrak zdefiniowanych grup! Najpierw dodaj grupy.")
            return
        
        print("\nDostępne grupy:")
        for i, grupa in enumerate(self.grupy, 1):
            print(f"{i}. {grupa.nazwa}")
        
        try:
            numer_grupy = int(input("\nWybierz numer grupy: "))
            if 1 <= numer_grupy <= len(self.grupy):
                grupa = self.grupy[numer_grupy-1]
            else:
                print("Nieprawidłowy numer grupy!")
                return
        except ValueError:
            print("Nieprawidłowa wartość!")
            return
        
        # 3. Wybór przedziału wielkości
        print("\nDostępne przedziały wielkości:")
        for i, przedzial in enumerate(self.przedzialy, 1):
            print(f"{i}. {przedzial}")
        
        try:
            numer_przedzialu = int(input("\nWybierz numer przedziału: "))
            if 1 <= numer_przedzialu <= len(self.przedzialy):
                przedzial = self.przedzialy[numer_przedzialu-1]
            else:
                print("Nieprawidłowy numer przedziału!")
                return
        except ValueError:
            print("Nieprawidłowa wartość!")
            return
        
        # 4. Tworzenie obiektu produktu
        produkt = Produkt(kod, grupa, przedzial)
        
        # 5. Wprowadzenie ilości metrów dla każdej metody
        print(f"\nWprowadź ilość metrów zgrzewania dla każdej metody:")
        
        for metoda in grupa.metody:
            while True:
                try:
                    metry = float(input(f"{metoda.nazwa}: "))
                    if metry >= 0:
                        produkt.metry_zgrzewania[metoda.nazwa] = metry
                        break
                    else:
                        print("Wartość musi być nieujemna!")
                except ValueError:
                    print("Nieprawidłowa wartość! Wprowadź liczbę.")
        
        # 6. Opcjonalne wymuszenie liczby pracowników
        print("\n--- WYMUSZENIE LICZBY PRACOWNIKÓW (opcjonalne) ---")
        print("Możesz wymusić liczbę pracowników dla każdej metody.")
        print("Jeśli nie chcesz wymuszać, naciśnij Enter.")
        
        for metoda in grupa.metody:
            odpowiedz = input(f"\nCzy wymusić liczbę pracowników dla '{metoda.nazwa}'? (T/N): ")
            if odpowiedz.upper() == 'T':
                while True:
                    try:
                        pracownicy = int(input(f"Podaj liczbę pracowników dla '{metoda.nazwa}': "))
                        if pracownicy > 0:
                            produkt.wymuszeni_pracownicy[metoda.nazwa] = pracownicy
                            break
                        else:
                            print("Liczba pracowników musi być większa od 0!")
                    except ValueError:
                        print("Nieprawidłowa wartość! Wprowadź liczbę całkowitą.")
        
        # 7. Obliczenia
        produkt.oblicz_czasy()
        czas_calkowity = produkt.oblicz_calkowity_czas()
        
        # 8. Wyświetlenie wyników
        print("\n" + "="*60)
        print("WYNIKI OBLICZEŃ")
        print("="*60)
        print(f"Kod produktu: {produkt.kod}")
        print(f"Grupa: {produkt.grupa.nazwa}")
        print(f"Przedział wielkości: {produkt.przedzial}")
        print("\nSzczegółowe obliczenia:")
        print("-"*60)
        
        for nazwa_metody, wynik in produkt.wyniki.items():
            print(f"\n{wynik['metry']} m²")
            print(f"{nazwa_metody}:")
            print(f"  Czas na metr: {wynik['czas_na_metr']} min")
            print(f"  Liczba pracowników: {wynik['pracownicy']} {'(wymuszeni)' if wynik['czy_wymuszeni'] else ''}")
            print(f"  Czas całkowity: {wynik['czas_calkowity']:.2f} min")
        
        print("\n" + "-"*60)
        print(f"CAŁKOWITY CZAS ZGRZEWANIA: {czas_calkowity:.2f} min")
        
        # 9. Walidacja z czasem produkcji
        print("\n--- WALIDACJA Z CZASEM PRODUKCJI (opcjonalne) ---")
        odpowiedz = input("Czy chcesz wprowadzić czas z produkcji dla walidacji? (T/N): ")
        
        if odpowiedz.upper() == 'T':
            while True:
                try:
                    czas_produkcji = float(input("Podaj czas z produkcji (w minutach): "))
                    if czas_produkcji >= 0:
                        produkt.czas_produkcji = czas_produkcji
                        break
                    else:
                        print("Czas musi być nieujemny!")
                except ValueError:
                    print("Nieprawidłowa wartość! Wprowadź liczbę.")
            
            odchylenie = produkt.oblicz_odchylenie()
            if odchylenie is not None:
                print("\n" + "="*60)
                print("WYNIK WALIDACJI")
                print("="*60)
                print(f"Czas obliczony: {czas_calkowity:.2f} min")
                print(f"Czas z produkcji: {produkt.czas_produkcji:.2f} min")
                print(f"Odchylenie: {odchylenie:+.2f}%")
                
                if abs(odchylenie) <= 10:
                    print("Status: W normie (odchylenie ≤ 10%)")
                elif abs(odchylenie) <= 20:
                    print("Status: Dopuszczalne (odchylenie ≤ 20%)")
                else:
                    print("Status: Poza normą (odchylenie > 20%)")
        
        print("\nNaciśnij Enter, aby kontynuować...")
        input()
    
    def waliduj_kod(self, kod: str) -> bool:
        """Waliduje format kodu produktu"""
        pattern = r'^\d{3}-\d{4}-\d{3}$'
        return re.match(pattern, kod) is not None
    
    def uruchom(self):
        """Główna pętla programu"""
        while True:
            self.pokaz_menu()
            
            wybor = input("\nWybierz opcję (1-5): ")
            
            if wybor == "1":
                self.zarzadzaj_grupami()
            elif wybor == "2":
                self.oblicz_czas_produktu()
            elif wybor == "3":
                self.pokaz_grupy()
            elif wybor == "4":
                self.zapisz_dane()
                print("\nDane zostały zapisane!")
            elif wybor == "5":
                self.zapisz_dane()
                print("\nDane zapisane. Do widzenia!")
                break
            else:
                print("Nieprawidłowy wybór!")


def main():
    """Funkcja główna programu"""
    program = ProgramZgrzewania()
    program.uruchom()


if __name__ == "__main__":
    main()