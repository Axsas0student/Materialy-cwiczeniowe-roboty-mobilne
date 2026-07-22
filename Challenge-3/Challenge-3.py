import event
import time
import cyberpi
import mbot2
import mbuild


ETAP_ODCZYT_ZLECENIA = 0
ETAP_DO_ZAOPATRZENIA = 1
ETAP_POSZUKIWANIE = 2
ETAP_KORYTARZE = 3
ETAP_STREFA_CIEMNA = 4
ETAP_DO_STREFY_BEZPIECZNEJ = 5
ETAP_POWROT = 6
ETAP_ZAKONCZONY = 7

POD_DO_WEJSCIA_SEKTORA = 0
POD_W_SEKTORZE = 1
POD_POWROT_Z_PUSTEGO_SEKTORA = 2
POD_POWROT_Z_ODNALEZIONA_OSOBA = 3

POD_DO_SKRZYZOWANIA_STREF = 0
POD_DO_WLASCIWEJ_STREFY = 1

OSOBA_BRAK = 0
OSOBA_R = 1
OSOBA_B = 2

STREFA_BRAK = 0
STREFA_Z1 = 1
STREFA_Z2 = 2

KOLOR_CZERWONY = "red"
KOLOR_NIEBIESKI = "blue"
KOLOR_ZIELONY = "green"
KOLOR_FIOLETOWY = "purple"
KOLOR_ZOLTY = "yellow"
KOLOR_TURKUSOWY = "cyan"

LED_CZERWONY = (250, 2, 32)
LED_NIEBIESKI = (15, 1, 208)
LED_ZIELONY = (1, 208, 19)
LED_FIOLETOWY = (135, 15, 220)
LED_OSTRZEGAWCZY = (210, 0, 0)
LED_TURKUSOWY = (0, 180, 180)

LIMIT_CZASU_S = 300

PREDKOSC_STANDARDOWA = 32
PREDKOSC_OGRANICZONA = 18
KP = 0.45

ODL_DO_DRUGIEGO_ZNACZNIKA_CM = 12
ODL_OPUSZCZENIA_ZLECENIA_CM = 12
ODL_WJAZDU_DO_ZAOPATRZENIA_CM = 10
ODL_OPUSZCZENIA_ZAOPATRZENIA_CM = 12
ODL_DO_SRODKA_SKRZYZOWANIA_CM = 6
ODL_OPUSZCZENIA_SKRZYZOWANIA_CM = 8
ODL_WJAZDU_PRZY_OSOBIE_CM = 10
ODL_OPUSZCZENIA_ZNACZNIKA_OSOBY_CM = 8
ODL_OPUSZCZENIA_KONCA_SEKTORA_CM = 8
ODL_PRZEJAZDU_PRZEZ_POMINIETE_WEJSCIE_CM = 12
ODL_WJAZDU_DO_KORYTARZA_CM = 8
ODL_WJAZDU_DO_STREFY_BEZPIECZNEJ_CM = 10
ODL_WJAZDU_NA_TRASE_POWROTNA_CM = 10
ODL_OPUSZCZENIA_PUNKTU_KONTROLNEGO_CM = 8
ODL_WJAZDU_DO_BAZY_CM = 10

PROG_ZABLOKOWANEGO_KORYTARZA_CM = 45
PROG_AWARYJNEGO_STOPU_CM = 12
LICZBA_PROBEK_ODLEGLOSCI = 5

PROG_WEJSCIA_W_CIEMNOSC = 20
PROG_WYJSCIA_Z_CIEMNOSCI = 30
WYMAGANE_POMIARY_SWIATLA = 3

MAKS_CZAS_BEZ_LINII_S = 0.8
OPOZNIENIE_PETLI_S = 0.01

ORANGE_R_MIN = 110
ORANGE_G_MIN = 35
ORANGE_G_MAX = 190
ORANGE_B_MAX = 110
ORANGE_R_DO_G_MIN = 1.15
ORANGE_G_DO_B_MIN = 1.20


