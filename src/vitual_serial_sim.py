from serial import Serial
import time

PORT="COM21"                                            #上传实时流数据的虚拟串口
BAUT_RATE=115200                                        #串口波特率
SIM_FILE_PATH="data/Real_Time/wuh20790.24o.b2b.log"     #仿真实时流的数据源文件

ser_server=Serial(PORT,BAUT_RATE)

#ASCII模拟
#ASCII Simulation
with open(SIM_FILE_PATH,'r') as f:
    lines=f.readlines()

#循环传输
for line in lines:
    ser_server.write(bytearray((line[:-1]+'\r\n').encode()))        #逐行发送以仿真模块芯片向上位机实际数据传输过程
    time.sleep(0.01)                                                #延时以等待串口处理, 该项不能设置过小