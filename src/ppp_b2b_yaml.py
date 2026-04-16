import numpy as np
import os
import yaml
import sys
sys.path.append("src")
from satpos import *
from sppp import *
from sppp_multiGNSS import *
from ppp_b2b import IODC2SatPVC,B2b_Orbit_corr

#字符转4 bit位
def char2bit(a):
    if(a=='0'):
        return [0,0,0,0]
    if(a=='1'):
        return [0,0,0,1]
    if(a=='2'):
        return [0,0,1,0]
    if(a=='3'):
        return [0,0,1,1]
    if(a=='4'):
        return [0,1,0,0]
    if(a=='5'):
        return [0,1,0,1]
    if(a=='6'):
        return [0,1,1,0]
    if(a=='7'):
        return [0,1,1,1]
    if(a=='8'):
        return [1,0,0,0]
    if(a=='9'):
        return [1,0,0,1]
    if(a=='A'or a=='a'):
        return [1,0,1,0]
    if(a=='B' or a=='b'):
        return [1,0,1,1]
    if(a=='C' or a=='c'):
        return [1,1,0,0]
    if(a=='D' or a=='d'):
        return [1,1,0,1]
    if(a=='E' or a=='e'):
        return [1,1,1,0]
    if(a=='F' or a=='f'):
        return [1,1,1,1]

#Info1解码
def B2b_Info1_decode(line,B2b_Info_mat):
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line.split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    B2b_Info_mat['Info1']['rt']=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)            
    #消息体前置信息解码
    msg_body_ls=msg_body.split(',')
    B2b_Info_mat['Info1']['Prn']=int(msg_body_ls[0])        #和芯消息协议
    B2b_Info_mat['Info1']['Iodssr']=int(msg_body_ls[1])     #状态空间描述数据的版本号
    B2b_Info_mat['Info1']['Iodp']=int(msg_body_ls[2])       #卫星掩码的数据版本号 
    B2b_Info_mat['Info1']['Sow']=float(msg_body_ls[3])      #日内秒
    #消息体掩码信息解码
    Mask=[0 for t in range(256)]
    Mask_char=msg_body_ls[4][:-10]
    for i in range(0,32):
        t_mask=char2bit(Mask_char[i])
        Mask[4*i]=t_mask[0]
        Mask[4*i+1]=t_mask[1]
        Mask[4*i+2]=t_mask[2]
        Mask[4*i+3]=t_mask[3]
    B2b_Info_mat['Info1']['Mask']=Mask.copy()

#Info2解码
def B2b_Info2_decode(line,B2b_Info_mat):
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line.split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    B2b_Info_mat['Info2']['rt']=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)            
    #消息体前置信息解码
    msg_body_ls=msg_body.split(',')
    B2b_Info_mat['Info2']['Prn']=int(msg_body_ls[0])        #和芯消息协议
    B2b_Info_mat['Info2']['Iodssr']=int(msg_body_ls[1])     #状态空间描述数据的版本号
    # try:
    #     if(B2b_Info_mat['Info2']['Sow']!=float(msg_body_ls[3])):
    #         B2b_Info_mat['Info2']['StOribitCorr']=[[0 for x in range(8)] for t in range(256)]
    #         B2b_Info_mat['Info2']['Sow']=float(msg_body_ls[3])
    # except:
    #     B2b_Info_mat['Info2']['Sow']=float(msg_body_ls[3])      #日内秒
    
    #消息体轨道改正数据解码(每条消息6颗卫星)
    Orb_Corr=[]
    for i in range(6):
        usPrn=int(msg_body_ls[4+7*i])        #卫星掩码位置Satslot
        usiodn=int(msg_body_ls[4+7*i+1])     #IODN基本导航电文版本号
        sRadial=int(msg_body_ls[4+7*i+2])*0.0016    #径向改正数(m)
        sInTrack=int(msg_body_ls[4+7*i+3])*0.0064   #法向改正数(m)
        sCross=int(msg_body_ls[4+7*i+4])*0.0064     #切向改正数(m)
        ucIODcorr=int(msg_body_ls[4+7*i+5])              
        ucURAI=msg_body_ls[4+7*i+6]
        URA_CLASS=char2bit(ucURAI[0])[2]*4+char2bit(ucURAI[0])[3]*2+char2bit(ucURAI[1])[0]
        URA_VALUE=char2bit(ucURAI[1])[1]*4+char2bit(ucURAI[1])[2]*2+char2bit(ucURAI[1])[3]        
        Orb_Corr.append([usPrn,usiodn,sRadial,sInTrack,sCross,ucIODcorr,URA_CLASS,URA_VALUE])
        B2b_Info_mat['Info2']['StOribitCorr'][usPrn-1]=[usPrn,usiodn,sRadial,sInTrack,sCross,ucIODcorr,URA_CLASS,URA_VALUE]

#Info3解码
def B2b_Info3_decode(line,B2b_Info_mat):
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line[:-10].split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    B2b_Info_mat['Info3']['rt']=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)            
    #消息体前置信息解码
    msg_body_ls=msg_body.split(',')
    B2b_Info_mat['Info3']['Prn']=int(msg_body_ls[0])        #和芯消息协议
    B2b_Info_mat['Info3']['Iodssr']=int(msg_body_ls[1])     #状态空间描述数据的版本号
    sat_num=int(msg_body_ls[2])
    # try:
    #     if(B2b_Info_mat['Info3']['Sow']!=float(msg_body_ls[3])):
    #         B2b_Info_mat['Info3']['StCodeBias_t']=[[0 for x in range(32)] for t in range(256)]
    #         B2b_Info_mat['Info3']['Sow']=float(msg_body_ls[3])
    #except:
    B2b_Info_mat['Info3']['Sow']=float(msg_body_ls[3])      #日内秒

    #消息体DCB解码信息
    for i in range(sat_num):
        usSatSlot=int(msg_body_ls[4+i*32])      #掩码位置
        usBiasNum=int(msg_body_ls[4+i*32+1])    #码间偏差数量
        B2b_Info_mat['Info3']['StCodeBias_t'][usSatSlot-1][0]=usSatSlot
        B2b_Info_mat['Info3']['StCodeBias_t'][usSatSlot-1][1]=usBiasNum
        for code in range(15):
            B2b_Info_mat['Info3']['StCodeBias_t'][usSatSlot-1][2+code*2]=int(msg_body_ls[4+i*32+2+2*code])
            B2b_Info_mat['Info3']['StCodeBias_t'][usSatSlot-1][2+code*2+1]=int(msg_body_ls[4+i*32+2+2*code+1])*0.017

#Info4解码
def B2b_Info4_decode(line,B2b_Info_mat):
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line[:-10].split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    B2b_Info_mat['Info4']['rt']=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)            
    #消息体前置信息解码
    msg_body_ls=msg_body.split(',')
    B2b_Info_mat['Info4']['Prn']=int(msg_body_ls[0])        #和芯消息协议
    B2b_Info_mat['Info4']['Iodssr']=int(msg_body_ls[1])     #状态空间描述数据的版本号
    B2b_Info_mat['Info4']['Iodp']=int(msg_body_ls[2])       #卫星掩码的数据版本号
    # try:
    #     if(B2b_Info_mat['Info4']['Sow']!=float(msg_body_ls[3])):
    #         B2b_Info_mat['Info4']['StClkCorr_t']=[[0 for x in range(3)] for t in range(256)]
    #         B2b_Info_mat['Info4']['Sow']=float(msg_body_ls[3])
    # except:
    B2b_Info_mat['Info4']['Sow']=float(msg_body_ls[3])      #日内秒
    #钟差改正数子类型标识
    SubType=int(msg_body_ls[4])
    #尝试提出掩码Mask
    try:
        Info1_Mask=B2b_Info_mat['Info1']['Mask'].copy()
    except:
        return
    #消息体钟差解码信息
    for i in range(23):
        shift=SubType*23                       #掩码位次在当前子类型下的shift值
        target_mask=0
        count=0
        #在mask列表中查找对应掩码位置
        for j in range(len(Info1_Mask)):
            if(Info1_Mask[j]==1):
                target_mask=j
                count+=1
                if(count==shift+i+1):
                    break
        B2b_Info_mat['Info4']['StClkCorr_t'][target_mask][0]=target_mask+1
        B2b_Info_mat['Info4']['StClkCorr_t'][target_mask][1]=int(msg_body_ls[8+2*i])
        B2b_Info_mat['Info4']['StClkCorr_t'][target_mask][2]=int(msg_body_ls[8+2*i+1])*0.0016

