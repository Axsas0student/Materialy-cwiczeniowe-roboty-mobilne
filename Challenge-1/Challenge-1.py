"""
Challenge 1 – Autonomiczny kurier
Wersja tekstowa programu odpowiadająca projektowi blokowemu Ch1(5).mblock.

Robot:
- odczytuje czerwony albo niebieski znacznik celu,
- jedzie po linii z regulacją proporcjonalną,
- omija przeszkodę,
- wybiera właściwe odgałęzienie,
- realizuje dostawę i wraca do bazy,
- pilnuje limitu 180 sekund.
"""

import event
import time
import cyberpi
import mbot2
import mbuild


cel = 0
etap = 0
odchylenie = 0
korekta = 0
predkosc = 35
Kp = 0.7
blokada_przeszkody = 0
czas_omijania = 0
program_zatrzymany = False


# Kolory diod CyberPi użyte w bloczkach.
KOLOR_CZERWONY = (250, 2, 32)
KOLOR_NIEBIESKI = (15, 1, 208)
KOLOR_OSTRZEGAWCZY = (146, 1, 18)
KOLOR_ZIELONY = (1, 208, 19)


def ustaw_diody(kolor):
    """Ustawia wszystkie diody CyberPi na podany kolor RGB."""
    cyberpi.led.on(kolor[0], kolor[1], kolor[2], "all")


def odczytaj_cel():
    """Odczytuje znacznik w bazie: 1 – czerwony, 2 – niebieski."""
    global cel

    if mbuild.quad_rgb_sensor.is_color("red", "any", 1):
        cel = 1

    if mbuild.quad_rgb_sensor.is_color("blue", "any", 1):
        cel = 2


def sygnalizuj_rozpoczecie():
    """Wyświetla wybraną strefę i ustawia odpowiadający jej kolor diod."""
    if cel == 1:
        ustaw_diody(KOLOR_CZERWONY)
        cyberpi.console.print("Cel: strefa czerwona")

    if cel == 2:
        ustaw_diody(KOLOR_NIEBIESKI)
        cyberpi.console.print("Cel: strefa niebieska")

    time.sleep(1)


def krok_jazdy_po_linii():
    """Wykonuje pojedynczą korektę toru jazdy według regulatora P."""
    global odchylenie, korekta

    odchylenie = mbuild.quad_rgb_sensor.get_offset_track(1)
    korekta = odchylenie * Kp

    lewa_moc = -1 * (predkosc + korekta)
    prawa_moc = predkosc - korekta
    mbot2.drive_power(lewa_moc, prawa_moc)


def przekroczono_czas():
    """Kończy misję po przekroczeniu limitu 180 sekund."""
    global etap, program_zatrzymany

    mbot2.EM_stop("ALL")
    ustaw_diody(KOLOR_OSTRZEGAWCZY)
    cyberpi.console.print("Przekroczono czas")
    etap = 3
    program_zatrzymany = True


def omin_przeszkode():
    """Omija przeszkodę i próbuje ponownie odnaleźć czarną linię."""
    global blokada_przeszkody, czas_omijania, etap, program_zatrzymany

    blokada_przeszkody = 1

    mbot2.EM_stop("ALL")
    ustaw_diody(KOLOR_OSTRZEGAWCZY)
    time.sleep(0.5)

    mbot2.turn(-90)   # w lewo
    mbot2.straight(25)
    mbot2.turn(90)    # w prawo
    mbot2.straight(35)
    mbot2.turn(90)    # w prawo, w kierunku linii

    czas_omijania = 0

    while (
        not mbuild.quad_rgb_sensor.is_line("any", 1)
        and czas_omijania <= 3
        and cyberpi.timer.get() <= 180
    ):
        mbot2.motor_set(20, "all")
        time.sleep(0.1)
        czas_omijania = czas_omijania + 0.1

    mbot2.EM_stop("ALL")

    if cyberpi.timer.get() > 180:
        przekroczono_czas()
        return

    if mbuild.quad_rgb_sensor.is_line("any", 1):
        mbot2.turn(-90)   # w lewo, aby ustawić się wzdłuż linii
        mbot2.straight(5)

        if cel == 1:
            ustaw_diody(KOLOR_CZERWONY)

        if cel == 2:
            ustaw_diody(KOLOR_NIEBIESKI)

    else:
        mbot2.EM_stop("ALL")
        ustaw_diody(KOLOR_OSTRZEGAWCZY)
        cyberpi.console.print("Nie znaleziono linii")
        etap = 3
        program_zatrzymany = True


