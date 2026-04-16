#文件名:ppp_b2b.py
#Source File Name: ppp_b2b.py
#PPP-B2b信号和CNAV电文解析与精密轨道钟差恢复函数库
#A pure Python Core Source File for PPP-B2b deconding and Satellite SSR based Orbits/Clocks generation
#作者: 蒋卓君, 杨泽恩, 黄文静, 钱闯, 武汉理工大学
#Copyright 2025-, by Zhuojun Jiang, Zeen Yang, Wenjing Huang, Chuang Qian, Wuhan University of Technology, China

from tqdm import tqdm
from satpos import *
from RINEX import *
import sys

def RINEX2CNAV(filename):
# 函数: 读取IGMAS版本的CNAV电文并保存为字典
# 输入: RINEX格式的BDS-3 CNAV电文(IGMAS版本)
# 输出: BDSK模型参数数组; BDGIM模型发播系数数组; B1C星历数组; B2a星历数组
    ion_params_BDSK={}
    ion_params_BDGIM={}
    B1C_CNAV=[]
    B2a_CNAV=[]
    data_split={}
    cnav_line=0
    with open(filename,"r") as f:
        lines=f.readlines()
        header_in=1
        for line in lines:
            ls=line.split()
            #读取电离层参数
            if("IONOSPHERIC CORR" in line):
                #BDSK_A
                if("BDSA" in line):
                    ion_params_BDSK[ls[-4]]=[]
                    ion_params_BDSK[ls[-4]].append(float(ls[1]))
                    ion_params_BDSK[ls[-4]].append(float(ls[2]))
                    ion_params_BDSK[ls[-4]].append(float(ls[3]))
                    ion_params_BDSK[ls[-4]].append(float(ls[4]))
                #BDSK_B
                if("BDSB" in line):
                    ion_params_BDSK[ls[-4]].append(float(ls[1]))
                    ion_params_BDSK[ls[-4]].append(float(ls[2]))
                    ion_params_BDSK[ls[-4]].append(float(ls[3]))
                    ion_params_BDSK[ls[-4]].append(float(ls[4]))
                #BDGIM_1
                if("BDS1" in line):
                    ion_params_BDGIM[ls[-4]]=[]
                    ion_params_BDGIM[ls[-4]].append(float(ls[1]))
                    ion_params_BDGIM[ls[-4]].append(float(ls[2]))
                    ion_params_BDGIM[ls[-4]].append(float(ls[3]))
                #BDGIM_2
                if("BDS2" in line):
                    ion_params_BDGIM[ls[-4]].append(float(ls[1]))
                    ion_params_BDGIM[ls[-4]].append(float(ls[2]))
                    ion_params_BDGIM[ls[-4]].append(float(ls[3]))
                #BDGIM_3
                if("BDS3" in line):
                    ion_params_BDGIM[ls[-4]].append(float(ls[1]))
                    ion_params_BDGIM[ls[-4]].append(float(ls[2]))
                    ion_params_BDGIM[ls[-4]].append(float(ls[3]))
            if("END OF HEADER" in line):
                header_in=0                 #文件头读取终止
            
            if(not header_in):
                #读到BDS星历, 处理第一行
                if(line[0]=='C'):
                    #开始读取一个新的北斗星历数据块
                    cnav_line=1
                    prn=line[0:3]#卫星PRN
                    toc_y=int(line[3:3+5])#Toc年
                    toc_m=int(line[3+5:3+5+3])#Toc月
                    toc_d=int(line[3+5+3:3+5+3+3])#Toc日
                    toc_h=int(line[3+5+3+3:3+5+3+3+3])#Toc时
                    toc_min=int(line[3+5+3+3+3:3+5+3+3+3+3])#Toc分
                    toc_sec=float(line[3+5+3+3+3+3:3+5+3+3+3+3+3])#Toc秒
                    toc=epoch2time(COMMTIME(toc_y,toc_m,toc_d,toc_h,toc_min,toc_sec))#卫星钟时间(BDT)
                    a0=float(line[3+5+3+3+3+3+3:3+5+3+3+3+3+3+19])
                    a1=float(line[3+5+3+3+3+3+3+19:3+5+3+3+3+3+3+19+19])
                    a2=float(line[3+5+3+3+3+3+3+19+19:3+5+3+3+3+3+3+19+19+19])
                    data_split['prn']=prn
                    data_split['toc']=toc
                    data_split['a0']=a0
                    data_split['a1']=a1
                    data_split['a2']=a2
                    cnav_line+=1
                    continue
                #处理星历第二行
                if(cnav_line==2):
                    AODE=line[4:4+19]
                    crs=line[4+19:4+19+19]
                    delta_n0=line[4+19+19:4+19+19+19]
                    M0=line[4+19+19+19:]
                    data_split['AODE']=float(AODE)
                    data_split['crs']=float(crs)
                    data_split['delta_n0']=float(delta_n0)#临时
                    data_split['M0']=float(M0)#临时
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第三行
                if(cnav_line==3):
                    cuc=line[4:4+19]
                    e=line[4+19:4+19+19]
                    cus=line[4+19+19:4+19+19+19]
                    dA=line[4+19+19+19:]
                    data_split['cuc']=float(cuc)
                    data_split['e']=float(e)
                    data_split['cus']=float(cus)
                    data_split['dA']=float(dA)
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第四行
                if(cnav_line==4):
                    toe=line[4:4+19]            #星历参考时刻(BDT)
                    cic=line[4+19:4+19+19]
                    OMEGA0=line[4+19+19:4+19+19+19]
                    cis=line[4+19+19+19:]
                    data_split['toe']=float(toe)
                    data_split['cic']=float(cic)
                    data_split['OMEGA0']=float(OMEGA0)#临时
                    data_split['cis']=float(cis)
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第五行
                if(cnav_line==5):
                    i0=line[4:4+19]
                    crc=line[4+19:4+19+19]
                    omega=line[4+19+19:4+19+19+19]
                    OMEGA_DOT=line[4+19+19+19:]
                    data_split['i0']=float(i0)#临时
                    data_split['crc']=float(crc)
                    data_split['omega']=float(omega)#临时
                    data_split['OMEGA_DOT']=float(OMEGA_DOT)#临时
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第六行
                if(cnav_line==6):
                    IDOT=line[4:4+19]
                    Data=line[4+19:4+19+19]#电文来源
                    BDSweek=line[4+19+19:4+19+19+19]#北斗周
                    A_DOT=line[4+19+19+19:]#长半轴变化率
                    data_split['IDOT']=float(IDOT)#临时
                    data_split['Data']=round(float(Data))#电文来源1=B1C CNAV1; 2=B2b CNAV1; 4=B2a CNAV2
                    data_split['week']=round(float(BDSweek))+1356    #BDS周转GPS周, 适配旧有函数time2gpst
                    data_split['A_DOT']=float(A_DOT)
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第七行
                if(cnav_line==7):
                    SV_accuracy=line[4:4+19]
                    Health=line[4+19:4+19+19]
                    TGD=line[4+19+19:4+19+19+19]
                    ISC=line[4+19+19+19:]
                    data_split['SV_accuracy']=round(float(SV_accuracy))
                    data_split['Health']=round(float(Health))
                    data_split['TGD']=float(TGD)
                    data_split['ISC']=float(ISC)
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第八行
                if(cnav_line==8):
                    SOW=line[4:4+19]
                    IODC=line[4+19:4+19+19]
                    delta_n0_DOT=line[4+19+19:4+19+19+19]
                    Sat_Type=line[4+19+19+19:]
                    data_split['SOW']=float(SOW)
                    data_split['IODC']=round(float(IODC))
                    data_split['delta_n0_DOT']=float(delta_n0_DOT)
                    data_split['Sat_Type']=round(float(Sat_Type))#1=GEO; 2=IGSO; 3=MEO
                    
                    #星历数据读取完毕, 开始计算卫星类型相关变量
                    if(data_split['Sat_Type'] in [1,2]):
                        #GEO/IGSO
                        data_split['A']=42162200+data_split['dA']
                    else:
                        #MEO
                        data_split['A']=27906100+data_split['dA']
                    
                    #根据电文类型保存星历\
                    if(data_split['Data']==1):
                        B1C_CNAV.append(data_split.copy())
                    elif(data_split['Data']==4):
                        B2a_CNAV.append(data_split.copy())
                    else:
                        pass
                    #重置星历块
                    data_split={}
                    #print(ls)
                    cnav_line=0
                    continue    
    return ion_params_BDSK,ion_params_BDGIM,B1C_CNAV,B2a_CNAV


