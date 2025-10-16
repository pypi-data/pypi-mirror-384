import numpy as np
import socket
import time
from dev.common import (BaseDriver, QBool, QInteger, QList, QOption, QReal,QString,
                        QVector, get_coef)



class Driver(BaseDriver):
    support_models = ['CY_AD']

    CHs_num = 4 #16频点4通道
    CHs = [9, 10, 11, 12]
    default_triggertime = 200  # us
    trigger_source = 1  # 0：外部触发，1：内部触发

    #段数
    seqNum = 1023
    #段长
    seqLen = 5000
    #激励扫频频率
    sweepFreq = []
    # sock =None
    sockSync = None
    quants = [
        #通道9
        QReal('TriggerDelay', value=0, ch=9, unit='ns',),
        QReal('rdAtt', value=0, ch=9, unit=' ',),
        QInteger('Demodu', value=[5], ch=9),#value = [段长、段数、解模频率、相位、解算模块索引]
        QInteger('AquPram', value=[3], ch=9),#value = [段数、段长、采集通道使能选通]
        QInteger('TrigType', value=0, ch=9),#1-内触发、0-同步机触发
        QInteger('TrigType', value=0, ch=9),
        QInteger('ReadRawData', value=[2], ch=9),#value = [段数、段长]
        QInteger('ReadDemoduData', value=[2], ch=9),#value = [解算模块索引、段数]
        QInteger('StartCapture',value = [],ch=9),
        QInteger('Shot', value = 1023, ch=9),#value = [段数、段长]
        QInteger('ReadDemoduData', value=[2], ch=9),#value = [解算模块索引、段数]
        QList('Coefficient', value=None, ch=9), 
        QString('CaptureMode', value='alg', ch=9),
        QVector('TraceIQ', value=[], ch=9),
        QVector('IQ', value=[], ch=9),
        QVector('algIQ', value=[], ch=9),
        #通道10
        QReal('TriggerDelay', value=0, ch=10, unit='ns',),
        QReal('rdAtt', value=0, ch=10, unit=' ',),
        QInteger('Demodu', value=[5], ch=10),#value = [段长、段数、解模频率、相位、解算模块索引]
        QInteger('AquPram', value=[3], ch=10),#value = [段数、段长、采集通道使能选通]
        QInteger('ReadRawData', value=[2], ch=10),#value = [段数、段长]
        QInteger('ReadDemoduData', value=[2], ch=10),#value = [解算模块索引、段数]

        #通道11
        QReal('TriggerDelay', value=0, ch=11, unit='ns',),
        QReal('rdAtt', value=0, ch=11, unit=' ',),
        QInteger('Demodu', value=[5], ch=11),#value = [段长、段数、解模频率、相位、解算模块索引]
        QInteger('AquPram', value=[3], ch=11),#value = [段数、段长、采集通道使能选通]
        QInteger('ReadRawData', value=[2], ch=11),#value = [段数、段长]
        QInteger('ReadDemoduData', value=[2], ch=11),#value = [解算模块索引、段数]

        #通道12
        QReal('TriggerDelay', value=0, ch=12, unit='ns',),
        QReal('rdAtt', value=0, ch=12, unit=' ',),
        QInteger('Demodu', value=[5], ch=12),#value = [段长、段数、解模频率、相位、解算模块索引]
        QInteger('AquPram', value=[3], ch=12),#value = [段数、段长、采集通道使能选通]
        QInteger('ReadRawData', value=[2], ch=12),#value = [段数、段长]
        QInteger('ReadDemoduData', value=[2], ch=12),#value = [解算模块索引、段数]


    ]

    def __init__(self, addr, **kw):
        super().__init__(addr, **kw)
        self.model = 'CY_AD'
        self.srate = 5e9

    def open(self):
        #建立连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.addr, 4196))
        sock.settimeout(40)
        self.sockSync = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockSync.connect(('192.168.2.100',4196))
        self.sockSync.settimeout(40)
        #复位
        self.set('*RST')
        #同步
        #外触发
        self.set(':TRIG:TYPE',0)
        #触发模式：7044同步
        self.set(':TRIG:CTRL',0)
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
        self.set_SYNC_TrigCycle(self.sockSync,1)

        #触发模式：波形触发模式
        self.set(':TRIG:CTRL',2)
        # self.set(':TRIG:CTRL',1)
        # self.set(':TRIG:CHLS')
        # self.set(':TRIG:CTRL',2)
        #初始化
        self.set(':ADCIN')
        #触发延时
        self.ChlSel(0)
        self.set(':READ:DELAY',800)

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
        elif name in ['Demodu',]:
            self.rd_DemoDu(value,ch)
        elif name in ['AquPram',]:
            self.rd_AquPram(value,ch)
        elif name in ['TrigType',]:
            self.set('TRIGER:TYPE',value)
            if value ==1:
                self.set(':TRIGER:ONCE')
        elif name in ['ReadRawData',]:
            self.rd_RawData(value,ch)
        # elif name in ['ReadDemoduData',]:
        #     self.rd_IO_data(value,ch)
    ############################################################
        elif name in ['StartCapture',]:
            self.adc_startCature(value,ch)
        elif name in ['Shot',]:
            self.rd_Shot_data(value,ch)
        elif name in ['Coefficient',]:
            self.rd_Coefficient(value)
        elif name in ['CapturnMode',]:
            self.Set_CapturnMode(value,ch)
        else:
            return super().write(name, value, **kw)

        return value

    def read(self, name: str, **kw):
        # mode = self.config[name][ch]['value']

        # if mode == "raw":
        #     return self.getTrace()
        # elif mode == 'alg':
        #     return self.get_FPGA_IQ_new()
        ch = kw.get('ch', 9)
        if name in ['TraceIQ']:
            return self.rd_RawData()
        elif name in ['algIQ']:
            return self.getsingleIQ()
        elif name in ['IQ']:
            return self.read_IQ_data(0,ch)#回读解模数据
            # return self.getsingleIQ()
        else:
            return super().read(name, ch=ch, **kw)

    # *#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*# user defined #*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#

    def socket_query(self,sock, cmd_name, params = 0, buffer_size=1024):
        self.send_command(sock, cmd_name, params)
        
        # 循环接收直到获取所有数据（示例：假设响应以 b'END' 结尾）
        response = b''
        while True:
            chunk = sock.recv(buffer_size)
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
        # print(cmd_bytes)
        # 3. 发送指令
        sock.sendall(cmd_bytes)
        # time.sleep(0.1)
        # print(f"已发送指令：{cmd_str}")

    def set(self, name, params=None,readlen = 10):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.addr, 4196))
        sock.settimeout(20)# 超时时间为10秒
        # self.socket_query(sock, name, value)
        # time.sleep(0.1)
        self.send_command(sock, name, params)
        # time.sleep(0.1)
        if readlen == self.seqNum*8:
            """接收已知总长度的数据"""
            data = b''
            while len(data) < readlen:
                # 计算剩余需要接收的字节数
                remaining = readlen - len(data)
                # 每次最多接收readlen字节，或剩余字节数（取较小值）
                chunk = sock.recv(min(remaining, 1446))  # 4096是缓冲区大小，可调整
                # time.sleep(0.01)
                if not chunk:  # 如果连接关闭且未接收完数据
                    raise ConnectionError("连接意外关闭，数据不完整")
                data += chunk
            # print(len(data))
            print(data)
            return data
        else:
            # 循环接收直到获取所有数据（示例：假设响应以 b'END' 结尾）
            response = b''
            while True:
                chunk = sock.recv(readlen)
                if not chunk:
                    break  # 连接关闭
                response += chunk
                if b'\n' in chunk:
                    break  # 达到结束标志
            return response


    
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
    def rd_DemoDu(self,value,chl):
        self.ChlSel( chl)
        self.set(':READ:DEMODU:WINLEN',value[0])
        self.set(':READ:DEMODU:WINHEAD',value[1])
        self.set(':READ:DEMODU:FREQUENCY',value[2])
        self.set(':READ:DEMODU:PHASE',value[3])
        self.set(':READ:DEMODU:INDEX',value[4])
        self.set(':READ:DEMODU:LOADCHL',chl-1)
        return
    def rd_AquPram(self,value,chl):
        self.ChlSel(chl)
        self.set(':READ:SEQNUM',value[0])
        self.set(':READ:SEQLEN',value[1])
        self.set(':READ:CHLCHOOSE',value[2])#1-15 采集通道选通
        self.set(':READ:STARTA')
        return
    # ------------------------------------------------------------------------
    # 功能说明: 【rdOut】原始数据回读       * 长数据
    # 输入参数:
    #       Handle: 【数据类型: TCPIPSocket】
    #               【参数意义: 待操作的仪器句柄】
    #       Len_bytes: 【数据类型: int】
    #                  【取值范围: [1,单次采集长度*采集段数]】
    #                  【参数意义: 回读数据长度, 单位:Byte】
    # 返回值: 返回Bytes类型数据序列
    # ------------------------------------------------------------------------
    def read_Data_long(self, Len_bytes):
        list_data_bytes = []
        # len_once = 16000
        len_once = 1000
        m_rdLen_bytes = Len_bytes%len_once
        m_rdLen_count = Len_bytes//len_once
        if m_rdLen_count != 0:
            for k in range(m_rdLen_count):
                sock = self.set(':READ:OUT',len_once)
                self.send_command(sock, ':READ:OUT?',None)
                reData = sock.recv(len_once)
                list_data_bytes.append(reData)
                # print(len_once*(k+1))
                # print(f"\r当前回读到的字节数: {len_once*(k+1)} bytes", end="")
        if m_rdLen_bytes != 0:
            self.set(':READ:OUT',m_rdLen_bytes)
            self.send_command(sock, ':READ:OUT?')
            reData = sock.recv(m_rdLen_bytes)
            list_data_bytes.append(reData)
            # print(f"\r当前回读到的字节数: {len_once*(k+1)} bytes", end="")
        return b''.join(list_data_bytes)
    # ------------------------------------------------------------------------
    # 功能说明: bytes转float，并归一化(normalization)    【用于转换采集数据】
    # 特别说明: 中间参数 d_uint16
    #          d_uint16：数据有效位【14位】 【第14位为符号位，[13:0]为数据位】
    # 输入参数:
    #       data:【数据类型: bytes】
    #            【数据说明: 每16位为一组, 范围: 0~0xFFFF, 低14位有效】
    #            【参数意义: 待处理的bytes数据】
    # 输出参数:
    #       data_float:【数据类型: list】
    #                  【取值范围: 0~1】
    #                  【参数意义: 转换后生成的float数据列表】
    #       x_Data.tolist():【数据类型: list】
    #                       【取值范围: 正整数】
    #                       【参数意义: 计数用, x坐标】
    # 返回值: x_Data.tolist(), data_float
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # 功能说明: bytes转float，并归一化(normalization)    【用于转换解模数据】
    # 特别说明: 中间参数 d_uint32
    #          d_uint32: 数据有效位【32位】 【第32位为符号位，[31:0]为数据位】
    # 输入参数:
    #       data:【数据类型: bytes】
    #            【数据说明: 每32位为一组, 范围: 0~0xFFFFFFFF】
    #            【参数意义: 待处理的bytes数据】
    # 输出参数:
    #       data_float:【数据类型: list】
    #                  【取值范围: 0~1】
    #                  【参数意义: 转换后生成的float数据列表】
    # 返回值: data_float
    # ------------------------------------------------------------------------
    def bytes2float_u32(self,data):
        Step = 4
        data_float = []
        for i in range(int(len(data)/Step)):
            d_uint32 = int.from_bytes(data[i*Step:(i+1)*Step], byteorder="little")
            if d_uint32 >= pow(2,31):
                d_float = (d_uint32 - (pow(2,32)-1))
            else:
                d_float = d_uint32
            data_float.append(d_float)
        return data_float
    def bytes2float(self,data):
        Step = 2
        data_float = []
        x_Data = np.linspace(0, (int(len(data)/Step)-1), int(len(data)/Step), dtype=int)

        for i in range(int(len(data)/Step)):
            d_uint16 = int.from_bytes(data[i*Step:(i+1)*Step], byteorder="little")
            if d_uint16 >= pow(2,13):
                d_float = (d_uint16 - (pow(2,14)-1))/pow(2,13)
            else:
                d_float = d_uint16/(pow(2,13)-1)
            data_float.append(d_float)

        return x_Data.tolist(), data_float

    def rd_RawData(self,value = 0,chl = 9):
        EndFlag = 0
        rd_count = 0
        # 存储结束标志位回读
        while EndFlag==0:
            EndFlag=self.set(':READ:ENDSTORE?')
        self.ChlSel(chl)
        rdOut_reData_bytes = self.read_Data_long(self.seqNum*self.seqLen*2)
        x, data_real = self.bytes2float(rdOut_reData_bytes)
        return x, data_real

    # def rd_IO_data(self,value,chl):
    #     self.set(':READ:DEMODU:RINDEX',value[0])
    #     self.ChlSel(chl)
    #     sock = self.set(':READ:DEMODU:READ',value[1])
    #     self.send_command(sock, ':READ:DEMODU:READ?',None)
    #     reData_bytes = sock.recv(value[1]*8)
    #     reData_float = self.bytes2float_u32(reData_bytes)
    #     reData_i = reData_float[::2]#选取索引为偶数的元素
    #     reData_q = reData_float[1::2]
    #     return reData_i,reData_q


    ###################################
    # ------------------------------------------------------------------------
    # 功能说明: bytes转float，并归一化(normalization)    【用于转换解模数据】
    # 特别说明: 中间参数 d_uint32
    #          d_uint32: 数据有效位【32位】 【第32位为符号位，[31:0]为数据位】
    # 输入参数:
    #       data:【数据类型: bytes】
    #            【数据说明: 每32位为一组, 范围: 0~0xFFFFFFFF】
    #            【参数意义: 待处理的bytes数据】
    # 输出参数:
    #       data_float:【数据类型: list】
    #                  【取值范围: 0~1】
    #                  【参数意义: 转换后生成的float数据列表】
    # 返回值: data_float
    # ------------------------------------------------------------------------
    def bytes2float_u32(self,data):
        Step = 4
        data_float = []
        for i in range(int(len(data)/Step)):
            d_uint32 = int.from_bytes(data[i*Step:(i+1)*Step], byteorder="little")
            if d_uint32 >= pow(2,31):
                d_float = (d_uint32 - (pow(2,32)-1))
            else:
                d_float = d_uint32
            data_float.append(d_float)
        return data_float
        # ------------------------------------------------------------------------
    # 功能说明: 【rdOut】【主板】解模数据回读
    # 输入参数:
    #       Handle: 【数据类型: TCPIPSocket】
    #               【参数意义: 待操作的仪器句柄】
    #       Index: 【数据类型: int】
    #              【取值范围: [0,9]】
    #              【参数意义: 解模模块序号】
    #       rd_chl: 【数据类型: int】
    #               【取值范围: [0,15]】
    #               【参数意义: 数据回读通道】
    # 返回值: reData_i, reData_q
    #           【数据类型: list】
    #           【参数意义: 所选通道，所选解模模块解模结果(I&Q两路结果)】
    # ------------------------------------------------------------------------
    def demodu_read_M_new(self, Index, rd_chl,num):
        self.set(':READ:DEMODU:RINDEX',Index) #解模模块选择
        self.set(':READ:CHLSEL',rd_chl-1)
        self.set(':READ:DEMODU:READ',num)#解模读取的长度（等于设置的段数）
        reData_bytes = self.set(':READ:DEMODU:READ?',None,num*8)
        # print('reData_bytes长度:',len(reData_bytes))
        #处理返回的解模数据
        reData_float = self.bytes2float_u32(reData_bytes)
        reData_i = reData_float[::2]#选取索引为偶数的元素
        reData_q = reData_float[1::2]
        print('reData_i长度:',len(reData_i))
        print('reData_q长度:',len(reData_q))
        return reData_i,reData_q

    def read_IQ_data(self,value,chl):
        #下发解模参数（在开始采集时下发）
        #回读解模数据：
        # reData_i_list = []
        # reData_q_list = []
        num = self.seqNum #段数
        for i in range(0,1):
            Index = i
            reData_i,reData_q = self.demodu_read_M_new(Index,chl,num) #i解模模块读取
            # reData_i_list.append(reData_i)
            # reData_q_list.append(reData_q)
        # 转换为NumPy数组
        # array1 = np.array(reData_i)
        # array2 = np.array(reData_q)
        # print(len(reData_i))
        # print(len(reData_q))
        # 也可以组合成一个二维数组
        combined_array = np.array([reData_i, reData_q])
        return combined_array
    
    #################################开始采集####################################
    def set_demo_Params(self,params = None,value = 0,chl = 9):
        freq = self.sweepFreq[0]/1e6 #单位为MHz  解模频率
        phase = 30 #首个解模频点相位
        acqHeadNum = 0 #解模窗口 起始位置(舍弃前多少个采样点)】
        self.seqLen = 5000 #段长
        self.ChlSel(chl)
        for i in range(0,1):
            Index = i
            self.set(':READ:DEMODU:INDEX',Index)
            self.set(':READ:DEMODU:FREQUENCY',freq)
            self.set(':READ:DEMODU:PHASE',phase*i)
            self.set(':READ:DEMODU:WINHEAD',acqHeadNum)
            self.set(':READ:DEMODU:WINLEN',self.seqLen)
            # self.set(':READ:DEMODU:JUDGEANGLEONE',JudgeAngle_1)
            # self.set(':READ:DEMODU:JUDGETHREONE',JudgeThreshold_1)
            # self.set(':READ:DEMODU:JUDGEANGLETWO',JudgeAngle_2)
            # self.set(':READ:DEMODU:JUDGETHRETWO',JudgeThreshold_2)
            # self.set(':READ:DEMODU:JUDGEANGLETHREE',JudgeAngle_3)
            # self.set(':READ:DEMODU:JUDGETHRETHREE',JudgeThreshold_3)
            self.set(':READ:DEMODU:LOADCHL',chl-1)
        return
    def set_acq_Params(self,params = None,chl = 9):
        SeqNum = self.seqNum
        SeqLen = self.seqLen
        acqInterval = 0
        acqTimes = 1
        self.set(':READ:SEQNUM',SeqNum)
        self.set(':READ:SEQLEN',SeqLen)
        self.set(':READ:ACQINTER',acqInterval)
        self.set(':READ:ACQTIMES',acqTimes)
        self.set(':READ:CHLCHOOSE',255) #对应通道使能，255表示全开
        self.set(':READ:STARTA')
        return
    def set_SYNC_TrigCycle(self,sock,trigNum):

        #同步机循环触发
        Trig_interv_s = 0.0001         # 触发间隔 单位:s
        Trig_loop = trigNum              # 触发次数 【0:无限循环】
        time.sleep(0.01)
        self.send_command(sock,'GLOB:TRIGS CYCLE',None)
        time.sleep(0.01)
        self.send_command(sock,'GLOB:SPAC',Trig_interv_s)
        time.sleep(0.01)
        self.send_command(sock,'GLOB:LOOP',Trig_loop)

        time.sleep(0.01)

        return
    def adc_startCature(self,value = 0,chl = 9):
        #下发解模参数
        self.set_demo_Params()
        #下发采集参数
        self.set_acq_Params()
        #同步机循环触发
        self.set_SYNC_TrigCycle(self.sockSync,self.seqNum)
        return

################################################
    def rd_Shot_data(self,value =1023,chl = 9):
        self.seqNum = value
        return

    def Set_CapturnMode(self,value,chl):
        return
    
    def rd_Coefficient(self,coef_info):
        self.sweepFreq = [kw['Delta'] for kw in coef_info['wList']]
        print(len(self.sweepFreq))
        print(self.sweepFreq)
        return


