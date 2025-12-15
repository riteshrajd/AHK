#!/usr/bin/env python3
import evdev
from evdev import ecodes, UInput, InputDevice
import sys
import time
import threading
import signal
import os

# Check for root/sudo
if os.getuid() != 0:
    print("❌ ERROR: This script must be run with sudo.")
    print("   Run: sudo python3 key_remapper.py")
    sys.exit(1)

print("Looking for typing keyboard...")

# Find the correct keyboard device
devices = [InputDevice(path) for path in evdev.list_devices()]
keyboard_device = None

for device in devices:
    if ecodes.EV_KEY in device.capabilities():
        keys = device.capabilities()[ecodes.EV_KEY]
        if ecodes.KEY_A in keys:
            print(f"✅ Found typing keyboard: {device.name} ({device.path})")
            keyboard_device = device
            if 'USB USB Keyboard' in device.name or 'AT Translated' in device.name:
                break

if not keyboard_device:
    print("❌ No typing keyboard found!")
    sys.exit(1)

# ============ CONFIGURATION ============
KEY_REPEAT_DELAY = 0.3
KEY_REPEAT_RATE = 0.05 

# Mouse Settings - Speeds (Supports decimals/floats now!)
MOUSE_SPEED_NORMAL = 1
MOUSE_SPEED_MEDIUM = 12     # Dot held
MOUSE_SPEED_FAST = 25       # Space held

SCROLL_SPEED_NORMAL = 0.2
SCROLL_SPEED_MEDIUM = 3     # Dot held
SCROLL_SPEED_FAST = 10       # Space held

# State Tracking
comma_held = False
dot_held = False
caps_held = False
caps_layer_active = False
numpad_mode = False
mouse_mode = False
processed_keys = set()
alt_held_for_switching = False

# Mouse Modifiers
scroll_held = False        # Toggled by holding 'M' in mouse mode
space_speed_boost = False  # Space = Fast boost

# Mouse Movement State
mouse_directions = {
    'up': False,
    'down': False,
    'left': False,
    'right': False
}

# Sub-pixel Accumulators (To handle float speeds and smooth movement)
# These store the "fractional" part of movement until it adds up to 1 pixel
accumulators = {
    'x': 0.0,
    'y': 0.0,
    'wheel': 0.0,
    'hwheel': 0.0
}

# Repeat Tracking
repeat_timers = {}
repeat_active = {}

# CapsLock Double-tap
caps_last_press_time = 0
caps_press_count = 0
DOUBLE_TAP_THRESHOLD = 0.2

# ============ MAPPINGS ============
comma_map = {
    ecodes.KEY_Q: ('`', True), ecodes.KEY_W: ('.', False), ecodes.KEY_E: (',', False),
    ecodes.KEY_R: ('7', True), ecodes.KEY_T: ('6', True), ecodes.KEY_A: ('2', True),
    ecodes.KEY_S: ('5', True), ecodes.KEY_D: ('[', True), ecodes.KEY_F: ('[', False),
    ecodes.KEY_G: ("'", False), ecodes.KEY_Z: ('3', True), ecodes.KEY_X: ('`', False),
    ecodes.KEY_C: (']', True), ecodes.KEY_V: (']', False), ecodes.KEY_B: ('\\', True),
}

dot_map = {
    ecodes.KEY_K: ecodes.KEY_ENTER, ecodes.KEY_J: ecodes.KEY_BACKSPACE,
    ecodes.KEY_I: (ecodes.KEY_ENTER, 'shift'), ecodes.KEY_M: (ecodes.KEY_BACKSPACE, 'ctrl'),
    ecodes.KEY_N: ecodes.KEY_DELETE, ecodes.KEY_E: ecodes.KEY_UP,
    ecodes.KEY_D: ecodes.KEY_DOWN, ecodes.KEY_S: ecodes.KEY_LEFT,
    ecodes.KEY_F: ecodes.KEY_RIGHT, ecodes.KEY_R: (ecodes.KEY_RIGHT, 'ctrl'),
    ecodes.KEY_W: (ecodes.KEY_LEFT, 'ctrl'), ecodes.KEY_H: 'delete_line',
}

numpad_map = {
    ecodes.KEY_W: '7', ecodes.KEY_E: '8', ecodes.KEY_R: '9',
    ecodes.KEY_S: '4', ecodes.KEY_D: '5', ecodes.KEY_F: '6', ecodes.KEY_G: '0',
    ecodes.KEY_X: '1', ecodes.KEY_C: '2', ecodes.KEY_V: '3',
    ecodes.KEY_A: ',', ecodes.KEY_Z: '.',
}