#RINEX4版本的星历转CNAV-1电文
def BRD4toCNAV(filename,nav_type='CNV1'):
    # 函数: 读取IGS BRD4版本的CNAV-1电文并保存为字典
    # 输入: RINEX格式的BDS-3 CNAV电文
    # 输出: B1C星历数组; B2a星历数组
    B1C_CNAV=[]
    B2a_CNAV=[]
    data_split={}
    cnav_line=0
    with open(filename,"r") as f:
        lines=f.readlines()
        header_in=1
        for line in lines:
            #文件头
            ls=line.split()
            if("END OF HEADER" in line):
                header_in=0                 #文件头读取终止
            
            if(not header_in):
                #读到BDS星历, 处理第一行
                if(line[0]=='>' and "EPH" in line and nav_type in line):
                    #读到北斗目标类型的星历导引头
                    cnav_line=1
                    continue
                if(cnav_line==1):
                    #开始读取一个新的北斗星历数据块
                    prn=line[0:3]#卫星PRN
                    toc_y=int(line[3:3+5])#Toc年
                    toc_m=int(line[3+5:3+5+3])#Toc月
                    toc_d=int(line[3+5+3:3+5+3+3])#Toc日
                    toc_h=int(line[3+5+3+3:3+5+3+3+3])#Toc时
                    toc_min=int(line[3+5+3+3+3:3+5+3+3+3+3])#Toc分
                    toc_sec=float(line[3+5+3+3+3+3:3+5+3+3+3+3+3])#Toc秒
                    toc=epoch2time(COMMTIME(toc_y,toc_m,toc_d,toc_h,toc_min,toc_sec))#卫星钟时间(BDT)
                    a0=float(line[3+5+3+3+3+3+3:3+5+3+3+3+3+3+19])
                    a1=float(line[3+5+3+3+3+3+3+19:3+5+3+3+3+3+3+19+19])
                    a2=float(line[3+5+3+3+3+3+3+19+19:3+5+3+3+3+3+3+19+19+19])
                    data_split['prn']=prn
                    data_split['toc']=toc
                    data_split['a0']=a0
                    data_split['a1']=a1
                    data_split['a2']=a2
                    cnav_line+=1
                    continue
                #处理星历第二行
                if(cnav_line==2):
                    A_DOT=line[4:4+19]
                    crs=line[4+19:4+19+19]
                    delta_n0=line[4+19+19:4+19+19+19]
                    M0=line[4+19+19+19:]
                    data_split['A_DOT']=float(A_DOT)
                    data_split['crs']=float(crs)
                    data_split['delta_n0']=float(delta_n0)#临时
                    data_split['M0']=float(M0)#临时
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第三行
                if(cnav_line==3):
                    cuc=line[4:4+19]
                    e=line[4+19:4+19+19]
                    cus=line[4+19+19:4+19+19+19]
                    sqrtA=line[4+19+19+19:]
                    data_split['cuc']=float(cuc)
                    data_split['e']=float(e)
                    data_split['cus']=float(cus)
                    data_split['sqrtA']=float(sqrtA)
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第四行
                if(cnav_line==4):
                    toe=line[4:4+19]            #星历参考时刻(BDT)
                    cic=line[4+19:4+19+19]
                    OMEGA0=line[4+19+19:4+19+19+19]
                    cis=line[4+19+19+19:]
                    data_split['toe']=float(toe)
                    data_split['cic']=float(cic)
                    data_split['OMEGA0']=float(OMEGA0)#临时
                    data_split['cis']=float(cis)
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第五行
                if(cnav_line==5):
                    i0=line[4:4+19]
                    crc=line[4+19:4+19+19]
                    omega=line[4+19+19:4+19+19+19]
                    OMEGA_DOT=line[4+19+19+19:]
                    data_split['i0']=float(i0)#临时
                    data_split['crc']=float(crc)
                    data_split['omega']=float(omega)#临时
                    data_split['OMEGA_DOT']=float(OMEGA_DOT)#临时
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第六行
                if(cnav_line==6):
                    IDOT=line[4:4+19]
                    delta_n0_DOT=line[4+19:4+19+19]     #
                    Sat_Type=line[4+19+19:4+19+19+19]    #卫星类型
                    t_top=line[4+19+19+19:]             #t_top
                    data_split['IDOT']=float(IDOT)      #临时
                    data_split['delta_n0_DOT']=float(delta_n0_DOT)  
                    data_split['Sat_Type']=round(float(Sat_Type))    #卫星类型
                    data_split['t_top']=float(t_top)
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第七行
                if(cnav_line==7):
                    SISAI_oe=line[4:4+19]
                    SISAI_ocb=line[4+19:4+19+19]
                    SISAI_oc1=line[4+19+19:4+19+19+19]
                    SISAI_oc2=line[4+19+19+19:]
                    data_split['SISAI_oe']=float(SISAI_oe)
                    data_split['SISAI_ocb']=float(SISAI_ocb)
                    data_split['SISAI_oc1']=float(SISAI_oc1)
                    data_split['SISAI_oc2']=float(SISAI_oc2)
                    #print(ls)
                    cnav_line+=1
                    continue
                #处理星历第八行
                if(cnav_line==8):
                    ISC_B1Cd=line[4:4+19]
                    #IODC=line[4+19:4+19+19]
                    TGD_B1Cp=line[4+19+19:4+19+19+19]
                    TGD_B2ap=line[4+19+19+19:]
                    data_split['ISC_B1Cd']=float(ISC_B1Cd)
                    data_split['TGD_B1Cp']=float(TGD_B1Cp)
                    data_split['TGD_B2ap']=float(TGD_B2ap)
                    cnav_line+=1
                    continue
                #处理星历第九行
                if(cnav_line==9):
                    SISNAI=line[4:4+19]
                    Health=line[4+19:4+19+19]
                    B1C_Inter_flag=line[4+19+19:4+19+19+19]
                    IODC=line[4+19+19+19:]
                    data_split['SISNAV']=float(SISNAI)
                    data_split['Health']=round(float(Health))
                    data_split['B1C_Inter_flag']=float(B1C_Inter_flag)
                    data_split['IODC']=round(float(IODC))
                    cnav_line+=1
                    continue
                #处理星历第十行
                if(cnav_line==10):
                    t_tm=line[4:4+19]
                    #Health=line[4+19:4+19+19]
                    #B1C_Inter_flag=line[4+19+19:4+19+19+19]
                    IODE=line[4+19+19+19:]
                    data_split['t_tm']=float(t_tm)
                    data_split['IODE']=round(float(IODE))

                    #星历数据读取完毕, 开始计算卫星类型相关变量(BRD4中将dA协议吸收回sqrtA协议)
                    if(data_split['Sat_Type'] in [1,2]):
                        #GEO/IGSO
                        data_split['A']=data_split['sqrtA']*data_split['sqrtA']
                    else:
                        #MEO
                        data_split['A']=data_split['sqrtA']*data_split['sqrtA']
                    
                    #补充星历块中缺失的GPS周
                    data_split['week']=time2gpst(toc)[0]
                    
                    #根据电文类型保存星历\
                    if(nav_type=='CNV1'):
                        data_split['Data']=1
                        data_split['TGD']=data_split['TGD_B1Cp']
                        data_split['ISC']=data_split['ISC_B1Cd']
                        B1C_CNAV.append(data_split.copy())
                    elif(nav_type=='CNV2'):
                        data_split['Data']=4
                        data_split['TGD']=data_split['TGD_B2ap']
                        B2a_CNAV.append(data_split.copy())
                    else:
                        pass
                    #重置星历块
                    data_split={}
                    #print(ls)
                    cnav_line=0
                    continue    
    return B1C_CNAV,B2a_CNAV

