import event
import time
import cyberpi
import mbot2
import mbuild


ETAP_ODCZYT_ZLECENIA = 0
ETAP_DO_POBRANIA = 1
ETAP_DO_DOSTAWY = 2
ETAP_POWROT_DO_BAZY = 3
ETAP_ZAKONCZONY = 4


POD_POWROT_DO_PIERWSZEGO_SKRZYZOWANIA = 0
POD_DO_ROZWIDLENIA_KORYTARZY = 1
POD_W_KORYTARZU = 2
POD_STREFA_OGRANICZONEJ_PREDKOSCI = 3
POD_DO_SKRZYZOWANIA_DOSTAWY = 4
POD_DO_STREFY_DOSTAWY = 5


STACJA_BRAK = 0
STACJA_A = 1
STACJA_B = 2


DOSTAWA_BRAK = 0
DOSTAWA_C = 1
DOSTAWA_D = 2


KOLOR_CZERWONY_CZUJNIK = "red"
KOLOR_NIEBIESKI_CZUJNIK = "blue"
KOLOR_ZIELONY_CZUJNIK = "green"
KOLOR_FIOLETOWY_CZUJNIK = "purple"
KOLOR_ZOLTY_CZUJNIK = "yellow"
KOLOR_TURKUSOWY_CZUJNIK = "cyan"


LED_CZERWONY = (250, 2, 32)
LED_NIEBIESKI = (15, 1, 208)
LED_ZIELONY = (1, 208, 19)
LED_FIOLETOWY = (135, 15, 220)
LED_OSTRZEGAWCZY = (210, 0, 0)
LED_TURKUSOWY = (0, 180, 180)

LIMIT_CZASU_S = 240


PREDKOSC_STANDARDOWA = 32
PREDKOSC_OGRANICZONA = 18


KP = 0.45


ODL_DO_DRUGIEGO_ZNACZNIKA_ZLECENIA_CM = 12
ODL_OPUSZCZENIA_PASA_ZLECENIA_CM = 12
ODL_DO_SRODKA_SKRZYZOWANIA_CM = 6
ODL_OPUSZCZENIA_SKRZYZOWANIA_CM = 8
ODL_WJAZDU_W_STACJE_CM = 10
ODL_OPUSZCZENIA_STACJI_CM = 20
ODL_WJAZDU_W_STREFE_DOSTAWY_CM = 10
ODL_WJAZDU_NA_TRASE_POWROTNA_CM = 8
ODL_WJAZDU_DO_BAZY_CM = 10


PROG_ZABLOKOWANEGO_KORYTARZA_CM = 45


PROG_AWARYJNEGO_STOPU_CM = 12


ORANGE_R_MIN = 110
ORANGE_G_MIN = 35
ORANGE_G_MAX = 190
ORANGE_B_MAX = 110
ORANGE_R_DO_G_MIN = 1.15
ORANGE_G_DO_B_MIN = 1.20


LICZBA_PROBEK_ODLEGLOSCI = 5


stacja_pobrania = STACJA_BRAK
strefa_dostawy = DOSTAWA_BRAK
etap = ETAP_ODCZYT_ZLECENIA
podetap = POD_POWROT_DO_PIERWSZEGO_SKRZYZOWANIA

predkosc_biezaca = PREDKOSC_STANDARDOWA
odchylenie = 0
korekta = 0

wybrany_korytarz = 0
liczba_wykonanych_etapow = 0
program_zatrzymany = False
misja_udana = False


blokada_zoltego_znacznika = False


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


    trafienia = 0
    for _ in range(liczba_prob):
        if wykryto_kolor(kolor):
            trafienia += 1
        time.sleep(0.03)
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

    trafienia = 0
    for _ in range(3):
        if wykryto_pomaranczowy():
            trafienia += 1
        time.sleep(0.03)
    return trafienia >= 2


def diagnostyka_rgb():


    l1 = odczytaj_rgb("L1")
    r1 = odczytaj_rgb("R1")
    cyberpi.console.print("L1: " + str(l1))
    cyberpi.console.print("R1: " + str(r1))


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


def ustaw_led_celu_pobrania():

    if stacja_pobrania == STACJA_A:
        ustaw_diody(LED_CZERWONY)
    elif stacja_pobrania == STACJA_B:
        ustaw_diody(LED_NIEBIESKI)


def ustaw_led_celu_dostawy():

    if strefa_dostawy == DOSTAWA_C:
        ustaw_diody(LED_ZIELONY)
    elif strefa_dostawy == DOSTAWA_D:
        ustaw_diody(LED_FIOLETOWY)


