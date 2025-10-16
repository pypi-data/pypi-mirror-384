import numpy as np
import socket
import time
from waveforms import Waveform
from dev.common import (BaseDriver, QBool, QInteger, QList, QOption, QReal,Quantity,
                        QVector, get_coef)



class Driver(BaseDriver):
    support_models = ['CY_6DA']

    CHs_num = 8 #8通道
    CHs = [9, 10, 11, 12,13,14,15,16]
    default_triggertime = 200  # us
    trigger_source = 1  # 0：外部触发，1：内部触发
    sock = None
    sockSync = None
    freq = []

    quants = [
        #通道9
        QReal('TriggerDelay', value=0, ch=9, unit='ns',),
        QReal('rdAtt', value=0, ch=9, unit=' ',),
        QInteger('CAWWave', value=[3], ch=9),#value = [频率、相位、波形选择（1-载波 0-任意波）]
        QInteger('Waveform', value=[], ch=9),
        
        QInteger('TrigType', value=0, ch=9),#1-内触发、0-同步机触发
        QInteger('TrigType', value=0, ch=9),
        Quantity('Coefficient', value=None, ch=9),

        #通道10
        QReal('TriggerDelay', value=0, ch=10, unit='ns',),
        QReal('rdAtt', value=0, ch=10, unit=' ',),
        QInteger('Waveform', value=[3], ch=10),#value = [频率、相位、波形选择（1-载波 0-任意波）]

        #通道11
        QReal('TriggerDelay', value=0, ch=11, unit='ns',),
        QReal('rdAtt', value=0, ch=11, unit=' ',),
        QInteger('waveform', value=[3], ch=11),#value = [频率、相位、波形选择（1-载波 0-任意波）]

        #通道12
        QReal('TriggerDelay', value=0, ch=12, unit='ns',),
        QReal('rdAtt', value=0, ch=12, unit=' ',),
        QInteger('Waveform', value=[3], ch=12),#value = [频率、相位、波形选择（1-载波 0-任意波）]

        #通道13
        QReal('TriggerDelay', value=0, ch=13, unit='ns',),
        QReal('rdAtt', value=0, ch=13, unit=' ',),
        QInteger('CAWWave', value=[3], ch=13),#value = [频率、相位、波形选择（1-载波 0-任意波）]
        QInteger('Waveform', value=[], ch=13),
        
        QInteger('TrigType', value=0, ch=13),#1-内触发、0-同步机触发
        QInteger('TrigType', value=0, ch=13),
        Quantity('Coefficient', value=None, ch=13),

        #通道14
        QReal('TriggerDelay', value=0, ch=14, unit='ns',),
        QReal('rdAtt', value=0, ch=14, unit=' ',),
        QInteger('waveform', value=[3], ch=14),#value = [频率、相位、波形选择（1-载波 0-任意波）]

        #通道15
        QReal('TriggerDelay', value=0, ch=15, unit='ns',),
        QReal('rdAtt', value=0, ch=15, unit=' ',),
        QInteger('waveform', value=[3], ch=15),#value = [频率、相位、波形选择（1-载波 0-任意波）]

        #通道16
        QReal('TriggerDelay', value=0, ch=16, unit='ns',),
        QReal('rdAtt', value=0, ch=16, unit=' ',),
        QInteger('waveform', value=[3], ch=16),#value = [频率、相位、波形选择（1-载波 0-任意波）]





    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'CY_6DA'
        self.srate = 6e9

    def open(self):
        #建立连接
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.addr, 4196))
        self.sock.settimeout(10)
        #与同步机连接
        self.sockSync = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockSync.connect(('192.168.2.100',4196))
        self.sockSync.settimeout(10)
        #复位
        self.set('*RST')
        #同步
        # self.set(':TRIG:CTRL',1)
        # self.set(':TRIG:CHLS')
        # self.set(':TRIG:CTRL',2)

            #外触发
        self.set(':TRIG:TYPE',1)
    #触发模式：7044同步
        self.set(':TRIG:CTRL',0)
        #同步机发一个触发信号
        self.set_SYNC_TrigCycle(self.sockSync,1)
        time.sleep(1)
        self.set_SYNC_TrigCycle(self.sockSync,1)
        time.sleep(1)
        self.set_SYNC_TrigCycle(self.sockSync,1)
        time.sleep(1)

     #触发模式：多通道同步
        self.set(':TRIG:CTRL',1)
        #通道同步复位
        self.set(':TRIG:CHLS')
        #同步机发一个触发信号
        self.set_SYNC_TrigCycle(self.sockSync,1)

        #触发模式：波形触发模式
        self.set(':TRIG:CTRL',2)

        #设置奈奎斯特区间为2区
        self.set('::AWG:NYZONE',2)


        self.ChlSel(0)
        att = 0
        self.set(':READ:ATT',att)
        delay_ns = 0
        self.set(':READ:DELAY',delay_ns)

    def close(self, **kw):
        return super().close(**kw)  

    def write(self, name: str, value, **kw):
        ch = kw.get('ch', 9)
        self.config[name][ch]['value'] = value  # 更新到config

        if name in ['TriggerDelay',]:
            # self.config['TriggerDelay'][ch]['value'] = value
            self.rd_Delay( ch, value)
        elif name in ['rdAtt',]:
            self.rd_Att(ch, value)  
        elif name in ['Waveform',]:
            if isinstance(value, Waveform):
                value = value.sample(self.srate)
            # elif isinstance(value, tuple):
            #     value = self.dist(*value)
            else:
                print('type error')
                return
            assert len(np.nonzero(value)[0]) <= int(
                50e-6 * self.srate), 'Wave is too long!'
            # freq = value[0]
            # data_0, t_0 = self.GenWave_Cos(freq,65*32*4, self.srate)
            # print('实验波形数据:',value)
            self.download_AWG_waveData(value,ch)
        elif name in ['CAWWave',]:
            self.Generate_Caw_Wave(value,ch)
        elif name in ['Coefficient',]:
            self.set_Coefficient(value)

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
        # elif name in ['algIQ']:
        #     return self.getsingleIQ()
        elif name in ['IQ']:
            return self.get_FPGA_IQ_new()
            # return self.getsingleIQ()
        else:
            return super().read(name, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def socket_query(self,sock, cmd_name, params = 0, buffer_size=1024):
        self.send_command(self.sock, cmd_name, params)
        
        # 循环接收直到获取所有数据（示例：假设响应以 b'END' 结尾）
        response = b''
        num = 0
        while True:
            chunk = self.sock.recv(buffer_size)
            # print(chunk)
            num = num + 1
            if not chunk:
                break  # 连接关闭
            response += chunk
            if num == 1:
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
        if len(cmd_bytes)>1472:
            #分片处理
            for i in range(0,len(cmd_bytes),1472):
                self.sock.sendall(cmd_bytes[i:i+1472])
        else:
            self.sock.sendall(cmd_bytes)
        # print(f"已发送指令：{cmd_str}")

    def set(self, name, value=None):
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.connect((self.addr, 4196))
        # sock.settimeout(10)
        self.socket_query(self.sock, name, value)
        return self.sock

    
    ##########################################################################################################
    def ChlSel(self,chl,name = ':AWG:CHLSEL'):
        chl = chl -1
        self.set(name,chl)


    def rd_Delay(self, chl, delay_ns):
        self.ChlSel(chl)
        self.set(':READ:DELAY',delay_ns)
        return
    def rd_Att(self, chl, att):
        self.ChlSel( chl)
        self.set(':READ:ATT',att)
        return
    def Generate_Caw_Wave(self,value,chl):
        # self.ChlSel(chl)
        # delay_ns =800
        # self.set(':READ:DELAY',delay_ns)
        # value[0] = 6500 
        # value[1] = 90
        # value[2] = 1 # 波形选择：1-载波 0-任意波
        
        freq = value[0]
        self.set(':CAW:FREQ',freq)
        self.set(':CAW:PHA',90)
        self.set(':CAW:ONLY',1)

    # def set_Connect_Sync(self,ip,port):
    #     #与同步机建立连接
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     addr_ip = ip  #使用方给的网段
    #     sock.connect((addr_ip, port))
    #     sock.settimeout(10)
    #     #同步机通道使能
    #     time.sleep(0.1)
    #     self.send_command(sock,'GLOB:SELC',6)
    #     time.sleep(0.1)
    #     self.send_command(sock,'GLOB:CHLO',"ON")
    #     socket_Sync = sock
    #     return socket_Sync
    def set_SYNC_TrigCycle(self,sock,trigNum):

        #同步机循环触发
        Trig_interv_s = 0.02         # 触发间隔 单位:s
        Trig_loop = trigNum              # 触发次数 【0:无限循环】
        time.sleep(0.1)
        self.send_command(sock,'GLOB:TRIGS CYCLE',None)
        time.sleep(0.1)
        self.send_command(sock,'GLOB:SPAC',Trig_interv_s)
        time.sleep(0.1)
        self.send_command(sock,'GLOB:LOOP',Trig_loop)

        return
    
    ##############################################################
    def set_Coefficient(self,coef_info):
        self.freq = [kw['Delta'] for kw in coef_info['wList']]
        return
    #########################下发任意波数据#################################################
    # ------------------------------------------------------------------------
    # 功能说明: 【载波】 *用于任意波形数据下发
    #       输入参数:波形数据
    #
    # 返回值: 无
    # ------------------------------------------------------------------------
    def AWG_Data_Download(self,waveData):
        # handle.query(':AWG:SEQLEN {}'.format(len(waveData)))
        #建立连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.addr, 4196))
        sock.settimeout(10)
        self.ChlSel(13)
        #下发波形数据
        len_once = 100000
        m_Len_bytes = len(waveData)%len_once
        m_Len_count = len(waveData)//len_once
        if m_Len_count != 0:
            for k in range(m_Len_count):
                self.set(':AWG:SEQLEN',len_once)
                start = k * len_once  # 计算当前块的起始偏移量（整数）
                end = start + len_once  # 计算当前块的结束偏移量
                current_block = waveData[start:end]  # 通过切片获取当前块数据（bytes 类型）
                sock.sendall(current_block)
                time.sleep(0.03)
                # print("6DAC手动延时0.5秒")
        if m_Len_bytes != 0:
            self.set(':AWG:SEQLEN',m_Len_bytes)
            start = len_once*m_Len_count  # 计算当前块的起始偏移量（整数）
            end = start + m_Len_bytes  # 计算当前块的结束偏移量
            current_block = waveData[start:end]  # 通过切片获取当前块数据（bytes 类型）
            sock.sendall(current_block)
            time.sleep(0.03)
            # print("6DA手动延时1秒")
        return
    # ------------------------------------------------------------------------
    # 功能说明: 量化float数据 并转bytes 【用于转换任意波形数据】
    # 输入参数:
    #       data:【数据类型: ndarray或list】 
    #            【取值范围: 0~1】
    #            【参数意义: 待处理的float数据数组或列表】
    # 输出参数:
    #       data_bytes:【数据类型: bytes】
    #                  【数据说明: 每16位为一组, 范围: 0~0xFFFF, 低14位有效】
    #                  【参数意义: 转换后的生成的bytes数据】
    # 返回值: data_bytes
    # ------------------------------------------------------------------------
    def float2bytes(self,data):
        # 如果为list格式，则转为array进行处理
        if isinstance(data,list):
            data = np.array(data).reshape(1,-1)
        else:
            # 转换为1维数组
            data = data.reshape(1,-1)

        len_data = np.size(data)
        # 是否为偶数个元素，如果不是，补1个0
        if len_data % 2 != 0:
            np.append(data,0)
            len_data = len_data +1
        # -------- 元素两个一组，每组前后对调 -----------------    
        data_uint16 = np.uint16(data*(pow(2,15)-1))
        #####################
        # data_uint16 = np.bitwise_or(data_uint16,1)
        ##################
        data_bytes = data_uint16.tobytes()
        return data_bytes
    
    # 函数功能: zAWG 波形数据量化
    # 参数说明: z_coffe: 数据量化系数: 0~1[满量程]
    #           Data_chl0、Data_chl1、Data_chl2、Data_chl3
    #           需为list类型
    def z_GenData(self,z_coffe, Data_chl0):
        reData_array = np.array(Data_chl0).reshape(-1,1)
        z_data_bytes = self.float2bytes(z_coffe*reData_array)
        print("下发波形数据长度为:",len(z_data_bytes),"字节")
        return z_data_bytes

    def download_AWG_waveData(self,data,chl = 9):
        # self.ChlSel(chl)
        # delay_ns =800
        # self.set(':READ:DELAY',delay_ns)
        # with np.printoptions(threshold=np.inf):
        #     print('实验波形数据:',data)  # 仅在该上下文中完整显示
        z_coeff = 0.4        # 数据量化系数: 0~1[满量程]
        waveData = self.z_GenData(z_coeff, data)
        #波形模块使能复位
        self.ChlSel(0)
        self.set(':AWG:BDOWNLC')
        #波形下发与控制
        self.AWG_Data_Download(waveData)
       
        waveType = 0
        self.set(':CAW:ONLY',waveType)# 波形选择：1-载波 0-任意波
        playMode = 1
        self.set(':AWG:SEQNUM',playMode) # 波形循环播放次数：0-循环播放，1-单次播放
        #通道输出打开
        self.ChlSel(0)
        self.set(':AWG:SWITCH','ON')
        # #触发：
        # #与同步机连接
        # sockSync = self.set_Connect_Sync('192.168.2.100',4196)
        # #同步机发一个触发信号
        # self.set_SYNC_TrigCycle(sockSync,1)
        #外触发
        self.set(':TRIG:TYPE',0)
        #触发模式：波形触发模式
        self.set(':TRIG:CTRL',2)

    # ------------------------------------------------------------------------
    # 功能说明: 余弦数据生成
    # 输入参数:
    #       f0_cos:【数据类型: float】
    #              【参数意义: 频率, 单位:Hz】
    #       cycle: 【数据类型: int】
    #              【取值: 需根据数据长度计算】
    #              【参数意义: 周期数】
    #       fs_cos: 【数据类型: float】
    #               【参数意义: 采样率, 单位:Hz】
    # *参数示例: fs_cos = 1.2e9, f0_cos = 50e6, cycle = 10
    # 输出参数:
    #       y_cos.tolist():【数据类型: list】
    #                      【取值范围: 0~1】
    #                      【参数意义: 余弦幅度值】
    #       t_cos: 【数据类型: ndarray】
    #              【参数意义: 时间轴坐标】
    # 返回值: y_cos.tolist(), t_cos
    # ------------------------------------------------------------------------
    def GenWave_Cos(self,f0_cos, cycle, fs_cos):
        T_cos = abs(cycle/f0_cos)
        N = round(T_cos*fs_cos)
        t_cos = np.linspace(0,T_cos-1/fs_cos,N)
        y_cos = np.cos(2*np.pi*f0_cos*t_cos)
        return y_cos.tolist(), t_cos