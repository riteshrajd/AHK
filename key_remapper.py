#!/usr/bin/env python3
import evdev
from evdev import ecodes, UInput, InputDevice
import sys
import time
import threading

print("Looking for keyboard device...")

# Find keyboard device
devices = [InputDevice(path) for path in evdev.list_devices()]
keyboard_device = None

for device in devices:
    if 'keyboard' in device.name.lower() or 'AT Translated Set 2 keyboard' in device.name:
        keyboard_device = device
        print(f"Found keyboard: {device.name}")
        break

if not keyboard_device:
    print("No keyboard found! Available devices:")
    for device in devices:
        print(f"  - {device.name}")
    sys.exit(1)

# ============ KEY REPEAT CONFIGURATION ============
KEY_REPEAT_DELAY = 0.3  # Seconds before repeat starts (adjustable)
KEY_REPEAT_RATE = 0.05  # Seconds between repeats

# Track key states
comma_held = False
dot_held = False
caps_held = False
caps_layer_active = False
numpad_mode = False
processed_keys = set()
alt_held_for_switching = False

# Key repeat tracking
repeat_timers = {}
repeat_active = {}

# CapsLock double-tap tracking
caps_last_press_time = 0
caps_press_count = 0
DOUBLE_TAP_THRESHOLD = 0.2

# Comma layer mappings
comma_map = {
    ecodes.KEY_Q: ('`', True),   # ~
    ecodes.KEY_W: ('.', False),  # .
    ecodes.KEY_E: (',', False),  # ,
    ecodes.KEY_R: ('7', True),   # &
    ecodes.KEY_T: ('6', True),   # ^
    ecodes.KEY_A: ('2', True),   # @
    ecodes.KEY_S: ('5', True),   # %
    ecodes.KEY_D: ('[', True),   # {
    ecodes.KEY_F: ('[', False),  # [
    ecodes.KEY_G: ("'", False),  # '
    ecodes.KEY_Z: ('3', True),   # #
    ecodes.KEY_X: ('`', False),  # `
    ecodes.KEY_C: (']', True),   # }
    ecodes.KEY_V: (']', False),  # ]
    ecodes.KEY_B: ('\\', True),  # |
}

# Dot layer mappings
dot_map = {
    ecodes.KEY_K: ecodes.KEY_ENTER,
    ecodes.KEY_J: ecodes.KEY_BACKSPACE,
    ecodes.KEY_I: (ecodes.KEY_ENTER, 'shift'),
    ecodes.KEY_M: (ecodes.KEY_BACKSPACE, 'ctrl'),
    ecodes.KEY_N: ecodes.KEY_DELETE,
    ecodes.KEY_E: ecodes.KEY_UP,
    ecodes.KEY_D: ecodes.KEY_DOWN,
    ecodes.KEY_S: ecodes.KEY_LEFT,
    ecodes.KEY_F: ecodes.KEY_RIGHT,
    ecodes.KEY_R: (ecodes.KEY_RIGHT, 'ctrl'),
    ecodes.KEY_W: (ecodes.KEY_LEFT, 'ctrl'),
    ecodes.KEY_H: 'delete_line',
}

# Numpad layer mappings
numpad_map = {
    ecodes.KEY_W: '7',
    ecodes.KEY_E: '8',
    ecodes.KEY_R: '9',
    ecodes.KEY_S: '4',
    ecodes.KEY_D: '5',
    ecodes.KEY_F: '6',
    ecodes.KEY_G: '0',
    ecodes.KEY_X: '1',
    ecodes.KEY_C: '2',
    ecodes.KEY_V: '3',
    ecodes.KEY_A: ',',
    ecodes.KEY_Z: '.',
}

