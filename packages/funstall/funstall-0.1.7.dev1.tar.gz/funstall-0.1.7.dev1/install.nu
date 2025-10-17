# Parameters (optional):
# --pyenv-root: Path to the directory in which pyenv should install Python
#   versions. If not passed, pyenv will use it's default.
# --install-dir: Directory in which funstall will be installed.
# --reinstall: If passed, the installer will remove an existing installation
#   and reinstall it. Otherwise, an existing installation will lead to the
#   script failing.
export def main [
  --pyenv-root: string
  --install-dir: string = "/opt/funstall"
  --reinstall
] {
  if (which funstall | is-not-empty) and not $reinstall {
    error make { msg: "funstall is already installed and --reinstall was not passed" }
  }

  # TODO reinstall does not remove the old installation if the install_dir has
  # changed

  if (which pyenv | is-empty) {
    install-pyenv
  }

  let python_version = (
    curl
      --silent
      --show-error
      --location
      https://raw.githubusercontent.com/hbibel/funstall/refs/heads/main/.python-version |
    collect
  )

  if ($pyenv_root | is-not-empty) {
    $env.PYENV_ROOT = $pyenv_root
  }
  pyenv install --skip-existing $python_version | complete

  let versions_dir = if ($pyenv_root | is-not-empty) {
    $pyenv_root | path join "versions"
  } else {
    $env.HOME | path join ".pyenv/versions"
  }
  let python_dir = ls $versions_dir | where name =~ $'.*($python_version)' | last | get name
  let python_bin = ($python_dir | path join $"bin/python($python_version)")

  ^$python_bin -m pip install --upgrade pip

  rm -rf $install_dir
  ^$python_bin -m venv $install_dir
  ^($install_dir | path join "bin/pip") install funstall

  ln -s ($install_dir | path join "bin/funstall") ($env.HOME | path join ".local/bin/funstall")
}

def install-pyenv [] {
  # For Python build dependencies see
  # https://github.com/pyenv/pyenv/wiki#suggested-build-environment
  if (uname | get kernel-name) == "Darwin" {
    brew update
    brew install pyenv
    # To build Python
    brew install openssl readline sqlite3 xz tcl-tk libb2 zstd zlib pkgconfig
  } else if (uname | get kernel-name) == "Linux" {
    if (uname | get kernel-release | str contains "arch") {
      sudo pacman -S --noconfirm pyenv
      # To build Python
      sudo pacman -S --noconfirm --needed base-devel openssl zlib xz tk zstd
    } else {
      error make {msg: $"Not implemented yet for distribution (uname | get kernel-release)" } 
    }
  } else {
    error make {msg: $"Not implemented yet for Kernel (uname | get kernel-name)" } 
  }
}