poszukiwana_osoba = OSOBA_BRAK
strefa_bezpieczna = STREFA_BRAK
etap = ETAP_ODCZYT_ZLECENIA
podetap_poszukiwania = POD_DO_WEJSCIA_SEKTORA
podetap_strefy = POD_DO_SKRZYZOWANIA_STREF

aktualny_sektor = 1
sektor_odnalezienia = 0
odwiedzono_s1 = False
odwiedzono_s2 = False
odwiedzono_s3 = False
osoba_odnaleziona = False
pakiet_pobrany = False

pozostale_wejscia_do_pominiecia = 0
wybrany_korytarz = 0
punkt_kontrolny_zaliczony = False
liczba_wykonanych_etapow = 0

predkosc_biezaca = PREDKOSC_STANDARDOWA
odchylenie = 0
korekta = 0

licznik_ciemnych_pomiarow = 0
licznik_jasnych_pomiarow = 0
czas_bez_linii = 0.0

blokada_zoltego_znacznika = False
blokada_turkusowego_znacznika = False
program_zatrzymany = False
misja_udana = False


def ustaw_diody(kolor):
    cyberpi.led.on(kolor[0], kolor[1], kolor[2], "all")


def ogranicz_wartosc(wartosc, minimum, maksimum):
    if wartosc < minimum:
        return minimum
    if wartosc > maksimum:
        return maksimum
    return wartosc


def wykryto_kolor(kolor):
    return mbuild.quad_rgb_sensor.is_color(kolor, "any", 1)


def wykryto_kolor_stabilnie(kolor, wymagane_trafienia=2, liczba_prob=3):
    if not wykryto_kolor(kolor):
        return False
    trafienia = 1
    for _ in range(liczba_prob - 1):
        time.sleep(0.03)
        if wykryto_kolor(kolor):
            trafienia += 1
    return trafienia >= wymagane_trafienia


def odczytaj_rgb(kanal):
    r = mbuild.quad_rgb_sensor.get_red(kanal, 1)
    g = mbuild.quad_rgb_sensor.get_green(kanal, 1)
    b = mbuild.quad_rgb_sensor.get_blue(kanal, 1)
    return r, g, b


def kanal_widzi_pomaranczowy(kanal):
    r, g, b = odczytaj_rgb(kanal)
    if r < ORANGE_R_MIN:
        return False
    if g < ORANGE_G_MIN or g > ORANGE_G_MAX:
        return False
    if b > ORANGE_B_MAX:
        return False
    if g <= 0:
        return False
    if r < g * ORANGE_R_DO_G_MIN:
        return False
    if g < b * ORANGE_G_DO_B_MIN:
        return False
    return True


def wykryto_pomaranczowy():
    return kanal_widzi_pomaranczowy("L1") or kanal_widzi_pomaranczowy("R1")


def wykryto_pomaranczowy_stabilnie():
    if not wykryto_pomaranczowy():
        return False
    trafienia = 1
    for _ in range(2):
        time.sleep(0.03)
        if wykryto_pomaranczowy():
            trafienia += 1
    return trafienia >= 2