# CapsLock layer mappings
caps_map = {
    ecodes.KEY_Y: ('4', True),   # $
    ecodes.KEY_U: ('.', True),   # >
    ecodes.KEY_I: ('=', False),  # =
    ecodes.KEY_O: ('\\', False), # \
    ecodes.KEY_P: ('1', True),   # !
    ecodes.KEY_LEFTBRACE: ('/', True),  # ?
    ecodes.KEY_H: (',', True),   # <
    ecodes.KEY_J: ('9', True),   # (
    ecodes.KEY_K: ('=', True),   # +
    ecodes.KEY_L: ('8', True),   # *
    ecodes.KEY_SEMICOLON: ('-', False),  # -
    ecodes.KEY_N: ('-', True),   # _
    ecodes.KEY_M: ('0', True),   # )
}

# CapsLock special function mappings
caps_special_map = {
    ecodes.KEY_F: 'alt+tab',
    ecodes.KEY_D: 'alt+shift+tab',
}

# Character to key code mapping
char_to_key = {
    '`': ecodes.KEY_GRAVE,
    '.': ecodes.KEY_DOT,
    ',': ecodes.KEY_COMMA,
    '0': ecodes.KEY_0, '1': ecodes.KEY_1, '2': ecodes.KEY_2,
    '3': ecodes.KEY_3, '4': ecodes.KEY_4, '5': ecodes.KEY_5,
    '6': ecodes.KEY_6, '7': ecodes.KEY_7, '8': ecodes.KEY_8,
    '9': ecodes.KEY_9,
    '[': ecodes.KEY_LEFTBRACE,
    "'": ecodes.KEY_APOSTROPHE,
    ']': ecodes.KEY_RIGHTBRACE,
    '\\': ecodes.KEY_BACKSLASH,
    '=': ecodes.KEY_EQUAL,
    '-': ecodes.KEY_MINUS,
    '/': ecodes.KEY_SLASH,
}

# Grab exclusive access
keyboard_device.grab()

# Create virtual output keyboard
capabilities = keyboard_device.capabilities()
del capabilities[ecodes.EV_SYN]

ui = UInput(capabilities, name='remapped-keyboard')

print("\n=== Key Remapper Started ===")
print(f"\n⚙️  KEY REPEAT: Delay = {KEY_REPEAT_DELAY}s, Rate = {KEY_REPEAT_RATE}s")
print("\nCOMMA LAYER (hold ,):")
print("  a → @   s → %   d → {   f → [   g → '")
print("  z → #   x → `   c → }   v → ]   b → |")
print("\nDOT LAYER (hold .):")
print("  k → Enter    j → Backspace    e → Up    d → Down")
print("  s → Left     f → Right        h → Delete Line")
print("\nCAPSLOCK LAYER (hold CapsLock):")
print("  y → $   u → >   i → =   o → \\   p → !")
print("  h → <   j → (   k → +   l → *   n → _   m → )")
print("  f → Alt+Tab (switch apps)   d → Alt+Shift+Tab (reverse)")
print("\nNUMPAD LAYER (hold . then tap/hold ,):")
print("  w → 7   e → 8   r → 9")
print("  s → 4   d → 5   f → 6   g → 0")
print("  x → 1   c → 2   v → 3")
print("  a → ,   z → .")
print("\nCAPSLOCK: Double-tap within 0.2s to toggle CapsLock")
print("\nPress Ctrl+C to exit\n")

def repeat_key_action(key_id, action_func):
    """Continuously repeat a key action"""
    while repeat_active.get(key_id, False):
        action_func()
        time.sleep(KEY_REPEAT_RATE)

def start_repeat(key_id, action_func):
    """Start key repeat after delay"""
    if key_id in repeat_timers:
        repeat_timers[key_id].cancel()
    
    def delayed_repeat():
        repeat_active[key_id] = True
        repeat_thread = threading.Thread(target=repeat_key_action, args=(key_id, action_func))
        repeat_thread.daemon = True
        repeat_thread.start()
    
    timer = threading.Timer(KEY_REPEAT_DELAY, delayed_repeat)
    timer.daemon = True
    timer.start()
    repeat_timers[key_id] = timer