caps_map = {
    ecodes.KEY_Y: ('4', True), ecodes.KEY_U: ('.', True), ecodes.KEY_I: ('=', False),
    ecodes.KEY_O: ('\\', False), ecodes.KEY_P: ('1', True), ecodes.KEY_LEFTBRACE: ('/', True),
    ecodes.KEY_H: (',', True), ecodes.KEY_J: ('9', True), ecodes.KEY_K: ('=', True),
    ecodes.KEY_L: ('8', True), ecodes.KEY_SEMICOLON: ('-', False), ecodes.KEY_N: ('-', True),
    ecodes.KEY_M: ('0', True),
}
caps_special_map = { ecodes.KEY_F: 'alt+tab', ecodes.KEY_D: 'alt+shift+tab' }

char_to_key = {
    '`': ecodes.KEY_GRAVE, '.': ecodes.KEY_DOT, ',': ecodes.KEY_COMMA,
    '0': ecodes.KEY_0, '1': ecodes.KEY_1, '2': ecodes.KEY_2,
    '3': ecodes.KEY_3, '4': ecodes.KEY_4, '5': ecodes.KEY_5,
    '6': ecodes.KEY_6, '7': ecodes.KEY_7, '8': ecodes.KEY_8, '9': ecodes.KEY_9,
    '[': ecodes.KEY_LEFTBRACE, "'": ecodes.KEY_APOSTROPHE,
    ']': ecodes.KEY_RIGHTBRACE, '\\': ecodes.KEY_BACKSLASH,
    '=': ecodes.KEY_EQUAL, '-': ecodes.KEY_MINUS, '/': ecodes.KEY_SLASH,
}

# Mouse Keys
MOUSE_MOVE_KEYS = {ecodes.KEY_E, ecodes.KEY_S, ecodes.KEY_D, ecodes.KEY_F}
MOUSE_CLICK_KEYS = {ecodes.KEY_J, ecodes.KEY_K}  # J=Left, K=Right

# Grab device
try:
    keyboard_device.grab()
except IOError:
    print("❌ ERROR: Could not grab device.")
    sys.exit(1)

# ============ UINPUT SETUP ============
cap = keyboard_device.capabilities()
if ecodes.EV_SYN in cap: del cap[ecodes.EV_SYN]
if ecodes.EV_REL not in cap: cap[ecodes.EV_REL] = []

# Add relative axes
cap[ecodes.EV_REL].extend([ecodes.REL_X, ecodes.REL_Y, ecodes.REL_WHEEL, ecodes.REL_HWHEEL])
# Add mouse buttons
if ecodes.EV_KEY not in cap: cap[ecodes.EV_KEY] = []
cap[ecodes.EV_KEY].extend([ecodes.BTN_LEFT, ecodes.BTN_RIGHT])

ui = UInput(cap, name='remapped-keyboard-mouse')

print("\n=== Key Remapper Active ===")
print("Mouse Mode: Toggle with Dot + U")
print("Mouse Clicks: J=Left Click, K=Right Click")
print("Scroll Toggle: Hold M")

# Signal Handler
def cleanup(signum, frame):
    stop_all_repeats()
    try: keyboard_device.ungrab()
    except: pass
    ui.close()
    sys.exit(0)
signal.signal(signal.SIGINT, cleanup)

# ============ HELPER FUNCTIONS ============
def repeat_key_action(key_id, action_func):
    while repeat_active.get(key_id, False):
        action_func()
        delay = 0.016 if key_id[0] == 'mouse' else KEY_REPEAT_RATE
        time.sleep(delay)

def start_repeat(key_id, action_func):
    if key_id in repeat_timers: repeat_timers[key_id].cancel()
    
    if key_id[0] == 'mouse':
        repeat_active[key_id] = True
        t = threading.Thread(target=repeat_key_action, args=(key_id, action_func))
        t.daemon = True
        t.start()
    else:
        def delayed_repeat():
            repeat_active[key_id] = True
            t = threading.Thread(target=repeat_key_action, args=(key_id, action_func))
            t.daemon = True
            t.start()
        timer = threading.Timer(KEY_REPEAT_DELAY, delayed_repeat)
        timer.daemon = True
        timer.start()
        repeat_timers[key_id] = timer

def stop_repeat(key_id):
    repeat_active[key_id] = False
    if key_id in repeat_timers:
        repeat_timers[key_id].cancel()
        del repeat_timers[key_id]

def stop_all_repeats():
    for k in list(repeat_active.keys()): repeat_active[k] = False
    for t in list(repeat_timers.values()): t.cancel()
    repeat_timers.clear(); repeat_active.clear()

def type_char_simple(char, needs_shift):
    target_key = char_to_key[char]
    if needs_shift: ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1); ui.syn()
    ui.write(ecodes.EV_KEY, target_key, 1); ui.syn()
    ui.write(ecodes.EV_KEY, target_key, 0); ui.syn()
    if needs_shift: ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0); ui.syn()