def odczytaj_pierwszy_znacznik():

    global stacja_pobrania

    stacja_pobrania = STACJA_BRAK

    if wykryto_kolor_stabilnie(KOLOR_CZERWONY_CZUJNIK):
        stacja_pobrania = STACJA_A
    elif wykryto_kolor_stabilnie(KOLOR_NIEBIESKI_CZUJNIK):
        stacja_pobrania = STACJA_B

    return stacja_pobrania != STACJA_BRAK


def odczytaj_drugi_znacznik():

    global strefa_dostawy

    strefa_dostawy = DOSTAWA_BRAK

    if wykryto_kolor_stabilnie(KOLOR_ZIELONY_CZUJNIK):
        strefa_dostawy = DOSTAWA_C
    elif wykryto_kolor_stabilnie(KOLOR_FIOLETOWY_CZUJNIK):
        strefa_dostawy = DOSTAWA_D

    return strefa_dostawy != DOSTAWA_BRAK


def odczytaj_zlecenie():

    if not odczytaj_pierwszy_znacznik():
        blad_misji("Bledne zlecenie: pobranie")
        return False


    mbot2.straight(ODL_DO_DRUGIEGO_ZNACZNIKA_ZLECENIA_CM)
    time.sleep(0.2)

    if not odczytaj_drugi_znacznik():
        blad_misji("Bledne zlecenie: dostawa")
        return False


    mbot2.straight(ODL_OPUSZCZENIA_PASA_ZLECENIA_CM)
    return True


def sygnalizuj_zlecenie():

    if stacja_pobrania == STACJA_A:
        pobranie = "A"
    else:
        pobranie = "B"

    if strefa_dostawy == DOSTAWA_C:
        dostawa = "C"
    else:
        dostawa = "D"

    cyberpi.console.print("Pobranie: " + pobranie)
    cyberpi.console.print("Dostawa: " + dostawa)
    ustaw_led_celu_pobrania()
    time.sleep(1)


def krok_jazdy_po_linii():

    global odchylenie, korekta

    odchylenie = mbuild.quad_rgb_sensor.get_offset_track(1)
    korekta = odchylenie * KP


    lewa_moc = -1 * (predkosc_biezaca + korekta)
    prawa_moc = predkosc_biezaca - korekta

    lewa_moc = ogranicz_wartosc(lewa_moc, -100, 100)
    prawa_moc = ogranicz_wartosc(prawa_moc, -100, 100)

    mbot2.drive_power(lewa_moc, prawa_moc)


def obsluz_skrzyzowanie_do_pobrania():

    global blokada_zoltego_znacznika

    mbot2.EM_stop("ALL")
    mbot2.straight(ODL_DO_SRODKA_SKRZYZOWANIA_CM)

    if stacja_pobrania == STACJA_A:
        mbot2.turn(-90)
    else:
        mbot2.turn(90)

    mbot2.straight(ODL_OPUSZCZENIA_SKRZYZOWANIA_CM)
    blokada_zoltego_znacznika = True


def wykryto_wlasciwa_stacje_pobrania():

    if stacja_pobrania == STACJA_A:
        return wykryto_kolor_stabilnie(KOLOR_CZERWONY_CZUJNIK)
    return wykryto_kolor_stabilnie(KOLOR_NIEBIESKI_CZUJNIK)


def pobierz_ladunek():

    global etap, podetap, liczba_wykonanych_etapow


    mbot2.straight(ODL_WJAZDU_W_STACJE_CM)
    mbot2.EM_stop("ALL")

    ustaw_diody(LED_ZIELONY)
    cyberpi.console.print("Ladunek pobrany")
    time.sleep(3)

    if limit_czasu_przekroczony():
        przekroczono_czas()
        return

    liczba_wykonanych_etapow += 1

    mbot2.turn(180)


    mbot2.straight(ODL_OPUSZCZENIA_STACJI_CM)

    etap = ETAP_DO_DOSTAWY
    podetap = POD_POWROT_DO_PIERWSZEGO_SKRZYZOWANIA
    ustaw_led_celu_dostawy()
    cyberpi.console.print("Przejazd do dostawy")


def obsluz_powrot_z_pobrania():

    global podetap, blokada_zoltego_znacznika

    mbot2.EM_stop("ALL")
    mbot2.straight(ODL_DO_SRODKA_SKRZYZOWANIA_CM)


    if stacja_pobrania == STACJA_A:
        mbot2.turn(-90)
    else:
        mbot2.turn(90)

    mbot2.straight(ODL_OPUSZCZENIA_SKRZYZOWANIA_CM)
    podetap = POD_DO_ROZWIDLENIA_KORYTARZY
    blokada_zoltego_znacznika = True