def obsluz_skrzyzowanie():
    """Na żółtym znaczniku wybiera właściwy kierunek jazdy."""
    mbot2.EM_stop("ALL")
    mbot2.straight(6)

    if etap == 1:
        if cel == 1:
            mbot2.turn(-90)   # czerwony – w lewo

        if cel == 2:
            mbot2.turn(90)    # niebieski – w prawo

    if etap == 2:
        if cel == 1:
            mbot2.turn(90)    # powrót z czerwonej – w prawo

        if cel == 2:
            mbot2.turn(-90)   # powrót z niebieskiej – w lewo

    mbot2.straight(8)


def wykonaj_dostawe():
    """Wjeżdża do strefy, potwierdza dostawę i rozpoczyna powrót."""
    global etap

    mbot2.straight(10)
    mbot2.EM_stop("ALL")
    ustaw_diody(KOLOR_ZIELONY)
    cyberpi.console.print("Dostawa zakończona")
    time.sleep(3)

    mbot2.turn(180)
    mbot2.straight(20)
    etap = 2

    if cel == 1:
        ustaw_diody(KOLOR_CZERWONY)

    if cel == 2:
        ustaw_diody(KOLOR_NIEBIESKI)

    cyberpi.console.print("Powrót do bazy")


def zakoncz_misje():
    """Wjeżdża całym robotem do bazy i kończy misję."""
    global etap

    mbot2.straight(10)
    mbot2.EM_stop("ALL")

    if cyberpi.timer.get() > 180:
        przekroczono_czas()
    else:
        ustaw_diody(KOLOR_ZIELONY)
        cyberpi.console.print("Misja zakończona")
        etap = 3


@event.start
def on_start():
    global cel, etap, predkosc, Kp, blokada_przeszkody
    global program_zatrzymany

    mbot2.EM_stop("ALL")
    cyberpi.led.off("all")
    cyberpi.console.print("Naciśnij A, aby rozpocząć")

    cel = 0
    etap = 0
    predkosc = 35
    Kp = 0.7
    blokada_przeszkody = 0
    program_zatrzymany = False

    while not cyberpi.controller.is_press("a"):
        time.sleep(0.01)

    cyberpi.timer.reset()
    odczytaj_cel()

    if cel == 0:
        cyberpi.console.print("Nie rozpoznano koloru")
        return

    sygnalizuj_rozpoczecie()

    mbot2.straight(12)
    etap = 1

    while etap != 3 and not program_zatrzymany:
        if cyberpi.timer.get() > 180:
            przekroczono_czas()
            break

        odleglosc = mbuild.ultrasonic2.get(1)

        if odleglosc > 25:
            blokada_przeszkody = 0

        if odleglosc < 15 and blokada_przeszkody == 0:
            omin_przeszkode()
            if program_zatrzymany:
                break

        if mbuild.quad_rgb_sensor.is_color("yellow", "any", 1):
            obsluz_skrzyzowanie()

        if etap == 1:
            if cel == 1 and mbuild.quad_rgb_sensor.is_color("red", "any", 1):
                wykonaj_dostawe()

            if cel == 2 and mbuild.quad_rgb_sensor.is_color("blue", "any", 1):
                wykonaj_dostawe()

        elif etap == 2:
            if cel == 1 and mbuild.quad_rgb_sensor.is_color("red", "any", 1):
                zakoncz_misje()

            if cel == 2 and mbuild.quad_rgb_sensor.is_color("blue", "any", 1):
                zakoncz_misje()

        if etap != 3 and not program_zatrzymany:
            krok_jazdy_po_linii()
