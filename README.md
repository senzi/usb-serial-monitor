# USB Serial Monitor

一个用于Windows系统的USB串口监视工具，可以实时显示USB-to-Serial设备的COM端口信息。

## 功能特点

- 实时监控USB串口设备的插拔
- 显示设备的COM端口号、VID、PID等信息
- 支持通过PuTTY快速连接到选定的串口
- 支持自定义串口连接参数
- 系统托盘运行，占用资源少

## 系统要求

- Windows 7/8/10/11
- Python 3.6+

## 安装使用

1. 从Release下载编译好的可执行文件
2. 直接运行USBMonitor.exe

## 从源码构建

1. 克隆仓库：
```bash
git clone [repository-url]
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 构建可执行文件：
```bash
python build.py
```

编译后的文件将在`dist`目录中生成。

## 许可证

本项目基于MIT许可证开源。
