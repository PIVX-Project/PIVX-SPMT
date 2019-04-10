# -*- mode: python -*-
import sys
import os
import os.path
import simplejson as json

os_type = sys.platform
block_cipher = None
base_dir = os.path.dirname(os.path.realpath('__file__'))

# look for version string
version_str = ''
with open(os.path.join(base_dir, 'src', 'version.txt')) as version_file:
	version_data = json.load(version_file)
version_file.close()
version_str = version_data["number"] + version_data["tag"]

add_files = [('src/version.txt', '.'), ('img', 'img')]
lib_path = next(p for p in sys.path if 'site-packages' in p)
add_files.append( (os.path.join(lib_path, 'bitcoin/english.txt'),'bitcoin') )
add_files.append( (os.path.join(lib_path, 'trezorlib/coins.json'), 'trezorlib') )
add_files.append( (os.path.join(lib_path, 'trezorlib/transport'), 'trezorlib/transport') )

if os_type == 'darwin':
    add_files.append( ('/usr/local/lib/libusb-1.0.dylib', '.') )
elif os_type == 'win32':
    import ctypes.util
    l = ctypes.util.find_library('libusb-1.0.dll')
    if l:
       add_files.append( (l, '.') )



a = Analysis(['spmt.py'],
             pathex=[base_dir, 'src', 'src/qt'],
             binaries=[],
             datas=add_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[ 'numpy',
                        'cryptography',
                        'lib2to3',
                        'pkg_resources',
                        'distutils',
                        'Crypto',
                        'pyi_rth_qt5',
                        'pytest',
                        'scipy',
                        'pycparser',
                        'pydoc',
                        'PyQt5.QtHelp',
                        'PyQt5.QtMultimedia',
                        'PyQt5.QtNetwork',
                        'PyQt5.QtOpenGL',
                        'PyQt5.QtPrintSupport',
                        'PyQt5.QtQml',
                        'PyQt5.QtQuick',
                        'PyQt5.QtQuickWidgets',
                        'PyQt5.QtSensors',
                        'PyQt5.QtSerialPort',
                        'PyQt5.QtSql',
                        'PyQt5.QtSvg',
                        'PyQt5.QtTest',
                        'PyQt5.QtWebEngine',
                        'PyQt5.QtWebEngineCore',
                        'PyQt5.QtWebEngineWidgets',
                        'PyQt5.QtXml',
                        'win32com',
                        'xml.dom.domreg',
                        ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='SecurePivxMasternodeTool',
          debug=False,
          strip=False,
          upx=False,
          console=False,
          icon=os.path.join(base_dir, 'img', 'spmt.%s' % ('icns' if os_type=='darwin' else 'ico')) )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='app')

if os_type == 'darwin':
	app = BUNDLE(coll,
             name='SecurePivxMasternodeTool.app',
             icon=os.path.join(base_dir, 'img', 'spmt.icns'),
             bundle_identifier=None,
             info_plist={'NSHighResolutionCapable': 'True'})


# Prepare bundles
dist_path = os.path.join(base_dir, 'dist')
app_path = os.path.join(dist_path, 'app')
os.chdir(dist_path)

# Copy Readme Files
from shutil import copyfile, copytree
print('Copying README.md')
copyfile(os.path.join(base_dir, 'README.md'), 'README.md')
copytree(os.path.join(base_dir, 'docs'), 'docs')


if os_type == 'win32':
	# Copy Qt5 Platforms
	os.system('xcopy app\PyQt5\Qt\plugins\platforms app\platforms\ /i')
	os.chdir(base_dir)
	# Rename dist Dir
	dist_path_win = os.path.join(base_dir, 'SPMT-v' + version_str + '-Win64')
	os.rename(dist_path, dist_path_win)
	# Compress dist Dir
	print('Compressing Windows App Folder')
	os.system('"C:\\Program Files\\7-Zip\\7z.exe" a %s %s -mx0' % (dist_path_win + '.zip', dist_path_win))


if os_type == 'linux':
	os.chdir(base_dir)
	# Rename dist Dir
	dist_path_linux = os.path.join(base_dir, 'SPMT-v' + version_str + '-gnu_linux')
	os.rename(dist_path, dist_path_linux)
	# Compress dist Dir
	print('Compressing Linux App Folder')
	os.system('tar -zcvf %s -C %s %s' % ('SPMT-v' + version_str + '-x86_64-gnu_linux.tar.gz',
                base_dir, 'SPMT-v' + version_str + '-gnu_linux'))


if os_type == 'darwin':
    os.chdir(base_dir)
    # Rename dist Dir
    dist_path_mac = os.path.join(base_dir, 'SPMT-v' + version_str + '-MacOSX')
    os.rename(dist_path, dist_path_mac)
    # Remove 'app' folder
    print("Removin 'app' folder")
    os.chdir(dist_path_mac)
    os.system('rm -rf app')
    os.chdir(base_dir)
    # Compress dist Dir
    print('Compressing Mac App Folder')
    os.system('tar -zcvf %s -C %s %s' % ('SPMT-v' + version_str + '-MacOSX.tar.gz',
                base_dir, 'SPMT-v' + version_str + '-MacOSX'))