def korytarz_jest_przejezdny():


    time.sleep(0.25)
    odleglosc = zmierz_odleglosc_mediana()
    cyberpi.console.print("Odleglosc: " + str(odleglosc))


    return odleglosc > PROG_ZABLOKOWANEGO_KORYTARZA_CM


def wybierz_przejezdny_korytarz():


    global wybrany_korytarz, podetap, blokada_zoltego_znacznika

    mbot2.EM_stop("ALL")


    mbot2.straight(ODL_DO_SRODKA_SKRZYZOWANIA_CM)


    mbot2.turn(-90)
    cyberpi.console.print("Sprawdzam korytarz 1")

    if korytarz_jest_przejezdny():
        wybrany_korytarz = 1
        cyberpi.console.print("Wybrano korytarz 1")
        ustaw_led_celu_dostawy()
        mbot2.straight(ODL_OPUSZCZENIA_SKRZYZOWANIA_CM)
        podetap = POD_W_KORYTARZU
        blokada_zoltego_znacznika = True
        return

    ustaw_diody(LED_OSTRZEGAWCZY)
    cyberpi.console.print("Trasa 1 zablokowana")


    mbot2.turn(180)
    cyberpi.console.print("Sprawdzam korytarz 2")

    if korytarz_jest_przejezdny():
        wybrany_korytarz = 2
        cyberpi.console.print("Wybrano korytarz 2")
        ustaw_led_celu_dostawy()
        mbot2.straight(ODL_OPUSZCZENIA_SKRZYZOWANIA_CM)
        podetap = POD_W_KORYTARZU
        blokada_zoltego_znacznika = True
        return

    ustaw_diody(LED_OSTRZEGAWCZY)
    cyberpi.console.print("Trasa 2 zablokowana")
    blad_misji("Brak dostepnej trasy")


def kontrola_awaryjna_w_korytarzu():


    odleglosc = mbuild.ultrasonic2.get(1)
    if odleglosc < PROG_AWARYJNEGO_STOPU_CM:
        blad_misji("Awaryjny stop w korytarzu")
        return False
    return True


def rozpocznij_strefe_ograniczenia():

    global predkosc_biezaca, podetap

    predkosc_biezaca = PREDKOSC_OGRANICZONA
    podetap = POD_STREFA_OGRANICZONEJ_PREDKOSCI
    ustaw_diody(LED_TURKUSOWY)
    cyberpi.console.print("Ograniczenie predkosci")


    mbot2.straight(6)


def zakoncz_strefe_ograniczenia():

    global predkosc_biezaca, podetap

    predkosc_biezaca = PREDKOSC_STANDARDOWA
    podetap = POD_DO_SKRZYZOWANIA_DOSTAWY
    ustaw_led_celu_dostawy()
    cyberpi.console.print("Predkosc standardowa")


    mbot2.straight(6)


def obsluz_skrzyzowanie_dostawy():

    global podetap, blokada_zoltego_znacznika

    mbot2.EM_stop("ALL")
    mbot2.straight(ODL_DO_SRODKA_SKRZYZOWANIA_CM)

    if strefa_dostawy == DOSTAWA_C:
        mbot2.turn(-90)
    else:
        mbot2.turn(90)

    mbot2.straight(ODL_OPUSZCZENIA_SKRZYZOWANIA_CM)
    podetap = POD_DO_STREFY_DOSTAWY
    blokada_zoltego_znacznika = True


def wykryto_wlasciwa_strefe_dostawy():

    if strefa_dostawy == DOSTAWA_C:
        return wykryto_kolor_stabilnie(KOLOR_ZIELONY_CZUJNIK)
    return wykryto_kolor_stabilnie(KOLOR_FIOLETOWY_CZUJNIK)


def dostarcz_ladunek():

    global etap, liczba_wykonanych_etapow


    mbot2.straight(ODL_WJAZDU_W_STREFE_DOSTAWY_CM)
    mbot2.EM_stop("ALL")

    ustaw_diody(LED_ZIELONY)
    cyberpi.console.print("Ladunek dostarczony")
    time.sleep(3)

    if limit_czasu_przekroczony():
        przekroczono_czas()
        return

    liczba_wykonanych_etapow += 1


    if strefa_dostawy == DOSTAWA_C:
        mbot2.turn(-90)
    else:
        mbot2.turn(90)

    mbot2.straight(ODL_WJAZDU_NA_TRASE_POWROTNA_CM)
    etap = ETAP_POWROT_DO_BAZY
    ustaw_diody(LED_TURKUSOWY)
    cyberpi.console.print("Powrot zewnetrzna trasa")


