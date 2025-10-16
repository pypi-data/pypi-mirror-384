import numpy as np
import socket
import time
from dev.common import (BaseDriver, QBool, QInteger, QList, QOption, QReal,
                        QVector, get_coef)



class Driver(BaseDriver):
    support_models = ['CY_SYNC']

    CHs_num = 21 #21条触发通道
    CHs = [9]
    default_triggertime = 200  # us
    trigger_source = 1  # 0：外部触发，1：内部触发
    sock = None
    quants = [
        QInteger('TrigerSingle', value=0, ch=9),
        QInteger('TrigerCycle', value=[2], ch=9),#[间隔，循环次数]
        QInteger('TRIG', value=0, ch=9),

    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'CY_SYNC'
        # self.srate = 5e9

    def open(self):
        #建立连接
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.addr, 4196))
        self.sock.settimeout(10)
        #参考时钟选择
        self.set('GLOB:CLKSEL',1)
        self.set('GLOB:TRIGS',"CLOSE")
        #使能所有通道
        # for i in range(1,21):
        time.sleep(0.1)
        self.set('GLOB:SELC',6)
        time.sleep(0.1)
        self.set('GLOB:CHLO',"ON")
        time.sleep(0.1)
        self.set('GLOB:SELC',7)
        time.sleep(0.1)
        self.set('GLOB:CHLO',"ON")
        time.sleep(0.1)
        self.set('GLOB:SELC',8)
        time.sleep(0.1)
        self.set('GLOB:CHLO',"ON")

    def close(self, **kw):
        return super().close(**kw)  

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 9)
        self.config[name][ch]['value'] = value  # 更新到config

        if name in ['TrigerSingle',]:
            self.sync_triger_single(value)
        elif name in ['TrigerCycle',]:
            self.sync_triger_cycle(value)  
        
        else:
            return super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        # mode = self.config[name][ch]['value']

        # if mode == "raw":
        #     return self.getTrace()
        # elif mode == 'alg':
        #     return self.get_FPGA_IQ_new()
        ch = kw.get('ch', 1)
        if name in ['TraceIQ']:
            return self.getTrace()
        elif name in ['algIQ']:
            return self.getsingleIQ()
        elif name in ['IQ']:
            return self.get_FPGA_IQ_new()
            # return self.getsingleIQ()
        else:
            return super().read(name, ch=ch, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def socket_query(self,sock, cmd_name, params = 0, buffer_size=1024):
        self.send_command(sock, cmd_name, params)
        
        # 循环接收直到获取所有数据（示例：假设响应以 b'END' 结尾）
        response = b''
        while True:
            chunk = self.sock.recv(buffer_size)
            if not chunk:
                break  # 连接关闭
            response += chunk
            if b'\n' in chunk:
                break  # 达到结束标志
        return response

    def send_command(self,sock, cmd_name, params,a = 0):
        """
        发送带参数的程控指令
        :param sock: 已连接的socket对象
        :param cmd_name: 指令名称（如"SET_FREQ"）
        :param params: 可变参数（如频率值、通道号等）
        """

        # 1. 拼接指令字符串（例如："SET_FREQ,100000 1;" 表示设置通道1的频率为100000Hz）
        if params != None:
            # param_str = ",".join(map(str, params))  # 将参数转换为字符串并拼接
            param_str = str(params)
            cmd_str = f"{cmd_name} {param_str};"    # 组合成完整指令（带结束符）
        else:
            cmd_str = f"{cmd_name};"    # 组合成完整指令（带结束符）
        
        # 2. 转换为字节流（socket传输必须是bytes类型）
        cmd_bytes = cmd_str.encode('utf-8')
        
        # 3. 发送指令
        self.sock.sendall(cmd_bytes)
        # print(f"已发送指令：{cmd_str}")

    def set(self, name, value=None):
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.connect((self.addr, 4196))
        # sock.settimeout(10)
        self.socket_query(self.sock, name, value)
        return self.sock

    
    ##########################################################################################################
    def sync_triger_single(self,value):
        self.set('GLOB:TRIGS',value)
    def sync_triger_cycle(self,value):
        self.set('GLOB:TRIGS',"CYCLE")
        self.set('GLOB:SPAC',value[0])
        self.set('GLOB:LOOP',value[1])



