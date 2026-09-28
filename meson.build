project(
  'yeet',
  version: '1.0.0',
  meson_version: '>= 0.60.0'
)

py_mod = import('python')
python = py_mod.find_installation('python3')

prefix = get_option('prefix')
bindir = prefix / get_option('bindir')
datadir = prefix / get_option('datadir')
pkgdatadir = datadir / meson.project_name()

conf_data = configuration_data()
conf_data.set('PYTHON', python.full_path())
conf_data.set('VERSION', meson.project_version())
conf_data.set('BINDIR', bindir)
conf_data.set('PKGDATADIR', pkgdatadir)

# 1. Launcher Executable
configure_file(
  input: 'bin/yeet.in',
  output: 'yeet',
  configuration: conf_data,
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x'
)

# 2. Python Package Modules
install_subdir(
  'yeet',
  install_dir: pkgdatadir
)

# 3. Static Web Overlay & Physics Engine
install_subdir(
  'overlay',
  install_dir: pkgdatadir
)

# 4. Default Asset Presets (Items & Sounds)
install_subdir(
  'assets',
  install_dir: pkgdatadir
)

# 5. FreeDesktop Desktop Entry
desktop_file = configure_file(
  input: 'data/gay.geeks.Yeet.desktop.in',
  output: 'gay.geeks.Yeet.desktop',
  configuration: conf_data,
  install: true,
  install_dir: datadir / 'applications'
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

# 6. AppStream Metainfo XML
metainfo_file = configure_file(
  input: 'data/gay.geeks.Yeet.metainfo.xml.in',
  output: 'gay.geeks.Yeet.metainfo.xml',
  configuration: conf_data,
  install: true,
  install_dir: datadir / 'metainfo'
)

appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test('Validate metainfo file', appstreamcli, args: ['validate', '--no-net', metainfo_file])
endif

# 7. Scalable & Symbolic Icons
install_data(
  'data/icons/hicolor/scalable/apps/gay.geeks.Yeet.svg',
  install_dir: datadir / 'icons/hicolor/scalable/apps'
)

install_data(
  'data/icons/hicolor/symbolic/apps/gay.geeks.Yeet-symbolic.svg',
  install_dir: datadir / 'icons/hicolor/symbolic/apps'
)

# 8. Automated Unit Test Suite
test('Qt6 application unit tests', python, args: [meson.current_source_dir() / 'tests/test_yeet_qt.py'])

# Post-install hooks
gnome = import('gnome')
gnome.post_install(
  gtk_update_icon_cache: false,
  update_desktop_database: true
)