#RINEX4版本的星历转LNAV电文
def BRD4toLNAV(filename,nav_type='LNAV'):
    # 函数: 读取LNAV电文并保存为字典
    # 输入: IGS BRD4格式的多系统导航文件
    # 输出: GPS LNAV星历数组
    GPS_LNAV=[]
    data_split={}
    lnav_line=0
    with open(filename,"r") as f:
        lines=f.readlines()
        header_in=1
        for line in lines:
            #文件头
            ls=line.split()
            if("END OF HEADER" in line):
                header_in=0                 #文件头读取终止
            
            if(not header_in):
                #读到GPS星历, 处理第一行
                if(line[0]=='>' and "EPH" in line and nav_type in line and 'G' in line):
                    #读到GPS目标类型的星历导引头
                    lnav_line=1
                    continue
                if(lnav_line==1):
                    #开始读取一个新的GPS星历数据块
                    prn=line[0:3]#卫星PRN
                    toc_y=int(line[3:3+5])#Toc年
                    toc_m=int(line[3+5:3+5+3])#Toc月
                    toc_d=int(line[3+5+3:3+5+3+3])#Toc日
                    toc_h=int(line[3+5+3+3:3+5+3+3+3])#Toc时
                    toc_min=int(line[3+5+3+3+3:3+5+3+3+3+3])#Toc分
                    toc_sec=float(line[3+5+3+3+3+3:3+5+3+3+3+3+3])#Toc秒
                    toc=epoch2time(COMMTIME(toc_y,toc_m,toc_d,toc_h,toc_min,toc_sec))#卫星钟时间(BDT)
                    a0=float(line[3+5+3+3+3+3+3:3+5+3+3+3+3+3+19])
                    a1=float(line[3+5+3+3+3+3+3+19:3+5+3+3+3+3+3+19+19])
                    a2=float(line[3+5+3+3+3+3+3+19+19:3+5+3+3+3+3+3+19+19+19])
                    data_split['prn']=prn
                    data_split['toc']=toc
                    data_split['a0']=a0
                    data_split['a1']=a1
                    data_split['a2']=a2
                    lnav_line+=1
                    continue
                #处理星历第二行
                if(lnav_line==2):
                    IODE=line[4:4+19]
                    crs=line[4+19:4+19+19]
                    delta_n0=line[4+19+19:4+19+19+19]
                    M0=line[4+19+19+19:]
                    data_split['IODE']=round(float(IODE))
                    data_split['crs']=float(crs)
                    data_split['delta_n0']=float(delta_n0)#临时
                    data_split['M0']=float(M0)#临时
                    #print(ls)
                    lnav_line+=1
                    continue
                #处理星历第三行
                if(lnav_line==3):
                    cuc=line[4:4+19]
                    e=line[4+19:4+19+19]
                    cus=line[4+19+19:4+19+19+19]
                    sqrtA=line[4+19+19+19:]
                    data_split['cuc']=float(cuc)
                    data_split['e']=float(e)
                    data_split['cus']=float(cus)
                    data_split['sqrtA']=float(sqrtA)
                    #print(ls)
                    lnav_line+=1
                    continue
                #处理星历第四行
                if(lnav_line==4):
                    toe=line[4:4+19]            #星历参考时刻(BDT)
                    cic=line[4+19:4+19+19]
                    OMEGA0=line[4+19+19:4+19+19+19]
                    cis=line[4+19+19+19:]
                    data_split['toe']=float(toe)
                    data_split['cic']=float(cic)
                    data_split['OMEGA0']=float(OMEGA0)#临时
                    data_split['cis']=float(cis)
                    #print(ls)
                    lnav_line+=1
                    continue
                #处理星历第五行
                if(lnav_line==5):
                    i0=line[4:4+19]
                    crc=line[4+19:4+19+19]
                    omega=line[4+19+19:4+19+19+19]
                    OMEGA_DOT=line[4+19+19+19:]
                    data_split['i0']=float(i0)#临时
                    data_split['crc']=float(crc)
                    data_split['omega']=float(omega)#临时
                    data_split['OMEGA_DOT']=float(OMEGA_DOT)#临时
                    #print(ls)
                    lnav_line+=1
                    continue
                #处理星历第六行
                if(lnav_line==6):
                    IDOT=line[4:4+19]
                    Codes_on_L2_channel=line[4+19:4+19+19]     #
                    week=line[4+19+19:4+19+19+19]    #卫星类型
                    L2_P_data_flag=line[4+19+19+19:]             #t_top
                    data_split['IDOT']=float(IDOT)      #临时
                    data_split['Codes_on_L2_channel']=float(Codes_on_L2_channel)  
                    data_split['week']=round(float(week))    #卫星类型
                    data_split['L2_P_data_flag']=float(L2_P_data_flag)
                    #print(ls)
                    lnav_line+=1
                    continue
                #处理星历第七行
                if(lnav_line==7):
                    SV_accuracy=line[4:4+19]
                    Health=line[4+19:4+19+19]
                    TGD=line[4+19+19:4+19+19+19]
                    IODC=line[4+19+19+19:]
                    data_split['SV_accuracy']=float(SV_accuracy)
                    data_split['Health']=round(float(Health))
                    data_split['TGD']=float(TGD)
                    data_split['IODC']=round(float(IODC))
                    #print(ls)
                    lnav_line+=1
                    continue
                #处理星历第八行
                if(lnav_line==8):
                    t_tm=line[4:4+19]
                    #Fit=line[4+19:4+19+19]
                    #B1C_Inter_flag=line[4+19+19:4+19+19+19]
                    #Fit=line[4+19+19+19:]
                    data_split['t_tm']=float(t_tm)
                    #data_split['Fit']=round(float(Fit))

                    #星历数据读取完毕, 开始计算卫星类型相关变量
                    data_split['A']=data_split['sqrtA']*data_split['sqrtA']
                    data_split['A_DOT']=0.0
                    data_split['delta_n0_DOT']=0.0
                    GPS_LNAV.append(data_split.copy())

                    #重置星历块
                    data_split={}
                    #print(ls)
                    lnav_line=0
                    continue    
        print("")
    return GPS_LNAV

#CRC32校验
def crc32_c_style(buff, poly=0xEDB88320):
    """
    POLYCRC32通常为0xEDB8832 (IEEE 802.3标准)
    """
    crc = 0
    for i in range(len(buff)):
        crc ^= buff[i]
        for j in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
    return crc

