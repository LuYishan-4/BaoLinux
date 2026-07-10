# BaoLinux

BaoLinux is a Live ISO automated build system extended and customized from `archiso`, the official Arch Linux tool. This project simplifies the `airootfs` configuration workflow and integrates environment initialization with global settings management, allowing users to rapidly build custom Linux distributions packaged with specific packages and configurations.

## Project Background & Features

The core architecture of this project is fully derived from the Arch Linux `archiso` toolchain. `archiso` is the official tool used by Arch to generate the monthly Live ISO images. Its fundamental principle relies on using predefined package lists and `airootfs` (a custom root filesystem overlay) to install and package the system within an isolated environment.

BaoLinux extends this foundation to offer the following key advantages:
* **Workflow Automation:** Simplifies tedious environment setup and permission configurations via scripts.
* **Global Configuration Management:** Provides a unified configuration tool to prevent omissions caused by manually modifying multiple config files.
* **Automatic Path Correction:** Pre-checks and resolves common errors related to `chroot` and relative paths.

---

## System Requirements

Before you begin the build process, ensure your host environment meets the following prerequisites:
* **Operating System:** Arch Linux (or any Linux environment with `archiso` installed and supported)
* **Required Packages:** `archiso`, `git`, `bash`, `python3`
* **Privileges:** `sudo` (root) privileges are required for certain initialization steps

---

## Build & Usage Instructions

Please follow these steps in order to build BaoLinux:

### 1. Installation & Setup
```bash
git clone [https://github.com/LuYishan-4/BaoLinux.git](https://github.com/LuYishan-4/BaoLinux.git)
cd BaoLinux
sudo ./init
./gloablConfigManger
