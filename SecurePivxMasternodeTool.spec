# -*- mode: python -*-
import sys
import os
import os.path
import simplejson as json

os_type = sys.platform
block_cipher = None
base_dir = os.path.dirname(os.path.realpath('__file__'))

# look for version string
with open(os.path.join(base_dir, 'src', 'version.txt')) as version_file:
	version_data = json.load(version_file)
version_file.close()
version_str = version_data["number"]

add_files = [('src/masternodes.json', '.'), ('src/rpcServer.json', '.'), ('src/version.txt', '.'), ('img', 'img')]

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
          upx=True,
          console=False )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='secure_pivx_masternode_tool')

app = BUNDLE(coll,
             name='SecurePivxMasternodeTool%s' % ('.app' if os_type=='darwin' else ''),
             icon=os.path.join(base_dir, 'img', 'spmt.%s' % ('icns' if os_type=='darwin' else 'ico')),
             bundle_identifier=None)