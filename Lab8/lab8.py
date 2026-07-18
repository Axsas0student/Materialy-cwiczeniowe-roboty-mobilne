import event
import time
import cyberpi
import mbuild
import mbot2

zamowienie = ""
cel = ""
left_eng = 0
right_eng = 0


def line_follow_proportional(speed, steering, deviation):
    global left_eng, right_eng

    left_eng = -1 * (speed + steering * deviation)
    right_eng = speed - steering * deviation

    mbot2.drive_speed(left_eng, right_eng)


def przyjmij_zamowienie():
    global zamowienie

    cyberpi.display.clear()
    cyberpi.cloud.tts(
        "english",
        "Hello. What would you like to order: water or juice?"
    )
    cyberpi.cloud.listen("english", 3)

    zamowienie = cyberpi.cloud.listen_result()

    cyberpi.display.clear()
    cyberpi.console.print(zamowienie)


def potwierdz_zamowienie():
    global zamowienie, cel

    if "water" in zamowienie:
        cel = "czerwony"
        cyberpi.cloud.tts("english", "Order received: water.")
        cyberpi.cloud_broadcast.set("zamówienie", zamowienie)

    elif "juice" in zamowienie:
        cel = "zielony"
        cyberpi.cloud.tts("english", "Order received: juice.")
        cyberpi.cloud_broadcast.set("zamówienie", zamowienie)

    else:
        cel = ""
        cyberpi.display.clear()
        cyberpi.console.print("Nieznane zamówienie")
        cyberpi.cloud.tts(
            "english",
            "Unknown order. Please repeat."
        )


def dostarcz_zamowienie():
    global zamowienie, cel

    mbot2.straight(5)

    while not (
        (
            cel == "czerwony"
            and mbuild.quad_rgb_sensor.is_color("red", "any", 1)
        )
        or
        (
            cel == "zielony"
            and mbuild.quad_rgb_sensor.is_color("green", "any", 1)
        )
    ):
        line_follow_proportional(
            40,
            0.6,
            mbuild.quad_rgb_sensor.get_offset_track(1)
        )

    mbot2.EM_stop("ALL")
    cyberpi.display.clear()
    cyberpi.console.print("Zamówienie dostarczone")
    cyberpi.cloud.tts("english", "Order delivered")
    time.sleep(3)

    zamowienie = ""
    cel = ""

    cyberpi.display.clear()
    cyberpi.console.print("Naciśnij A, aby złożyć zamówienie")


@event.start
def on_start():
    global zamowienie, cel

    #placeholder
    cyberpi.wifi.connect("ssid", "password")
    cyberpi.led.on(208, 2, 27)

    while not cyberpi.wifi.is_connect():
        time.sleep(0.1)

    cyberpi.led.on(8, 208, 1)
    #placeholder
    cyberpi.cloud.setkey("CLOUD_KEY")

    zamowienie = ""
    cel = ""

    cyberpi.display.clear()
    cyberpi.console.print("Robot-kelner gotowy")
    time.sleep(2)

    cyberpi.display.clear()
    cyberpi.console.print("Naciśnij A, aby złożyć zamówienie")


@event.is_press("a")
def on_button_a():
    przyjmij_zamowienie()
    potwierdz_zamowienie()

    if cel != "":
        dostarcz_zamowienie()