def send_key_simple(key_code):
    ui.write(ecodes.EV_KEY, key_code, 1); ui.syn()
    ui.write(ecodes.EV_KEY, key_code, 0); ui.syn()

def send_modified_key(key_code, modifier):
    mod = ecodes.KEY_LEFTSHIFT if modifier == 'shift' else ecodes.KEY_LEFTCTRL
    ui.write(ecodes.EV_KEY, mod, 1); ui.syn()
    ui.write(ecodes.EV_KEY, key_code, 1); ui.syn()
    ui.write(ecodes.EV_KEY, key_code, 0); ui.syn()
    ui.write(ecodes.EV_KEY, mod, 0); ui.syn()

def delete_line():
    ui.write(ecodes.EV_KEY, ecodes.KEY_HOME, 1); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_HOME, 0); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_END, 1); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_END, 0); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_BACKSPACE, 1); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_BACKSPACE, 0); ui.syn()

def alt_tab_action():
    ui.write(ecodes.EV_KEY, ecodes.KEY_TAB, 1); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_TAB, 0); ui.syn()

def alt_shift_tab_action():
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_TAB, 1); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_TAB, 0); ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0); ui.syn()

# ============ MOUSE FUNCTIONS ============
def get_current_speed():
    """Determine current speed based on modifiers"""
    if space_speed_boost:
        return MOUSE_SPEED_FAST, SCROLL_SPEED_FAST
    elif dot_held: 
        return MOUSE_SPEED_MEDIUM, SCROLL_SPEED_MEDIUM
    else:
        return MOUSE_SPEED_NORMAL, SCROLL_SPEED_NORMAL

def move_mouse_combined():
    """Move mouse with Accumulator logic for smooth float speeds"""
    speed, scroll_spd = get_current_speed()
    
    # Add raw speed to accumulators
    if scroll_held:
        if mouse_directions['up']: accumulators['wheel'] += scroll_spd
        if mouse_directions['down']: accumulators['wheel'] -= scroll_spd
        if mouse_directions['left']: accumulators['hwheel'] -= scroll_spd
        if mouse_directions['right']: accumulators['hwheel'] += scroll_spd
    else:
        if mouse_directions['up']: accumulators['y'] -= speed
        if mouse_directions['down']: accumulators['y'] += speed
        if mouse_directions['left']: accumulators['x'] -= speed
        if mouse_directions['right']: accumulators['x'] += speed

    # Extract Integer parts
    move_x = int(accumulators['x'])
    move_y = int(accumulators['y'])
    move_wheel = int(accumulators['wheel'])
    move_hwheel = int(accumulators['hwheel'])

    # Update accumulators (keep only the fraction)
    accumulators['x'] -= move_x
    accumulators['y'] -= move_y
    accumulators['wheel'] -= move_wheel
    accumulators['hwheel'] -= move_hwheel

    # Write events only if there is movement
    if move_x != 0: ui.write(ecodes.EV_REL, ecodes.REL_X, move_x)
    if move_y != 0: ui.write(ecodes.EV_REL, ecodes.REL_Y, move_y)
    if move_wheel != 0: ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, move_wheel)
    if move_hwheel != 0: ui.write(ecodes.EV_REL, ecodes.REL_HWHEEL, move_hwheel)
    
    if move_x or move_y or move_wheel or move_hwheel:
        ui.syn()

def click_mouse(btn, val):
    ui.write(ecodes.EV_KEY, btn, val)
    ui.syn()

