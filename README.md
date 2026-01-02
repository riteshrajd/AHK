# ⌨️ Key Remapper for a Better Typing Experience

This project remaps keys to minimize hand movement and improve the touch-typing experience. By using trigger keys (`capslock`, `,`, `.`), you can access all special symbols, navigation, numpad functionality, and **mouse controls** directly from the three main alphabet rows, eliminating the need to reach for other keys (except for standard Ctrl/Shift/Alt/Win combos).

---

## 🟩 Installation

This key remapper is available for Windows (AutoHotkey) and Linux (Kanata or Python).

### 🐧 Linux Method 1: Kanata (Recommended)
**Best for:** Performance, gaming, and Online Assessments (Undetectable). Runs at the kernel level.

**Quick Setup (Fedora/Debian/Arch)**
Copy and paste this entire block into your terminal to set up and run Kanata immediately:

```bash
# 1. Download Kanata binary
mkdir -p ~/kanata
wget [https://github.com/jtroo/kanata/releases/download/v1.6.1/kanata](https://github.com/jtroo/kanata/releases/download/v1.6.1/kanata) -O ~/kanata/kanata
chmod +x ~/kanata/kanata

# 2. Setup permissions (uinput) so it runs smoothly
sudo groupadd uinput
sudo usermod -aG uinput $USER
echo 'KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-input.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# 3. Run it! (Assuming you are inside this repo folder)
# Note: You might need to logout/login once for permissions to take full effect without sudo.
# For now, we run with sudo to ensure it works instantly:
sudo ~/kanata/kanata -c kanata/config.kbd

```

---

### 🐧 Linux Method 2: Python Script (Legacy)

The Python script uses the `evdev` library to intercept and inject input events. Good for quick testing if you don't want to download binaries.

1. **Install the Dependency**: The script requires the `evdev` Python library.
```bash
# Fedora
sudo dnf install python3-evdev
# OR via pip (globally or in a venv)
sudo pip install evdev

```


2. **Run the Script**: Navigate to the repository folder and run the script with `sudo`:
```bash
sudo python3 key_remapper.py

```


*Note: The script must be run as root to grab the input device successfully.*
3. **(Optional) Run on Startup**: To run this automatically, you will need to create a systemd service or add a sudo-enabled command to your startup applications.

### 🪟 Windows

1. 💾 **Install AHK**: Download and install AutoHotkey from the official [AutoHotkey website](https://www.autohotkey.com/).
2. 📥 **Run the Scripts**: Download all the `.ahk` files and run them in the following order by double-clicking them:
1. `first > , . caps.ahk`
2. `then > num_pad_handling.ahk`



You are now good to go!

---

## ❓ How to Disable / Toggle

#### **Linux (Kanata)**

* Press `Ctrl+C` in the terminal window running Kanata.
* If running in background: `sudo pkill kanata`

#### **Linux (Python)**

* **To Disable**: The script runs in your terminal. simply press `Ctrl+C` to stop it safely. The keyboard will return to normal immediately.
* **If running in background**:
```bash
sudo pkill -f key_remapper.py

```



#### **Windows**

* The remappings can be toggled on and off from the Windows taskbar. Go to the system tray, right-click the green 'H' hotkey icons, and select "Pause Script" or "Exit."

---

## 🔵 Remappings

The keys `,`, `.`, and `capslock` are **trigger keys**. When you hold one of them down, the keys on the alphabet rows are remapped to new functions.

* **To use Caps Lock normally**: Press `capslock` twice within 0.2 seconds.

### **🖱️ Mouse Mode (Linux Python Only)**

*Note: Mouse mode is currently only available in the Python version of the script.*

A dedicated mode to control your cursor without leaving the keyboard.

* **Toggle ON/OFF**: Press `.` (Dot) + `u`
*(Hold Dot, tap U, release both)*

**Once Mouse Mode is Active:**

| Function | Key | Description |
| --- | --- | --- |
| **Movement** | `e`, `s`, `d`, `f` | Up, Left, Down, Right (Matches Arrow/Vim positions) |
| **Clicks** | `j` | **Left Click** |
|  | `k` | **Right Click** |
| **Scrolling** | Hold `m` | Turns `e/s/d/f` into **Scroll** Up/Left/Down/Right |
| **Speed** | (None) | Normal Speed |
|  | Hold `.` | Medium Speed / Medium Scroll |
|  | Hold `Space` | **Turbo Speed** / Fast Scroll |

*current mouse settings*

```
# Mouse Settings - Speeds (Supports decimals/floats now!)
MOUSE_SPEED_NORMAL = 1
MOUSE_SPEED_MEDIUM = 12     # Dot held
MOUSE_SPEED_FAST = 25       # Space held

SCROLL_SPEED_NORMAL = 0.2
SCROLL_SPEED_MEDIUM = 3     # Dot held
SCROLL_SPEED_FAST = 10       # Space held

```

---

### **Core Remappings (Global)**

#### **Hold `Capslock` Layer (Symbols)**

* `y` → `$` | `u` → `>` | `i` → `=` | `o` → `\` | `p` → `!`
* `h` → `<` | `j` → `(` | `k` → `+` | `l` → `*` | `;` → `-`
* `n` → `_` | `m` → `)` | `[` → `?`

#### **Hold `,` Layer (Symbols)**

* `q` → `~` | `w` → `.` | `e` → `,` | `r` → `&` | `t` → `^`
* `a` → `@` | `s` → `%` | `d` → `{` | `f` → `[` | `g` → `'`
* `z` → `#` | `x` → ` | `c` → `}` | `v` → `]` | `b` → `|`

#### **Hold `.` Layer (Navigation & Editing)**

* `k` → `Enter`
* `j` → `Backspace`
* `i` → `Shift` + `Enter`
* `m` → `Ctrl` + `Backspace` (delete word)
* `n` → `Delete`
* `e` → `Up Arrow`
* `d` → `Down Arrow`
* `s` → `Left Arrow`
* `f` → `Right Arrow`
* `r` → `Ctrl` + `Right Arrow` (next word)
* `w` → `Ctrl` + `Left Arrow` (previous word)

#### **Hold `.` then hold `,` Layer (Numpad)**

*First hold down `.`, and while holding it, also hold down `,` to activate this layer.*

* `w` → `7` | `e` → `8` | `r` → `9`
* `s` → `4` | `d` → `5` | `f` → `6` | `g` → `0`
* `x` → `1` | `c` → `2` | `v` → `3`
* `a` → `,` | `z` → `.`

### **✨ Linux Extras**

* `Capslock` + `f` → `Alt` + `Tab` (App Switcher)
* `Capslock` + `d` → `Alt` + `Shift` + `Tab` (App Switcher Reverse)
* `.` + `h` → **Delete Whole Line**

```