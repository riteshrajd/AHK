# ⌨️ Key Remapper for a Better Typing Experience

This project remaps keys to minimize hand movement and improve the touch-typing experience. By using trigger keys (`capslock`, `,`, `.`), you can access all special symbols, navigation, and numpad functionality directly from the three main alphabet rows, eliminating the need to reach for other keys (except for standard Ctrl/Shift/Alt/Win combos).

---

## 🟩 Installation

This key remapper is available for both Windows (via AutoHotkey) and Linux (via a Python script). Please follow the instructions for your operating system.

### 🐧 Linux (Fedora)

The Python script uses the `evdev` library to read keyboard input directly. You'll need to install this dependency and grant your user the correct permissions.

1.  **Install the Dependency**: The script requires the `evdev` Python library. Open a terminal and install it using pip:
    ```bash
    pip install evdev
    ```

2.  **Run the Script**: After logging back in, navigate to the repository folder and run the Python script:
    ```bash
    python3 key_remapper.py
    ```
    The script will now run without `sudo` and will continue running in that terminal until you stop it (`Ctrl+C`).

3.  **(Optional) Run on Startup**: To have the script run automatically every time you log in, you can add it to your desktop environment's "Startup Applications."

### 🪟 Windows

1.  💾 **Install AHK**: Download and install AutoHotkey from the official [AutoHotkey website](https://www.autohotkey.com/).
2.  📥 **Run the Scripts**: Download all the `.ahk` files and run them in the following order by double-clicking them:
    1.  `first > , . caps.ahk`
    2.  `then > num_pad_handling.ahk`

You are now good to go!

---

## ❓ How to Disable / Toggle

#### **Linux**

-   **To Disable**: You need to stop the Python script. Find its Process ID (PID) and kill it, or use `pkill`.
    ```bash
    # This will find and kill the process running the script
    sudo pkill -f key_remapper.py
    ```
-   **To Re-enable**: Simply run the script again as mentioned in the installation steps.

#### **Windows**

-   The remappings can be toggled on and off from the Windows taskbar. Go to the system tray (the "show hidden icons" arrow in the bottom-right), right-click the green 'H' hotkey icons, and select "Pause Script," "Suspend Hotkeys," or "Exit."
-   To re-enable, just run the `.ahk` files again.

---

## 🔵 Remappings

The keys `,`, `.`, and `capslock` are **trigger keys**. When you hold one of them down, the keys on the alphabet rows are remapped to new functions.

-   **To use Caps Lock normally**: Press `capslock` twice within 0.2 seconds.

### **Core Remappings (Both Windows & Linux)**

![Remappings for comma and capslock triggers](images/comma_&_capslock_remappings.jpg)

#### **Hold `Capslock` Layer (Symbols)**

-   `y` → `$`
-   `u` → `>`
-   `i` → `=`
-   `o` → `\`
-   `p` → `!`
-   `[` → `?`
-   `h` → `<`
-   `j` → `(`
-   `k` → `+`
-   `l` → `*`
-   `;` → `-`
-   `n` → `_`
-   `m` → `)`

#### **Hold `,` Layer (Symbols)**

-   `q` → `~`
-   `w` → `.`
-   `e` → `,`
-   `r` → `&`
-   `t` → `^`
-   `a` → `@`
-   `s` → `%`
-   `d` → `{`
-   `f` → `[`
-   `g` → `'`
-   `z` → `#`
-   `x` → \`
-   `c` → `}`
-   `v` → `]`
-   `b` → `|`

#### **Hold `.` Layer (Navigation & Editing)**

-   `k` → `Enter`
-   `j` → `Backspace`
-   `i` → `Shift` + `Enter`
-   `m` → `Ctrl` + `Backspace` (delete word)
-   `n` → `Delete`
-   `e` → `Up Arrow`
-   `d` → `Down Arrow`
-   `s` → `Left Arrow`
-   `f` → `Right Arrow`
-   `r` → `Ctrl` + `Right Arrow` (next word)
-   `w` → `Ctrl` + `Left Arrow` (previous word)

#### **Hold `.` then hold `,` Layer (Numpad - Experimental)**

*First hold down `.`, and while holding it, also hold down `,` to activate this layer.*

-   `w` → `7` | `e` → `8` | `r` → `9`
-   `s` → `4` | `d` → `5` | `f` → `6` | `g` → `0`
-   `x` → `1` | `c` → `2` | `v` → `3`
-   `a` → `,`
-   `z` → `.`

### **✨ Linux (Python Script) Extras**

These additional mappings are available in the `key_remapper.py` script:

-   `Capslock` + `f` / `d` → **App Switching** (`Alt`+`Tab`)
-   `.` + `h` → **Delete Whole Line** (`Shift`+`Home` then `Delete`)