import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import serial.tools.list_ports
import threading
import time
from datetime import datetime
import json
import os
import sys
import subprocess
import tempfile
import atexit

def get_putty_path():
    """获取putty可执行文件的路径"""
    try:
        # 如果是打包后的环境
        if getattr(sys, 'frozen', False):
            # 创建临时目录
            temp_dir = tempfile.gettempdir()
            putty_path = os.path.join(temp_dir, 'putty.exe')
            
            # 如果临时目录中没有putty，就从打包的资源中提取
            if not os.path.exists(putty_path):
                # 从打包的资源中复制putty到临时目录
                with open(os.path.join(sys._MEIPASS, 'putty.exe'), 'rb') as f:
                    putty_data = f.read()
                with open(putty_path, 'wb') as f:
                    f.write(putty_data)
            
            # 注册程序退出时删除临时文件
            atexit.register(lambda: os.remove(putty_path) if os.path.exists(putty_path) else None)
            
            return putty_path
        else:
            # 开发环境直接使用当前目录的putty
            return os.path.join(os.path.dirname(__file__), 'putty.exe')
    except Exception as e:
        print(f"Error extracting putty: {e}")
        return 'putty.exe'  # fallback到默认值

class SerialConfig:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("串口配置")
        self.window.geometry("300x450")  # 增加高度
        self.window.transient(parent)
        
        # 创建主frame来容纳所有控件
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建一个框架来包含串口参数
        param_frame = ttk.LabelFrame(main_frame, text="串口参数", padding="10")
        param_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 串口参数
        self.create_param_widgets(param_frame)
        
        # Putty设置框架
        putty_frame = ttk.LabelFrame(main_frame, text="Putty设置", padding="10")
        putty_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Putty路径配置
        ttk.Label(putty_frame, text="程序路径:").pack(anchor=tk.W)
        self.putty_path = ttk.Entry(putty_frame)
        self.putty_path.pack(fill=tk.X, pady=(2, 0))
        self.putty_path.insert(0, get_putty_path())
        
        # 底部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 保存和取消按钮
        ttk.Button(
            button_frame, 
            text="保存配置", 
            command=self.save_config,
            style="Accent.TButton"  # 可选：突出显示保存按钮
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="取消", 
            command=self.window.destroy
        ).pack(side=tk.RIGHT)
        
        # 加载配置
        self.load_config()
        
        # 设置窗口大小固定
        self.window.resizable(False, False)
        
        # 设置模态窗口
        self.window.grab_set()
        
    def create_param_widgets(self, parent):
        # 使用网格布局来排列参数
        params = [
            ("波特率:", [
                "1200", "2400", "4800", "9600", "19200", "38400", 
                "57600", "115200", "230400", "460800", "921600"
            ], "115200"),
            ("数据位:", ["5", "6", "7", "8"], "8"),
            ("停止位:", ["1", "1.5", "2"], "1"),
            ("校验位:", ["NONE", "EVEN", "ODD", "MARK", "SPACE"], "NONE"),
            ("流控制:", ["NONE", "XON/XOFF", "RTS/CTS", "DSR/DTR"], "NONE")
        ]
        
        self.param_widgets = {}
        for i, (label, values, default) in enumerate(params):
            ttk.Label(parent, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            combo = ttk.Combobox(parent, values=values, width=25)
            combo.set(default)
            combo.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            self.param_widgets[label] = combo
    
    def save_config(self):
        config = {
            "baudrate": self.param_widgets["波特率:"].get(),
            "data_bits": self.param_widgets["数据位:"].get(),
            "stop_bits": self.param_widgets["停止位:"].get(),
            "parity": self.param_widgets["校验位:"].get(),
            "flow_control": self.param_widgets["流控制:"].get(),
            "putty_path": self.putty_path.get()
        }
        
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        messagebox.showinfo("提示", "配置已保存")
        self.window.destroy()
        
    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                self.param_widgets["波特率:"].set(config.get("baudrate", "115200"))
                self.param_widgets["数据位:"].set(config.get("data_bits", "8"))
                self.param_widgets["停止位:"].set(config.get("stop_bits", "1"))
                self.param_widgets["校验位:"].set(config.get("parity", "NONE"))
                self.param_widgets["流控制:"].set(config.get("flow_control", "NONE"))
                self.putty_path.delete(0, tk.END)
                self.putty_path.insert(0, get_putty_path())
        except FileNotFoundError:
            self.putty_path.delete(0, tk.END)
            self.putty_path.insert(0, get_putty_path())
            pass  # 使用默认值

class USBMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("USB串口监测器")
        self.root.geometry("400x500")
        self.set_window_icon()
        self.is_monitoring = False
        self.monitor_thread = None
        self.previous_ports = set()
        self.new_ports = set()
        self.config = self.load_config()
        
        self.create_widgets()
    
    def set_window_icon(self):
        try:
            icon = PhotoImage(file='icon.png')
            self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"加载图标失败: {e}")
        
    def create_widgets(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # 控制按钮
        self.control_btn = ttk.Button(
            toolbar,
            text="开始监测",
            command=self.toggle_monitoring
        )
        self.control_btn.pack(side=tk.LEFT, padx=5)
        
        # 配置按钮
        self.config_btn = ttk.Button(
            toolbar,
            text="串口配置",
            command=self.show_config
        )
        self.config_btn.pack(side=tk.LEFT, padx=5)
        
        # 说明标签
        self.info_label = ttk.Label(
            self.root,
            text="本程序仅监测串口，不会占用串口。\n双击COM口可启动Putty连接。",
            justify=tk.CENTER,
            wraplength=380
        )
        self.info_label.pack(pady=5)
        
        # 显示区域
        self.display_frame = ttk.LabelFrame(self.root, text="当前可用的COM口", padding=10)
        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 使用Text组件
        self.port_text = tk.Text(
            self.display_frame,
            height=12,
            font=('Consolas', 11),
            wrap=tk.WORD,
            cursor="hand2"  # 使用手型光标
        )
        self.port_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加标签样式
        self.port_text.tag_configure('new', background='#e6ffe6')
        self.port_text.tag_configure('timestamp', foreground='#666666')
        self.port_text.tag_configure('header', font=('Consolas', 11, 'bold'))
        self.port_text.tag_configure('clickable', underline=1)
        
        # 绑定双击事件
        self.port_text.tag_bind('clickable', '<Double-Button-1>', self.on_port_click)
        
        # 设备计数标签
        self.count_label = ttk.Label(
            self.root,
            text="检测到 0 个串口设备",
            justify=tk.CENTER
        )
        self.count_label.pack(pady=2)
        
        # 状态标签
        self.status_label = ttk.Label(
            self.root,
            text="状态：未监测",
            justify=tk.CENTER
        )
        self.status_label.pack(pady=2)
    
    def show_config(self):
        SerialConfig(self.root)
        
    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "baudrate": "115200",
                "data_bits": "8",
                "stop_bits": "1",
                "parity": "NONE",
                "flow_control": "NONE",
                "putty_path": "putty.exe"
            }
    
    def on_port_click(self, event):
        # 获取点击位置
        index = self.port_text.index(f"@{event.x},{event.y}")
        line = self.port_text.get(f"{index} linestart", f"{index} lineend")
        
        # 提取COM口号
        import re
        match = re.search(r'COM\d+', line)
        if match:
            com_port = match.group()
            self.launch_putty(com_port)
    
    def launch_putty(self, com_port):
        config = self.load_config()  # 重新加载配置
        putty_path = config.get("putty_path", "putty.exe")
        baudrate = config.get("baudrate", "115200")
        
        if not os.path.exists(putty_path):
            messagebox.showerror("错误", f"未找到Putty程序：{putty_path}")
            return
        
        try:
            # 构建putty命令行
            cmd = [
                putty_path,
                "-serial", com_port,
                "-sercfg", f"{baudrate},{config.get('data_bits')}," \
                          f"{config.get('parity')[0]}," \
                          f"{config.get('stop_bits')}"
            ]
            subprocess.Popen(cmd)
        except Exception as e:
            messagebox.showerror("错误", f"启动Putty失败：{str(e)}")
    
    def get_port_info(self, port):
        """获取端口详细信息"""
        info = f"{port.device}"
        if port.manufacturer:
            info += f" [{port.manufacturer}]"
        if port.description:
            info += f" - {port.description}"
        return info
            
    def monitor_ports(self):
        while self.is_monitoring:
            try:
                current_ports = {}
                for port in serial.tools.list_ports.comports():
                    current_ports[port.device] = self.get_port_info(port)
                
                current_port_set = set(current_ports.keys())
                new_ports = current_port_set - self.previous_ports
                
                if current_port_set != self.previous_ports:
                    self.new_ports = new_ports
                    self.update_display(current_ports)
                    self.previous_ports = current_port_set
                
                time.sleep(1)
                
            except Exception as e:
                print(f"监测过程中出现错误: {e}")
                continue
    
    def update_display(self, ports):
        self.root.after(0, self._update_text, ports)
    
    def _update_text(self, ports):
        self.port_text.delete(1.0, tk.END)
        
        device_count = len(ports)
        self.count_label.config(text=f"检测到 {device_count} 个串口设备")
        
        if ports:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.port_text.insert(tk.END, f"更新时间: {timestamp}\n", 'timestamp')
            self.port_text.insert(tk.END, "-" * 20 + "\n")
            
            sorted_ports = sorted(ports.keys(), key=lambda x: int(x[3:]))
            
            for port in sorted_ports:
                port_info = ports[port]
                tags = ('clickable',)  # 所有端口都可点击
                if port in self.new_ports:
                    tags = ('clickable', 'new')  # 新端口添加新标记
                self.port_text.insert(tk.END, f"   {port_info}\n", tags)
        else:
            self.port_text.insert(tk.END, "未检测到COM口\n")
        
        self.port_text.see(tk.END)

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.control_btn.config(text="停止监测")
            self.status_label.config(text="状态：正在监测")
            self.monitor_thread = threading.Thread(target=self.monitor_ports)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
        else:
            self.is_monitoring = False
            self.control_btn.config(text="开始监测")
            self.status_label.config(text="状态：未监测")

if __name__ == "__main__":
    root = tk.Tk()
    app = USBMonitor(root)
    root.mainloop()