def stop_repeat(key_id):
    """Stop key repeat"""
    repeat_active[key_id] = False
    if key_id in repeat_timers:
        repeat_timers[key_id].cancel()
        del repeat_timers[key_id]

def stop_all_repeats():
    """Stop all active repeats"""
    for key_id in list(repeat_active.keys()):
        repeat_active[key_id] = False
    for timer in list(repeat_timers.values()):
        timer.cancel()
    repeat_timers.clear()
    repeat_active.clear()

def type_char_simple(char, needs_shift):
    """Type a character"""
    target_key = char_to_key[char]
    
    if needs_shift:
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
        ui.syn()
    
    ui.write(ecodes.EV_KEY, target_key, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, target_key, 0)
    ui.syn()
    
    if needs_shift:
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
        ui.syn()

def send_key_simple(key_code):
    """Send a simple key press"""
    ui.write(ecodes.EV_KEY, key_code, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, key_code, 0)
    ui.syn()

def send_modified_key(key_code, modifier):
    """Send a key with modifier"""
    if modifier == 'shift':
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
        ui.syn()
        ui.write(ecodes.EV_KEY, key_code, 1)
        ui.syn()
        ui.write(ecodes.EV_KEY, key_code, 0)
        ui.syn()
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
        ui.syn()
    elif modifier == 'ctrl':
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
        ui.syn()
        ui.write(ecodes.EV_KEY, key_code, 1)
        ui.syn()
        ui.write(ecodes.EV_KEY, key_code, 0)
        ui.syn()
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
        ui.syn()

def delete_line():
    """Delete entire line"""
    ui.write(ecodes.EV_KEY, ecodes.KEY_HOME, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_HOME, 0)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_END, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_END, 0)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_BACKSPACE, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_BACKSPACE, 0)
    ui.syn()

def alt_tab_action():
    """Press Tab (Alt already held)"""
    ui.write(ecodes.EV_KEY, ecodes.KEY_TAB, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_TAB, 0)
    ui.syn()

def alt_shift_tab_action():
    """Press Shift+Tab (Alt already held)"""
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_TAB, 1)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_TAB, 0)
    ui.syn()
    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
    ui.syn()

