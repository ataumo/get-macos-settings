# `get-macos-settings` - A Tool to Track and Compare macOS Configuration Changes

[![License](https://img.shields.io/github/license/ataumo/get-macos-settings)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/ataumo/get-macos-settings)](https://github.com/ataumo/get-macos-settings/stargazers)

Easily track and compare macOS configuration changes!  
This tool helps developers, system admins, and macOS power users extract key system settings, allowing them to track, save, and compare macOS configurations for better control, reproducibility, and system optimization.

## Overview

`get-macos-settings` is a powerful Python utility designed to:
- Retrieve and record system domain and key modifications made to macOS preferences.
- Compare two different system configurations to highlight what’s changed.
- Leverage system utilities like `defaults` and `PlistBuddy` to apply or manage macOS settings programmatically.

---

## Features

- **Snapshot macOS Configurations**: Capture macOS domain configurations for later reference.
- **Compare Configurations**: Identify differences between two system configurations, making it ideal for system audits or migrations.
- **Verbose Logging**: Enable detailed output for thorough debugging and tracking of changes.
- **All Domains**: Record settings across all macOS domains, or focus on specific common domains.
- **Config Export**: Save your configuration data for easy version control or sharing across systems.

## Use Cases

- **System Auditing**: Ensure no undesired changes occur after system updates or software installations.
- **System Hardening**: Easily identify and track security-related settings before and after applying hardening scripts like [HardeningPuppy](https://github.com/ataumo/macos_hardening).
  - Details : This tool could be used to identify precisely what the differences between two macOS configurations (on the same hardware), after editing configuration for example, and then, apply this configuration with `defaults` or `PlistBuddy` commands, or automatically with [HardeningPuppy](https://github.com/ataumo/macos_hardening) script.

---

## Installation

Before using the tool, it's recommended to create a dedicated Python virtual environment to avoid dependency conflicts.

```bash
python3.12 -m venv myenv
source myenv/bin/activate
```

This project requires the pbPlist package, which has been modified for compatibility with newer versions of Python:
```diff
# File: myenv/lib/python3.12/site-packages/pbPlist/pbRoot.py
+ from collections.abc import MutableMapping

- class pbRoot(collections.MutableMapping):
+ class pbRoot(MutableMapping):
```

---

## Usage

The script provides several options to snapshot, record, or compare macOS settings. Below is a breakdown of available commands and options:

```
get-setting.py [-h] [-r] [-a] [-s] [-v] [-d old-config-directory new-config-directory]

Does a thing to some stuff.

optional arguments:
  -h, --help            show this help message and exit
  -r, --record          to record a modification in files settings
  -a, --allDomains      to record a modification in files settings from all domains
  -s, --snapshot        to take a snapshot of a current configuration
  -v, --verbose         to enable a verbose mode
  -d old-config-directory new-config-directory, --diff old-config-directory new-config-directory
                        to compare 2 configurations (they mys be already saved in directory)
```

---

## Examples 

1. Scan Current Configuration
To capture a snapshot of common macOS domains (like NSGlobalDomain, com.apple.finder, com.apple.Safari):
```bash
./get-setting.py -s
```
> The common domains are ['NSGlobalDomain', 'com.apple.systempreferences', 'com.apple.finder', 'com.apple.desktopservices', 'com.apple.Safari', 'com.apple.AppleMultitouchTrackpad', 'com.apple.dock', 'com.apple.universalaccess']
> All settings domains are captured in `/tmp/config-<timestamp>` directory.

2. Capture Settings Across All Domains
```bash
./get-setting.py -sa
```
> All domains are retreive with `defaults domains` command.


3. Compare Two Configurations
To compare settings between two previously saved configurations:
```bash
./get-setting.py -d /tmp/config-220924-211341 /tmp/config-220924-212359
```

![title](output-example.png)

---

## Sources & Reference Material

The tool is inspired by and built upon concepts and examples from the following projects:

- [macos-defaults by yannbertrand](https://github.com/yannbertrand/macos-defaults)
- [macOS-Defaults by kevinSuttle](https://github.com/kevinSuttle/macOS-Defaults/blob/master/REFERENCE.md)

---

## Contribution Guidelines

We welcome contributions! Feel free to explore the [TODO.md](TODO.md) file for ideas on what could be improved or added. Submit a pull request or raise an issue for any bugs or features you would like to see.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.