def CNAV2SatPVC(B1C_CNAV,rt,prn,iodc=None,rho=0):
    #函数: 根据CNAV星历计算卫星位置
    #输入: 导航电文, 观测时间(GPST), 卫星PRN, 可选参数: 星历编号
    #输出: 卫星位置, 速度, 钟差, 钟速
    GM_BDS=3.986004418e14   #BDCS地球引力常数
    OMGE_BDS= 7.2921150e-5  #BDCS地球自转速度

    #首先确定目标星历
    cnav_rts=[t['toc'] for t in B1C_CNAV]
    rt_hour=int(rt/3600)*3600   #目标星历秒数
    id=cnav_rts.index(rt_hour)
    satellite={}
    #GPST转BDST
    rt=rt-14
    for i in range(id,id+65):
        if(B1C_CNAV[i]['toc']!=rt_hour):
            break
        if(B1C_CNAV[i]['prn']==prn):
            satellite=B1C_CNAV[i]
            break
    #根据IODC编制
    if(iodc!=None):
        flag=0
        for i in range(len(B1C_CNAV)):
            if(B1C_CNAV[i]['IODC']==iodc and B1C_CNAV[i]['prn']==prn):
                satellite=B1C_CNAV[i]
                flag=1
                break
        if(not flag):
            print("Warning: IODC {} not match".format(iodc))
    #星历存在性与有效性校验
    if(satellite=={}):# or satellite['Health']!=0):
        print(rt,"No",prn)
        return False
    ##开始计算卫星位置
    toe=gpst2time(satellite['week'],satellite['toe'])
    toc=satellite['toc']
    #计算卫星轨道长半轴
    A=satellite['A']
    #计算参考时刻的平均运动角速度
    n0 =sqrt(GM_BDS/A/A/A)
    #计算相对星历参考历元的时间
    tk=rt-rho/clight-toe#(satellite['a0']+satellite['a1']*(rt-toe)+satellite['a2']*((rt-toe)**2))+satellite['TGD']-toe
    if(tk>302400):
        tk=tk-604800
    elif(tk<-302400):
        tk=tk+604800
    else:
        tk=tk
    #计算长半轴
    Ak=A+satellite['A_DOT']*tk
    #计算卫星平均运动角速度的偏差
    dnA=satellite['delta_n0']+0.5*satellite['delta_n0_DOT']*tk
    #计算改正后的卫星平均角速度
    n=n0+dnA
    #计算平近点角
    Mk=satellite['M0']+n*tk
    #迭代计算偏近点角
    Ek=Mk
    Ek1=0.0
    ek_count=0
    while(1):
        Ek1=Mk+satellite['e']*sin(Ek)
        ek_count+=1
        if(abs(Ek1-Ek)<1e-13):# or ek_count>200):
            break  
        Ek=Ek1
    Ek=Ek1
    #计算真近点角
    vk = atan2(sqrt(1-satellite['e']*satellite['e'])*sin(Ek)/(1-satellite['e']*cos(Ek)), (cos(Ek)-satellite['e'])/(1-satellite['e']*cos(Ek)))
    #计算升交点角距Phik
    Phik=vk+satellite['omega']
    #计算二阶调和改正数
    deltauk = satellite['cus'] * sin(2 * Phik) + satellite['cuc'] * cos(2 * Phik)
    deltark = satellite['crs'] * sin(2 * Phik) + satellite['crc'] * cos(2 * Phik)
    deltaik = satellite['cis'] * sin(2 * Phik) + satellite['cic'] * cos(2 * Phik)
    #计算改进的升交角距
    uk=Phik+deltauk
    #计算改进的向径
    rk= Ak * (1- satellite['e'] * cos(Ek)) + deltark;   
    #计算改正的轨道倾角
    ik = satellite['i0'] + deltaik + satellite['IDOT'] * tk
    #计算卫星在轨道平面内的坐标
    xk1 = rk * cos(uk)
    yk1 = rk * sin(uk)
    #计算经过改正的升交点经度(MEO/IGSO)
    Omegak = satellite['OMEGA0'] + (satellite['OMEGA_DOT']- OMGE_BDS) * tk- OMGE_BDS *satellite['toe']
    #计算IGSO/MEO卫星在BDCS-ECEF下的位置
    Xk=xk1*cos(Omegak)-yk1*cos(ik)*sin(Omegak)
    Yk=xk1*sin(Omegak)+yk1*cos(ik)*cos(Omegak)
    Zk=yk1*sin(ik)

    ##开始计算卫星速度
    #计算偏近点角的时间导数
    dotEk=n/(1-satellite['e']*cos(Ek))
    #计算真近点角的时间导数
    dotvk=sqrt((1+satellite['e'])/(1-satellite['e']))*cos(vk/2)*cos(vk/2)/cos(Ek/2)/cos(Ek/2)*dotEk
    #计算升交角距的时间导数
    dotuk=dotvk*(1+2*satellite['cus']*cos(2*Phik)-2*satellite['cuc']*sin(2*Phik))
    #计算向径的时间导数
    dotrk=dotEk*Ak*satellite['e']*sin(Ek)+2*dotvk*(satellite['crs']*cos(2*Phik)-satellite['crc']*sin(2*Phik))
    #计算轨道倾角的时间导数
    dotik=satellite['IDOT']+2*dotvk*(satellite['cis']*cos(2*Phik)-satellite['cic']*sin(2*Phik))
    #计算卫星轨道平面位置的时间导数
    dotxk = cos(uk) * dotrk- rk * sin(uk) * dotuk
    dotyk = sin(uk) * dotrk + rk * cos(uk) * dotuk
    #计算卫星在BDCS-ECEF下的速度
    dotR12=[[cos(Omegak),-sin(Omegak)*cos(ik),-xk1*sin(Omegak)-yk1*cos(Omegak)*cos(ik), yk1*sin(Omegak)*sin(ik)],
            [sin(Omegak), cos(Omegak)*cos(ik), xk1*cos(Omegak)-yk1*sin(Omegak)*cos(ik),-yk1*cos(Omegak)*sin(ik)],
            [0,sin(ik),0,Yk*cos(ik)]]
    tx=[[dotxk],[dotyk],[satellite['OMEGA_DOT']-OMGE_BDS],[dotik]]
    dxyz=np.array(dotR12).dot(np.array(tx))
    #
    #计算卫星钟差&钟速
    #tdts=satellite['a0']+satellite['a1']*(rt-toe)+satellite['a2']*((rt-toe)**2)
    Fclk=-2*sqrt(GM_BDS)/clight/clight*satellite['e']*sqrt(Ak)*sin(Ek)#相对论效应
    tdts=satellite['a0']+satellite['a1']*(rt-toc)+satellite['a2']*((rt-toc)**2)#-satellite['TGD']
    tdtss=satellite['a1']+2*satellite['a2']*(rt-toc)
    return [Xk,Yk,Zk,tdts,float(dxyz[0][0]),float(dxyz[1][0]),float(dxyz[2][0]),tdtss]


