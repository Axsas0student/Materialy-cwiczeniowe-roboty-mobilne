import event
import time
import cyberpi
import mbot2


@event.start
def on_start():
    mbot2.motor_set(50, "all")
    cyberpi.display.clear()
    mbot2.straight(50)
    time.sleep(1)
    cyberpi.console.print("Światło: ")
    cyberpi.console.print(cyberpi.get_bri())
    time.sleep(3)
    cyberpi.display.clear()
    mbot2.turn(90)
    mbot2.straight(50)
    time.sleep(1)
    cyberpi.console.print("Dźwięk: ")
    cyberpi.console.print(cyberpi.get_loudness())
    time.sleep(3)
    cyberpi.display.clear()
    cyberpi.console.print("Koniec")
    time.sleep(3)
    mbot2.EM_stop("ALL")
    cyberpi.stop_all()