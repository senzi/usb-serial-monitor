import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',
    '--name=USBMonitor',
    '--windowed',
    '--onefile',
    f'--icon={os.path.join(current_dir, "icon.png")}',
    '--add-binary=putty.exe;.',
    '--add-data=config.json;.',
    '--noconfirm',
    '--clean'
])