def IODC2SatPVC(satellite,rt,prn,iodc,rho=0):
    #函数: 根据单个星历块计算卫星位置
    #输入: 导航电文, 观测时间(GPST), 卫星PRN, 星历种编号, 伪距
    #输出: 卫星位置, 速度, 钟差, 钟速
    GM_BDS=3.986004418e14   #BDCS地球引力常数
    OMGE_BDS= 7.2921150e-5  #BDCS地球自转速度
    if(prn[0]=='G'):
        OMGE_BDS=7.2921151467e-5        #GPS星历地球引力常数
        GM_BDS= 3.986005e14             #GPS星历地球自转速度
    #GPST转BDST
    if(prn[0]=='C'):
        rt=rt-14
    #根据IODC编制
    if(iodc!=None):
        flag=0
        if(satellite['IODC']==iodc and satellite['prn']==prn):
            flag=1
        if(not flag):
            print("Warning: IODC {} not match".format(iodc))
    #星历存在性与有效性校验
    if(satellite=={}):# or satellite['Health']!=0):
        print(rt,"No",prn)
        return False
    ##开始计算卫星位置
    toe=gpst2time(satellite['week'],satellite['toe'])
    toc=satellite['toc']
    #计算卫星轨道长半轴
    A=satellite['A']
    #计算参考时刻的平均运动角速度
    n0 =sqrt(GM_BDS/A/A/A)
    #计算相对星历参考历元的时间
    tk=rt-rho/clight-toe-(satellite['a0']+satellite['a1']*(rt-toe)+satellite['a2']*((rt-toe)**2))
    if(tk>302400):
        tk=tk-604800
    elif(tk<-302400):
        tk=tk+604800
    else:
        tk=tk
    #计算长半轴
    Ak=A+satellite['A_DOT']*tk
    #计算卫星平均运动角速度的偏差
    dnA=satellite['delta_n0']+0.5*satellite['delta_n0_DOT']*tk
    #计算改正后的卫星平均角速度
    n=n0+dnA
    #计算平近点角
    Mk=satellite['M0']+n*tk
    #迭代计算偏近点角
    Ek=Mk
    Ek1=0.0
    ek_count=0
    while(1):
        Ek1=Mk+satellite['e']*sin(Ek)
        ek_count+=1
        if(abs(Ek1-Ek)<1e-13):# or ek_count>200):
            break  
        Ek=Ek1
    Ek=Ek1
    #计算真近点角
    vk = atan2(sqrt(1-satellite['e']*satellite['e'])*sin(Ek)/(1-satellite['e']*cos(Ek)), (cos(Ek)-satellite['e'])/(1-satellite['e']*cos(Ek)))
    #计算升交点角距Phik
    Phik=vk+satellite['omega']
    #计算二阶调和改正数
    deltauk = satellite['cus'] * sin(2 * Phik) + satellite['cuc'] * cos(2 * Phik)
    deltark = satellite['crs'] * sin(2 * Phik) + satellite['crc'] * cos(2 * Phik)
    deltaik = satellite['cis'] * sin(2 * Phik) + satellite['cic'] * cos(2 * Phik)
    #计算改进的升交角距
    uk=Phik+deltauk
    #计算改进的向径
    rk= Ak * (1- satellite['e'] * cos(Ek)) + deltark;   
    #计算改正的轨道倾角
    ik = satellite['i0'] + deltaik + satellite['IDOT'] * tk
    #计算卫星在轨道平面内的坐标
    xk1 = rk * cos(uk)
    yk1 = rk * sin(uk)
    #计算经过改正的升交点经度(MEO/IGSO)
    Omegak = satellite['OMEGA0'] + (satellite['OMEGA_DOT']- OMGE_BDS) * tk- OMGE_BDS *satellite['toe']
    #计算IGSO/MEO卫星在BDCS-ECEF下的位置
    Xk=xk1*cos(Omegak)-yk1*cos(ik)*sin(Omegak)
    Yk=xk1*sin(Omegak)+yk1*cos(ik)*cos(Omegak)
    Zk=yk1*sin(ik)

    ##开始计算卫星速度
    #计算偏近点角的时间导数
    dotEk=n/(1-satellite['e']*cos(Ek))
    #计算真近点角的时间导数
    dotvk=sqrt((1+satellite['e'])/(1-satellite['e']))*cos(vk/2)*cos(vk/2)/cos(Ek/2)/cos(Ek/2)*dotEk
    #计算升交角距的时间导数
    dotuk=dotvk*(1+2*satellite['cus']*cos(2*Phik)-2*satellite['cuc']*sin(2*Phik))
    #计算向径的时间导数
    dotrk=dotEk*Ak*satellite['e']*sin(Ek)+2*dotvk*(satellite['crs']*cos(2*Phik)-satellite['crc']*sin(2*Phik))
    #计算轨道倾角的时间导数
    dotik=satellite['IDOT']+2*dotvk*(satellite['cis']*cos(2*Phik)-satellite['cic']*sin(2*Phik))
    #计算卫星轨道平面位置的时间导数
    dotxk = cos(uk) * dotrk- rk * sin(uk) * dotuk
    dotyk = sin(uk) * dotrk + rk * cos(uk) * dotuk
    #计算卫星在BDCS-ECEF下的速度
    dotR12=[[cos(Omegak),-sin(Omegak)*cos(ik),-xk1*sin(Omegak)-yk1*cos(Omegak)*cos(ik), yk1*sin(Omegak)*sin(ik)],
            [sin(Omegak), cos(Omegak)*cos(ik), xk1*cos(Omegak)-yk1*sin(Omegak)*cos(ik),-yk1*cos(Omegak)*sin(ik)],
            [0,sin(ik),0,Yk*cos(ik)]]
    tx=[[dotxk],[dotyk],[satellite['OMEGA_DOT']-OMGE_BDS],[dotik]]
    dxyz=np.array(dotR12).dot(np.array(tx))

    #计算卫星钟差&钟速
    #tdts=satellite['a0']+satellite['a1']*(rt-toe)+satellite['a2']*((rt-toe)**2)
    Fclk=-2*sqrt(GM_BDS)/clight/clight*satellite['e']*sqrt(Ak)*sin(Ek)                  #相对论效应
    tdts=satellite['a0']+satellite['a1']*(rt-toc)+satellite['a2']*((rt-toc)**2)+Fclk    #-satellite['TGD']
    tdtss=satellite['a1']+2*satellite['a2']*(rt-toc)
    return [Xk,Yk,Zk,tdts,float(dxyz[0][0]),float(dxyz[1][0]),float(dxyz[2][0]),tdtss]


