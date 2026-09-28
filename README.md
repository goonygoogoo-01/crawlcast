# CRAWLCAST

Turn-based isometric dungeon crawler. You are a contestant on an intergalactic reality show.

Desktop builds are on the [v1.0.0 release](https://github.com/goonygoogoo-01/crawlcast/releases/tag/v1.0.0).

| Computer | File |
| --- | --- |
| Windows | crawlcast_windows.zip |
| Linux | crawlcast_linux.zip |
| macOS | crawlcast_macos.zip |

## Windows

Unzip and double-click `CRAWLCAST.exe`. This build is unsigned, so SmartScreen may say Windows protected your PC. Choose More info, then Run anyway.

## Linux

```bash
unzip crawlcast_linux.zip
chmod +x CRAWLCAST/Linux/CRAWLCAST.x86_64
./CRAWLCAST/Linux/CRAWLCAST.x86_64
```

The game uses Vulkan. If that fails to start:

```bash
./CRAWLCAST/Linux/CRAWLCAST.x86_64 --rendering-method gl_compatibility
```

## macOS

Unzip, then right-click `CRAWLCAST.app` and choose Open the first time. The build is unsigned and not notarized. It is a universal app (Apple Silicon and Intel).

## Saves

The run saves after every turn. Continue is on the title screen. Finished runs go to the Hall of Fame. Those files live in the CRAWLCAST user-data folder, not next to the program:

- Linux: `~/.local/share/godot/app_userdata/CRAWLCAST/`
- Windows: `%APPDATA%\Godot\app_userdata\CRAWLCAST\`
- macOS: `~/Library/Application Support/Godot/app_userdata/CRAWLCAST/`

This build does not include gamepad support.
