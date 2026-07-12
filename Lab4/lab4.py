import event
import time
import mbuild
import mbot2


@event.start
def on_start():
    mbuild.ultrasonic2.set_bri(20, "all", 1)
    while True:
        distance = mbuild.ultrasonic2.get(1)
        if distance < 15:
            mbot2.motor_stop("all")
            mbuild.ultrasonic2.set_bri(100, "all", 1)
            time.sleep(1)
            mbot2.turn(90)
            mbuild.ultrasonic2.set_bri(20, "all", 1)
        else:
            mbot2.forward(50)
        time.sleep(0.05)