#函数: 将CNAV字典转换为ASCII码格式的实时流
def encode_BD3EPH(B1C_CNAV):
    bds_eph_lines,bdseph_line_times=[],[]
    iodc_prns,iode_prns=[[] for t in range(66)],[[] for t in range(66)]#设立IODC/IODE已编制列表
    for i in range(len(B1C_CNAV)):
    #if(B1C_CNAV[i]['toc']==1710720000.0+24*3600):
        line=[]
        line.append("#BD3EPH,")
        line.append("77,")
        line.append("GPS,")
        line.append("FINE,")
        line.append('{},'.format(B1C_CNAV[i]['week']))
        line.append("{},".format(round(B1C_CNAV[i]['t_tm']*1000))) #星历发布时间
        line.append('0,')
        line.append('0,')
        line.append('18,')
        line.append('4;')
        line.append("{},".format(int(B1C_CNAV[i]['prn'][1:])))
        line.append("{},".format(B1C_CNAV[i]['Health']))
        line.append("{},".format(B1C_CNAV[i]['Sat_Type']))
        line.append("{},".format(15))
        line.append("{},".format(B1C_CNAV[i]['IODE']))
        line.append("{},".format(B1C_CNAV[i]['IODC']))
        
        #排除已经存在对应版本号的星历
        if(B1C_CNAV[i]['IODE'] in iode_prns[int(B1C_CNAV[i]['prn'][1:])] and B1C_CNAV[i]['IODC'] in iodc_prns[int(B1C_CNAV[i]['prn'][1:])]):
            continue
        iode_prns[int(B1C_CNAV[i]['prn'][1:])].append(B1C_CNAV[i]['IODE'])
        iodc_prns[int(B1C_CNAV[i]['prn'][1:])].append(B1C_CNAV[i]['IODC'])
        
        line.append("{},".format(B1C_CNAV[i]['week']))
        line.append("{},".format(B1C_CNAV[i]['week']))
        line.append("{:.1f},".format(B1C_CNAV[i]['toe']))
        line.append("{:.1f},".format(B1C_CNAV[i]['toe']))
        if(B1C_CNAV[i]['Sat_Type']==3):
            line.append("{:.9e},".format(B1C_CNAV[i]['A']-27906100))    #MEO卫星
        else:   
            line.append("{:.9e},".format(B1C_CNAV[i]['A']-42162200))    #IGSO/GEO卫星
        line.append("{:.9e},".format(B1C_CNAV[i]['A_DOT']))
        line.append("{:.9e},".format(B1C_CNAV[i]['delta_n0']))
        line.append("{:.9e},".format(B1C_CNAV[i]['delta_n0_DOT']))
        line.append("{:.9e},".format(B1C_CNAV[i]['M0']))
        line.append("{:.9e},".format(B1C_CNAV[i]['e']))
        line.append("{:.9e},".format(B1C_CNAV[i]['omega']))
        line.append("{:.9e},".format(B1C_CNAV[i]['cuc']))
        line.append("{:.9e},".format(B1C_CNAV[i]['cus'])) 
        line.append("{:.9e},".format(B1C_CNAV[i]['crc'])) 
        line.append("{:.9e},".format(B1C_CNAV[i]['crs'])) 
        line.append("{:.9e},".format(B1C_CNAV[i]['cic'])) 
        line.append("{:.9e},".format(B1C_CNAV[i]['cis'])) 
        line.append("{:.9e},".format(B1C_CNAV[i]['i0'])) 
        line.append("{:.9e},".format(B1C_CNAV[i]['IDOT'])) 
        line.append("{:.9e},".format(B1C_CNAV[i]['OMEGA0']))  
        line.append("{:.9e},".format(B1C_CNAV[i]['OMEGA_DOT']))  
        line.append("{:.9e},".format(B1C_CNAV[i]['toe']))  
        line.append("{:.9e},".format(B1C_CNAV[i]['TGD_B1Cp']))  
        line.append("{:.9e},".format(B1C_CNAV[i]['TGD_B2ap']))  
        line.append("{:.9e},".format(0.0))   
        line.append("{:.9e},".format(0.0))   
        line.append("{:.9e},".format(0.0))   
        line.append("{:.9e},".format(B1C_CNAV[i]['ISC_B1Cd']))   
        line.append("{:.9e},".format(B1C_CNAV[i]['a0']))   
        line.append("{:.9e},".format(B1C_CNAV[i]['a1']))   
        line.append("{:.9e},".format(B1C_CNAV[i]['a2']))   
        line.append("{:.0f},".format(B1C_CNAV[i]['t_top']))   
        line.append("{:.0f},".format(B1C_CNAV[i]['SISAI_oe']))   
        line.append("{:.0f},".format(B1C_CNAV[i]['SISAI_ocb']))   
        line.append("{:.0f},".format(B1C_CNAV[i]['SISAI_oc1']))   
        line.append("{:.0f},".format(B1C_CNAV[i]['SISAI_oc2']))   
        line.append("{},".format(0))   
        line.append("{},".format(0))   
        line.append("{}".format(0))

        #计算CRC校验码
        total_line=""
        for d in line:
            total_line+=d
        crc=hex(crc32_c_style(total_line[1:].encode()))[2:]

        line.append("*{}\n".format(crc))   
        bds_eph_lines.append(line.copy())
        bdseph_line_times.append(gpst2time(B1C_CNAV[i]['week'],B1C_CNAV[i]['t_tm']))
    #返回ACIIC流
    return bds_eph_lines,bdseph_line_times

#函数: 将GPS系统LNAV星历字典转换为ASCII码格式的实时流
def encode_GPSEPH(GPS_LNAV):
    gps_eph_lines,gpseph_line_times=[],[]
    for i in range(len(GPS_LNAV)):
    #if(B1C_CNAV[i]['toc']==1710720000.0+24*3600):
        line=[]
        line.append("#GPSEPH,")
        line.append("97,")
        line.append("GPS,")
        line.append("FINE,")
        line.append('{},'.format(GPS_LNAV[i]['week']))
        line.append("{},".format(round(GPS_LNAV[i]['t_tm']*1000)))  #星历发布时间
        gpseph_line_times.append(gpst2time(GPS_LNAV[i]['week'],GPS_LNAV[i]['t_tm']))
        line.append('0,')
        line.append('0,')
        line.append('18,')
        line.append('4;')
        line.append("{},".format(int(GPS_LNAV[i]['prn'][1:])))
        line.append("{:.1f},".format(GPS_LNAV[i]['toe']))#用TOE代替TOW
        line.append("{},".format(GPS_LNAV[i]['Health']))
        line.append("{},".format(GPS_LNAV[i]['IODE']))
        line.append("{},".format(GPS_LNAV[i]['IODE']))
        line.append("{},".format(GPS_LNAV[i]['week']))
        line.append("{},".format(GPS_LNAV[i]['week']))
        line.append("{:.1f},".format(GPS_LNAV[i]['toe']))
        line.append("{:.9e},".format(GPS_LNAV[i]['A']))
        line.append("{:.9e},".format(GPS_LNAV[i]['delta_n0']))
        line.append("{:.9e},".format(GPS_LNAV[i]['M0']))
        line.append("{:.9e},".format(GPS_LNAV[i]['e']))
        line.append("{:.9e},".format(GPS_LNAV[i]['omega']))
        line.append("{:.9e},".format(GPS_LNAV[i]['cuc']))
        line.append("{:.9e},".format(GPS_LNAV[i]['cus'])) 
        line.append("{:.9e},".format(GPS_LNAV[i]['crc'])) 
        line.append("{:.9e},".format(GPS_LNAV[i]['crs'])) 
        line.append("{:.9e},".format(GPS_LNAV[i]['cic'])) 
        line.append("{:.9e},".format(GPS_LNAV[i]['cis'])) 
        line.append("{:.9e},".format(GPS_LNAV[i]['i0'])) 
        line.append("{:.9e},".format(GPS_LNAV[i]['IDOT'])) 
        line.append("{:.9e},".format(GPS_LNAV[i]['OMEGA0']))  
        line.append("{:.9e},".format(GPS_LNAV[i]['OMEGA_DOT']))  
        line.append("{},".format(GPS_LNAV[i]['IODC']))  
        line.append("{:.1f},".format(GPS_LNAV[i]['toe']))  
        line.append("{:.9e},".format(GPS_LNAV[i]['TGD']))    
        line.append("{:.9e},".format(GPS_LNAV[i]['a0']))   
        line.append("{:.9e},".format(GPS_LNAV[i]['a1']))   
        line.append("{:.9e},".format(GPS_LNAV[i]['a2']))     
        line.append("{},".format(0))   
        line.append("{:.9e},".format(0))   #改正的平均角速度(赋值为0)
        line.append("{:.9e}".format(0))        #URA, 赋值为零
        
        #计算CRC校验码
        total_line=""
        for d in line:
            total_line+=d
        crc=hex(crc32_c_style(total_line[1:].encode()))[2:]
        line.append("*{}\n".format(crc))   
        gps_eph_lines.append(line.copy())
    #返回ASCII码流
    return gps_eph_lines,gpseph_line_times

