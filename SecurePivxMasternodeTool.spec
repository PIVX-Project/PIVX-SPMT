# -*- mode: python -*-
import sys
import platform
import os.path as os_path
import simplejson as json
import subprocess

os_type = sys.platform
block_cipher = None
base_dir = os_path.dirname(os_path.realpath('__file__'))

def libModule(module, source, dest):
    m = __import__(module)
    module_path = os_path.dirname(m.__file__)
    del m
    print(f"libModule {(os_path.join(module_path, source), dest)}")
    return ( os_path.join(module_path, source), dest )

def is_tool(prog):
    for dir in os.environ['PATH'].split(os.pathsep):
        if os.path.exists(os.path.join(dir, prog)):
            try:
                subprocess.call([os.path.join(dir, prog)],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
            except(OSError, e):
                return False
            return True
    return False

# Set this to True if codesigning macOS bundles. Requires an Apple issued developer ID certificate.
code_sign = False
codesigner = 'fuzzbawls@pivx.org'

# detect CPU architecture
cpu_arch = platform.processor()
if os_type == 'darwin':
    if cpu_arch == 'arm': cpu_arch = 'arm64'
    if cpu_arch == 'i386': cpu_arch = 'x86_64'

# look for version string
version_str = ''
with open(os_path.join(base_dir, 'src', 'version.txt')) as version_file:
    version_data = json.load(version_file)
version_file.close()
version_str = version_data["number"] + version_data["tag"]

add_files = [('src/version.txt', '.'), ('img', 'img')]
add_files.append( libModule('bitcoin', 'english.txt','bitcoin') )
add_files.append( libModule('trezorlib', 'coins.json', 'trezorlib') )
add_files.append( libModule('trezorlib', 'transport', 'trezorlib/transport') )

if os_type == 'win32':
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
          a.binaries,
          a.zipfiles,
          a.datas,
          a.scripts,
          #exclude_binaries=True,
          name='SecurePivxMasternodeTool',
          debug=False,
          strip=False,
          upx=False,
          console=False,
          target_arch=f'{cpu_arch}',
          entitlements_file='contrib/macdeploy/entitlements.plist',
          codesign_identity=f'{codesigner if code_sign == True else ""}',
          icon = os_path.join(base_dir, 'img', f'spmt.{"icns" if os_type == "darwin" else "ico"}'))

if os_type == 'darwin':
    app = BUNDLE(exe,
             name='SecurePivxMasternodeTool.app',
             icon=os_path.join(base_dir, 'img', 'spmt.icns'),
             bundle_identifier='io.pivx.spmt',
             info_plist={
                'NSHighResolutionCapable': 'True',
                'CFBundleVersion': version_str,
                'CFBundleShortVersionString': version_str,
                'NSPrincipalClass': 'NSApplication',
                'LSApplicationCategoryType': 'public.app-category.finance'
             })


# Prepare bundles
dist_path = os_path.join(base_dir, 'dist')
app_path = os_path.join(dist_path, 'app')
os.chdir(dist_path)

# Copy Readme Files
#from shutil import copyfile, copytree
#print('Copying README.md')
#copyfile(os_path.join(base_dir, 'README.md'), 'README.md')
#copytree(os_path.join(base_dir, 'docs'), 'docs')

if os_type == 'win32':
    os.chdir(base_dir)
    # Rename dist Dir
    dist_path_win = os_path.join(base_dir, f'SPMT-v{version_str}-Win64')
    os.rename(dist_path, dist_path_win)
    # Check for NSIS
    prog_path = os.environ["ProgramFiles(x86)"]
    nsis_bin = os_path.join(prog_path, "NSIS", "makensis.exe")
    if os_path.exists(nsis_bin):
      # Create NSIS compressed installer
      print('Creating Windows installer')
      os.system(f'"{nsis_bin}" {os_path.join(base_dir, "setup.nsi")}')
    else:
      print('NSIS not found, cannot build windows installer.')


if os_type == 'linux':
    os.chdir(base_dir)
    # Rename dist Dir
    dist_path_linux = os_path.join(base_dir, f'SPMT-v{version_str}-{cpu_arch}-gnu_linux')
    os.rename(dist_path, dist_path_linux)
    # Compress dist Dir
    print('Compressing Linux App Folder')
    os.system(f'tar -zcvf SPMT-v{version_str}-{cpu_arch}-gnu_linux.tar.gz -C {base_dir} SPMT-v{version_str}-{cpu_arch}-gnu_linux')


if os_type == 'darwin':
    os.chdir(base_dir)
    # Rename dist Dir
    dist_path_mac = os_path.join(base_dir, f'SPMT-v{version_str}-{cpu_arch}-MacOS')
    os.rename(dist_path, dist_path_mac)
    # Remove 'app' folder
    print("Removing 'app' folder")
    os.chdir(dist_path_mac)
    os.system('rm -rf app')
    os.chdir(base_dir)
    # Compress dist Dir
    print('Compressing Mac App Folder')
    os.system(f'tar -zcvf SPMT-v{version_str}-{cpu_arch}-MacOS.tar.gz -C {base_dir} SPMT-v{version_str}-{cpu_arch}-MacOS')

    # dmg image creation uses the node.js appdmg package
    if is_tool("appdmg"):
        # Prepare dmg
        print("Preparing distribution dmg installer")
        os.chdir(dist_path_mac)
        with open(os_path.join(base_dir, 'contrib/macdeploy', 'appdmg.json.in')) as conf:
            confdata = conf.read()
        confdata = confdata.replace('%version%', version_str)
        confdata = confdata.replace('%signer%', f'{codesigner if code_sign == True else ""}')
        with open('appdmg.json', 'w') as newconf:
            newconf.write(confdata)

        os.system(f'sed \"s/PACKAGE_NAME/SPMT {version_str}/\" < \"../contrib/macdeploy/background.svg\" | rsvg-convert -f png -d 72 -p 72 | convert - background.tiff@2x.png')
        os.system('convert background.tiff@2x.png -resize 500x320 background.tiff.png')
        os.system('tiffutil -cathidpicheck background.tiff.png background.tiff@2x.png -out background.tiff')
        os.remove('background.tiff.png')
        os.system(f'appdmg appdmg.json ../SPMT-v{version_str}-{cpu_arch}-MacOS.dmg')
        os.remove('background.tiff@2x.png')
    else:
        print("appdmg not found, skipping DMG creation")