#观测值解码函数
def OBSVMA_Info_decode(line,f1,f2,MEO_only=0):
    #重置obsmat对象
    obs_mat=[{'type': 'Observation',
              'Epoch_OK': 0,
              'obstype': ['C2I', 'L2I', 'D2I', 'S2I', 'C6I', 'L6I', 'D6I', 'S6I']},[]]
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line[:-10].split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    rt=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)
    obs_mat[0]['GPSweek']=int(msg_header_ls[4])
    obs_mat[0]['GPSsec']=int(msg_header_ls[5])*0.001
    #记录观测值数量
    msg_body_ls=msg_body.split(',')
    obs_code_num=int(msg_body_ls[0])
    sats=[]
    for i in range(obs_code_num):
        prn="C{:02d}".format(int(msg_body_ls[1+11*i+1]))
        #提取观测值
        p=float(msg_body_ls[1+11*i+2])
        l=float(msg_body_ls[1+11*i+3])
        dopp=float(msg_body_ls[1+11*i+6])
        cno=int(msg_body_ls[1+11*i+7])/100
        #提取连续跟踪时间
        locktime=float(msg_body_ls[1+11*i+9])
        if(MEO_only and p>30000000):
            continue
        #计算伪频率
        t_f=clight*l/(p+1e-12)
        #伪频率不在B1I和B3I中, 跳过
        if(abs(abs(t_f)-abs(f1))>100000 and abs(abs(t_f)-abs(f2))>100000):
            continue
        
        #卫星系统和频率匹配成功
        if(prn not in sats):
            sats.append(prn)
            obs_mat[1].append({'PRN':prn,"OBS":[0.0 for t in range(10)]})

        obs_id=[t['PRN'] for t in obs_mat[1]].index(prn)
        if(abs(abs(t_f)-abs(f1))<100000):              #f1上伪距相位频率带宽匹配
            obs_mat[1][obs_id]['OBS'][0]=p
            obs_mat[1][obs_id]['OBS'][1]=abs(l)
            obs_mat[1][obs_id]['OBS'][2]=0
            obs_mat[1][obs_id]['OBS'][3]=dopp
            obs_mat[1][obs_id]['OBS'][4]=cno
        elif(abs(abs(t_f)-abs(f2))<100000):            #f2上伪距相位频率带宽匹配
            obs_mat[1][obs_id]['OBS'][5]=p
            obs_mat[1][obs_id]['OBS'][6]=abs(l)
            obs_mat[1][obs_id]['OBS'][7]=0
            obs_mat[1][obs_id]['OBS'][8]=dopp
            obs_mat[1][obs_id]['OBS'][9]=cno
    return obs_mat

#GPS观测值解码函数
def OBSVMA_Info_decode_G(line,f1=1575.42e6,f2=1227.60e6):
    #重置obsmat对象
    obs_mat=[{'type': 'Observation',
              'Epoch_OK': 0,
              'obstype': ['C1C', 'L1C', 'D1C', 'S1C', 'C2W', 'L2W', 'D2W', 'S2W']},[]]
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line[:-10].split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    rt=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)
    obs_mat[0]['GPSweek']=int(msg_header_ls[4])
    obs_mat[0]['GPSsec']=int(msg_header_ls[5])*0.001
    #记录观测值数量
    msg_body_ls=msg_body.split(',')
    obs_code_num=int(msg_body_ls[0])
    sats=[]
    for i in range(obs_code_num):
        prn="G{:02d}".format(int(msg_body_ls[1+11*i+1]))
        #提取观测值
        p=float(msg_body_ls[1+11*i+2])
        l=float(msg_body_ls[1+11*i+3])
        dopp=float(msg_body_ls[1+11*i+6])
        cno=int(msg_body_ls[1+11*i+7])/100
        #提取连续跟踪时间
        locktime=float(msg_body_ls[1+11*i+9])
        #计算伪频率
        t_f=clight*l/(p+1e-12)
        #伪频率不在B1I和B3I中, 跳过
        if(abs(abs(t_f)-abs(f1))>100000 and abs(abs(t_f)-abs(f2))>100000):
            continue
        
        #卫星系统和频率匹配成功
        if(prn not in sats):
            sats.append(prn)
            obs_mat[1].append({'PRN':prn,"OBS":[0.0 for t in range(10)]})

        obs_id=[t['PRN'] for t in obs_mat[1]].index(prn)
        if(abs(abs(t_f)-abs(f1))<100000):              #f1上伪距相位频率带宽匹配
            obs_mat[1][obs_id]['OBS'][0]=p
            obs_mat[1][obs_id]['OBS'][1]=abs(l)
            obs_mat[1][obs_id]['OBS'][2]=0
            obs_mat[1][obs_id]['OBS'][3]=dopp
            obs_mat[1][obs_id]['OBS'][4]=cno
        elif(abs(abs(t_f)-abs(f2))<100000):            #f2上伪距相位频率带宽匹配
            obs_mat[1][obs_id]['OBS'][5]=p
            obs_mat[1][obs_id]['OBS'][6]=abs(l)
            obs_mat[1][obs_id]['OBS'][7]=0
            obs_mat[1][obs_id]['OBS'][8]=dopp
            obs_mat[1][obs_id]['OBS'][9]=cno
    return obs_mat

def OBSVMA_Info_decode_E(line,f1=1575.42e6,f2=1176.45e6):
    #重置obsmat对象
    #请注意, B2b当前不支持GAL系统, 本函数返回空值
    obs_mat=[{'type': 'Observation',
              'Epoch_OK': 0,
              'obstype': ['C1C', 'L1C', 'D1C', 'S1C', 'C5Q', 'L5Q', 'D5Q', 'S5Q']},[]]
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line[:-10].split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    rt=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)
    obs_mat[0]['GPSweek']=int(msg_header_ls[4])
    obs_mat[0]['GPSsec']=int(msg_header_ls[5])*0.001
    #记录观测值数量
    msg_body_ls=msg_body.split(',')
    obs_code_num=int(msg_body_ls[0])
    sats=[]
    # for i in range(obs_code_num):
    #     prn="G{:02d}".format(int(msg_body_ls[1+11*i+1]))
    #     #提取观测值
    #     p=float(msg_body_ls[1+11*i+2])
    #     l=float(msg_body_ls[1+11*i+3])
    #     dopp=float(msg_body_ls[1+11*i+6])
    #     cno=int(msg_body_ls[1+11*i+7])/100
    #     #提取连续跟踪时间
    #     locktime=float(msg_body_ls[1+11*i+9])
    #     #计算伪频率
    #     t_f=clight*l/(p+1e-12)
    #     #伪频率不在B1I和B3I中, 跳过
    #     if(abs(abs(t_f)-abs(f1))>100000 and abs(abs(t_f)-abs(f2))>100000):
    #         continue
        
    #     #卫星系统和频率匹配成功
    #     if(prn not in sats):
    #         sats.append(prn)
    #         obs_mat[1].append({'PRN':prn,"OBS":[0.0 for t in range(10)]})

    #     obs_id=[t['PRN'] for t in obs_mat[1]].index(prn)
    #     if(abs(abs(t_f)-abs(f1))<100000):              #f1上伪距相位频率带宽匹配
    #         obs_mat[1][obs_id]['OBS'][0]=p
    #         obs_mat[1][obs_id]['OBS'][1]=abs(l)
    #         obs_mat[1][obs_id]['OBS'][2]=0
    #         obs_mat[1][obs_id]['OBS'][3]=dopp
    #         obs_mat[1][obs_id]['OBS'][4]=cno
    #     elif(abs(abs(t_f)-abs(f2))<100000):            #f2上伪距相位频率带宽匹配
    #         obs_mat[1][obs_id]['OBS'][5]=p
    #         obs_mat[1][obs_id]['OBS'][6]=abs(l)
    #         obs_mat[1][obs_id]['OBS'][7]=0
    #         obs_mat[1][obs_id]['OBS'][8]=dopp
    #         obs_mat[1][obs_id]['OBS'][9]=cno
    return obs_mat

def BD3EPH_Info_decode(line,B1C_CNAV_mat):
    #新建一个数据块对象
    data_split={}
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line[:-10].split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    rt=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)
    data_split['rt']=rt
    #消息体信息分离
    msg_body_ls=msg_body.split(',')
    data_split['prn']="C{:02d}".format(int(msg_body_ls[0]))
    data_split['Health']=int(msg_body_ls[1])    
    data_split['Sat_Type']=int(msg_body_ls[2])    
    data_split['SISMAI']=int(msg_body_ls[3])    
    data_split['IODE']=int(msg_body_ls[4])    
    data_split['IODC']=int(msg_body_ls[5])    
    data_split['week']=int(msg_body_ls[6])    
    data_split['Zweek']=int(msg_body_ls[7])    
    data_split['tow']=float(msg_body_ls[8])    
    data_split['toe']=float(msg_body_ls[9])    
    if(data_split['Sat_Type']==3):
        data_split['A']=27906100+float(msg_body_ls[10])   
    else:
        data_split['A']=42162200+float(msg_body_ls[10])
        #data_split['A']=27906100+float(msg_body_ls[10]) 
    data_split['A_DOT']=float(msg_body_ls[11])    
    data_split['delta_n0']=float(msg_body_ls[12])    
    data_split['delta_n0_DOT']=float(msg_body_ls[13])    
    data_split['M0']=float(msg_body_ls[14])    
    data_split['e']=float(msg_body_ls[15])    
    data_split['omega']=float(msg_body_ls[16])    
    data_split['cuc']=float(msg_body_ls[17])    
    data_split['cus']=float(msg_body_ls[18])    
    data_split['crc']=float(msg_body_ls[19])    
    data_split['crs']=float(msg_body_ls[20])    
    data_split['cic']=float(msg_body_ls[21])    
    data_split['cis']=float(msg_body_ls[22])    
    data_split['i0']=float(msg_body_ls[23])    
    data_split['IDOT']=float(msg_body_ls[24])    
    data_split['OMEGA0']=float(msg_body_ls[25])    
    data_split['OMEGA_DOT']=float(msg_body_ls[26])    
    data_split['toc']=float(msg_body_ls[27])    
    data_split['TGD_B1Cp']=float(msg_body_ls[28])    
    data_split['TGD_B2ap']=float(msg_body_ls[29])    
    data_split['TGD_B2bI']=float(msg_body_ls[30])    
    data_split['TGD_B2bQ']=float(msg_body_ls[31])    
    data_split['ISC_B2Ad']=float(msg_body_ls[32])    
    data_split['ISC_B1Cd']=float(msg_body_ls[33])    
    data_split['a0']=float(msg_body_ls[34])    
    data_split['a1']=float(msg_body_ls[35])    
    data_split['a2']=float(msg_body_ls[36])    
    data_split['t_top']=int(msg_body_ls[37])    
    data_split['SISAI_oe']=int(msg_body_ls[38])    
    data_split['SISAI_ocb']=int(msg_body_ls[39])    
    data_split['SISAI_oc1']=int(msg_body_ls[40])    
    data_split['SISAI_oc2']=int(msg_body_ls[41])
    #计算toc
    data_split['toc']=gpst2time(data_split['week'],data_split['toc'])

    #更新星历块
    B1C_CNAV_mat['Old'][int(data_split['prn'][1:])-1]=B1C_CNAV_mat['Now'][int(data_split['prn'][1:])-1].copy()   
    B1C_CNAV_mat['Now'][int(data_split['prn'][1:])-1]=data_split.copy()  
    return