#函数: 将Easy4PNT格式的观测值字典转换为实时原始观测值ASCII流
def encode_OBSVMA(obs_mat,obs_mat_G=[],obs_mat_E=[],obs_interval=30):
    obs_lines,obs_line_times=[],[]
    split=obs_interval
    for i in range(len(obs_mat)):
        obs=obs_mat[i]
        obs_G=obs_mat_G[i]
        #数据头
        line=[]
        line.append("#OBSVMA,")
        line.append("12,")
        line.append("GPS,")
        line.append("FINE,")
        line.append("{},".format(obs[0]['GPSweek']))
        line.append("{:.0f},".format(obs[0]['GPSsec']*1000))
        obs_line_times.append(gpst2time(obs[0]['GPSweek'],obs[0]['GPSsec']))
        if(obs[0]['GPSsec']%split!=0.0):
            continue
        line.append("0,")
        line.append("0,")
        line.append("18,")
        line.append("17;")
        #数据体
        line.append("{},".format(len(obs[1])*2+len(obs_G[1])*2))
        count=0
    
        for sat in obs_G[1]:
            count+=1
            #L1上观测值
            line.append('0,')
            line.append("{},".format(int(sat['PRN'][1:])))
            line.append("{:.3f},".format(sat['OBS'][0]))
            line.append("{:.6f},".format(sat['OBS'][1]))
            line.append("{:.0f},".format(30))
            line.append("{:.0f},".format(30))
            line.append("{:.3f},".format(sat['OBS'][3]))
            line.append("{:.0f},".format(sat['OBS'][4]*100))
            line.append("0,")
            line.append("{:.3f},".format(100))
            line.append("00000000,")
            #L2上观测值
            line.append("0,")
            line.append("{},".format(int(sat['PRN'][1:])))
            line.append("{:.3f},".format(sat['OBS'][5]))
            line.append("{:.6f},".format(sat['OBS'][6]))
            line.append("{:.0f},".format(30))
            line.append("{:.0f},".format(30))
            line.append("{:.3f},".format(sat['OBS'][8]))
            line.append("{:.0f},".format(sat['OBS'][9]*100))
            line.append("0,")
            line.append("{:.3f},".format(100))
            line.append("00000000,")

        count=0
        for sat in obs[1]:
            count+=1
            #B1I上观测值
            line.append('0,')
            line.append("{},".format(int(sat['PRN'][1:])))
            line.append("{:.3f},".format(sat['OBS'][0]))
            line.append("{:.6f},".format(sat['OBS'][1]))
            line.append("{:.0f},".format(30))
            line.append("{:.0f},".format(30))
            line.append("{:.3f},".format(sat['OBS'][3]))
            line.append("{:.0f},".format(sat['OBS'][4]*100))
            line.append("0,")
            line.append("{:.0f},".format(100))
            line.append("00288000,")
            #B3I上观测值
            line.append("0,")
            line.append("{},".format(int(sat['PRN'][1:])))
            line.append("{:.3f},".format(sat['OBS'][5]))
            line.append("{:.6f},".format(sat['OBS'][6]))
            line.append("{:.0f},".format(30))
            line.append("{:.0f},".format(30))
            line.append("{:.3f},".format(sat['OBS'][8]))
            line.append("{:.0f},".format(sat['OBS'][9]*100))
            line.append("0,")
            line.append("{:.3f},".format(100))
        
            if(count==len(obs[1])):
                #计算CRC校验码
                total_line=""
                for d in line:
                    total_line+=d
                crc=hex(crc32_c_style(total_line[1:].encode()))[2:]
                line.append("00000000*{}\n".format(crc))      #由于ASCII码跟踪通道设置问题, 所有的跟踪通道均设置为00000000
            else:
                line.append("00000000,")        
        obs_lines.append(line.copy())
    #返回原始观测值消息的ASCII码流
    return obs_lines,obs_line_times

#函数: 将原始的由Unicore接收机接收得到的 ASCII格式的 B2bInfo log文件转写为标准的LOG流并记录时间
def encode_B2BINFO(filename):
    b2b_lines,b2b_line_times=[],[]
    with open(filename,'r') as f:
        b2b_lines=f.readlines()
        for line in b2b_lines:
            b2b_line_times.append(gpst2time(int(line.split(",")[4]),float(line.split(',')[5])/1000))
    return b2b_lines,b2b_line_times

#函数: PPP-B2b轨道改正
def B2b_Orbit_corr(CNAV_xyz,B2b_RAC):
    #广播星历卫星位置矢量
    r=np.array([CNAV_xyz[0],CNAV_xyz[1],CNAV_xyz[2]])
    r_dot=np.array([CNAV_xyz[4],CNAV_xyz[5],CNAV_xyz[6]])
    #计算改正矩阵分量
    e_r=r/np.linalg.norm(r)
    e_c=np.cross(r,r_dot)/np.linalg.norm(np.cross(r,r_dot))
    e_a=np.cross(e_c,e_r)
    #计算改正矩阵
    dOX=np.array([[e_r[0],e_a[0],e_c[0]],
                  [e_r[1],e_a[1],e_c[1]],
                  [e_r[2],e_a[2],e_c[2]]])
    #计算改正向量
    dX=dOX.dot((np.array(B2b_RAC)).reshape(3,1))
    return list(dX.reshape(3,))


#CNAV-1+B2b转SP3
def SatPos2SP3(B1C_CNAV,rt_s,rt_e,split=300,sp3_path=""):
    rts_ct=time2COMMONTIME(rt_s)
    rts_week,rts_sec=time2gpst(rt_s)
    #文件头
    header=["#dP{:4d}{:3d}{:3d}0  0  0.00000000     288 d+D".format(rts_ct['year'],rts_ct['month'],rts_ct['day']),
            "## {:4d} {:.8f} {:.8f}".format(rts_week,rts_sec,split),
            '/* Intellegence Transportation Reaserch Center, Wuhan University of Technology(WUTITS)',                             
            '/* CNAV broadcast orbits and clocks',                                                          
            '/* Systems considered: BeiDou',                                                            
            '/* PCV:None      OL/AL:FES2014b NONE     YN ORB:CoN CLK:CoN']
    #数据体
    data=[]
    prns=[]
    for prn in B1C_CNAV:
        if(prn['prn'] not in prns):
            prns.append(prn['prn'])
    
    for rt in tqdm(range(rt_s,rt_e,split)):
        rt_c=time2COMMONTIME(rt)
        #历元标识
        data.append("*  {:4d}{:3d}{:3d}{:3d}{:3d}  {:.8f}".format(rt_c['year'],rt_c['month'],rt_c['day'],rt_c['hour'],rt_c['minute'],rt_c['second']))
        for prn in prns:
            try:
                xyzt=CNAV2SatPVC(B1C_CNAV,rt,"{}".format(prn))
                B2b_Orbit_corr(xyzt,[-0.0400,0.0000,-0.0128])
                data.append("P{}{:14.6f}{:14.6f}{:14.6f}{:14.6f}".format(prn,xyzt[0]*0.001,xyzt[1]*0.001,xyzt[2]*0.001,xyzt[3]*1e6))
            except:
                print("No {}".format(prn))
    with open(sp3_path,'w') as f:
        for head in header:
            f.write(head)
            f.write("\n")
        for d in data:
            f.write(d)
            f.write("\n")
    #卫星轨道写入完成
    return True

