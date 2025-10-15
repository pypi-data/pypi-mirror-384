pkgname=tuxmake
pkgver=1.34.0
pkgrel=1
pkgdesc='Thin wrapper to build Linux kernels'
url='https://tuxmake.org/'
license=('MIT')
arch=('any')
depends=('perl' 'python')
makedepends=('git' 'python-build' 'python-docutils' 'python-flit' 'python-installer' 'python-wheel')
checkdepends=('clang' 'git' 'lld' 'llvm' 'python-pytest' 'python-pytest-mock')
optdepends=('docker: Container-based build support'
            'podman: Container-based build support'
            'socat: Offline build support')
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$pkgname-$pkgver"

  make man
  make bash_completion

  python -m build --wheel --no-isolation
}

check() {
  cd "$pkgname-$pkgver"

  PYTHONDONTWRITEBYTECODE=1 pytest
}

package() {
  cd "$pkgname-$pkgver"

  python -m installer --destdir="$pkgdir" dist/*.whl

  install -Dvm644 tuxmake.1 -t "$pkgdir"/usr/share/man/man1
  install -Dvm644 bash_completion/tuxmake -t "$pkgdir"/usr/share/bash-completion/completions
  install -Dvm644 LICENSE -t "$pkgdir/usr/share/licenses/$pkgname"
}
