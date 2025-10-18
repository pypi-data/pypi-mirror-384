# Pomlock - A pomodoro application for Linux

![Demo Preview](demo-preview.gif)

A Linux utility that enforces regular breaks by temporarily blocking input devices. Perfect for developers, writers, and anyone who needs help stepping away from the keyboard.

## Features

- **Flexible Timer System**: Supports multiple timer presets, including the classic Pomodoro, Ultradian Rhythm (90/20), and a 50/10 cycle. New presets can be defined in the configuration file, and a one-time custom timer can be passed as a command-line argument.
- **Input Blocking**: Disables all input devices during break periods to ensure you step away.
- **Customizable Overlay**: A full-screen display during breaks with configurable font, colors, and opacity.
- **Desktop Notifications**: Get native desktop notifications when a break starts.
- **Activity Logging**: Keeps a simple log of work and break cycles at `~/.local/share/pomlock/pomlock.log`.
- **Safe Mode**: Run the timer without input blocking using the `--no-block-input` flag.
- **Smart Configuration**: Settings are loaded in a logical order: Defaults < Config File < CLI Arguments. CLI flags always have the final say.


## Installation

### pipx
```bash
pipx install pomlock
```

### Manual Installation (for Wayland users)

If you are on a Wayland system and intend to use `pomlock`'s input blocking features, you will need to manually copy the Polkit policy files. These files grant `pomlock` the necessary permissions to interact with input devices via `libinput` and `evtest`, which require `sudo` privileges.

1.  **Copy Polkit Policy Files**:
    ```bash
    sudo cp src/polkit-actions/*.policy /usr/share/polkit-1/actions/
    ```
    This step is crucial for `pomlock` to be able to block input devices on Wayland.

2.  **Install Dependencies**: Ensure you have `libinput` and `evtest` installed on your system. These are typically available through your distribution's package manager.
    *   For Debian/Ubuntu: `sudo apt install libinput-tools evtest`
    *   For Fedora: `sudo dnf install libinput-utils evtest`
    *   For Arch Linux: `sudo pacman -S libinput evtest`

3.  **Install `pomlock` (Python package)**:
    First, ensure you have `uv` installed:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    Then, navigate to the `pomlock` project directory and install it in editable mode:
    ```bash
    uv pip install -e .
    ```
    This will install `pomlock` and all its Python dependencies.

4.  **Waybar Integration (Optional)**:
    `pomlock` comes with a Waybar script that synchronizes automatically with your pomodoro sessions. You can find it at `src/pomlock/waybar.py`.

    To use it, copy the script to your Waybar scripts directory (e.g., `~/.config/waybar/scripts/`) and configure your Waybar `config` file.

    **Example Waybar Configuration**:
    ```json
    "custom/pomodoro": {
        "exec": "/path/to/your/waybar.py",
        "interval": 1,
        "return-type": "json",
        "on-click": "/path/to/your/waybar.py left",
        "on-click-right": "/path/to/your/waybar.py right"
    }
    ```
    Remember to replace `/path/to/your/waybar.py` with the actual path where you copied the script.