try:
    for event in keyboard_device.read_loop():
        if event.type == ecodes.EV_KEY:
            key_code = event.code
            key_value = event.value
            
            # Track comma state
            if key_code == ecodes.KEY_COMMA:
                if key_value == 1:
                    if dot_held:
                        numpad_mode = True
                        print("Numpad mode activated!")
                    else:
                        comma_held = True
                elif key_value == 0:
                    comma_held = False
                    if not dot_held:
                        numpad_mode = False
                    stop_all_repeats()
                    processed_keys.clear()
                continue
            
            # Track dot state
            if key_code == ecodes.KEY_DOT:
                if key_value == 1:
                    dot_held = True
                elif key_value == 0:
                    dot_held = False
                    numpad_mode = False
                    stop_all_repeats()
                    processed_keys.clear()
                continue
            
            # Track CapsLock state
            if key_code == ecodes.KEY_CAPSLOCK:
                if key_value == 1:
                    current_time = time.time()
                    
                    if current_time - caps_last_press_time <= DOUBLE_TAP_THRESHOLD:
                        caps_press_count += 1
                        if caps_press_count == 2:
                            print("CapsLock toggled!")
                            ui.write(ecodes.EV_KEY, ecodes.KEY_CAPSLOCK, 1)
                            ui.syn()
                            ui.write(ecodes.EV_KEY, ecodes.KEY_CAPSLOCK, 0)
                            ui.syn()
                            caps_press_count = 0
                    else:
                        caps_press_count = 1
                        caps_held = True
                        caps_layer_active = True
                    
                    caps_last_press_time = current_time
                elif key_value == 0:
                    caps_held = False
                    if caps_press_count != 2:
                        caps_layer_active = False
                    
                    if alt_held_for_switching:
                        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 0)
                        ui.syn()
                        alt_held_for_switching = False
                    
                    stop_all_repeats()
                    processed_keys.clear()
                continue
            
            # NUMPAD LAYER
            if numpad_mode and key_code in numpad_map:
                key_id = ('numpad', key_code)
                if key_value == 1:
                    if key_code not in processed_keys:
                        processed_keys.add(key_code)
                        char = numpad_map[key_code]
                        target_key = char_to_key[char]
                        
                        # First press
                        send_key_simple(target_key)
                        
                        # Start repeat
                        start_repeat(key_id, lambda tk=target_key: send_key_simple(tk))
                elif key_value == 0:
                    stop_repeat(key_id)
                    processed_keys.discard(key_code)
                continue
            
            # CAPSLOCK LAYER
            if caps_layer_active and key_code in caps_map:
                key_id = ('caps', key_code)
                if key_value == 1:
                    if key_code not in processed_keys:
                        processed_keys.add(key_code)
                        char, needs_shift = caps_map[key_code]
                        
                        # First press
                        type_char_simple(char, needs_shift)
                        
                        # Start repeat
                        start_repeat(key_id, lambda c=char, ns=needs_shift: type_char_simple(c, ns))
                elif key_value == 0:
                    stop_repeat(key_id)
                    processed_keys.discard(key_code)
                continue
            
            # CAPSLOCK SPECIAL FUNCTIONS
            if caps_layer_active and key_code in caps_special_map:
                key_id = ('caps_special', key_code)
                if key_value == 1:
                    if key_code not in processed_keys:
                        processed_keys.add(key_code)
                        action = caps_special_map[key_code]
                        
                        if action == 'alt+tab':
                            if not alt_held_for_switching:
                                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 1)
                                ui.syn()
                                alt_held_for_switching = True
                            
                            # First press
                            alt_tab_action()
                            
                            # Start repeat
                            start_repeat(key_id, alt_tab_action)
                        elif action == 'alt+shift+tab':
                            if not alt_held_for_switching:
                                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTALT, 1)
                                ui.syn()
                                alt_held_for_switching = True
                            
                            # First press
                            alt_shift_tab_action()
                            
                            # Start repeat
                            start_repeat(key_id, alt_shift_tab_action)
                elif key_value == 0:
                    stop_repeat(key_id)
                    processed_keys.discard(key_code)
                continue
            
            # DOT LAYER
            if dot_held and not numpad_mode and key_code in dot_map:
                key_id = ('dot', key_code)
                if key_value == 1:
                    if key_code not in processed_keys:
                        processed_keys.add(key_code)
                        mapping = dot_map[key_code]
                        
                        if mapping == 'delete_line':
                            # First press
                            delete_line()
                            
                            # Start repeat
                            start_repeat(key_id, delete_line)
                        elif isinstance(mapping, tuple):
                            target_key, modifier = mapping
                            
                            # First press
                            send_modified_key(target_key, modifier)
                            
                            # Start repeat
                            start_repeat(key_id, lambda tk=target_key, m=modifier: send_modified_key(tk, m))
                        else:
                            # First press
                            send_key_simple(mapping)
                            
                            # Start repeat
                            start_repeat(key_id, lambda m=mapping: send_key_simple(m))
                elif key_value == 0:
                    stop_repeat(key_id)
                    processed_keys.discard(key_code)
                continue
            
            # COMMA LAYER
            if comma_held and not numpad_mode and key_code in comma_map:
                key_id = ('comma', key_code)
                if key_value == 1:
                    if key_code not in processed_keys:
                        processed_keys.add(key_code)
                        char, needs_shift = comma_map[key_code]
                        
                        # First press
                        type_char_simple(char, needs_shift)
                        
                        # Start repeat
                        start_repeat(key_id, lambda c=char, ns=needs_shift: type_char_simple(c, ns))
                elif key_value == 0:
                    stop_repeat(key_id)
                    processed_keys.discard(key_code)
                continue
            
        # Forward all other events
        ui.write_event(event)
        ui.syn()
        
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    keyboard_device.ungrab()
    ui.close()