def GPSEPH_Info_decode(line,GPS_LNAV_mat):
    #新建一个数据块对象
    data_split={}
    #消息头/体分离
    msg_header=line.split(";")[0]
    msg_body=line[:-10].split(";")[1]
    #消息头信息分离
    msg_header_ls=msg_header.split(',')
    rt=gpst2time(int(msg_header_ls[4]),int(msg_header_ls[5])*0.001)
    data_split['rt']=rt
    #消息体信息分离
    msg_body_ls=msg_body.split(',')
    data_split['prn']="G{:02d}".format(int(msg_body_ls[0]))
    data_split['tow']=float(msg_body_ls[1])
    data_split['Health']=int(msg_body_ls[2])
    data_split['IODE']=int(msg_body_ls[3])
    data_split['IODE']=int(msg_body_ls[4])
    data_split['week']=int(msg_body_ls[5])
    data_split['Z_week']=int(msg_body_ls[6])
    data_split['toe']=float(msg_body_ls[7])
    data_split['A']=float(msg_body_ls[8])
    data_split['delta_n0']=float(msg_body_ls[9])
    data_split['M0']=float(msg_body_ls[10])
    data_split['e']=float(msg_body_ls[11])
    data_split['omega']=float(msg_body_ls[12])    
    data_split['cuc']=float(msg_body_ls[13])    
    data_split['cus']=float(msg_body_ls[14])    
    data_split['crc']=float(msg_body_ls[15])    
    data_split['crs']=float(msg_body_ls[16])    
    data_split['cic']=float(msg_body_ls[17])    
    data_split['cis']=float(msg_body_ls[18])    
    data_split['i0']=float(msg_body_ls[19])    
    data_split['IDOT']=float(msg_body_ls[20])
    data_split['OMEGA0']=float(msg_body_ls[21])    
    data_split['OMEGA_DOT']=float(msg_body_ls[22])     
    data_split['IODC']=int(msg_body_ls[23])     
    data_split['toc']=float(msg_body_ls[24])     
    data_split['TGD']=float(msg_body_ls[25])     
    data_split['a0']=float(msg_body_ls[26])     
    data_split['a1']=float(msg_body_ls[27])     
    data_split['a2']=float(msg_body_ls[28])     
    #计算toc
    data_split['toc']=gpst2time(data_split['week'],data_split['toc'])
    #16参数星历->18参数星历
    data_split['delta_n0_DOT']=0.0
    data_split['A_DOT']=0.0
    #更新星历块
    if(int(data_split['prn'][1:])>0 and int(data_split['prn'][1:])<=32):#合法GPS星历
        GPS_LNAV_mat['Old'][int(data_split['prn'][1:])-1]=GPS_LNAV_mat['Now'][int(data_split['prn'][1:])-1].copy()   
        GPS_LNAV_mat['Now'][int(data_split['prn'][1:])-1]=data_split.copy()  
    return 

#主业务流程函数
def CNAV_B2bCorr_pair(B1C_CNAV_mat,B2b_Info_mat,GPS_LNAV_mat={},GPS_DCB_TGD=1):
    #构建广播星历与改正数对
    t_CNAVS=[]
    t_B2B_orbs=[]
    t_B2B_clks=[]
    t_B2B_dcbs=[]
    #取出全部BDS星历块
    for i in range(0,66):
        #当前无星历
        if(B1C_CNAV_mat['Now'][i]=={}):
            continue
        #首先尝试检查当前星历与B2b轨道改正数匹配程度
        if(B1C_CNAV_mat['Now'][i]['IODE']==B2b_Info_mat['Info2']['StOribitCorr'][i][1]):
            t_CNAV=B1C_CNAV_mat['Now'][i].copy()
        else:
            #过往无星历
            if(B1C_CNAV_mat['Old'][i]=={}):
                continue
            if(B1C_CNAV_mat['Old'][i]['IODE']==B2b_Info_mat['Info2']['StOribitCorr'][i][1]):
                t_CNAV=B1C_CNAV_mat['Old'][i].copy()
                #print("Updating")
            else:
                continue
        #取出轨道改正数
        drac=B2b_Info_mat['Info2']['StOribitCorr'][i]
        #取出钟差改正数
        dsatt=B2b_Info_mat['Info4']['StClkCorr_t'][i]
        #取出码间偏差
        satdcb=B2b_Info_mat['Info3']['StCodeBias_t'][i]
        #PRN不匹配
        if(drac[0]!=dsatt[0] or satdcb[0]!=dsatt[0] or drac[0]!=satdcb[0]):
            continue
        #IODcorr不匹配(轨钟不匹配)
        # if(drac[5]!=dsatt[1]):
        #     continue
        #print(t_CNAV['prn'],"Orb_corr",drac,"Clk_corr",dsatt,'DCB',satdcb)
        #保存有效信息
        t_CNAVS.append(t_CNAV.copy())
        t_B2B_orbs.append(drac.copy())
        t_B2B_dcbs.append(satdcb.copy())
        t_B2B_clks.append(dsatt.copy())

    #取出全部GPS星历块
    for i in range(0,33):
        #没有GPS星历, 跳过GPS星历匹配
        if(GPS_LNAV_mat=={}):
            continue
        #当前无星历
        if(GPS_LNAV_mat['Now'][i]=={}):
            continue
        #首先尝试检查当前星历与B2b轨道改正数匹配程度
        if(GPS_LNAV_mat['Now'][i]['IODC']==B2b_Info_mat['Info2']['StOribitCorr'][i+63][1]):
            t_CNAV=GPS_LNAV_mat['Now'][i].copy()
        else:
            #过往无星历
            if(GPS_LNAV_mat['Old'][i]=={}):
                continue
            if(GPS_LNAV_mat['Old'][i]['IODC']==B2b_Info_mat['Info2']['StOribitCorr'][i+63][1]):
                t_CNAV=GPS_LNAV_mat['Old'][i].copy()
                #print("Updating")
            else:
                continue
        #取出轨道改正数
        drac=B2b_Info_mat['Info2']['StOribitCorr'][i+63]
        #取出钟差改正数
        dsatt=B2b_Info_mat['Info4']['StClkCorr_t'][i+63]
        #取出码间偏差
        satdcb=B2b_Info_mat['Info3']['StCodeBias_t'][i+63]
        if(GPS_DCB_TGD):#使用广播星历TGD替代未播发的GPS DCB
            satdcb=[0 for t in range(32)]
            satdcb[0],satdcb[1]=i+63,2#卫星掩码
            satdcb[2],satdcb[3]=0,clight*t_CNAV['TGD']
            satdcb[4],satdcb[5]=1,clight*1575.42*1575.42/1227.60/1227.60*t_CNAV['TGD']
        #PRN不匹配(注意: 当前B2b不播发GPS的DCB, 因此只考虑轨道和钟差的匹配程度即可)
        if(drac[0]!=dsatt[0]): #or satdcb[0]!=dsatt[0] or drac[0]!=satdcb[0]):
            continue
        #IODcorr不匹配(轨钟不匹配)
        # if(drac[5]!=dsatt[1]):
        #     continue
        #print(t_CNAV['prn'],"Orb_corr",drac,"Clk_corr",dsatt,'DCB',satdcb)
        #保存有效信息
        t_CNAVS.append(t_CNAV.copy())
        t_B2B_orbs.append(drac.copy())
        t_B2B_dcbs.append(satdcb.copy())
        t_B2B_clks.append(dsatt.copy())
    return t_CNAVS,t_B2B_orbs,t_B2B_dcbs,t_B2B_clks