#CNAV+1星历+B2b转写CLK
def SatPos2CLK(B1C_CNAV,rt_s,rt_e,split=30,clk_path=""):
    rts_ct=time2COMMONTIME(rt_s)
    rts_week,rts_sec=time2gpst(rt_s)
    #文件头
    header=["3.04                 C                    M                      RINEX VERSION / TYPE",
            'Intellegence Transportation Reaserch Center,                     COMMENT', 
            'Wuhan University of Technology(WUTITS)                           COMMENT',                             
            'CNAV broadcast clock infomation                                  COMMENT',
            "Satellite/receiver clock values at intervals of 30 sec           COMMENT",                                                                                                                      
            '   BDS                                                           TIME SYSTEM ID ',
            '                                                                 END OF HEADER ']
    #数据体
    data=[]
    prns=[]
    for prn in B1C_CNAV:
        if(prn['prn'] not in prns):
            prns.append(prn['prn'])
    
    for rt in tqdm(range(rt_s,rt_e,split)):
        rt_c=time2COMMONTIME(rt)
        #历元标识
        #data.append("*  {:4d}{:3d}{:3d}{:3d}{:3d}  {:.8f}".format(rt_c['year'],rt_c['month'],rt_c['day'],rt_c['hour'],rt_c['minute'],rt_c['second']))
        for prn in prns:
            try:
                xyzt=CNAV2SatPVC(B1C_CNAV,rt,"{}".format(prn))
                #B2b_Orbit_corr(xyzt,[-0.0400,0.0000,-0.0128])
                data.append("AS {}       {:4d} {:02d} {:02d} {:02d} {:02d} {:2.6f}   1   {:20.12E}".format(prn,rt_c['year'],
                                                                                                           rt_c['month'],
                                                                                                           rt_c['day'],
                                                                                                           rt_c['hour'],
                                                                                                           rt_c['minute'],
                                                                                                           rt_c['second'],
                                                                                                           xyzt[3]))
            except:
                print("No {}".format(prn))
    with open(clk_path,'w') as f:
        for head in header:
            f.write(head)
            f.write("\n")
        for d in data:
            f.write(d)
            f.write("\n")
    #卫星轨道写入完成
    return True

def reconstruct_obs_mat(obs_mat):
    #函数: 重整有效观测数据字典(根据Epoch_OK标识)
    #输入: 有效观测数据字典
    #输出: 重整后的观测数据字典
    r_obsmat=[]
    for i in range(len(obs_mat)):
        if(obs_mat[i][0]['Epoch_OK'])!=0:
            continue
        else:
            r_obsmat.append(obs_mat[i])
    #返回观测数据字典
    return r_obsmat


#主函数, B2b实时流仿真
if __name__=='__main__':
    
    #所需文件列表
    obs_path="data/OBS/FDCORS/wuh21010.26o"
    brd4_path="data/BRD4/brd41010.26p"
    B2b_log_path="data/Logs/SPET1010_B2b_26b.log"
    out_path="data/test/"
    #观测值采样率(s)
    obs_interval=30

    #如果有命令行输入
    if(len(sys.argv)-1):
        obs_path=sys.argv[1]
        brd4_path=sys.argv[2]
        B2b_log_path=sys.argv[3]
        out_path=sys.argv[4]
        try:
            obs_interval=float(sys.argv[5])    #默认30s采样率
        except:
            pass

    #读取全部B2b消息并编码
    print("Reading B2b Info lines from",B2b_log_path,end='\r')
    b2b_lines,b2b_line_times=encode_B2BINFO(B2b_log_path)
    print("B2b Info lines readed")

    print("Reading BRD4 lines from",brd4_path,end='\r')
    #读取全部星历消息并编码
    B1C_CNAV,_=BRD4toCNAV(brd4_path,'CNV1')
    GPS_LNAV=BRD4toLNAV(brd4_path,'LNAV')
    gps_eph_lines,gpseph_line_times=encode_GPSEPH(GPS_LNAV)
    bds_eph_lines,bdseph_line_times=encode_BD3EPH(B1C_CNAV)
    print("BRD4 lines readed")
    
    
    #读取全部观测值消息并编码
    print("Reading Observation lines from",obs_path,end="\r")
    obs_mat=RINEX3_to_obsmat(obs_path,
                         ['C2I','L2I','D2I','S2I','C6I','L6I','D6I','S6I'], #由于硬件限制，目前仅支持B1I/B3I非组合
                         'C',
                         f1=1561.098e6,f2=1268.52e6)
    obs_mat_G=RINEX3_to_obsmat(obs_path,
                         ['C1C','L1C','D1C','S1C','C2W','L2W','D2W','S2W'], #由于B2b不播发GPS的DCB, 目前仅支持L1C/L2W非组合
                         'G',
                         f1=1575.42e6,f2=1227.60e6)
    obs_mat=reconstruct_obs_mat(obs_mat)
    obs_mat_G=reconstruct_obs_mat(obs_mat_G)
    obs_lines,obs_line_times=encode_OBSVMA(obs_mat,obs_mat_G,obs_interval=obs_interval)
    print("Observation lines readed, interval: {} seconds".format(obs_interval))

    #创建栈顶指针, 实现以B2b信息时间列表为基础的快速仿真
    b2b_top,obs_top,gpseph_top,bdseph_top=0,0,0,0
    #创建输出文件名, 以观测文件名为基准
    file_out=obs_path.split('/')[-1]+".b2b.log"
    now_eph_bds,now_eph_gps=[],[]#记录星历统计历元
    with open(out_path+file_out,'w') as f:
        #逐真实接收机数据流历元遍历
        for i in tqdm(range(len(b2b_line_times))):
            if(i<b2b_top):
                continue    #未达到栈顶指针
            now=b2b_line_times[i]   #记录当前B2b列栈顶指针所示GPS秒
            
            #处理GPS LNAV星历(由于星历属于乱序, 需要应用查找算法进行组织而非栈操作)
            gps_space=np.where(np.array(gpseph_line_times)==now)[0]
            if(i==0):
                gps_space=np.where(np.array(gpseph_line_times)<=now)[0]
            for j in gps_space:
                for d in gps_eph_lines[j]:
                    f.write(d)

            #处理BDS-3星历(由于星历属于乱序, 需要应用查找算法进行组织而非栈)
            bds_space=np.where(np.array(bdseph_line_times)==now)[0]
            if(i==0):
                bds_space=np.where(np.array(bdseph_line_times)<=now)[0]
            for j in bds_space:
                for d in bds_eph_lines[j]:
                    f.write(d)
            
            
            #处理B2b栈数据(B2b数据流有时间顺序, 应当按照栈操作)
            for j in range(b2b_top,len(b2b_line_times)):
                if (b2b_line_times[j]<=now):
                    #逐字段写入
                    for d in b2b_lines[j]:
                        f.write(d)
                    b2b_top=j
                elif(b2b_line_times[j]>now):
                    b2b_top=j
                    break   #记录栈顶指针并跳出
            
            #处理观测值栈数据(观测值有时间顺序, 应当按照栈操作)
            for j in range(obs_top,len(obs_line_times)):
                if(obs_line_times[j]==now):
                    #逐字段写入
                    for d in obs_lines[j]:
                        f.write(d)
                    obs_top=j
                elif(obs_line_times[j]>now):
                    obs_top=j
                    break
    print("Simulated Real-Time PPP-B2b data stream is saved in ",out_path+file_out,end='')