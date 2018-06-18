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
if os_type == 'win32':
    qt5_path = os.path.join(lib_path, 'PyQt5\\Qt\\bin')
    sys.path.append(qt5_path)
    # add file vcruntime140.dll manually, due to not including by pyinstaller
    found = False
    for p in os.environ["PATH"].split(os.pathsep):
        file_name = os.path.join(p, "vcruntime140.dll")
        if os.path.exists(file_name):
            found = True
            add_files.append((file_name, ''))
            print('Adding file ' + file_name)
            break
    if not found:
        raise Exception('File vcruntime140.dll not found in the system path.')

	
# add bitcoin library data file
add_files.append( (os.path.join(lib_path, 'bitcoin/english.txt'),'bitcoin') )
	
a = Analysis(['spmt.py'],
             pathex=[base_dir, 'src', 'src/qt'],
             binaries=[],
             datas=add_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
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
from shutil import copyfile
print('Copying README.md')
copyfile(os.path.join(base_dir, 'README.md'), 'README.md')


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

    