#B2b卫星位置计算与伪距标准定位
def SPP_from_B2b(obs_mat,obs_index,t_CVAVs,t_B2B_orbs,t_B2B_dcbs,t_B2B_clks,sat_out,ion_param,sat_pcos,sol_mode='SF',f1=1561.098*1e6,f2=1268.52*1e6,f1_G=1575.42e6,f2_G=1227.60e6,el_threthod=7.0,obslist=[],pre_rr=[]):
    rr=[100,100,100]
    #观测值列表构建(异常值剔除选星)
    if(not len(obslist)):
        obslist=[]
        for sys in range(len(obs_mat[obs_index])):
            for i in range(len(obs_mat[obs_index][sys][1])):
                obsdata=obs_mat[obs_index][sys][1][i]['OBS']
                obshealth=1
                if(obsdata[0]==0.0 or obsdata[1]==0.0 or obsdata[5]==0.0 or obsdata[6]==0.0):
                    obshealth=0
                #通过PRN查找星历并核验Health标签
                prn=obs_mat[obs_index][sys][1][i]['PRN']
                try:
                    prn_id=[t['prn'] for t in t_CVAVs].index(prn)
                except:
                    obshealth=0
                try:
                    if(t_CVAVs[prn_id]['Health']!=0):
                        obshealth=0
                except:
                    obshealth=0
                #卫星通过健康校验
                if(obshealth):
                    if obs_mat[obs_index][sys][1][i]['PRN'] not in sat_out:
                        obslist.append(obs_mat[obs_index][sys][1][i])  
    obslist_new=obslist.copy()#高度角截至列表
    sat_num=len(obslist)#记录总卫星数量
    #记录各系统卫星数量
    sat_num_C,sat_num_G,sat_num_E=0,0,0
    for obs in obslist:
        if(obs['PRN'][0]=='C'):
            sat_num_C+=1
        if(obs['PRN'][0]=='G'):
            sat_num_G+=1
        if(obs['PRN'][0]=='E'):
            sat_num_E+=1
    #确定卫星系统数量
    sys_num=0
    if(sat_num_G!=0):
        sys_num+=1
    if(sat_num_C!=0):
        sys_num+=1
    if(sat_num_E!=0):
        sys_num+=1
    #初始化高度角排除列表
    ex_index=np.zeros(sat_num,dtype=int)
    
    if(sat_num<3+sys_num):
        print("The number of Satellites is not enough, pass epoch.")
        return [0,0,0,0],[],[]
    
    #卫星列表构建
    peph_sat_pos={}
    for i in range(0,sat_num):
        #光速
        clight=2.99792458e8
        #观测时间&观测值
        rt_week=obs_mat[obs_index][0][0]['GPSweek']
        rt_sec=obs_mat[obs_index][0][0]['GPSsec']
        rt_unix=satpos.gpst2time(rt_week,rt_sec)
        
        #原始伪距
        p1=obslist[i]['OBS'][0]
        s1=obslist[i]['OBS'][4]
        p2=obslist[i]['OBS'][5]
        s2=obslist[i]['OBS'][9]
        #print(p1,p2,phi1,phi2)
            
        #卫星位置内插
        si_PRN=obslist[i]['PRN']
        prn_id=[t['prn'] for t in t_CVAVs].index(si_PRN)
        rs_pvc=IODC2SatPVC(t_CVAVs[prn_id],rt_unix,si_PRN,iodc=t_CVAVs[prn_id]['IODC'],rho=p1)
        rs=[rs_pvc[0],rs_pvc[1],rs_pvc[2]]    #广播卫星轨道
        drs=[rs_pvc[4],rs_pvc[5],rs_pvc[6]]   #广播卫星速度
        #轨道改正
        try:
            dXYZ=B2b_Orbit_corr(rs_pvc,t_B2B_orbs[prn_id][2:5])
        except:
            dXYZ=[0,0,0]
        rs[0]=rs[0]-dXYZ[0]
        rs[1]=rs[1]-dXYZ[1]
        rs[2]=rs[2]-dXYZ[2]
        #钟差改正
        dts=rs_pvc[3]                         #广播卫星钟差(含相对论效应改正)
        try:
            dts=dts-t_B2B_clks[prn_id][2]/clight
        except:
            pass    
        
        peph_sat_pos[si_PRN]=[rs[0],rs[1],rs[2],dts,drs[0],drs[1],drs[2],rs_pvc[7]]
    if(sol_mode=="Sat only"):
        return peph_sat_pos
        
    #伪距单点定位
    if(len(pre_rr)):
        #有先验位置
        rr[0]=pre_rr[0]
        rr[1]=pre_rr[1]
        rr[2]=pre_rr[2]
    result=np.zeros((6),dtype=np.float64)
    result[0:3]=rr
    result[3:6]=0.0
    if(len(pre_rr)):
        result[3]=pre_rr[3]
        result[4]=pre_rr[4]
        result[5]=pre_rr[5]
    
    #print("标准单点定位求解滤波状态初值")
    #最小二乘求解滤波初值
    ls_count=0
    while(1):
        #光速, GPS系统维持的地球自转角速度(弧度制)
        clight=2.99792458e8
        OMGE=7.2921151467E-5

        #观测值矩阵初始化
        Z=np.zeros(sat_num,dtype=np.float64)
        #设计矩阵初始化
        H=np.zeros((sat_num,6),dtype=np.float64)
        #单位权中误差矩阵初始化
        var=[]
        #权重矩阵初始化
        #W=np.zeros((sat_num,sat_num),dtype=np.float64)
    
        #观测值、设计矩阵构建
        for i in range(0,sat_num):
        
            si_PRN=obslist[i]['PRN']
            prn_id=[t['prn'] for t in t_CVAVs].index(si_PRN)
            #观测时间&观测值
            rt_week=obs_mat[obs_index][0][0]['GPSweek']
            rt_sec=obs_mat[obs_index][0][0]['GPSsec']
            rt_unix=satpos.gpst2time(rt_week,rt_sec)
            #print(rt_week,rt_sec,rt_unix)
        
            #伪距
            p1=obslist[i]['OBS'][0]
            s1=obslist[i]['OBS'][4]
            p2=obslist[i]['OBS'][5]
            s2=obslist[i]['OBS'][6]
            #print(p1,p2,phi1,phi2)
            #DCB改正, 由于B2b钟差基准为B3信号，故需要将各观测值上信号改正至B3上即可
            #北斗DCB直接由B2b信息改正
            if(si_PRN[0]=='C'):
                try:
                    p1=p1-t_B2B_dcbs[prn_id][3]                  #PPP-B2b-ICD中描述, B1I改正至B3I
                except:
                    pass
            #GPS-DCB当前未播发, 由TGD改正
            if(si_PRN[0]=='G'):
                try:
                    p1=p1-t_B2B_dcbs[prn_id][3]                 #GPS-ICD中描述, L12-IF改正至L1
                    p2=p2-t_B2B_dcbs[prn_id][5]                 #GPS-ICD中描述, L12-IF改正至L2
                except:
                    pass

            #卫星位置
            si_PRN=obslist[i]['PRN']
            rs=[peph_sat_pos[si_PRN][0],peph_sat_pos[si_PRN][1],peph_sat_pos[si_PRN][2]]
            dts=peph_sat_pos[si_PRN][3]
            
            r0=sqrt( (rs[0]-rr[0])*(rs[0]-rr[0])+(rs[1]-rr[1])*(rs[1]-rr[1])+(rs[2]-rr[2])*(rs[2]-rr[2]) )
            #线性化的站星单位向量
            urs_x=(rr[0]-rs[0])/r0
            urs_y=(rr[1]-rs[1])/r0
            urs_z=(rr[2]-rs[2])/r0
            
            #单卫星设计矩阵赋值&钟差
            H[i]=[urs_x,urs_y,urs_z,0,0,0]
            clk_isb=result[3]
            if(si_PRN[0]=='C'):
                H[i][4]=1.0
                clk_isb=result[4]
                f1,f2=f1,f2
            if(si_PRN[0]=='G'):
                H[i][3]=1.0
                clk_isb=result[3]
                f1,f2=f1_G,f2_G
            if(si_PRN[0]=='E'):
                H[i][5]=1.0
                clk_isb=result[5]

            #地球自转改正到卫地距上
            r0=r0+OMGE*(rs[0]*rr[1]-rs[1]*rr[0])/clight
            
            #观测矩阵
            if(sol_mode=='SF'):
                Z[i]=p1-r0-clk_isb-satpos.get_Tropdelay(rr,rs)-satpos.get_ion_GPS(rt_unix,rr,rs,ion_param)+clight*dts
            
            #双频无电离层延迟组合
            elif(sol_mode=='IF'):
                f12=f1*f1
                f22=f2*f2
                p_IF=f12/(f12-f22)*p1-f22/(f12-f22)*p2
                Z[i]=p_IF-r0-clk_isb-satpos.get_Tropdelay(rr,rs)+clight*dts
            elif(sol_mode=='BDGIM'):
                Z[i]=p1-r0-clk_isb-satpos.get_Tropdelay(rr,rs)-40.28*satpos.get_BDSGIM(rt_unix,ion_param,rr,rs,MF_mode=2)/(f1/1e8)/(f1/1e8)+clight*dts

            #随机模型
            #var[i][i]= 0.00224*10**(-s1 / 10) 
            _,el=satpos.getazel(rs,rr)
            var.append(0.3*0.3+0.3*0.3/sin(el)/sin(el))
            if(el*180.0/satpos.pi<el_threthod):
                var[i]=var[i]*100#低高度角拒止
                ex_index[i]=1
            if(ex_index[i]==1 and el*180.0/satpos.pi>=el_threthod):
                ex_index[i]=0
            
            if(sol_mode=='IF'):
                var[i]=var[i]*9
        
        #各系统钟差失配,添加虚拟零观测确保H满秩
        if(sat_num_G==0):
            H_sub_G=np.array([0,0,0,1,0,0]).reshape(1,6)
            var.append(0.01)#虚拟方差
            H=np.concatenate((H,H_sub_G)) #设计矩阵处理
            Z=np.append(Z,0.0)
        if(sat_num_C==0):
            H_sub_C=np.array([0,0,0,0,1,0]).reshape(1,6)
            var.append(0.01)#虚拟方差
            H=np.concatenate((H,H_sub_C)) #设计矩阵处理
            Z=np.append(Z,0.0)
        if(sat_num_E==0):
            H_sub_E=np.array([0,0,0,0,0,1]).reshape(1,6)
            var.append(0.01)#虚拟方差
            H=np.concatenate((H,H_sub_E)) #设计矩阵处理
            Z=np.append(Z,0.0)

        #权重矩阵
        W=np.zeros((len(var),len(var)),dtype=np.float64)
        for i in range(len(var)):
            W[i][i]=1.0/var[i]
        
        #最小二乘求解:
        dresult=getLSQ_solution(H,Z,W=W,weighting_mode='S')
        
        #迭代值更新
        result[0]+=dresult[0]
        result[1]+=dresult[1]
        result[2]+=dresult[2]
        result[3]+=dresult[3]
        result[4]+=dresult[4]
        result[5]+=dresult[5]

        #更新测站位置
        rr[0]=result[0]
        rr[1]=result[1]
        rr[2]=result[2]
        #print(dresult)
        ls_count+=1
        if(abs(dresult[0])<1e-4 and abs(dresult[1])<1e-4 and abs(dresult[2])<1e-4):
            #估计先验精度因子
            break
        if(ls_count>200):
            break
    
    #排除低高度角卫星
    for i in range(sat_num):
        if(ex_index[i]):
            obslist_new.remove(obslist[i])
    #修改原始观测值(DCB校正)
    for i in range(len(obslist_new)):
        si_PRN=obslist_new[i]['PRN']
        prn_id=[t['prn'] for t in t_CVAVs].index(si_PRN)
        #北斗DCB直接由B2b信息改正
        if(si_PRN[0]=='C'):
            try:
                obslist_new[i]['OBS'][0]=obslist_new[i]['OBS'][0]-t_B2B_dcbs[prn_id][3]     #PPP-B2b-ICD中描述, B1I改正至B3I
            except:
                pass
        #GPS-DCB当前未播发, 由TGD改正
        if(si_PRN[0]=='G'):
            try:
                obslist_new[i]['OBS'][0]=obslist_new[i]['OBS'][0]-t_B2B_dcbs[prn_id][3]
                obslist_new[i]['OBS'][5]=obslist_new[i]['OBS'][5]-t_B2B_dcbs[prn_id][5]
            except:
                pass
    return result,obslist_new,peph_sat_pos

