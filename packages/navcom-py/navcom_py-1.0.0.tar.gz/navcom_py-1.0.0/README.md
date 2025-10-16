# navcom - Navigate Git Commits

A simple bash script to navigate through git repository commits chronologically, perfect for studying a codebase's evolution.

![Demo](demo.gif)

## What It Does

- Lets you step through commits in chronological order (oldest to newest)
- Jump to first commit with `first`, navigate forward with `next`, or backward with `prev`
- Automatically tracks your progress
- Shows commit details at each step

## Installation

### MacOS/Linux

```bash
make install
```

This installs the script as `navcom` in `/usr/local/bin`.

### Manual Installation

```bash
sudo cp bin /usr/local/bin/navcom
sudo chmod +x /usr/local/bin/navcom
```

## Usage

Navigate to any git repository and run:

```bash
# Jump to first commit
navcom first

# Move to next commit (chronologically)
navcom next

# Move to previous commit
navcom prev
```

On first run, it will initialize by scanning the repository's commit history.

## How It Works

1. **First Run**: Creates a chronological list of all commits in the default branch
2. **Navigation**: Checks out commits in order and tracks your position
3. **Progress**: Stores tracking data in `.git/nc-progress` and `.git/nc-commits`

## Reset Progress

To start over from the beginning:

```bash

rm .git/nc-progress .git/nc-commits
```

## Uninstall

```bash
make uninstall
```
