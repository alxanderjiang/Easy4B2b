#多核并行计算处理
import multiprocessing
#包括ppp_yaml
from ppp_b2b import *
import os

brd4_path='data/BRD4/brd40790.24p'                  #BRD4星历文件路径
B2b_log_path='data/Logs/20240319_B2b-PPP.25b.txt'   #B2b原始消息
out_path='data/Real_Time/'                          #仿真数据流文件输出路径
obs_interval=30                                                           #观测文件采样时间间隔(s)


#以yaml为函数入口, 创建单个进程
def task(log_path):
    os.system('python src/ppp_b2b.py {} {} {} {} {}'.format(log_path,brd4_path,B2b_log_path,out_path,obs_interval))
    return 

if __name__ == '__main__':
    main_path='data/OBS/'                               #观测数据文件夹路径(需带'/')
    #以下开始多线程求解
    task_paths=os.listdir(main_path)
    task_range=[]
    for t in task_paths:
        task_range.append(main_path+t)
    print("process list: ",task_paths)    
    with multiprocessing.Pool(processes=12) as pool:     # 创建进程池，指定进程数
        results = pool.map(task, task_range)            # 将任务分配给进程池中的进程
        print(results)