def index_UCPPPM(si_PRN,freqs):
    sys_shift=0
    f1=freqs[0][0]
    f2=freqs[0][1]
    sys_sat_num=32          #GPS系统星座卫星数量
    if('C' in si_PRN):
        sys_shift=32        #多系统索引偏置(GPS)
        sys_sat_num=65
        f1=freqs[1][0]
        f2=freqs[1][1]
    if('E' in si_PRN):
        sys_shift=32+65     #多系统索引偏置(GPS+BDS)
        sys_sat_num=37
        f1=freqs[2][0]
        f2=freqs[2][1] 
    PRN_index=int(si_PRN[1:])-1
    ion_index=5+3*sys_shift+PRN_index
    N1_index=5+3*sys_shift+sys_sat_num+PRN_index
    N2_index=5+3*sys_shift+sys_sat_num*2+PRN_index
    return PRN_index,ion_index,N1_index,N2_index,f1,f2

#PPP状态初始化
def init_UCPPP_CNAV(obs_mat,obs_start,t_CNAVS,sat_out,ion_param,sat_pcos,sys_sat_num,freqs):
    #准备
    #1.单点定位最小二乘求解滤波初值
    obs_index=obs_start #设置初始化时间索引
    
    rr,obslist,peph_sat_pos=SPP_from_B2b(obs_mat,obs_index,t_CNAVS,[],[],[],sat_out,ion_param,sat_pcos,sol_mode='IF',el_threthod=0.0,f1=freqs[1][0],f2=freqs[1][1])

    #位置、接收机钟差、天顶对流层延迟初值向量
    #观测时间&观测值
    rt_week=obs_mat[obs_index][0][0]['GPSweek']
    rt_sec=obs_mat[obs_index][0][0]['GPSsec']
    rt_unix=satpos.gpst2time(rt_week,rt_sec)
    X0_xyztm=np.array([rr[0],rr[1],rr[2],rr[3],0.15])                   #初始化位置/钟差/对流层
    X0_xyztm_time=np.array([rt_unix,rt_unix,rt_unix,rt_unix,rt_unix])   #初始化位置/钟差/电离层时标

    #观测列表卫星数量
    s_num=len(obslist)

    #电离层延迟改正数初值向量()
    X=np.zeros(7+3*sys_sat_num,dtype=np.float64)
    X_time=np.zeros(7+3*sys_sat_num,dtype=np.float64)

    #基础导航状态
    for i in range(5):
        X[i]=X0_xyztm[i]
        X_time[i]=X0_xyztm_time[i]

    #电离层状态
    for i in range(s_num):
        si_PRN=obslist[i]['PRN']
        _,PRN_index,_,_,f1,f2=index_UCPPPM(si_PRN,freqs)
        
        #双频伪距计算电离层初值
        p1=obslist[i]['OBS'][0]
        s1=obslist[i]['OBS'][4]
        p2=obslist[i]['OBS'][5]
    
        #卫星位置
        #X0_I[i]=satpos.get_ion_GPS(rt_unix,rr,rs,ion_param)
        ion=(p1-p2)/((f2*f2-f1*f1)/f2/f2)                              #伪距双差获取电离层延迟初值
        X[PRN_index]=ion                                            #估计电离层延迟初值
        X_time[PRN_index]=rt_unix

    #L1载波上各星模糊度初值
    for i in range(s_num):
        si_PRN=obslist[i]['PRN']
        _,_,PRN_index,_,f1,f2=index_UCPPPM(si_PRN,freqs)
    
        p1=obslist[i]['OBS'][0]
        p2=obslist[i]['OBS'][5]
        l1=obslist[i]['OBS'][1]
    
        #伪距IF组合与相位互差求解模糊度初值
        # P_Ion_free=f1*f1/(f1*f1-f2*f2)*p1-f2*f2/(f1*f1-f2*f2)*p2
        X[PRN_index]=update_phase_amb(p1,l1,f1,p1,p2,f1=f1,f2=f2)
        X_time[PRN_index]=rt_unix
    
    #L2载波上各星模糊度初值
    for i in range(s_num):
        si_PRN=obslist[i]['PRN']
        _,_,_,PRN_index,f1,f2=index_UCPPPM(si_PRN,freqs)
    
        p1=obslist[i]['OBS'][0]
        p2=obslist[i]['OBS'][5]
        l2=obslist[i]['OBS'][6]
    
        #伪距IF组合与相位互差求解模糊度初值
        # P_Ion_free=f1*f1/(f1*f1-f2*f2)*p1-f2*f2/(f1*f1-f2*f2)*p2
        X[PRN_index]=update_phase_amb(p2,l2,f2,p1,p2,f1=f1,f2=f2)
        X_time[PRN_index]=rt_unix
    
    #相位相关误差字典初始化
    phase_bias={}
    for i in range(s_num):
        si_PRN=obslist[i]['PRN']
        phase_bias[si_PRN]={}
        phase_bias[si_PRN]['phw']=0.0

    #BDS和GAL系统钟差状态
    X[5+3*sys_sat_num]=rr[4]
    X[5+3*sys_sat_num+1]=rr[5]

    #状态初值
    X=X.reshape(X.shape[0],1)
    X_time=X_time.reshape(X_time.shape[0],1)

    #系统噪声方差阵(初始值)
    Qk=np.eye(X.shape[0],dtype=np.float64)
    for i in range(X.shape[0]):
        if(i in [0,1,2,3]):                     #接收机位置、钟差(标准差100m)
            Qk[i][i]=30*30
        if(i in [4]):                           #对流层先验(标准差0.8m)
            Qk[i][i]=30*30   
        if(i in range(5,5+sys_sat_num)):            #电离层先验(标准差100m)
            Qk[i][i]=30*30
        if(i in range(5+sys_sat_num,5+2*sys_sat_num)):  #L1模糊度先验(标准差100m)
            Qk[i][i]=30*30
        if(i in range(5+2*sys_sat_num,5+3*sys_sat_num)):#L2模糊度先验(标准差100m)
            Qk[i][i]=30*30
    Pk=Qk.copy()

    #周跳检验量(每历元均更新)
    GF_sign=np.zeros((sys_sat_num),dtype=np.float64)
    Mw_sign=np.zeros((sys_sat_num),dtype=np.float64)
    #周跳标志(每历元均重置为0)
    slip_sign=np.zeros((sys_sat_num),dtype=int)
    #周跳修复累计列表(随状态初始化重置)
    dN_sign=np.zeros((sys_sat_num,2),dtype=np.float64)

    return X,Pk,Qk,GF_sign,Mw_sign,slip_sign,dN_sign,X_time,phase_bias

