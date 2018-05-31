import machine


ON = 1
OFF = 0

LED = machine.Pin(2, machine.Pin.OUT)

timer = machine.Timer(-1)


def blink_led(duration=0.5):
    if LED.value() == OFF:
        return False  # don't blink if already lighted

    LED.value(OFF)
    timer.init(period=int(duration * 1000), mode=machine.Timer.ONE_SHOT, callback=lambda t: LED.value(ON))

    return True
