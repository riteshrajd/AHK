Here is the updated **README.md**.

I have restructured the **Linux** section to prioritize **Kanata** (as it is safer and faster) while keeping the Python script as a "Legacy" option since it still offers mouse control. I also included the **One-Click Setup Command** for Fedora users.

---

# ⌨️ Key Remapper for a Better Typing Experience

This project remaps keys to minimize hand movement and improve the touch-typing experience. By using trigger keys (`capslock`, `,`, `.`), you can access all special symbols, navigation, numpad functionality, and **mouse controls** directly from the three main alphabet rows, eliminating the need to reach for other keys (except for standard Ctrl/Shift/Alt/Win combos).

---

## 🟩 Installation

### 🐧 Linux (Fedora/Debian/Arch)

You have two options. **Option A (Kanata)** is recommended for speed, safety (undetectable in Online Assessments), and reliability. **Option B (Python)** is a legacy version that includes Mouse Keys.

#### **Option A: Kanata (Recommended 🚀)**

This runs at the kernel level using `uinput`. It is 100% undetectable by browsers and has zero latency.

**Fedora / Linux Quick Start (Copy & Paste):**
Run this entire block in your terminal to download Kanata, generate the config, and start it immediately.

```bash
# 1. Create directory and download Kanata binary
mkdir -p ~/kanata
wget https://github.com/jtroo/kanata/releases/download/v1.6.1/kanata -O ~/kanata/kanata
chmod +x ~/kanata/kanata

# 2. Generate the Configuration File (Caps, Dot, Comma layers)
cat > ~/kanata/config.kbd <<'EOF'
(defsrc
  caps  q  w  e  r  t  y  u  i  o  p  [  ]  \
  a     s  d  f  g  h  j  k  l  ;  '
  z     x  c  v  b  n  m  ,  .  /
)

(defalias
  ;; --- TRIGGERS ---
  ;; Caps: Tap=Nothing, DoubleTap=RealCaps, Hold=CapsLayer
  d_caps    (tap-dance 200 (XX caps))
  my_caps   (tap-hold-press 200 200 @d_caps (layer-toggle caps_layer))

  ;; Comma & Dot: Aggressive 1ms trigger (Instant Layer Switch)
  my_comma  (tap-hold-press 1 1 , (layer-toggle comma_layer))
  my_dot    (tap-hold-press 1 1 . (layer-toggle dot_layer))

  ;; Macros
  del_ln    (macro home S-end bspc)
)

;; 1. DEFAULT LAYER
(deflayer default
  @my_caps  q  w  e  r  t  y  u  i  o  p  [  ]  \
  a         s  d  f  g  h  j  k  l  ;  '
  z         x  c  v  b  n  m  @my_comma  @my_dot  /
)

;; 2. CAPS LAYER (Symbols 1)
(deflayer caps_layer
  _         _    _    _    _    _    S-4  S-.  =    \    S-1  S-/  _  _
  _         _    _    _    _    S-,  S-9  S-=  S-8  -    _
  _         _    _    _    _    S--  S-0  _    _    _
)

;; 3. COMMA LAYER (Symbols 2)
(deflayer comma_layer
  _         S-`  .    ,    S-7  S-6  _    _    _    _    _    _    _  _
  S-2       S-5  S-[  [    '    _    _    _    _    _    _
  S-3       `    S-]  ]    S-\  _    _    _    _    _
)

;; 4. DOT LAYER (Navigation)
(deflayer dot_layer
  _         _    C-lft up   C-rght _    _    _    S-ret _    _    _    _  _
  _         lft  down  rght _    _    bspc ret  _    _    _
  _         _    _     _    _    del  C-bspc (layer-toggle numpad_layer) _ _
)

;; 5. NUMPAD LAYER (Activated by holding . then ,)
(deflayer numpad_layer
  _         _    7    8    9    _    _    _    _    _    _    _    _  _
  ,         4    5    6    0    _    _    _    _    _    _
  .         1    2    3    _    _    _    _    _    _
)
EOF

# 3. Run Kanata (Requires sudo to grab keyboard input)
sudo ~/kanata/kanata -c ~/kanata/config.kbd

```

#### **Option B: Python Script (Legacy)**

*Best for: Users who strictly need Mouse Keys (Kanata config currently excludes mouse).*

1. **Install Dependency**:
```bash
sudo dnf install python3-evdev  # Fedora
# OR
sudo pip install evdev

```


2. **Run Script**:
```bash
sudo python3 key_remapper.py

```



### 🪟 Windows

1. 💾 **Install AHK**: Download [AutoHotkey](https://www.autohotkey.com/).
2. 📥 **Run Scripts**: Double-click the files in this order:
1. `first > , . caps.ahk`
2. `then > num_pad_handling.ahk`



---

## ❓ How to Disable / Toggle

**Linux (Kanata or Python)**

* Press `Ctrl+C` in the terminal window running the script.
* If running in background: `sudo pkill kanata` or `sudo pkill -f key_remapper`.

**Windows**

* Right-click the green 'H' icon in the system tray and select "Exit".

---

## 🔵 Remappings

The keys `,`, `.`, and `capslock` are **trigger keys**. Hold them down to access layers.

### **Core Remappings (Global)**

#### **Hold `Capslock` Layer (Symbols)**

*Double-tap CapsLock to toggle actual CapsLock.*

* `y` → `$` | `u` → `>` | `i` → `=` | `o` → `\` | `p` → `!`
* `h` → `<` | `j` → `(` | `k` → `+` | `l` → `*` | `;` → `-`
* `n` → `_` | `m` → `)` | `[` → `?`

#### **Hold `,` Layer (Symbols)**

* `q` → `~` | `w` → `.` | `e` → `,` | `r` → `&` | `t` → `^`
* `a` → `@` | `s` → `%` | `d` → `{` | `f` → `[` | `g` → `'`
* `z` → `#` | `x` → ` | `c` → `}` | `v` → `]` | `b` → `|`

#### **Hold `.` Layer (Navigation & Editing)**

* `k` → `Enter` | `i` → `Shift+Enter`
* `j` → `Backspace` | `m` → `Ctrl+Backspace`
* `n` → `Delete`
* `e` / `d` / `s` / `f` → `Up` / `Down` / `Left` / `Right`
* `w` / `r` → `Ctrl+Left` / `Ctrl+Right` (Word skip)
* `Capslock` + `f` → `Alt+Tab` | `Capslock` + `d` → `Alt+Shift+Tab`

#### **Hold `.` then hold `,` Layer (Numpad)**

*First hold down `.`, and while holding it, also hold down `,` to activate this layer.*

* `w` → `7` | `e` → `8` | `r` → `9`
* `s` → `4` | `d` → `5` | `f` → `6` | `g` → `0`
* `x` → `1` | `c` → `2` | `v` → `3`
* `a` → `,` | `z` → `.`

---

### **🖱️ Mouse Mode (Python Script Only)**

*Note: The Kanata version does not currently support mouse keys. Use the Python script if you need this.*

* **Toggle ON/OFF**: Press `.` (Dot) + `u`
* **Move**: `e` `s` `d` `f`
* **Click**: `j` (Left), `k` (Right)
* **Scroll**: Hold `m` + Move