def add_PPP_RTK_corr(H,R,v,corr_v,corr_sstd,ref_ids,rnx_obs):
    #函数: PPP-RTK约束函数
    #输入: 非约束观测模型HRv, 约束向量corr_v, 约束向量的方差corr_sstd
    #输出: 有约束观测模型H_corr, R_corr, v_corr
    H_corr=H.copy()
    R_corr=R.copy()
    v_corr=v.copy()
    prns=[t['PRN'] for t in rnx_obs]
    for i in range(len(corr_v)):        #顺序为卫星列表顺序

        if(corr_v[i]==0.0):
            continue                    #该状态量无改正数
        H_corr=np.append(H_corr,np.zeros((1,H_corr.shape[1])),axis=0)#设计矩阵添加一行
        H_corr[-1][i]=1.0                                            #约束对应状态的系数置1(基准站位置约束)
        
        if(i>=5):                                                    #电离层约束
            prn=prns[i-5]                     #卫星PRN码
            sys_id=['G','C','E'].index(prn[0])
            H_corr[-1][5+ref_ids[sys_id]]=-1.0                       #参考星
        v_corr=np.append(v_corr,np.array([[corr_v[i]]]),axis=0)      #残差向量添加一行
        
        #观测噪声阵向右下添加一块
        R_corr=np.append(R_corr,np.zeros((1,R_corr.shape[1])),axis=0)   #先添加一行
        R_corr=np.append(R_corr,np.zeros((R_corr.shape[0],1)),axis=1)   #再添加一列
        R_corr[-1][-1]=corr_sstd[i]                                #虚拟观测值赋权重
    
    #返回添加PPP-RTK改正数约束后的观测模型
    return H_corr,R_corr,v_corr
    
    #返回添加PPP-RTK改正数约束后的观测模型
    return H_corr,R_corr,v_corr

def KF_UCPPP_RTK_Base(X,X_time,Pk,Qk,ion_param,peph_sat_pos,rnx_obs,ex_threshold_v,ex_threshold_sigma,rt_unix,phase_bias,freqs,STA_P,STA_Q):
    #扩展卡尔曼滤波
    #扩展卡尔曼滤波
    for KF_times in range(8):
        #相位改正值拷贝
        t_phase_bias=phase_bias.copy()
        
        #观测模型(两次构建, 验前粗差剔除)
        #print(rnx_obs)
        X,X_time,H,R,_,v,rnx_obs=createKF_HRZ_M(rnx_obs,rt_unix,X,X_time,Pk,Qk,ion_param,t_phase_bias,peph_sat_pos,freqs=freqs,exthreshold_v_sigma=ex_threshold_sigma,post=False,ex_threshold_v=ex_threshold_v)
        if(not len(rnx_obs)):
            #无先验通过数据
            #全部状态重置
            X[0]=100.0
            X[1]=100.0
            X[2]=100.0
            # for i in range(len(X)):
            #     X_time[i]=0.0
            #     break
        X,X_time,H,R,_,v,rnx_obs=createKF_HRZ_M(rnx_obs,rt_unix,X,X_time,Pk,Qk,ion_param,t_phase_bias,peph_sat_pos,freqs=freqs,exthreshold_v_sigma=ex_threshold_sigma,post=False,ex_threshold_v=ex_threshold_v)

        #基准站约束
        corr_v=[STA_P[0]-X[0][0], STA_P[1]-X[1][0], STA_P[2]-X[2][0]]
        corr_sstd=[STA_Q[0],STA_Q[1],STA_Q[2]]
        ref_id=0
        H,R,v=add_PPP_RTK_corr(H,R,v,corr_v,corr_sstd,[],rnx_obs)

        #系统模型(根据先验抗差得到的数据)
        t_Xk,t_Pk,t_Qk=createKF_XkPkQk_M(rnx_obs,X,Pk,Qk)

        #抗差滤波准备
        #R=IGGIII(v,R)
        #扩展卡尔曼滤波
        #1.状态一步预测
        PHIk_1_k=np.eye(t_Xk.shape[0],dtype=np.float64)
        X_up=PHIk_1_k.dot(t_Xk)
        #2.状态一步预测误差
        Pk_1_k=(PHIk_1_k.dot(t_Pk)).dot(PHIk_1_k.T)+t_Qk
        #3.滤波增益计算
        #Kk=(Pk_1_k.dot(H.T)).dot(inv((H.dot(Pk_1_k)).dot(H.T)+R))
        Kk=(Pk_1_k.dot(H.T)).dot(numba_inv((H.dot(Pk_1_k)).dot(H.T)+R))
        #滤波结果
        Xk_dot=X_up+Kk.dot(v)
        #滤波方差更新
        t_Pk=((np.eye(t_Xk.shape[0],dtype=np.float64)-Kk.dot(H))).dot(Pk_1_k)  
        t_Pk=t_Pk.dot((np.eye(t_Xk.shape[0],dtype=np.float64)-Kk.dot(H)).T)+Kk.dot(R).dot(Kk.T)
        #滤波暂态更新
        t_Xk_f,t_Pk_f,t_Qk_f,t_X_time=upstateKF_XkPkQk_M(rnx_obs,rt_unix,Xk_dot,t_Pk,t_Qk,X,Pk,Qk,X_time)
        
        #验后方差
        info='KF fixed'
        info,rnx_obs,tt_phase_bias,v=createKF_HRZ_M(rnx_obs,rt_unix,t_Xk_f,t_X_time,t_Pk_f,t_Qk_f,ion_param,t_phase_bias,peph_sat_pos,freqs=freqs,exthreshold_v_sigma=ex_threshold_sigma,post=True)
        #_,info=get_post_v(rnx_obs,rt_unix,Xk_dot,ion_param,phase_bias)
        
        if(info=='KF fixed'):    
            #验后校验通过
            X,Pk,Qk,X_time=upstateKF_XkPkQk_M(rnx_obs,rt_unix,Xk_dot,t_Pk,t_Qk,X,Pk,Qk,X_time)
            phase_bias=tt_phase_bias.copy()
            break
    if(info!='KF fixed'):
        print("Warning: KF itertion overflow")

    return X,Pk,Qk,X_time,v,phase_bias,rnx_obs

#大气约束
def rtkinfo2SIONTRO(rtk_info,freqs,Qi_init=2.0):
    SION,TRO={},{}
    for prn in rtk_info.keys():
        #1. 剔除低高度角改正数
        try:
            el=rtk_info[prn]['azel'][1]
            if(el<10.0):
                continue
        except:
            pass
        #2. 分发频率
        f1=freqs[['G','C','E'].index(prn[0])][0]
        #3. 构建电离层延迟改正数群组
        SION[prn]=[rtk_info[prn]['STEC']*40.28/(f1/1e8)/(f1/1e8),Qi_init**2]
        try:
            SION[prn][1]=(rtk_info[prn]['std_STEC']+Qi_init**2)*(40.28/(f1/1e8)/(f1/1e8))**2
        except:
            pass
    #3. 分发基准站位置 (用于定权)
    base_pos=[0,0,0]
    if(rtk_info!={}):
        base_x=rtk_info[list(rtk_info.keys())[0]]['sta_x']
        base_y=rtk_info[list(rtk_info.keys())[0]]['sta_y']
        base_z=rtk_info[list(rtk_info.keys())[0]]['sta_z']
        base_pos=[base_x,base_y,base_z]
        try:
            TRO['ZTD']=rtk_info[list(rtk_info.keys())[0]]['ztd_w']+rtk_info[list(rtk_info.keys())[0]]['ztd_h']    #含模型值的ZTD必须传递原始值
            TRO['ZTD-Q']=rtk_info[list(rtk_info.keys())[0]]['std_ztd_w']    #利用估计量的代替模型值
        except:
            TRO['ZTD']=get_Trop_delay_dry(base_pos)+0.15
            TRO['ZTD-W-Q']=1.0
    
    return SION,TRO,base_pos

def get_IPP_rad(rr,rs):
    #B2b信号推荐参数设置
    H_ion=350000            #电离层薄层高度
    Re=6378000              #地球平均半径
    lng_M=-72.58/180*pi     #地磁北极的地理经度
    lat_M=80.27/180*pi      #地磁北极的地理纬度
    
    #站星射线与高度角计算
    #Calculation of star ray and height angle at station 
    az,el=getazel(rs,rr)
    #测站经纬度
    rrb,rrl,rrh=xyz2blh(rr[0],rr[1],rr[2])
    rrb=rrb/180*pi
    rrl=rrl/180*pi
    #电离层穿刺点地心张角计算
    PHI=pi/2-el-asin(Re/(Re+H_ion)*cos(el))
    #电离层穿刺点在地球表面投影的地理经纬度
    lat_g=asin( sin(rrb)*cos(PHI)+cos(rrb)*sin(PHI)*cos(az) )
    lng_g=rrl+atan2(sin(PHI)*sin(az)*cos(rrb),cos(PHI)-sin(rrb)*sin(lat_g))
    #电离层延迟在地球表面投影的地磁经纬度
    lat_m=asin(sin(lat_M)*sin(lat_g) + cos(lat_M)*cos(lat_g)*cos(lng_g-lng_M) )
    lng_m=atan2(cos(lat_g)*sin(lng_g-lng_M)*cos(lat_M) , sin(lat_M)*sin(lat_m)-sin(lat_g) )
    return lat_g,lng_g

