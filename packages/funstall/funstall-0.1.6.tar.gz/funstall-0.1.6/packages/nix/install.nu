export def main [] {
  if not (which nix | is-empty) {
    print "already installed: nix"
    return
  }

  # Determinate installer is better than the official one:
  # https://github.com/DeterminateSystems/nix-installer
  curl -fsSL https://install.determinate.systems/nix | sh -s -- install --determinate --no-confirm
}
