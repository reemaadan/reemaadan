from machine import Pin
import time

# gpio pin setup
q7_fb = Pin(4, Pin.IN)      # shift register feedback
shcp = Pin(18, Pin.OUT)     # shift register clock
stcp = Pin(19, Pin.OUT)     # storage register clock
ds = Pin(20, Pin.OUT)       # serial data input
oe = Pin(21, Pin.OUT)       # output enable

# button setup with pull down resistors
sw1 = Pin(10, Pin.IN, Pin.PULL_DOWN)  # north
sw2 = Pin(11, Pin.IN, Pin.PULL_DOWN)  # east
sw3 = Pin(12, Pin.IN, Pin.PULL_DOWN)  # south
sw4 = Pin(13, Pin.IN, Pin.PULL_DOWN)  # west

# global variables for car counting
cars = {
    'north': 0,
    'east': 0,
    'south': 0,
    'west': 0
}

# led states 16 bits total
# r1 y1 g1 w1  r2 y2 g2 w2  r3 y3 g3 w3  r4 y4 g4 w4
led_states = [0] * 16

def shift_out(value):
    # shift out one bit to the shift register
    ds.value(value)
    shcp.value(1)
    shcp.value(0)

def update_shift_register():
    # update the entire shift register with current led states
    # shift out all 16 bits
    for bit in reversed(led_states):
        shift_out(bit)
    
    # latch the data
    stcp.value(1)
    stcp.value(0)

def set_traffic_lights(ns_state, ew_state):
    # set traffic light states for north south and east west directions
    # define light patterns
    patterns = {
        'red': [1, 0, 0],    # red only
        'green': [0, 0, 1],  # green only
        'yellow': [0, 1, 0]  # yellow only
    }
    
    # get the patterns for each direction
    ns_pattern = patterns[ns_state]
    ew_pattern = patterns[ew_state]
    
    # update north south lights
    led_states[0:3] = ns_pattern  # north
    led_states[8:11] = ns_pattern  # south
    
    # update east west lights
    led_states[4:7] = ew_pattern  # east
    led_states[12:15] = ew_pattern  # west
    
    update_shift_register()

def update_car_indicators():
    # update white leds based on waiting cars
    # set white leds positions 3 7 11 15
    led_states[3] = 1 if cars['north'] > 0 else 0   # north
    led_states[7] = 1 if cars['east'] > 0 else 0    # east
    led_states[11] = 1 if cars['south'] > 0 else 0  # south
    led_states[15] = 1 if cars['west'] > 0 else 0   # west
    
    update_shift_register()

def check_buttons():
    # check all buttons and update car counters
    if sw1.value():
        cars['north'] += 1
        time.sleep(0.2)  # simple debounce
    if sw2.value():
        cars['east'] += 1
        time.sleep(0.2)
    if sw3.value():
        cars['south'] += 1
        time.sleep(0.2)
    if sw4.value():
        cars['west'] += 1
        time.sleep(0.2)

def process_cars_clearing(direction1, direction2):
    # process cars clearing the intersection for given directions
    if time.time() % 3 < 0.1:  # check every 3 seconds
        if cars[direction1] > 0:
            cars[direction1] -= 1
        if cars[direction2] > 0:
            cars[direction2] -= 1

def main():
    # constants
    MAX_CARS = 5      # maximum cars before forcing light change
    GREEN_A = 5       # initial green time
    GREEN_B = 5       # extended green time
    YELLOW_TIME = 3   # yellow light duration
    
    # initialize shift register
    oe.value(1)  # disable outputs during initialization
    update_shift_register()
    oe.value(0)  # enable outputs
    
    # main control loop
    while True:
        # north south green cycle
        start_time = time.time()
        
        # green a phase mandatory 5 seconds
        set_traffic_lights('green', 'red')
        while time.time() - start_time < GREEN_A:
            check_buttons()
            update_car_indicators()
        
        # green b phase up to 5 more seconds
        while (time.time() - start_time < GREEN_A + GREEN_B and 
               (cars['east'] + cars['west']) < MAX_CARS):
            check_buttons()
            update_car_indicators()
            process_cars_clearing('north', 'south')
        
        # yellow phase
        set_traffic_lights('yellow', 'red')
        yellow_start = time.time()
        while time.time() - yellow_start < YELLOW_TIME:
            check_buttons()
            update_car_indicators()
        
        # east west green cycle
        start_time = time.time()
        
        # green a phase
        set_traffic_lights('red', 'green')
        while time.time() - start_time < GREEN_A:
            check_buttons()
            update_car_indicators()
        
        # green b phase
        while (time.time() - start_time < GREEN_A + GREEN_B and 
               (cars['north'] + cars['south']) < MAX_CARS):
            check_buttons()
            update_car_indicators()
            process_cars_clearing('east', 'west')
        
        # yellow phase
        set_traffic_lights('red', 'yellow')
        yellow_start = time.time()
        while time.time() - yellow_start < YELLOW_TIME:
            check_buttons()
            update_car_indicators()

# start the program
if __name__ == '__main__':
    main()