def caculate_PPP_RTK_corr_M(rnx_obs, X, pos=[], TRO={}, SION={}, peph_sat_pos={}, base_pos=None, rove_pos=[], Qi_scale=10e3, Qi_ele_threshold=10,Qt_scale=10e6):
    # 函数: 计算PPP_RTK约束向量与方差向量
    # 输入: 有效观测列表rnx_obs, 位置约束(初始化为空), 大气约束(初始化为空字典), 电离层约束(初始化为空字典),  
    # 输出: PPP_RTK约束向量corr_v, 方差向量corr_sstd
    corr_v=[]
    corr_sstd=[]
    sys_sat_num=round((len(X)-5)/3)
    #位置约束
    if(len(pos)!=3):
        corr_v.append(0.0)
        corr_v.append(0.0)
        corr_v.append(0.0)
        corr_sstd.append(0.001)
        corr_sstd.append(0.001)
        corr_sstd.append(0.001)
    else:
        corr_v.append(pos[0]-X[0][0])
        corr_v.append(pos[1]-X[1][0])
        corr_v.append(pos[2]-X[2][0])
        corr_sstd.append(0.001)
        corr_sstd.append(0.001)
        corr_sstd.append(0.001)
    
    #钟差约束预留位置
    corr_v.append(0.0)
    corr_sstd.append(0.0)

    #对流层约束(当前仅支持ZWD加入约束)
    if(TRO!={} and Qt_scale!=-1):
        baseline=sqrt( (base_pos[0]-X[0][0])**2+(base_pos[1]-X[1][0])**2+(base_pos[2]-X[2][0])**2 )
        corr_v.append((TRO['ZTD']-get_Trop_delay_dry(rove_pos))-X[4][0])
        #corr_v.append(0.0)
        corr_sstd.append(TRO['ZTD-Q']+(baseline/Qt_scale)**2)#以10cm为方差
        #corr_sstd.append(1.0*1.0)
    else:
        corr_v.append(0.0)
        corr_sstd.append(0.0)
    
    #电离层约束(星间单差模式)
    #首先选择参考星
    ref_prns=['X00','X00','X00']
    el_maxs=[0,0,0]
    ref_ids=[999,999,999]
    count_id=0
    for sat in rnx_obs:
        prn=sat["PRN"]
        _,el=getazel(peph_sat_pos[prn],[X[0][0],X[1][0],X[2][0]])   #获取高度角
        if(prn not in SION.keys()):                            #无SSR的卫星跳过
            count_id+=1
            continue
        if(el>el_maxs[0] and prn[0]=='G'):
            el_maxs[0]=el
            ref_prns[0],ref_ids[0]=prn,count_id
        if(el>el_maxs[1] and prn[0]=='C'):
            el_maxs[1]=el
            ref_prns[1],ref_ids[1]=prn,count_id
        if(el>el_maxs[2] and prn[0]=='E'):
            el_maxs[2]=el
            ref_prns[2],ref_ids[2]=prn,count_id
        count_id+=1
    
    for sat in rnx_obs:
        prn=sat['PRN']
        sys_id=['G','C','E'].index(prn[0])
        sys_shift=[0,3*32,3*(32+65)]
        sat_count=int(prn[1:])-1
        ref_count=int(ref_prns[sys_id][1:])-1
        _,el=getazel(peph_sat_pos[prn],[X[0][0],X[1][0],X[2][0]])
        try:
            sion,sion_r=SION[prn][0],SION[ref_prns[sys_id]][0]              #基准站站解ION(单位为m)
            sion_q,sion_r_q=SION[prn][1],SION[ref_prns[sys_id]][1]          #基准站电离层质量因子(单位为m)
            ion,ion_r=X[5+sys_shift[sys_id]+sat_count][0],X[5+sys_shift[sys_id]+ref_count][0]
            #电离层状态方差信息
            Qi0=sion_q#+sion_r_q                                #基准站质量因子
            lat_b,lng_b=get_IPP_rad(base_pos,peph_sat_pos[prn])
            lat_r,lng_r=get_IPP_rad(rove_pos,peph_sat_pos[prn])
            Qid=(float(Qi_scale)**2)*((lat_b-lat_r)**2+(lng_b-lng_r)**2)        #基线质量衰减因子
            Qi1=Qid/sin(el)/sin(el)                             #高度角加权因子
            #所有约束信息校验通过, 添加约束和约束方差
            if(Qi_scale!=-1 and el/pi*180.0>=Qi_ele_threshold):
                corr_v.append((sion-sion_r)-(ion-ion_r))                        #虚拟观测约束添加
                corr_sstd.append(Qi0+Qi1)                           #电离层SSR约束方差
            else:
                corr_sstd.append(0.0)
                corr_v.append(0.0)
        except:
            corr_v.append(0.0)
            corr_sstd.append(0.0)
    return corr_v,corr_sstd,ref_ids


def KF_UCPPP_RTK_Rove(X,X_time,Pk,Qk,ion_param,peph_sat_pos,rnx_obs,ex_threshold_v,ex_threshold_sigma,rt_unix,phase_bias,freqs,RTK_Info):
    for KF_times in range(8):
        #相位改正值拷贝
        t_phase_bias=phase_bias.copy()
        
        #观测模型(两次构建, 验前粗差剔除)
        #print(rnx_obs)
        X,X_time,H,R,_,v,rnx_obs=createKF_HRZ_M(rnx_obs,rt_unix,X,X_time,Pk,Qk,ion_param,t_phase_bias,peph_sat_pos,freqs=freqs,exthreshold_v_sigma=ex_threshold_sigma,post=False,ex_threshold_v=ex_threshold_v)
        if(not len(rnx_obs)):
            #无先验通过数据
            #全部状态重置
            X[0]=100.0
            X[1]=100.0
            X[2]=100.0
            # for i in range(len(X)):
            #     X_time[i]=0.0
            #     break
        X,X_time,H,R,_,v,rnx_obs=createKF_HRZ_M(rnx_obs,rt_unix,X,X_time,Pk,Qk,ion_param,t_phase_bias,peph_sat_pos,freqs=freqs,exthreshold_v_sigma=ex_threshold_sigma,post=False,ex_threshold_v=ex_threshold_v)

        
        #流动站大气约束
        _,GPSsec=time2gpst(rt_unix)
        t_interval=RTK_Info['t_interval']
        GPSsec=round(GPSsec/t_interval)*t_interval      #SSR时间戳
        try:
            rtk_info_id=RTK_Info['rtk_corr_info_time'].index(GPSsec)
            rtk_info=RTK_Info['rtk_info'][rtk_info_id]#查找目标时间对应的SSR组
        except:
            rtk_info={}
        SION,TRO,base_pos=rtkinfo2SIONTRO(rtk_info,freqs,Qi_init=RTK_Info['Qi_init'])
        rove_pos=[X[0][0],X[1][0],X[2][0]]
        corr_v,corr_sstd,ref_ids=caculate_PPP_RTK_corr_M(rnx_obs,X,TRO=TRO,SION=SION,peph_sat_pos=peph_sat_pos,base_pos=base_pos,rove_pos=rove_pos,Qi_scale=RTK_Info['Qi_scale'],Qi_ele_threshold=RTK_Info['Qi_ele_threshold'],Qt_scale=RTK_Info['Qt_scale'])
        H,R,v=add_PPP_RTK_corr(H,R,v,corr_v,corr_sstd,ref_ids=ref_ids,rnx_obs=rnx_obs)
            
        #系统模型(根据先验抗差得到的数据)
        t_Xk,t_Pk,t_Qk=createKF_XkPkQk_M(rnx_obs,X,Pk,Qk)

        #抗差滤波准备
        #R=IGGIII(v,R)
        #扩展卡尔曼滤波
        #1.状态一步预测
        PHIk_1_k=np.eye(t_Xk.shape[0],dtype=np.float64)
        X_up=PHIk_1_k.dot(t_Xk)
        #2.状态一步预测误差
        Pk_1_k=(PHIk_1_k.dot(t_Pk)).dot(PHIk_1_k.T)+t_Qk
        #3.滤波增益计算
        #Kk=(Pk_1_k.dot(H.T)).dot(inv((H.dot(Pk_1_k)).dot(H.T)+R))
        Kk=(Pk_1_k.dot(H.T)).dot(numba_inv((H.dot(Pk_1_k)).dot(H.T)+R))
        #滤波结果
        Xk_dot=X_up+Kk.dot(v)
        #滤波方差更新
        t_Pk=((np.eye(t_Xk.shape[0],dtype=np.float64)-Kk.dot(H))).dot(Pk_1_k)  
        t_Pk=t_Pk.dot((np.eye(t_Xk.shape[0],dtype=np.float64)-Kk.dot(H)).T)+Kk.dot(R).dot(Kk.T)
        #滤波暂态更新
        t_Xk_f,t_Pk_f,t_Qk_f,t_X_time=upstateKF_XkPkQk_M(rnx_obs,rt_unix,Xk_dot,t_Pk,t_Qk,X,Pk,Qk,X_time)
        
        #验后方差
        info='KF fixed'
        info,rnx_obs,tt_phase_bias,v=createKF_HRZ_M(rnx_obs,rt_unix,t_Xk_f,t_X_time,t_Pk_f,t_Qk_f,ion_param,t_phase_bias,peph_sat_pos,freqs=freqs,exthreshold_v_sigma=ex_threshold_sigma,post=True)
        #_,info=get_post_v(rnx_obs,rt_unix,Xk_dot,ion_param,phase_bias)
        
        if(info=='KF fixed'):    
            #验后校验通过
            X,Pk,Qk,X_time=upstateKF_XkPkQk_M(rnx_obs,rt_unix,Xk_dot,t_Pk,t_Qk,X,Pk,Qk,X_time)
            phase_bias=tt_phase_bias.copy()
            break
    if(info!='KF fixed'):
        print("Warning: KF itertion overflow")
    return X,Pk,Qk,X_time,v,phase_bias,rnx_obs

