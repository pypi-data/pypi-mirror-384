# depends=("electron${_electronVersion}" "nodejs>20" "libvips")
# optdepends=('libappindicator-gtk3: for tray icon')
# arch=('x86_64')
# makedepends=('npm' 'git' 'rsync' 'python-setuptools' 'libxcrypt-compat')

export def main [] {
  # TODO hard-coded path
  let install_dir = ($env.HOME | path join "software/joplin")

  let workdir = "/tmp/joplin-install"
  rm -rf $workdir
  mkdir $workdir
  cd $workdir

  curl -sSL https://raw.githubusercontent.com/laurent22/joplin/dev/Joplin_install_and_update.sh -o install.sh
  sh install.sh $"--install-dir=($install_dir)"

  cd /
  rm -rf $workdir

  # rm -rf $install_dir
  # mkdir $install_dir
  # cd $install_dir
  #
  # # ╭────┬────────╮
  # # │  0 │ 3.5.4  │
  # # │  1 │ 3.4.12 │
  # # ...
  # let latest_release = (
  #   curl -sSL https://api.github.com/repos/laurent22/joplin/releases |
  #   from json |
  #   each { update name { ($in | str replace "v" "") } } |
  #   sort-by --custom {|a, b| compare-versions $a.name $b.name } |
  #   get 0
  # )
  #
  # let assets = $latest_release | get assets | select browser_download_url name digest
  # mut asset = null
  # if (uname | get kernel-name) == "Linux" {
  #   $asset = $assets | where name =~ '\.AppImage$' | get 0
  # } else {
  #   error make {msg: $"Not implemented yet for Kernel (uname | get kernel-name)" } 
  # }
  #
  # curl -sSL $asset.browser_download_url -o Joplin.AppImage
  # chmod +x Joplin.AppImage
  #

}

# def compare-versions [version_a: string, version_b: string] {
#   let parts_a = $version_a | split row --regex '\.'
#   let parts_b = $version_b | split row --regex '\.'
#   let comparison = $parts_a | zip $parts_b
#   for $it in $comparison {
#     if ($it | into int | get 0) > ($it | into int | get 1) {
#       return true
#     } else if ($it | into int | get 0) < ($it | into int | get 1) {
#       return false
#     }
#   }
#   true
# }
