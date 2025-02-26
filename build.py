import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',
    '--name=USB串口监测器',
    '--windowed',
    '--icon=icon.png',
    '--add-binary=putty.exe;.',
    '--add-data=config.json;.',
    '--noconfirm',
    '--clean',
    '--noconsole',
    '--onefile'
])
