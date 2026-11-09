# Maintainer: cptn_cosmo <cosmo@geeks.gay>
pkgname=yeet
pkgver=1.0.0
pkgrel=1
pkgdesc="Wayland-native Qt6 / KDE 6 Twitch Integrated Throwing System (T.I.T.S.) alternative for OBS Studio"
arch=('any')
url="https://github.com/cptn-cosmo/yeet"
license=('GPL-3.0-or-later')
depends=(
    'qt6-base'
    'qt6-svg'
    'pyside6'
    'python'
    'python-aiohttp'
)
makedepends=(
    'git'
    'meson'
    'ninja'
    'desktop-file-utils'
    'appstream'
)
provides=('gay.geeks.Yeet')
conflicts=('yeet-git')
source=("$pkgname::git+$url.git#tag=v$pkgver")
sha256sums=('SKIP')

build() {
    arch-meson "$pkgname" build
    meson compile -C build
}

check() {
    meson test -C build --print-errorlogs
}

package() {
    meson install -C build --destdir "$pkgdir"
}
