# Maintainer: Yeet Contributors <geeks@example.com>
pkgname=yeet
pkgver=1.0.0
pkgrel=1
pkgdesc="Wayland-native Twitch Integrated Throwing System (T.I.T.S.) alternative for OBS Studio"
arch=('any')
url="https://github.com/geeks/yeet"
license=('GPL-3.0-or-later')
depends=(
    'gtk4'
    'libadwaita'
    'python'
    'python-gobject'
    'python-cairo'
    'python-aiohttp'
)
makedepends=(
    'meson'
    'ninja'
    'desktop-file-utils'
    'appstream'
)
provides=('yeet' 'gay.geeks.Yeet')
conflicts=('yeet-git')
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    arch-meson "$pkgname-$pkgver" build
    meson compile -C build
}

check() {
    meson test -C build --print-errorlogs
}

package() {
    meson install -C build --destdir "$pkgdir"
}