<!-- ### Arch Linux (AUR) -->
<!-- ```bash -->
<!-- yay -S pomlock -->
<!-- ``` -->
<!-- ```bash -->
<!-- paru -S pomlock -->
<!-- ``` -->
<!---->
<!-- ### Manual -->
<!---->
<!-- <!-- TODO: some ideas -->
<!-- options: -->
<!-- 1. curl command:  -->
<!-- [uv package manager](https://github.com/astral-sh/uv?tab=readme-ov-file#installation) -->
<!-- ```bash -->
<!-- curl -LsSf https://astral.sh/uv/install.sh | sh   -->
<!-- ``` -->
<!-- [yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/Installation#installing-the-release-binary) -->
<!-- ```bash -->
<!-- curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o ~/.local/bin/yt-dlp -->
<!-- chmod a+rx ~/.local/bin/yt-dlp  # Make executable -->
<!-- ``` -->
<!---->
<!-- 2. pip -->
<!-- [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation) -->
<!-- ```bash -->
<!-- # With pip. -->
<!-- pip install uv -->
<!-- ``` -->
<!-- [yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/Installation#with-pip) -->
<!-- ```bash -->
<!-- python3 -m pip install -U "yt-dlp[default]" -->
<!-- ``` -->
<!---->
<!-- 3. pacman -->
<!-- [yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/Installation#pacman) -->
<!-- ```bash -->
<!-- sudo pacman -Syu yt-dlp -->
<!-- ``` -->


## Usage

```bash
# Start with the default 'standard' preset (25min work, 5min break)
pomlock

# Use the 'ultradian' preset for a long deep-work session (90min work, 20min break)
pomlock --timer ultradian

# Use the 'fifty_ten' preset for a 50/10 work-break cycle.
pomlock --timer fifty_ten

# Set a custom timer: 45min work, 15min short break, 30min long break after 3 cycles
pomlock --timer "45 15 30 3"

# Set a custom overlay text color for the session
pomlock --overlay-color "lime"

# Run without blocking input devices
pomlock --no-block-input
```

## Integrations

`pomlock` can be integrated with other tools like status bars (Waybar, Polybar, etc.) in two ways:

### Polling

On startup, `pomlock` creates a state file at `/tmp/pomlock.json`. This file contains the current timer information, including the action (pomodoro, short_break, long_break), duration, and start time.

You can write a script to poll this JSON file every second to create a custom status bar component. The file is automatically deleted when `pomlock` exits.

**Example State File Content:**
```json
{
    "action": "pomodoro",
    "time": 1,
    "start_time": 1756677567.9689746,
    "crr-cycle": 1,
    "total-cycles": 4,
    "crr-session": 1
}
```

### Callback

For event-driven integrations, you can use the `--callback` flag to execute a script whenever a pomodoro or break begins. `pomlock` will pass a JSON string with the timer data as the last argument to your script.

```bash
pomlock --callback /path/to/your/script.sh
```

Your script will be executed silently in the background to avoid disrupting the main `pomlock` terminal UI.

## Configuration

You can create a custom configuration file at `~/.config/pomlock/pomlock.conf` to override the default settings. CLI arguments will always override settings from this file.

Here is an example configuration showing all available options:
```ini
# ~/.config/pomlock/pomlock.conf

[pomodoro]
# These values define the timer components when not using a preset.
# timer = 30 5 15 4
pomodoro = 30
short_break = 5
long_break = 15
cycles_before_long = 4
block_input = true

[overlay]
# Customize the appearance of the break screen.
font_size = 64
color = red
bg_color = white
opacity = 0.5
notify = false
# notify_message = Time for a break!

[presets]
# Define your own custom timer presets.
# Format: "WORK SHORT_BREAK LONG_BREAK CYCLES"
standard = 25 5 20 4
ultradian = 90 20 20 1
fifty_ten = 50 10 10 1
```

## Log File

**Location**: `~/.local/share/pomlock/pomlock.log`

**Example Log Output**:
```log
2023-10-27 10:00:00 - INFO - Pomodoro started (25 minutes).
2023-10-27 10:25:00 - INFO - Pomodoro completed (Duration: 25m) (Cycle: 1)
2023-10-27 10:25:00 - INFO - Short break started (Duration: 5m) (Cycle: 1)
2023-10-27 10:30:00 - INFO - Break completed (Cycle: 1)
```

## Safety

- **Automatic Restoration**: Input devices are automatically re-enabled when the program exits cleanly or is interrupted (Ctrl+C).
- **Non-Blocking Mode**: Use `--no-block-input` for safe, non-blocking monitoring.
- **Force Quit**: If the application becomes unresponsive, you can force it to close and restore input by running:
  ```bash
  pkill -f pomlock.py
  ```
