import PyInstaller.__main__
import os
import shutil

# Hapus folder build dan dist jika ada
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

# Hapus file spec jika ada
if os.path.exists('PDF Compressor.spec'):
    os.remove('PDF Compressor.spec')

# Set correct working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

icon_path = os.path.abspath('src/icon.ico')
PyInstaller.__main__.run([
    'src/smart_compressor_gui.py',
    '--name=PDF Compressor',
    '--windowed',
    f'--icon={icon_path}',
    f'--add-data={icon_path};.',
    '--clean',
    '--onefile',
    '--noconfirm',
    '--distpath=dist',
    '--workpath=build',
    '--debug=all'
])