def init_UCPPP_IGS_M(obs_mats,freqs,obs_start,IGS,clk,sat_out,ion_param,sat_pcos,sys_sat_nums=[32,65,37]):
    obs_mat_GPS,obs_mat_BDS,obs_mat_GAL=obs_mats[0],obs_mats[1],obs_mats[2]
    sat_num_G,sat_num_C,sat_num_E=sys_sat_nums[0],sys_sat_nums[1],sys_sat_nums[2]
    X_G,Pk_G,Qk_G,GF_sign_G,Mw_sign_G,slip_sign_G,dN_sign_G,X_time_G,phase_bias_G=init_UCPPP(obs_mat_GPS,obs_start,IGS,clk,sat_out,ion_param,sat_pcos,sys_sat_num=sat_num_G,f1=freqs[0][0],f2=freqs[0][1])
    X_C,Pk_C,Qk_C,GF_sign_C,Mw_sign_C,slip_sign_C,dN_sign_C,X_time_C,phase_bias_C=init_UCPPP(obs_mat_BDS,obs_start,IGS,clk,sat_out,ion_param,sat_pcos,sys_sat_num=sat_num_C,f1=freqs[1][0],f2=freqs[1][1])
    X_E,Pk_E,Qk_E,GF_sign_E,Mw_sign_E,slip_sign_E,dN_sign_E,X_time_E,phase_bias_E=init_UCPPP(obs_mat_GAL,obs_start,IGS,clk,sat_out,ion_param,sat_pcos,sys_sat_num=sat_num_E,f1=freqs[2][0],f2=freqs[2][1])

    #多系统非差PPP滤波状态初始化
    X,Pk,Qk,GF_sign,Mw_sign,slip_sign,dN_sign,X_time,phase_bias=init_UCPPP_M(X_G,X_C,X_E,
                 Pk_G,Pk_C,Pk_E,
                 Qk_G,Qk_C,Qk_E,
                 GF_sign_G,GF_sign_C,GF_sign_E,
                 Mw_sign_G,Mw_sign_C,Mw_sign_E,
                 slip_sign_G,slip_sign_C,slip_sign_E,
                 dN_sign_G,dN_sign_C,dN_sign_E,
                 X_time_G,X_time_C,X_time_E,
                 phase_bias_G,phase_bias_C,phase_bias_E)
    return X,Pk,Qk,GF_sign,Mw_sign,slip_sign,dN_sign,X_time,phase_bias

#配置文件操作主函数
def PPP_B2b_YAML(B2b_cfg):
    #打印配置文件
    print("Easy4B2b Configurations:")
    for key in B2b_cfg.keys():
        print(key,B2b_cfg[key])
    
    #主业务流程(PPPB2b实时解码与卫星位置计算)
    sat_num=32+65+37
    #频率分发
    freqs=B2b_cfg['freqs']
    f1=freqs[1][0]
    f2=freqs[1][1]
    f1_G=freqs[0][0]
    f2_G=freqs[0][1]
    #求解常值配置
    el_threthod=B2b_cfg['el_threthod']                                #设置截止高度角
    ex_threshold_v=B2b_cfg['ex_threshold_v']                          #设置先验残差阈值
    ex_threshold_v_sigma=B2b_cfg['ex_threshold_v_sigma']              #设置后验残差阈值
    Mw_threshold=B2b_cfg['Mw_threshold']                              #设置Mw组合周跳检验阈值
    GF_threshold=B2b_cfg['GF_threshold']                              #设置GF组合周跳检验阈值
    out_age=B2b_cfg['out_age']                                        #失锁容限
    out_path=B2b_cfg['out_path']

    #流动站改正数约束信息(文件仿真)
    #基准站信息
    try:
        sta_mode=B2b_cfg['sta_mode']
        STA_P=B2b_cfg['STA_P']
        STA_Q=B2b_cfg['STA_Q']
    except:
        sta_mode='None'
        STA_P=None
        STA_Q=None

    #整理PPP-RTK信息
    RTK_Info={}
    try:
        RTK_Info['reinitial_sec']=B2b_cfg['reinitial_sec']  #记录重收敛信息
    except:
        RTK_Info['reinitial_sec']=0                         #没有重收敛信息
    
    if(sta_mode=='Base'):
        RTK_Info['STA_P']=STA_P
        RTK_Info['STA_Q']=STA_Q
    if(sta_mode=='Rove'):
        RTK_Info['t_interval']=B2b_cfg['t_interval']
        RTK_Info['rtk_info']=np.load(B2b_cfg["rtk_info_mat"],allow_pickle=True)
        
        rtk_corr_info_time=[]
        for log in RTK_Info['rtk_info']:
            try:
                rtk_corr_info_time.append(log[list(log.keys())[0]]['GPSsec'])
            except:
                rtk_corr_info_time.append(9999999)
        RTK_Info['rtk_corr_info_time']=rtk_corr_info_time
        RTK_Info['Qi_init']=B2b_cfg['Qi_init']
        RTK_Info['Qi_scale']=B2b_cfg['Qi_scale']
        RTK_Info['Qi_ele_threshold']=B2b_cfg['Qi_ele_threshold']
        RTK_Info['Qt_scale']=B2b_cfg['Qt_scale']
    IGS,CLK,sat_pcos=[],[],{}
    if(sta_mode=='IGSR'):
        CLK=getclk(B2b_cfg['CLK_file'])
        IGS=getsp3(B2b_cfg['SP3_file'])
        sat_pcos=RINEX3_to_ATX(B2b_cfg['ATX_file'])

    try:
        sat_out=B2b_cfg['sat_out']
    except:
        sat_out=0
    dy_mode=B2b_cfg['dy_mode']
    obs_start_time=epoch2time(COMMTIME(*B2b_cfg['obs_start_time']))
    obs_end_time=epoch2time(COMMTIME(*B2b_cfg['obs_end_time']))

    MEO_only=B2b_cfg['MEO_only']
    

    #配置读取完毕, 以下为主流程
    epoch=0                                                                #初始化历元标识
    Out_log=[]
    ion_params=[]
    
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
    
    with open(B2b_cfg['obs_stream'],'r') as f:
        lines=f.readlines()
        for line in lines:
            # 广播星历读取部分: Message ID 77
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
                #跳过非求解历元
                if(rt_unix<obs_start_time or rt_unix>obs_end_time):
                    continue
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
                    continue
                
                #滤波状态初始化
                if(not epoch or (RTK_Info['reinitial_sec'] and rt_sec%(RTK_Info['reinitial_sec'])==0)):
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
                print("[{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}]".format(ct['year'],ct['month'],ct['day'],ct['hour'],ct['minute'],int(ct['second'])),len(rnx_obs),"{:.6f} {:.6f} {:.6f}".format(abs(std_neu[0]),abs(std_neu[1]),abs(std_neu[2])),end='\r')
    #结果以numpy数组格式保存在指定输出目录下, 若输出目录为空, 则存于nav_result
    try:
        np.save(out_path+'/{}.out'.format(os.path.basename(B2b_cfg['obs_stream'])),Out_log,allow_pickle=True)
        print("\nNavigation results saved at ",out_path+'/{}.out'.format(os.path.basename(B2b_cfg['obs_stream'])))
    except:
        np.save('nav_result/{}.out'.format(os.path.basename(B2b_cfg['obs_stream'])),Out_log,allow_pickle=True)
        print("\nNavigation results saved at ",'nav_result/{}.out'.format(os.path.basename(B2b_cfg['obs_stream'])))


if __name__=='__main__':
    #根据配置文件计算PPP-B2b结果
    B2b_YAML="Easy4B2b.yaml"
    with open(B2b_YAML,"r",encoding='utf-8') as f:
        cfg=yaml.safe_load(f)
        print("sys_index set as multi-GNSS")
        PPP_B2b_YAML(cfg)