# Easy4B2b

[[中]](./README-zh.md) &ensp; [[EN]](./README.md)

An easily ported Real-Time PPP-B2b Toolbox coded in Python.

This is a part of open-source toolbox Easy4PNT. Other toolboxs of Easy4PNT is listed here (clicked to jump to the target): [[Easy4SPP]](https://github.com/alxanderjiang/Easy4SPP), [[Easy4RTK]](https://github.com/alxanderjiang/Easy4RTK), [[Easy4PPP]](https://github.com/alxanderjiang/Easy4PPP), [[Easy4PTK]](https://github.com/alxanderjiang/Easy4PTK).

## Quick Start
1. We provide a set of example data and a quick-start jupyter notebook tutorial "PPP_B2b_RTK_Service.ipynb". Make sure that you have sucessufully installed the Python as well as the numpy (for matrix computation), ipykernel (for running the Jupyter Notebook), numba (for accelerating Python computation), Pyyaml (for configuration files reading) and pyserial (for real time application) in your environment.
2. Due to the file size limitation of github (no more than 25MB for a file), we compress the "data" and "nav_result" folders into zip files and uploaded them to the Cloud Drive ([[Google Driver]](https://drive.google.com/drive/folders/1jiUGXHMB1W6iSe09Hc1iVTmT-9wfPqOy?usp=drive_link) or [[Lanzou Driver]](https://wwbwg.lanzouv.com/b01bjcqghe)). In order to try the provided example of G+C PPP-B2b solutions, you need first download and unzip the "data.zip" into the "data" folder in the project path. The example results for visualization is stored in 'nav_result.zip'. The above zip files are necessary to run Easy4PTK. 
3. After unzipping the "data" folder, run all the blocks of "PPP_B2b_RTK_Service.ipynb" or src/ppp_b2b_yaml.py, you all get an Easy4PNT solution log file in form of ".npy". The running script is following the configuration of Easy4B2b.yaml: using the B2b realtime log file "data/Real_Time/pimo0790.24o.b2b.log" to conduct static PPP-B2b results without any other constraints. The details of configuration is shown in Easy4B2b.yaml.
4. We provided an example of visualizing the solution log file. Run all the blocks of nav_result.ipynb, you can get figures about the PPP-B2b convergence curve, receiver clock bias, STEC scatter and the residuls scatter plot.

## Downloading and preperations
1. Download the **zip pakeage directly** or using git clone by running the following commend:
```bash
git clone https://github.com/alxanderjiang/Easy4B2b.git
```
2. Download the "data.zip" and "nav_result.zip" files from Google Drive ([[https://drive.google.com/drive/folders/1jiUGXHMB1W6iSe09Hc1iVTmT-9wfPqOy?usp=drive_link]](https://drive.google.com/drive/folders/1jiUGXHMB1W6iSe09Hc1iVTmT-9wfPqOy?usp=drive_link))) or LanZou Drive ([[https://wwbwg.lanzouv.com/b01bjcqghe]](https://wwbwg.lanzouv.com/b01bjcqghe)) . 
3. Unzip the sample data folders: data.zip and nav_result.zip to the same path of Easy4B2b. If linux but no GUI, please run the following commends:

```bash
cd Easy4B2b
unzip data.zip
unzip nav_result
```
4. Ensure that the numpy, tqdm, ipykernel, numba, Pyyaml and pyserial are available in your Python environment. If not, please run the following commends to install:

```bash
pip install numpy
pip install tqdm
pip install ipykernel
pip install numba
pip install Pyyaml
pip install pyserial
```

  numpy and tqdm is used in the core codes while ipykernel is necessary to run Jupyter Notebook tutorials. numba is used to accelerate the computation (this can be ignored by change all the "numba_inv" function to simple "inv()" function). Easy4B2b does not support running from a __main__ function with variables definition for post simulated solving, only Yaml Configuration file is supported. But the real-time solution script is runned by __main__ function with variables. Details will be shown in follow sections.
Some problems may happen when install or use numba because of laking the library scipy, please install it by running the following commends:

```bash
pip install scipy
```

## Post Mode: Replay and Re-solve the Real-Time Collected PPP-B2b Log Files form UM982



## Real-Time Mode: Real-Time PPP-B2b by the datastream transferred by UART


