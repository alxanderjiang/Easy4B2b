from serial import Serial
import numpy as np
import os
import sys
sys.path.append("src")
from satpos import *
from sppp import *
from sppp_multiGNSS import *
from ppp_b2b import IODC2SatPVC,B2b_Orbit_corr
from ppp_b2b_yaml import *
import time

COM_PORT='COM8'             #上位机(PC)的串口号
DEVICE_COM_PORT=''      #与上位机连接的UM982的输出串口号(根据用户电路设计自行调整)
BAUT_RATE=115200            #波特率
BUFF_SIZE=8192              #建议设置为4096以上, 以承接原始观测值消息

OBS_TIME_SPLIT=1            #观测数据观测时间间隔(单位, s)
MW_THR=1.0                  #设置Mw组合周跳检验阈值(cycle)
GF_THR=0.05                 #设置GF组合周跳检验阈值(m)
PRE_RES_THR=200             #先验残差排除阈值(m)
POST_RES_THR=4              #后验残差排除阈值(无单位, 倍数)


#以下为本文件主函数
if __name__ == "__main__":
    
    ser=Serial(COM_PORT,BAUT_RATE)
    ## 向UM982发送初始化配置数据

    # 1.重置所有输出与跟踪通道
    ser.write(b'unlog\r\n')
    ser.write(b'CONFIG SIGNALGROUP 3 6\r\n')
    ser.write(b'mask all\r\n')
    # 2.释放BDS跟踪通道
    ser.write(b'unmask bds\r\n')    
    # 2.释放GPS跟踪通道
    ser.write(b'unmask L1\r\n')
    ser.write(b'unmask L2\r\n')
    # 3.开启PPP功能
    ser.write(b'CONFIG PPP ENABLE B2b-PPP\r\n')
    # 3.首先获取星历(BDS CNAV + GPS LNAV)
    ser.write(('bd3epha '+DEVICE_COM_PORT+' onchanged\r\n').encode())
    ser.write(('gpsepha '+DEVICE_COM_PORT+' onchanged\r\n').encode())
    # 4.然后输出PPPB2b改正信息
    ser.write(('pppb2binfo1a '+DEVICE_COM_PORT+' onchanged\r\n').encode())
    ser.write(('pppb2binfo2a '+DEVICE_COM_PORT+' onchanged\r\n').encode())
    ser.write(('pppb2binfo3a '+DEVICE_COM_PORT+' onchanged\r\n').encode())
    ser.write(('pppb2binfo4a '+DEVICE_COM_PORT+' onchanged\r\n').encode())
    # 5.最后输出观测值(末尾数字为更新率, 默认5s)
    ser.write(('obsvma '+str(DEVICE_COM_PORT)+' '+str(OBS_TIME_SPLIT)+'\r\n').encode())
    ser.write(('pppnava '+str(OBS_TIME_SPLIT)+'\r\n').encode())

    print("CMD Sended, waiting for Response")
    time.sleep(1.0)#等待命令写入
    #以下为实时流业务流程
    count=0
    # 读取数据
    line_byte=[]
    line=""

    time_local=time.localtime()
    file_out="./data/Logs/{:04d}{:02d}{:02d}{:02d}{:02d}{:02d}_B2b-PPP.log".format(time_local.tm_year,
                                                                                  time_local.tm_mon,
                                                                                  time_local.tm_mday,
                                                                                  time_local.tm_hour,
                                                                                  time_local.tm_min,
                                                                                  time_local.tm_sec)
    file_out="./data/Logs/PPP_B2b_MSG.log"

    f=open(file_out,'w')

    #PPP配置
    #主业务流程模拟(PPPB2b实时解码与卫星位置计算)
    sat_num=32+65+37
    f1=1561.098e6
    f2=1268.52e6
    f1_G=1575.42e6
    f2_G=1227.60e6
    freqs=[[f1_G,f2_G],[f1,f2]]

    el_threthod=10.0                                 #设置截止高度角(默认10度)
    ex_threshold_v=PRE_RES_THR                                #设置先验残差阈值(默认30m)
    ex_threshold_v_sigma=POST_RES_THR                           #设置后验残差阈值(默认4)
    Mw_threshold=MW_THR                                 #设置Mw组合周跳检验阈值(cycle)
    GF_threshold=GF_THR                                #设置GF组合周跳检验阈值(m)
    out_age=OBS_TIME_SPLIT+1                         #失锁容限(s)
    #基准站模式设置
    sta_mode="None"                                  #可选配置: Base/IGSR/Rove/None;
                                                     #对于实时系统, 建议选择纯PPP-B2b(NONE模式); 
                                                     #如果有覆盖目标测量时间段内的预报精密轨钟(SP3/CLK格式), 可以选择IGSR模式;
                                                     #如果可以以npy格式给出预报的SSR产品, 可以选择Rove模式. 但不建议;
                                                     #如果需要基准站坐标约束, 可以选择Base模式(服务端使用)
                                                     #除IGSR外, 其余默认使用CNAV-1星历＋B2b改正数
    #基准站坐标约束信息
    STA_P=[-2267750.299921603, 5009154.572885088, 3221294.4058817304]   #以WUH2约束坐标为例
    STA_Q=[0.01, 0.01, 0.01]                                            #约束方差, 以0.1m**2为例

    #流动站改正数约束信息(文件仿真)
    RTK_Info=[]
    rtk_corr_info_time=[]
    if(sta_mode=='Rove'):
        RTK_Info=np.load("Rove_info.npy",allow_pickle=True)
        rtk_corr_info_time=[log[list(log.keys())[0]]['GPSsec'] for log in RTK_Info]

    #IGS实时产品文件读取
    if(sta_mode=='IGSR'):
        CLK=getclk("wum240318.clk")
        IGS=getsp3("wum240318.sp3")

    #B2b信息mat初始化
    B2b_Info_mat={'Info1':{},
              'Info2':{'StOribitCorr':[[0 for x in range(8)]  for t in range(256)]},
              'Info3':{'StCodeBias_t':[[0 for x in range(32)] for t in range(256)]},
              'Info4':{'StClkCorr_t': [[0 for x in range(3)]  for t in range(256)]}
              }

    B1C_CNAV_mat={'Old':[{} for t in range(66)],#存储上一星历
              'Now':[{} for t in range(66)]}#存储更新星历, 双星历配合完整B2b信息配对
    GPS_LNAV_mat={'Old':[{} for t in range(33)],#存储上一星历
              'Now':[{} for t in range(33)]}#存储更新星历, 双星历配合完整B2b信息配对

    sat_pcos={}
    if(sta_mode=='IGSR'):
        sat_pcos=RINEX3_to_ATX('data/ATX/igs20.atx')            

    #电离层参数
    ion_params=[]

    sat_out=[]                                                             #排除卫星列表
    MEO_only=0
    epoch=0                                                                #初始化历元标识
    dy_mode='static'                                                       #运动模式, 可选static/dynamic
    Out_log=[]
    obs_splite=0
    ser.set_buffer_size(rx_size=BUFF_SIZE)
    
    while True:
        #逐字符读取直至读到换行符
        response = ser.read(1)
        line_byte.append(response.decode())
        #读到换行符,解析一行
        if(line_byte[-1]=='\n'):
            for c in line_byte:
                line+=c
            #print(line,end="")
            f.write(line[:-1])
            line_byte=[]#重置行列表
            line=line[:-1]
            #line=''#测试不解算收数据

            #广播星历读取部分: Message ID 77
            if(line[:7]=="#BD3EPH" and "FINE" in line):
                BD3EPH_Info_decode(line,B1C_CNAV_mat)
            #GPS广播星历读取部分: Message ID 97
            if(line[:7]=='#GPSEPH' and "FINE" in line):
                GPSEPH_Info_decode(line,GPS_LNAV_mat)
                # PPPB2b信息解码部分: Message ID 2302/2304/2306/2308
                # 1. 信息类型一: 掩码解码
            if(line[:12]=="#PPPB2BINFO1" and "FINE" in line):
                B2b_Info1_decode(line,B2b_Info_mat)
                # 2. 信息类型二: 轨道改正数解码
            if(line[:12]=="#PPPB2BINFO2" and "FINE" in line):
                B2b_Info2_decode(line,B2b_Info_mat)
                # 3. 信息类型三: 码间偏差DCB解码
            if(line[:12]=="#PPPB2BINFO3" and "FINE" in line):
                B2b_Info3_decode(line,B2b_Info_mat)
                # 4. 信息类型四: 钟差
            if(line[:12]=="#PPPB2BINFO4" and "FINE" in line):
                B2b_Info4_decode(line,B2b_Info_mat)
                # 5. 信息类型五: PPP芯片解
            if(line[:7]== "#PPPNAV" and "FINE" in line):
                ls=line[:-1].split(',')
                lat,lon,ht=float(ls[11]),float(ls[12]),float(ls[13])+float(ls[14])
                #STA_P[0],STA_P[1],STA_P[2]=blh2xyz(lat,lon,ht)
            # 观测值读取与定位部分
            # 读到观测值
            if(line[:6]=="#OBSVM" and "FINE" in line):
                #记录观测时间
                rt_unix=gpst2time(int(line.split(";")[0].split(",")[4]),float(line.split(";")[0].split(",")[5])*0.001)
                rt_week=int(line.split(";")[0].split(",")[4])
                rt_sec=float(line.split(";")[0].split(",")[5])*0.001
                #解码本历元观测值信息
                try:
                    obs_mat=OBSVMA_Info_decode(line,f1,f2,MEO_only=MEO_only)
                    obs_mat_G=OBSVMA_Info_decode_G(line)
                    obs_mat_E=OBSVMA_Info_decode_E(line)
                except:
                    #解码失败
                    line_byte=[]#重置行列表
                    line=""
                    continue
                obs_mat=OBSVMA_Info_decode(line,f1,f2,MEO_only=MEO_only)
                obs_mat_G=OBSVMA_Info_decode_G(line)#GPS观测值单独读取
                #构建本历元有效星历与改正数匹配信息(轨钟匹配校验未开启)
                t_CNAVS,t_B2B_orbs,t_B2B_dcbs,t_B2B_clks=CNAV_B2bCorr_pair(B1C_CNAV_mat,B2b_Info_mat,GPS_LNAV_mat)
                if(sta_mode!='IGSR'):
                    spp_rr,rnx_obs,peph_sat_pos=SPP_from_B2b([[obs_mat_G,obs_mat]],0,t_CNAVS,t_B2B_orbs,t_B2B_dcbs,t_B2B_clks,
                          sat_out,                       #sat_out
                          ion_params,               #ion_params
                          sat_pcos,'IF',f1,f2,
                          el_threthod=el_threthod)
                #print(xyz2neu(spp_rr,STA_P))
                #标准单点定位(IGS-CNT模式, 以超快速产品仿真测试)
                else:
                    spp_rr,rnx_obs,peph_sat_pos=SPP_from_IGS_M([[obs_mat_G],[obs_mat]],0,IGS,CLK,
                          sat_out,                       #sat_out
                          ion_params,               #ion_params
                          sat_pcos,[[f1_G,f2_G],[f1,f2],[0,0]],'IF',
                          el_threthod=el_threthod)
                
                #无单点定位解
                if(not len(rnx_obs) or spp_rr[0]==0.0):
                    print("No valid observations, Pass epoch: Week: {}, sec: {}.".format(rt_week,rt_sec))
                    #解码失败
                    line_byte=[]#重置行列表
                    line=""
                    continue
                
                #滤波状态初始化
                if(epoch==0):
                    if(sta_mode!="IGSR"):
                        X,Pk,Qk,GF_sign,Mw_sign,slip_sign,dN_sign,X_time,phase_bias=init_UCPPP_CNAV([[obs_mat_G,obs_mat]],0,t_CNAVS,sat_out,ion_params,sat_pcos,sat_num,[[f1_G,f2_G],[f1,f2],[0,0]])
                    else:
                        X,Pk,Qk,GF_sign,Mw_sign,slip_sign,dN_sign,X_time,phase_bias=init_UCPPP_IGS_M([[obs_mat_G],[obs_mat],[obs_mat_E]],[[f1_G,f2_G],[f1,f2],[0,0]],0,IGS,CLK,sat_out,ion_params,sat_pcos)
                ##PPP状态更新
                updata_PPP_state_M(X,Pk,spp_rr,epoch,rt_unix,X_time,Qk,GF_sign,Mw_sign,slip_sign,dN_sign,GF_threshold,Mw_threshold,sat_num,rnx_obs,out_age,[[f1_G,f2_G],[f1,f2],[0,0]],dy_mode)
                epoch+=1
                #PPP时间更新
                if(sta_mode=="Base"):
                    X,Pk,Qk,X_time,v,phase_bias,rnx_obs=KF_UCPPP_RTK_Base(X,X_time,Pk,Qk,ion_params,peph_sat_pos,rnx_obs,ex_threshold_v,ex_threshold_v_sigma,rt_unix,phase_bias,[[f1_G,f2_G],[f1,f2]],STA_P,STA_Q)
                elif(sta_mode=='Rove'):
                    #从文件中读取RTK改正信息
                    X,Pk,Qk,X_time,v,phase_bias,rnx_obs=KF_UCPPP_RTK_Rove(X,X_time,Pk,Qk,ion_params,peph_sat_pos,rnx_obs,ex_threshold_v,ex_threshold_v_sigma,rt_unix,phase_bias,freqs,RTK_Info)
                else:
                    X,Pk,Qk,X_time,v,phase_bias,rnx_obs=KF_UCPPP_M(X,X_time,Pk,Qk,ion_params,peph_sat_pos,rnx_obs,ex_threshold_v,ex_threshold_v_sigma,rt_unix,phase_bias,[[f1_G,f2_G],[f1,f2],[0,0]])
                #结果保存
                Out_log.append(log2out_M(rt_unix,v,rnx_obs,X,X_time,Pk,peph_sat_pos,[[f1_G,f2_G],[f1,f2],[0,0]]))
                std_xyz=[sqrt(Pk[0][0]),sqrt(Pk[1][1]),sqrt(Pk[2][2])]
                std_neu=xyz2neu([X[0][0]+std_xyz[0],X[1][0]+std_xyz[1],X[2][0]+std_xyz[2]],[X[0][0],X[1][0],X[2][0]])
                ct=time2COMMONTIME(rt_unix)
                print()
                print([t['PRN'] for t in rnx_obs],"[{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}]".format(ct['year'],ct['month'],ct['day'],ct['hour'],ct['minute'],int(ct['second'])),len(rnx_obs),"{:.6f} {:.6f} {:.6f}".format(abs(std_neu[0]),abs(std_neu[1]),abs(std_neu[2])),end='\r')
            #处理完毕
            line=""     #清空行
            count+=1    #行数加一
        # 关闭串口
    ser.close()