# Funstall

This is my own custom software installer (well, mostly it's a wrapper around
other package managers) that keeps my Linux and Mac machines up-to-date.

## Usage

**NOTE** Since this tool currently requires
[pyenv](https://github.com/pyenv/pyenv) it does not run on Windows.

### Installation

**NOTE** This tool uses [pyenv](https://github.com/pyenv/pyenv) to install
itself and other software that runs on Python.
The installer will install pyenv if it is not available.

```nu
(
  ^curl
    --silent
    --show-error
    --location
    https://raw.githubusercontent.com/hbibel/funstall/refs/heads/main/install.nu
    -o /tmp/install-funstall.nu
)
nu /tmp/install-funstall.nu  # Add flags as required
rm /tmp/install-funstall.nu
```

A link to the executable will be placed at `~/.local/bin`. Make sure this is
on your `PATH`.

### Invokation

Run `funstall --help` or `funstall <COMMAND> --help` for usage instructions.

When software running on Node.js is installed, funstall will use
[fnm](https://github.com/Schniz/fnm) to install a suitable Node.js version.
If fnm is not installed or not on the `PATH`, funstall will install it.

## Why?

I use multiple operating systems on multiple machines, requiring me to switch
between package managers (mainly pacman and brew).
My goal is to have a consistent, personal workflow no matter which machine I
use, so I need a wrapper around platform-specific package managers.

As a side note, I also don't agree with how some AUR packages are implemented,
so I'm hesitant to use `yay` on Arch.
Implementing my own installation scripts based on AUR implementations also
makes me feel safer from supply-chain attacks.

## About Sources

Funstall can pull packages using various other tools, e.g. pip or brew, which
are called "sources".
Generally the source closest to the original developer's control is selected,
e.g. PyPI or NPM are usually more directly managed by the developers, and thus
tend to be more up-to-date.
The preferred order of sources is implemented in
`funstall/installation/source_priorities.py`.

## Implementation Considerations

Initially I planned to implement this in nushell within my dotfiles.
However I started to feel uneasy with the rather simplistic typing system in
nushell as data models surpassed a certain level of complexity.
Therefore I decided to reach for another programming language.

I started this project using Python because I want to avoid writing a GitHub
action for now to distribute this project across my computers.
While I quickly realized that I cannot easily get around a build step I stuck
with Python because I'm most productive with it.
Generally I prefer compiled languages for CLI applications though so I may
**rewrite in Rust™** in the future (or in another language).

## Development

Publish a new version:

First create a PyPI API key with access to the repository.
Then save it in `.pypi-token.secret`.

```sh
uv build
uv publish --token $(cat .pypi-token.secret)
```