def zmierz_odleglosc_mediana():
    pomiary = []
    for _ in range(LICZBA_PROBEK_ODLEGLOSCI):
        try:
            wartosc = mbuild.ultrasonic2.get(1)
        except Exception:
            wartosc = 0
        pomiary.append(wartosc)
        time.sleep(0.04)
    pomiary.sort()
    return pomiary[len(pomiary) // 2]


def odczytaj_jasnosc():
    try:
        return cyberpi.get_bri()
    except Exception:
        return None


def diagnostyka_czujnikow():
    cyberpi.console.print("Swiatlo: " + str(odczytaj_jasnosc()))
    cyberpi.console.print("L1 RGB: " + str(odczytaj_rgb("L1")))
    cyberpi.console.print("R1 RGB: " + str(odczytaj_rgb("R1")))
    cyberpi.console.print("Odleglosc: " + str(zmierz_odleglosc_mediana()))


def limit_czasu_przekroczony():
    return cyberpi.timer.get() > LIMIT_CZASU_S


def blad_misji(komunikat):
    global etap, program_zatrzymany, misja_udana
    mbot2.EM_stop("ALL")
    ustaw_diody(LED_OSTRZEGAWCZY)
    cyberpi.console.print(komunikat)
    etap = ETAP_ZAKONCZONY
    program_zatrzymany = True
    misja_udana = False


def przekroczono_czas():
    blad_misji("Przekroczono czas")


def ustaw_led_osoby():
    if poszukiwana_osoba == OSOBA_R:
        ustaw_diody(LED_CZERWONY)
    elif poszukiwana_osoba == OSOBA_B:
        ustaw_diody(LED_NIEBIESKI)


def ustaw_led_strefy():
    if strefa_bezpieczna == STREFA_Z1:
        ustaw_diody(LED_ZIELONY)
    elif strefa_bezpieczna == STREFA_Z2:
        ustaw_diody(LED_FIOLETOWY)


def krok_jazdy_po_linii():
    global odchylenie, korekta
    odchylenie = mbuild.quad_rgb_sensor.get_offset_track(1)
    korekta = odchylenie * KP
    lewa_moc = -1 * (predkosc_biezaca + korekta)
    prawa_moc = predkosc_biezaca - korekta
    lewa_moc = ogranicz_wartosc(lewa_moc, -100, 100)
    prawa_moc = ogranicz_wartosc(prawa_moc, -100, 100)
    mbot2.drive_power(lewa_moc, prawa_moc)


def czy_na_znaczniku():
    if wykryto_kolor(KOLOR_CZERWONY):
        return True
    if wykryto_kolor(KOLOR_NIEBIESKI):
        return True
    if wykryto_kolor(KOLOR_ZIELONY):
        return True
    if wykryto_kolor(KOLOR_FIOLETOWY):
        return True
    if wykryto_kolor(KOLOR_ZOLTY):
        return True
    if wykryto_kolor(KOLOR_TURKUSOWY):
        return True
    if wykryto_pomaranczowy():
        return True
    return False


def kontroluj_linie():
    global czas_bez_linii
    if mbuild.quad_rgb_sensor.is_line("any", 1) or czy_na_znaczniku():
        czas_bez_linii = 0.0
        return True
    czas_bez_linii += OPOZNIENIE_PETLI_S
    if czas_bez_linii >= MAKS_CZAS_BEZ_LINII_S:
        blad_misji("Utrata linii")
        return False
    return True


def odczytaj_zlecenie():
    global poszukiwana_osoba, strefa_bezpieczna
    poszukiwana_osoba = OSOBA_BRAK
    strefa_bezpieczna = STREFA_BRAK

    if wykryto_kolor_stabilnie(KOLOR_CZERWONY):
        poszukiwana_osoba = OSOBA_R
    elif wykryto_kolor_stabilnie(KOLOR_NIEBIESKI):
        poszukiwana_osoba = OSOBA_B
    else:
        blad_misji("Bledne zlecenie: osoba")
        return False

    mbot2.straight(ODL_DO_DRUGIEGO_ZNACZNIKA_CM)
    time.sleep(0.2)

    if wykryto_kolor_stabilnie(KOLOR_ZIELONY):
        strefa_bezpieczna = STREFA_Z1
    elif wykryto_kolor_stabilnie(KOLOR_FIOLETOWY):
        strefa_bezpieczna = STREFA_Z2
    else:
        blad_misji("Bledne zlecenie: strefa")
        return False

    if poszukiwana_osoba == OSOBA_R:
        osoba_tekst = "R"
    else:
        osoba_tekst = "B"

    if strefa_bezpieczna == STREFA_Z1:
        strefa_tekst = "Z1"
    else:
        strefa_tekst = "Z2"

    cyberpi.console.print("Osoba: " + osoba_tekst)
    cyberpi.console.print("Strefa: " + strefa_tekst)
    ustaw_led_osoby()
    time.sleep(1)
    mbot2.straight(ODL_OPUSZCZENIA_ZLECENIA_CM)
    return True


def pobierz_pakiet():
    global pakiet_pobrany, liczba_wykonanych_etapow, etap
    mbot2.straight(ODL_WJAZDU_DO_ZAOPATRZENIA_CM)
    mbot2.EM_stop("ALL")
    ustaw_diody(LED_ZIELONY)
    cyberpi.console.print("Pakiet pobrany")
    time.sleep(2)

    if limit_czasu_przekroczony():
        przekroczono_czas()
        return

    pakiet_pobrany = True
    liczba_wykonanych_etapow += 1
    mbot2.straight(ODL_OPUSZCZENIA_ZAOPATRZENIA_CM)
    ustaw_led_osoby()
    cyberpi.console.print("Rozpoczynam poszukiwania")
    etap = ETAP_POSZUKIWANIE


def sektor_odwiedzony(numer):
    if numer == 1:
        return odwiedzono_s1
    if numer == 2:
        return odwiedzono_s2
    if numer == 3:
        return odwiedzono_s3
    return True


def oznacz_sektor_odwiedzony(numer):
    global odwiedzono_s1, odwiedzono_s2, odwiedzono_s3
    if numer == 1:
        odwiedzono_s1 = True
    elif numer == 2:
        odwiedzono_s2 = True
    elif numer == 3:
        odwiedzono_s3 = True


def wjedz_do_sektora():
    global podetap_poszukiwania, blokada_zoltego_znacznika
    if aktualny_sektor < 1 or aktualny_sektor > 3:
        blad_misji("Nieprawidlowy numer sektora")
        return
    if sektor_odwiedzony(aktualny_sektor):
        blad_misji("Ponowny wjazd do sektora")
        return

    mbot2.EM_stop("ALL")
    mbot2.straight(ODL_DO_SRODKA_SKRZYZOWANIA_CM)
    mbot2.turn(90)
    mbot2.straight(ODL_OPUSZCZENIA_SKRZYZOWANIA_CM)
    cyberpi.console.print("Sektor S" + str(aktualny_sektor))
    podetap_poszukiwania = POD_W_SEKTORZE
    blokada_zoltego_znacznika = True


def wykryto_wlasciwa_osobe():
    if poszukiwana_osoba == OSOBA_R:
        return wykryto_kolor_stabilnie(KOLOR_CZERWONY)
    return wykryto_kolor_stabilnie(KOLOR_NIEBIESKI)


def potwierdz_odnalezienie():
    global osoba_odnaleziona, sektor_odnalezienia
    global liczba_wykonanych_etapow, podetap_poszukiwania

    if not pakiet_pobrany:
        blad_misji("Brak pakietu medycznego")
        return

    mbot2.straight(ODL_WJAZDU_PRZY_OSOBIE_CM)
    mbot2.EM_stop("ALL")
    ustaw_diody(LED_ZIELONY)
    cyberpi.console.print("Osoba odnaleziona")
    cyberpi.console.print("Sektor S" + str(aktualny_sektor))
    time.sleep(3)

    if limit_czasu_przekroczony():
        przekroczono_czas()
        return

    osoba_odnaleziona = True
    sektor_odnalezienia = aktualny_sektor
    oznacz_sektor_odwiedzony(aktualny_sektor)
    liczba_wykonanych_etapow += 1

    mbot2.turn(180)
    mbot2.straight(ODL_OPUSZCZENIA_ZNACZNIKA_OSOBY_CM)
    ustaw_led_strefy()
    podetap_poszukiwania = POD_POWROT_Z_ODNALEZIONA_OSOBA


def zakoncz_sprawdzanie_sektora():
    global podetap_poszukiwania
    oznacz_sektor_odwiedzony(aktualny_sektor)
    mbot2.EM_stop("ALL")
    mbot2.turn(180)
    mbot2.straight(ODL_OPUSZCZENIA_KONCA_SEKTORA_CM)
    podetap_poszukiwania = POD_POWROT_Z_PUSTEGO_SEKTORA


def opusc_sektor():
    global aktualny_sektor, podetap_poszukiwania, etap
    global pozostale_wejscia_do_pominiecia, blokada_zoltego_znacznika

    mbot2.EM_stop("ALL")
    mbot2.straight(ODL_DO_SRODKA_SKRZYZOWANIA_CM)
    mbot2.turn(90)
    mbot2.straight(ODL_OPUSZCZENIA_SKRZYZOWANIA_CM)
    blokada_zoltego_znacznika = True

    if podetap_poszukiwania == POD_POWROT_Z_PUSTEGO_SEKTORA:
        if aktualny_sektor >= 3:
            blad_misji("Nie znaleziono osoby")
            return
        aktualny_sektor += 1
        podetap_poszukiwania = POD_DO_WEJSCIA_SEKTORA
        ustaw_led_osoby()
        return

    if podetap_poszukiwania == POD_POWROT_Z_ODNALEZIONA_OSOBA:
        pozostale_wejscia_do_pominiecia = 3 - sektor_odnalezienia
        etap = ETAP_KORYTARZE
        ustaw_led_strefy()
        cyberpi.console.print("Droga ewakuacji")
        return

    blad_misji("Blad opuszczania sektora")


def pomin_wejscie_sektora():
    global pozostale_wejscia_do_pominiecia, blokada_zoltego_znacznika
    mbot2.EM_stop("ALL")
    mbot2.straight(ODL_PRZEJAZDU_PRZEZ_POMINIETE_WEJSCIE_CM)
    pozostale_wejscia_do_pominiecia -= 1
    blokada_zoltego_znacznika = True


def korytarz_jest_przejezdny():
    time.sleep(0.25)
    odleglosc = zmierz_odleglosc_mediana()
    cyberpi.console.print("Odleglosc: " + str(odleglosc))
    return odleglosc > PROG_ZABLOKOWANEGO_KORYTARZA_CM


def wybierz_korytarz():
    global wybrany_korytarz, blokada_zoltego_znacznika

    if not osoba_odnaleziona or not pakiet_pobrany:
        blad_misji("Brak warunkow ewakuacji")
        return

    mbot2.EM_stop("ALL")
    mbot2.straight(ODL_DO_SRODKA_SKRZYZOWANIA_CM)

    mbot2.turn(-90)
    cyberpi.console.print("Sprawdzam K1")
    if korytarz_jest_przejezdny():
        wybrany_korytarz = 1
        cyberpi.console.print("Wybrano K1")
        mbot2.straight(ODL_WJAZDU_DO_KORYTARZA_CM)
        blokada_zoltego_znacznika = True
        return

    ustaw_diody(LED_OSTRZEGAWCZY)
    cyberpi.console.print("K1 zablokowany")
    mbot2.turn(180)
    cyberpi.console.print("Sprawdzam K2")

    if korytarz_jest_przejezdny():
        wybrany_korytarz = 2
        cyberpi.console.print("Wybrano K2")
        ustaw_led_strefy()
        mbot2.straight(ODL_WJAZDU_DO_KORYTARZA_CM)
        blokada_zoltego_znacznika = True
        return

    cyberpi.console.print("K2 zablokowany")
    blad_misji("Brak drogi ewakuacji")


def kontroluj_przeszkode():
    try:
        odleglosc = mbuild.ultrasonic2.get(1)
    except Exception:
        odleglosc = 0
    if odleglosc > 0 and odleglosc < PROG_AWARYJNEGO_STOPU_CM:
        blad_misji("Przeszkoda na trasie")
        return False
    return True


def rozpocznij_strefe_ciemna():
    global etap, predkosc_biezaca
    global licznik_ciemnych_pomiarow, licznik_jasnych_pomiarow
    etap = ETAP_STREFA_CIEMNA
    predkosc_biezaca = PREDKOSC_OGRANICZONA
    licznik_ciemnych_pomiarow = 0
    licznik_jasnych_pomiarow = 0
    ustaw_diody(LED_OSTRZEGAWCZY)
    cyberpi.console.print("Strefa zagrozenia")


def zakoncz_strefe_ciemna():
    global etap, predkosc_biezaca, podetap_strefy
    global licznik_ciemnych_pomiarow, licznik_jasnych_pomiarow
    etap = ETAP_DO_STREFY_BEZPIECZNEJ
    podetap_strefy = POD_DO_SKRZYZOWANIA_STREF
    predkosc_biezaca = PREDKOSC_STANDARDOWA
    licznik_ciemnych_pomiarow = 0
    licznik_jasnych_pomiarow = 0
    ustaw_led_strefy()
    cyberpi.console.print("Strefa bezpieczna")


def aktualizuj_strefe_swiatla():
    global licznik_ciemnych_pomiarow, licznik_jasnych_pomiarow

    jasnosc = odczytaj_jasnosc()
    if jasnosc is None:
        blad_misji("Blad czujnika swiatla")
        return True

    if etap == ETAP_KORYTARZE and wybrany_korytarz != 0:
        if jasnosc < PROG_WEJSCIA_W_CIEMNOSC:
            licznik_ciemnych_pomiarow += 1
        else:
            licznik_ciemnych_pomiarow = 0

        if licznik_ciemnych_pomiarow >= WYMAGANE_POMIARY_SWIATLA:
            rozpocznij_strefe_ciemna()
            return True

    elif etap == ETAP_STREFA_CIEMNA:
        if jasnosc > PROG_WYJSCIA_Z_CIEMNOSCI:
            licznik_jasnych_pomiarow += 1
        else:
            licznik_jasnych_pomiarow = 0

        if licznik_jasnych_pomiarow >= WYMAGANE_POMIARY_SWIATLA:
            zakoncz_strefe_ciemna()
            return True

    return False


def wybierz_strefe_bezpieczna():
    global podetap_strefy, blokada_zoltego_znacznika

    if not osoba_odnaleziona or not pakiet_pobrany:
        blad_misji("Nie mozna zakonczyc ewakuacji")
        return

    mbot2.EM_stop("ALL")
    mbot2.straight(ODL_DO_SRODKA_SKRZYZOWANIA_CM)

    if strefa_bezpieczna == STREFA_Z1:
        mbot2.turn(-90)
    else:
        mbot2.turn(90)

    mbot2.straight(ODL_OPUSZCZENIA_SKRZYZOWANIA_CM)
    podetap_strefy = POD_DO_WLASCIWEJ_STREFY
    blokada_zoltego_znacznika = True


def wykryto_wlasciwa_strefe():
    if strefa_bezpieczna == STREFA_Z1:
        return wykryto_kolor_stabilnie(KOLOR_ZIELONY)
    return wykryto_kolor_stabilnie(KOLOR_FIOLETOWY)


def wykryto_niewlasciwa_strefe():
    if strefa_bezpieczna == STREFA_Z1:
        return wykryto_kolor_stabilnie(KOLOR_FIOLETOWY)
    return wykryto_kolor_stabilnie(KOLOR_ZIELONY)


def potwierdz_ewakuacje():
    global etap, liczba_wykonanych_etapow, punkt_kontrolny_zaliczony

    if not osoba_odnaleziona or not pakiet_pobrany:
        blad_misji("Niepelna misja ratunkowa")
        return

    mbot2.straight(ODL_WJAZDU_DO_STREFY_BEZPIECZNEJ_CM)
    mbot2.EM_stop("ALL")
    ustaw_diody(LED_ZIELONY)
    cyberpi.console.print("Ewakuacja zakonczona")
    time.sleep(3)

    if limit_czasu_przekroczony():
        przekroczono_czas()
        return

    liczba_wykonanych_etapow += 1
    punkt_kontrolny_zaliczony = False
    mbot2.straight(ODL_WJAZDU_NA_TRASE_POWROTNA_CM)
    ustaw_diody(LED_TURKUSOWY)
    cyberpi.console.print("Powrot zewnetrzna trasa")
    etap = ETAP_POWROT


def zalicz_punkt_kontrolny():
    global punkt_kontrolny_zaliczony, blokada_turkusowego_znacznika
    punkt_kontrolny_zaliczony = True
    cyberpi.console.print("Punkt kontrolny zaliczony")
    mbot2.straight(ODL_OPUSZCZENIA_PUNKTU_KONTROLNEGO_CM)
    blokada_turkusowego_znacznika = True


def zakoncz_misje():
    global etap, program_zatrzymany, misja_udana

    mbot2.straight(ODL_WJAZDU_DO_BAZY_CM)
    mbot2.EM_stop("ALL")

    if limit_czasu_przekroczony():
        przekroczono_czas()
        return
    if not pakiet_pobrany:
        blad_misji("Nie pobrano pakietu")
        return
    if not osoba_odnaleziona:
        blad_misji("Nie odnaleziono osoby")
        return
    if not punkt_kontrolny_zaliczony:
        blad_misji("Pominieto punkt kontrolny")
        return
    if liczba_wykonanych_etapow != 3:
        blad_misji("Nie wykonano wszystkich etapow")
        return

    ustaw_diody(LED_ZIELONY)
    cyberpi.console.print("Misja zakonczona")
    cyberpi.console.print("Sektor: S" + str(sektor_odnalezienia))
    cyberpi.console.print("Korytarz: K" + str(wybrany_korytarz))
    cyberpi.console.print("Czas: " + str(cyberpi.timer.get()) + " s")
    etap = ETAP_ZAKONCZONY
    program_zatrzymany = True
    misja_udana = True


def obsluz_zolty_znacznik():
    if etap == ETAP_POSZUKIWANIE:
        if podetap_poszukiwania == POD_DO_WEJSCIA_SEKTORA:
            wjedz_do_sektora()
            return
        if podetap_poszukiwania == POD_POWROT_Z_PUSTEGO_SEKTORA:
            opusc_sektor()
            return
        if podetap_poszukiwania == POD_POWROT_Z_ODNALEZIONA_OSOBA:
            opusc_sektor()
            return
        blad_misji("Nieoczekiwany znacznik sektora")
        return

    if etap == ETAP_KORYTARZE:
        if pozostale_wejscia_do_pominiecia > 0:
            pomin_wejscie_sektora()
            return
        if wybrany_korytarz == 0:
            wybierz_korytarz()
            return
        blad_misji("Nieoczekiwane skrzyzowanie")
        return

    if etap == ETAP_STREFA_CIEMNA:
        blad_misji("Nie opuszczono ciemnej strefy")
        return

    if etap == ETAP_DO_STREFY_BEZPIECZNEJ:
        if podetap_strefy == POD_DO_SKRZYZOWANIA_STREF:
            wybierz_strefe_bezpieczna()
            return
        blad_misji("Nieoczekiwane skrzyzowanie stref")
        return

    blad_misji("Nieoczekiwany zolty znacznik")


@event.start
def on_start():
    global poszukiwana_osoba, strefa_bezpieczna, etap
    global podetap_poszukiwania, podetap_strefy, aktualny_sektor
    global sektor_odnalezienia, odwiedzono_s1, odwiedzono_s2, odwiedzono_s3
    global osoba_odnaleziona, pakiet_pobrany
    global pozostale_wejscia_do_pominiecia, wybrany_korytarz
    global punkt_kontrolny_zaliczony, liczba_wykonanych_etapow
    global predkosc_biezaca, licznik_ciemnych_pomiarow, licznik_jasnych_pomiarow
    global czas_bez_linii, blokada_zoltego_znacznika
    global blokada_turkusowego_znacznika, program_zatrzymany, misja_udana

    mbot2.EM_stop("ALL")
    cyberpi.led.off("all")
    cyberpi.console.print("Nacisnij A, aby rozpoczac")

    poszukiwana_osoba = OSOBA_BRAK
    strefa_bezpieczna = STREFA_BRAK
    etap = ETAP_ODCZYT_ZLECENIA
    podetap_poszukiwania = POD_DO_WEJSCIA_SEKTORA
    podetap_strefy = POD_DO_SKRZYZOWANIA_STREF
    aktualny_sektor = 1
    sektor_odnalezienia = 0
    odwiedzono_s1 = False
    odwiedzono_s2 = False
    odwiedzono_s3 = False
    osoba_odnaleziona = False
    pakiet_pobrany = False
    pozostale_wejscia_do_pominiecia = 0
    wybrany_korytarz = 0
    punkt_kontrolny_zaliczony = False
    liczba_wykonanych_etapow = 0
    predkosc_biezaca = PREDKOSC_STANDARDOWA
    licznik_ciemnych_pomiarow = 0
    licznik_jasnych_pomiarow = 0
    czas_bez_linii = 0.0
    blokada_zoltego_znacznika = False
    blokada_turkusowego_znacznika = False
    program_zatrzymany = False
    misja_udana = False

    while not cyberpi.controller.is_press("a"):
        if cyberpi.controller.is_press("b"):
            diagnostyka_czujnikow()
            time.sleep(0.5)
        time.sleep(0.01)

    cyberpi.timer.reset()

    if not odczytaj_zlecenie():
        return

    etap = ETAP_DO_ZAOPATRZENIA

    while etap != ETAP_ZAKONCZONY and not program_zatrzymany:
        if limit_czasu_przekroczony():
            przekroczono_czas()
            break

        if etap == ETAP_KORYTARZE and wybrany_korytarz != 0:
            if not kontroluj_przeszkode():
                break
            if aktualizuj_strefe_swiatla():
                if program_zatrzymany:
                    break
                czas_bez_linii = 0.0
                time.sleep(OPOZNIENIE_PETLI_S)
                continue

        elif etap == ETAP_STREFA_CIEMNA:
            if not kontroluj_przeszkode():
                break
            if aktualizuj_strefe_swiatla():
                if program_zatrzymany:
                    break
                czas_bez_linii = 0.0
                time.sleep(OPOZNIENIE_PETLI_S)
                continue

        zolty = wykryto_kolor(KOLOR_ZOLTY)
        if zolty and not blokada_zoltego_znacznika:
            obsluz_zolty_znacznik()
            if program_zatrzymany:
                break
            czas_bez_linii = 0.0
            time.sleep(OPOZNIENIE_PETLI_S)
            continue
        if not zolty:
            blokada_zoltego_znacznika = False

        turkusowy = wykryto_kolor(KOLOR_TURKUSOWY)
        if not turkusowy:
            blokada_turkusowego_znacznika = False

        if etap == ETAP_DO_ZAOPATRZENIA:
            if turkusowy:
                pobierz_pakiet()
                if program_zatrzymany:
                    break
                czas_bez_linii = 0.0
                time.sleep(OPOZNIENIE_PETLI_S)
                continue

        elif etap == ETAP_POSZUKIWANIE:
            if podetap_poszukiwania == POD_W_SEKTORZE:
                if wykryto_wlasciwa_osobe():
                    potwierdz_odnalezienie()
                    if program_zatrzymany:
                        break
                    czas_bez_linii = 0.0
                    time.sleep(OPOZNIENIE_PETLI_S)
                    continue
                if wykryto_pomaranczowy_stabilnie():
                    zakoncz_sprawdzanie_sektora()
                    if program_zatrzymany:
                        break
                    czas_bez_linii = 0.0
                    time.sleep(OPOZNIENIE_PETLI_S)
                    continue

        elif etap == ETAP_DO_STREFY_BEZPIECZNEJ:
            if podetap_strefy == POD_DO_WLASCIWEJ_STREFY:
                if wykryto_niewlasciwa_strefe():
                    blad_misji("Niewlasciwa strefa bezpieczna")
                    break
                if wykryto_wlasciwa_strefe():
                    potwierdz_ewakuacje()
                    if program_zatrzymany:
                        break
                    czas_bez_linii = 0.0
                    time.sleep(OPOZNIENIE_PETLI_S)
                    continue

        elif etap == ETAP_POWROT:
            if turkusowy and not blokada_turkusowego_znacznika:
                zalicz_punkt_kontrolny()
                czas_bez_linii = 0.0
                time.sleep(OPOZNIENIE_PETLI_S)
                continue
            if wykryto_pomaranczowy_stabilnie():
                zakoncz_misje()
                break

        if not kontroluj_linie():
            break

        if etap != ETAP_ZAKONCZONY and not program_zatrzymany:
            krok_jazdy_po_linii()

        time.sleep(OPOZNIENIE_PETLI_S)