# ============ MAIN LOOP ============
for event in keyboard_device.read_loop():
    if event.type == ecodes.EV_KEY:
        key_code = event.code
        key_value = event.value
        
        # 1. MOUSE MODE TOGGLE CHECK (Dot + U)
        if key_code == ecodes.KEY_U and key_value == 1:
            if dot_held:
                mouse_mode = not mouse_mode
                print(f"🖱️ Mouse Mode: {'ON' if mouse_mode else 'OFF'}")
                processed_keys.add(key_code)
                stop_all_repeats()
                # Reset mouse state
                mouse_directions = {k: False for k in mouse_directions}
                accumulators = {k: 0.0 for k in accumulators} # Reset accumulators
                space_speed_boost = False
                scroll_held = False
                continue

        # 2. DOT Logic
        if key_code == ecodes.KEY_DOT:
            if key_value == 1:
                dot_held = True
            elif key_value == 0:
                dot_held = False
                if not mouse_mode:
                    numpad_mode = False
                    stop_all_repeats()
                    processed_keys.clear()
            if not mouse_mode:
                continue

        # 3. MOUSE MODE LOGIC
        if mouse_mode:
            if key_code == ecodes.KEY_DOT: continue
            
            if key_code == ecodes.KEY_SPACE:
                space_speed_boost = (key_value >= 1)
                continue
            
            # M = Scroll Toggle
            if key_code == ecodes.KEY_M:
                scroll_held = (key_value >= 1)
                # Clear accumulators when switching modes to prevent jumps
                accumulators['wheel'] = 0.0
                accumulators['hwheel'] = 0.0
                continue
            
            # Clicks (J=Left, K=Right)
            if key_code in MOUSE_CLICK_KEYS:
                btn = ecodes.BTN_LEFT if key_code == ecodes.KEY_J else ecodes.BTN_RIGHT
                click_mouse(btn, 1 if key_value >= 1 else 0)
                continue

            # Movement (E, S, D, F)
            if key_code in MOUSE_MOVE_KEYS:
                direction = {
                    ecodes.KEY_E: 'up', ecodes.KEY_D: 'down',
                    ecodes.KEY_S: 'left', ecodes.KEY_F: 'right'
                }[key_code]
                
                key_id = ('mouse', 'combined')
                
                if key_value == 1:  # Press
                    mouse_directions[direction] = True
                    move_mouse_combined()
                    if key_id not in repeat_active or not repeat_active[key_id]:
                        start_repeat(key_id, move_mouse_combined)
                elif key_value == 0:  # Release
                    mouse_directions[direction] = False
                    if not any(mouse_directions.values()):
                        stop_repeat(key_id)
                continue

        # 4. COMMA Logic
        if key_code == ecodes.KEY_COMMA:
            if key_value == 1:
                if dot_held:
                    numpad_mode = True
                    print("🔢 Numpad ON")
                else:
                    comma_held = True
            elif key_value == 0:
                comma_held = False
                if not dot_held:
                    numpad_mode = False
                    stop_all_repeats()
                    processed_keys.clear()
            continue

        # 5. CAPSLOCK Logic
        if key_code == ecodes.KEY_CAPSLOCK:
            if key_value == 1:
                curr = time.time()
                if curr - caps_last_press_time <= DOUBLE_TAP_THRESHOLD:
                    caps_press_count += 1
                    if caps_press_count == 2:
                        ui.write(ecodes.EV_KEY, ecodes.KEY_CAPSLOCK, 1); ui.syn()
                        ui.write(ecodes.EV_KEY, ecodes.KEY_CAPSLOCK, 0); ui.syn()
                        caps_press_count = 0
                else:
                    caps_press_count = 1
                    caps_held = True
                    caps_layer_active = True
                caps_last_press_time = curr
            elif key_value == 0:
                caps_held = False
                if caps_press_count != 2:
                    caps_layer_active = False
                if alt_held_for_switching:
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 0); ui.syn()
                    alt_held_for_switching = False
                stop_all_repeats()
                processed_keys.clear()
            continue

        # 6. Layer Execution
        active_layer_map = None
        layer_type = None

        if numpad_mode:
            if key_code in numpad_map: active_layer_map = numpad_map; layer_type = 'numpad'
        elif caps_layer_active:
            if key_code in caps_map: active_layer_map = caps_map; layer_type = 'caps'
            elif key_code in caps_special_map: active_layer_map = caps_special_map; layer_type = 'caps_special'
        elif dot_held and key_code in dot_map:
            active_layer_map = dot_map; layer_type = 'dot'
        elif comma_held and key_code in comma_map:
            active_layer_map = comma_map; layer_type = 'comma'

        if active_layer_map:
            key_id = (layer_type, key_code)
            if key_value == 1:
                if key_code not in processed_keys:
                    processed_keys.add(key_code)
                    mapping = active_layer_map[key_code]
                    action = None
                    
                    if layer_type == 'caps_special':
                        if mapping == 'alt+tab':
                            if not alt_held_for_switching:
                                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 1); ui.syn()
                                alt_held_for_switching = True
                            action = alt_tab_action
                        elif mapping == 'alt+shift+tab':
                            if not alt_held_for_switching:
                                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 1); ui.syn()
                                alt_held_for_switching = True
                            action = alt_shift_tab_action
                    elif layer_type == 'numpad':
                        action = lambda tk=char_to_key[mapping]: send_key_simple(tk)
                    elif layer_type == 'dot':
                        if mapping == 'delete_line': action = delete_line
                        elif isinstance(mapping, tuple): action = lambda tk=mapping[0], m=mapping[1]: send_modified_key(tk, m)
                        else: action = lambda m=mapping: send_key_simple(m)
                    else:
                        action = lambda c=mapping[0], ns=mapping[1]: type_char_simple(c, ns)

                    if action:
                        action()
                        start_repeat(key_id, action)

            elif key_value == 0:
                stop_repeat(key_id)
                processed_keys.discard(key_code)
            continue

        # 7. Passthrough
        ui.write_event(event)
        ui.syn()