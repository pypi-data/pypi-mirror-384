# Credit: https://aur.archlinux.org/packages/microsoft-edge-stable-bin

const BASE_DL_URL = "https://packages.microsoft.com/yumrepos/edge/Packages/m/"
const LAUNCH_SCRIPT = "microsoft-edge-stable"

export def main [] {
  print "Installing Edge ..."

  print "Installing dependencies"
  pacman -S --noconfirm --quiet 'gtk3' 'libcups' 'nss' 'alsa-lib' 'libxtst' 'libdrm' 'mesa'

  print "Finding latest version ..."
  let latest = (
    curl -sSL $BASE_DL_URL |
    lines |
    where { $in =~ microsoft-edge } |
    parse --regex '.*<a href="(?<ref>[^"]+)">microsoft-edge-stable-(?<version>.*).x86_64.rpm' |
    sort-by --custom {|a, b| compare-versions $a.version $b.version } |
    get 0
  )

  if ($env.HOME | path join ".config/microsoft-edge/Last Version" | path exists) {
    let current_version = cat ($env.HOME | path join ".config/microsoft-edge/Last Version")
    print $"Installed version: ($current_version), latest available version is ($latest.version)"
    if (compare-versions $current_version $latest.version) {
      print "Latest version is already installed"
      return
    }
  }

  let workdir = mktemp -d
  cd $workdir
  print $"Created working directory: ($workdir)"

  print $"Downloading version ($latest.version) ..."
  curl -sSL -o edge.rpm ($BASE_DL_URL + $latest.ref)

  print "Unpacking ..."
  bsdtar xf "edge.rpm"

  print "Copying files ..."
  ^cp --parents -a opt /
  ^cp --parents -a usr /
  chmod 4755 /opt/microsoft/msedge/msedge-sandbox

  for $res in [16 24 32 48 64 128 256] {
    (
      ^install -Dm644
      $"opt/microsoft/msedge/product_logo_($res).png"
      $"/usr/share/icons/hicolor/($res)x($res)/apps/microsoft-edge.png"
    )
  }

  curl -sSL -O $"https://raw.githubusercontent.com/hbibel/funstall/refs/heads/main/packages/edge/($LAUNCH_SCRIPT)"
  ^install -m755 $LAUNCH_SCRIPT /usr/bin/

  rm /opt/microsoft/msedge/product_logo_*.png

  cd /

  print "Edge was successfully installed"
  rm -rf $workdir
}

def compare-versions [version_a: string, version_b: string] {
  let parts_a = $version_a | split row --regex '\.|-'
  let parts_b = $version_b | split row --regex '\.|-'
  let comparison = $parts_a | zip $parts_b
  for $it in $comparison {
    if ($it | into int | get 0) > ($it | into int | get 1) {
      return true
    } else if ($it | into int | get 0) < ($it | into int | get 1) {
      return false
    }
  }
  true
}
