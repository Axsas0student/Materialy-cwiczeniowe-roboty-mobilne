import event
import time
import cyberpi
import mbot2


@event.start
def on_start():
    cyberpi.display.clear()
    while True:
        if cyberpi.get_shakeval() > 30:
            mbot2.motor_stop("all")
            cyberpi.display.clear()
            cyberpi.console.print("Wstrząs")
            time.sleep(1)
            cyberpi.display.clear()
        else:
            if cyberpi.get_pitch() > 10 or cyberpi.get_pitch() < -10:
                mbot2.forward(20)
                cyberpi.display.clear()
                cyberpi.console.print("Pochylenie")
            else:
                mbot2.forward(50)
                cyberpi.display.clear()
                cyberpi.console.print("Jazda")
        time.sleep(0.05)