def wykryto_znacznik_bazy():

    if stacja_pobrania == STACJA_A:
        return wykryto_kolor_stabilnie(KOLOR_CZERWONY_CZUJNIK)
    return wykryto_kolor_stabilnie(KOLOR_NIEBIESKI_CZUJNIK)


def zakoncz_misje():

    global etap, program_zatrzymany, misja_udana


    mbot2.straight(ODL_WJAZDU_DO_BAZY_CM)
    mbot2.EM_stop("ALL")


    if limit_czasu_przekroczony():
        przekroczono_czas()
        return

    if liczba_wykonanych_etapow != 2:
        blad_misji("Nie wykonano wszystkich etapow")
        return

    ustaw_diody(LED_ZIELONY)
    cyberpi.console.print("Misja zakonczona")
    cyberpi.console.print("Etapy: " + str(liczba_wykonanych_etapow) + "/2")
    cyberpi.console.print("Czas: " + str(cyberpi.timer.get()) + " s")

    etap = ETAP_ZAKONCZONY
    program_zatrzymany = True
    misja_udana = True


def obsluz_zolty_znacznik():

    if etap == ETAP_DO_POBRANIA:
        obsluz_skrzyzowanie_do_pobrania()
        return

    if etap != ETAP_DO_DOSTAWY:
        return

    if podetap == POD_POWROT_DO_PIERWSZEGO_SKRZYZOWANIA:
        obsluz_powrot_z_pobrania()
        return

    if podetap == POD_DO_ROZWIDLENIA_KORYTARZY:
        wybierz_przejezdny_korytarz()
        return

    if podetap == POD_DO_SKRZYZOWANIA_DOSTAWY:
        obsluz_skrzyzowanie_dostawy()
        return


    blad_misji("Nieoczekiwany zolty znacznik")


@event.start
def on_start():
    global stacja_pobrania, strefa_dostawy, etap, podetap
    global predkosc_biezaca, wybrany_korytarz
    global liczba_wykonanych_etapow, program_zatrzymany, misja_udana
    global blokada_zoltego_znacznika

    mbot2.EM_stop("ALL")
    cyberpi.led.off("all")
    cyberpi.console.print("Nacisnij A, aby rozpoczac")

    stacja_pobrania = STACJA_BRAK
    strefa_dostawy = DOSTAWA_BRAK
    etap = ETAP_ODCZYT_ZLECENIA
    podetap = POD_POWROT_DO_PIERWSZEGO_SKRZYZOWANIA
    predkosc_biezaca = PREDKOSC_STANDARDOWA
    wybrany_korytarz = 0
    liczba_wykonanych_etapow = 0
    program_zatrzymany = False
    misja_udana = False
    blokada_zoltego_znacznika = False

    while not cyberpi.controller.is_press("a"):


        if cyberpi.controller.is_press("b"):
            diagnostyka_rgb()
            time.sleep(0.5)
        time.sleep(0.01)


    cyberpi.timer.reset()

    if not odczytaj_zlecenie():
        return

    sygnalizuj_zlecenie()
    etap = ETAP_DO_POBRANIA

    while etap != ETAP_ZAKONCZONY and not program_zatrzymany:
        if limit_czasu_przekroczony():
            przekroczono_czas()
            break


        zolty = wykryto_kolor(KOLOR_ZOLTY_CZUJNIK)

        if zolty and not blokada_zoltego_znacznika:
            obsluz_zolty_znacznik()
            if program_zatrzymany:
                break

        if not zolty:
            blokada_zoltego_znacznika = False


        if etap == ETAP_DO_POBRANIA:
            if wykryto_wlasciwa_stacje_pobrania():
                pobierz_ladunek()
                if program_zatrzymany:
                    break


        elif etap == ETAP_DO_DOSTAWY:
            if podetap == POD_W_KORYTARZU:
                if not kontrola_awaryjna_w_korytarzu():
                    break


                if wykryto_pomaranczowy_stabilnie():
                    rozpocznij_strefe_ograniczenia()

            elif podetap == POD_STREFA_OGRANICZONEJ_PREDKOSCI:
                if wykryto_kolor_stabilnie(KOLOR_TURKUSOWY_CZUJNIK):
                    zakoncz_strefe_ograniczenia()

            elif podetap == POD_DO_STREFY_DOSTAWY:
                if wykryto_wlasciwa_strefe_dostawy():
                    dostarcz_ladunek()
                    if program_zatrzymany:
                        break


        elif etap == ETAP_POWROT_DO_BAZY:
            if wykryto_znacznik_bazy():
                zakoncz_misje()
                break


        if etap != ETAP_ZAKONCZONY and not program_zatrzymany:
            krok_jazdy_po_linii()

        time.sleep(0.01)
