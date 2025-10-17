"""
This script is part of the TIMESAT toolkit for the RAMONA project.

Author: Zhanzhang Cai

This Python script is designed to perform a variety of tasks related to time-series analysis of satellite sensor data, in the context of the RAMONA project.

Instructions for running the code:
1. Ensure that you have the necessary packages installed and the data available in the correct directories.
2. In the terminal, navigate to the directory containing this script.
3. Enter 'python run.py -help'.
4. Follow any prompts that appear in the terminal.

Please ensure you have read the associated documentation and understand the functions within this code before running it.

Please modify L20 in settings_test_evi2.json for the path of output.
For test:
Enter 'python run.py -i settings_test_evi2.json' in your terminal

For any further questions or assistance, contact Zhanzhang Cai.
"""

# from memory_profiler import profile
import json
import math
import os
import numpy as np
import timesat
import time
import copy
import re
import datetime
import argparse
import rasterio
from rasterio.windows import Window
import ray


def _readfilelist_(s3_data_list, s3_qa_list):

    with open(s3_data_list, 'r') as f:
        s3_flist = f.read().splitlines()
    if s3_qa_list != '':
        with open(s3_qa_list, 'r') as f:
            s3_qlist = f.read().splitlines()
        if len(s3_flist) != len(s3_qlist):
            print('No. of Data and QA are not consistent')
            exit()

    return s3_flist, s3_qlist


def _openimagedatafiles_(x_map, y_map, x, y, yflist, wflist, data_type, num_core):
    z = len(yflist)
    vi = np.ndarray((y, x, z), order='F', dtype=data_type)
    qa = np.ndarray((y, x, z), order='F', dtype=data_type)
    i = 0

    if num_core > 1:
        vi_para = np.ndarray((y, x), order='F', dtype=data_type)
        @ray.remote
        def _readimgpara_(yfname):
            with rasterio.open(yfname, 'r') as temp:
                vi_para[:, :] = temp.read(1, window=Window(x_map, y_map, x, y))
            return vi_para

        futures = [_readimgpara_.remote(i) for i in yflist]
        futures_out = ray.get(futures)
        vi = np.stack([item for item in futures_out], axis=2)
        futures_out = None

        
    else:
        for yfname in yflist:
            with rasterio.open(yfname, 'r') as temp:
                vi[:, :, i] = temp.read(1, window=Window(x_map, y_map, x, y))
            i += 1

    if wflist == '':
        qa = np.ones((y, x, z))
    else:
        i = 0
        for wfname in wflist:
            with rasterio.open(wfname, 'r') as temp2:
                # qatemp = temp2.read(1, window=Window(int(x_map/2), int(y_map/2), int(x/2), int(y/2)))
                # qa[:, :, i] = np.repeat(np.repeat(qatemp, 2, axis=1), 2, axis=0)
                qa[:, :, i] = temp2.read(1, window=Window(x_map, y_map, x, y))
            i += 1
    return vi, qa


def _readtv_(tlist, flistfull):
    flist = [os.path.basename(file_path) for file_path in flistfull]
    timevector = np.ndarray(int(len(flist)), order='F', dtype='uint32')
    if tlist == '':
        firstimg = flist[0]
        date_regex1 = r"\d{4}-\d{2}-\d{2}"
        date_regex2 = r"\d{4}\d{2}\d{2}"
        try:
            dates = re.findall(date_regex1, firstimg)
            position = firstimg.find(dates[0])
            pos_y = [i + position for i in [0, 4]]
            pos_m = [i + position for i in [5, 7]]
            pos_d = [i + position for i in [8, 10]]
            print("First date", firstimg[pos_y[0]:pos_y[1]], firstimg[pos_m[0]:pos_m[1]], firstimg[pos_d[0]:pos_d[1]])
        except:
            try:
                dates = re.findall(date_regex2, firstimg)
                position = firstimg.find(dates[0])
                pos_y = [i + position for i in [0, 4]]
                pos_m = [i + position for i in [4, 6]]
                pos_d = [i + position for i in [6, 8]]
                print("First date", firstimg[pos_y[0]:pos_y[1]], firstimg[pos_m[0]:pos_m[1]],
                      firstimg[pos_d[0]:pos_d[1]])
            except:
                print('No date found!')
                print('Please use date input')
                exit()
        i = 0
        for fname in flist:
            temp_y = int(fname[pos_y[0]:pos_y[1]])
            temp_m = int(fname[pos_m[0]:pos_m[1]])
            temp_d = int(fname[pos_d[0]:pos_d[1]])
            try:
                temp_t = datetime.date.toordinal(datetime.date(temp_y, temp_m, temp_d)) - datetime.date.toordinal(
                    datetime.date(temp_y, 1, 1)) + 1
                timevector[i] = temp_y * 1000 + temp_t
                i += 1
            except:
                print('File name is not consistent')
                exit()
    else:
        with open(tlist, 'r') as f:
            t = f.read().splitlines()
            timevector = [int(i) for i in t]

    yrstart = math.floor(min(timevector) / 1000)
    yrend = math.floor(max(timevector) / 1000)
    yr = yrend - yrstart + 1  # number of year
    return timevector, yr, yrstart, yrend

def _createlocaloutputfolder_(outfolder):
    # Define the name of the folder to create
    vpp_folder = outfolder + '/VPP'
    st_folder = outfolder + '/ST'
    # Use os.makedirs() function to create the folder
    try:
        os.makedirs(vpp_folder)
    except FileExistsError:
        print("VPP Folder already exists.")
    try:
        os.makedirs(st_folder)
    except FileExistsError:
        print("ST Folder already exists.")
    return st_folder, vpp_folder


def _ts_run_(data):

    print(data)
    
    jobname = data['settings']['jobname']['value']
    s3_data_list = data['settings']['image_file_list']['value']
    s3_qa_list = data['settings']['quality_file_list']['value']
    s3_tv_list = data['settings']['tv_list']['value']
    outfolder = data['settings']['outputfolder']['value']
    imwindow = data['settings']['imwindow']['value']
    p_ignoreday = data['settings']['p_ignoreday']['value']
    p_ylu = data['settings']['p_ylu']['value']
    p_a = [item for sublist in data['settings']['p_a']['value'] for item in sublist]
    outststep = data['settings']['p_st_timestep']['value']
    p_nodata = data['settings']['p_nodata']['value']
    p_outlier = data['settings']['p_outlier']['value']
    p_fitmethod = data['settings']['p_fitmethod']['value']
    p_nenvi = data['settings']['p_nenvi']['value']
    p_wfactnum = data['settings']['p_wfactnum']['value']
    p_startmethod = data['settings']['p_startmethod']['value']
    p_startcutoff = data['settings']['p_startcutoff']['value']
    p_low_percentile = data['settings']['p_low_percentile']['value']
    p_fillbase = data['settings']['p_fillbase']['value']
    p_hrvppformat = data['settings']['p_hrvppformat']['value']
    p_seasonmethod = data['settings']['p_seasonmethod']['value']
    p_seapar = data['settings']['p_seapar']['value']
    p_printflag = data['settings']['p_printflag']['value']
    max_memory_gb = data['settings']['max_memory_gb']['value']
    para_check = data['settings']['para_check']['value']
    ray_dir = data['settings']['ray_dir']['value']
    scale = data['settings']['scale']['value']
    offset = data['settings']['offset']['value']

    if para_check>0 and ray_dir!='':
        ray.init(_temp_dir=ray_dir)

    if outfolder == '':
        print('Nothing to do...')
        exit()

    if imwindow[2] + imwindow[3] == 2:
        imgprocessing = False
    else:
        imgprocessing = True

    flist, qlist = _readfilelist_(s3_data_list, s3_qa_list)

    timevector, yr, yrstart, yrend = _readtv_(s3_tv_list, flist)

    timevector, indices = np.unique(timevector, return_index=True)

    flist = [flist[i] for i in indices]
    if qlist != '':
        qlist = [qlist[i] for i in indices]

    z = len(flist)
    print(f'num of images: {z}')
    print('First image: ' + flist[0])
    print('Last image: ' + flist[z - 1])

    p_outindex = np.arange((datetime.datetime(yrstart, 1, 1) - datetime.datetime(yrstart, 1, 1)).days + 1, (datetime.datetime(yrstart+yr-1, 12, 31) - datetime.datetime(yrstart, 1, 1)).days + 1)[::outststep]
    p_outindex_num = len(p_outindex)

    with rasterio.open(flist[0], 'r') as temp:
        img_profile = temp.profile

    if sum(imwindow) == 0:
        dx = img_profile['width']
        dy = img_profile['height']
    else:
        dx = imwindow[2]
        dy = imwindow[3]

    if imgprocessing:
        local_st_folder, local_vpp_folder = _createlocaloutputfolder_(outfolder)  # need to modify if using S3 bucket

        vppname = ["SOSD", "SOSV", "LSLOPE", "EOSD", "EOSV", "RSLOPE", "LENGTH", "MINV", "MAXD", "MAXV", "AMPL",
                   "TPROD", "SPROD"]
        outyfitfn = ["" for x in range(p_outindex_num)]
        outvppfn = ["" for x in range(13 * 2 * (yrend - yrstart + 1))]
        i = 0
        j = 0
        for i_tv in p_outindex:
            yfitdate = datetime.date(yrstart, 1, 1) + datetime.timedelta(days=int(i_tv)) - datetime.timedelta(days=1)
            outyfitfn[i] = local_st_folder + '/TIMESAT_' + yfitdate.strftime('%Y-%m-%d') + '.tif'
            i += 1
        for i_yr in range(yrstart, yrend + 1):
            for i_seas in range(2):
                for i_seaspar in range(13):
                    outvppfn[j] = local_vpp_folder + '/TIMESAT_' + str(i_yr) +\
                                  '_season_' + str(i_seas + 1) + '_' + vppname[i_seaspar] + '.tif'
                    j += 1
        outnsfn = local_vpp_folder + '/TIMESAT_nsperyear.tif'

        img_profile_st = copy.deepcopy(img_profile)
        img_profile_st.update(compress='lzw')
        # scale and offset
        if scale != 0 or offset != 0:
            img_profile_st.update(dtype=rasterio.float32)

        img_profile_vpp = copy.deepcopy(img_profile)
        img_profile_vpp.update(nodata=p_nodata, dtype=rasterio.float32, compress='lzw')
        img_profile_ns = copy.deepcopy(img_profile)
        img_profile_ns.update(nodata=255, compress='lzw')

        if 1:
            with rasterio.open(outnsfn, 'w', **img_profile_ns) as outnsfile:
                0
            for i in outvppfn:
                with rasterio.open(i, 'w', **img_profile_vpp) as outvppfile:
                    0
            for i in outyfitfn:
                with rasterio.open(i, 'w', **img_profile_st) as outstfile:
                    0

    # Check the data type specified in img_profile_st
    data_type = img_profile['dtype']

    num_layers = p_outindex_num + z * 2 + (13 * 2) * yr
    # Number of elements in the array
    num_elements = dx * num_layers * dy
    # Memory required per element in bytes (32 bits / 8 bits per byte)
    memory_per_element_bytes = 32 / 8
    # Total memory required in bytes
    total_memory_bytes = num_elements * memory_per_element_bytes
    # Convert total memory required to megabytes (1 GB = 2^30 bytes)
    total_memory_mb = total_memory_bytes / (2 ** 30)

    print('maximum Memory Needed: ' + str(total_memory_mb))

    print('Memory used: ' + str(max_memory_gb))

    # Calculate num_layers based on given formula
    num_layers = p_outindex_num + z * 2 + (13 * 2) * yr

    # Memory per element in bytes for 32-bit floating point
    memory_per_element_bytes = 4

    # Calculate max dy
    max_memory_bytes = max_memory_gb * (2 ** 30)
    dy_max = max_memory_bytes / (dx * num_layers * memory_per_element_bytes)

    y_slice_size = min(np.floor(dy_max), dy)

    print('y_slice_size = ' + str(y_slice_size))

    num_block = int(np.ceil(dy / y_slice_size))

    if dy % y_slice_size > 0:
        y_slice_end = dy % y_slice_size
    else:
        y_slice_end = y_slice_size

    for iblock in range(num_block):
        print('Processing block: ' + str(iblock + 1) + '/' + str(num_block) + '  starttime: ' +
              str(datetime.datetime.now()))
        x = dx
        if iblock != num_block - 1:
            y = int(y_slice_size)  # 5490
        else:
            y = int(y_slice_end)
        x_map = int(imwindow[0])
        y_map = int(iblock * y_slice_size + imwindow[1])

        if is_s3_path(s3_data_list):
            with env:
                vi, qa = _openimagedatafiles_(x_map, y_map, x, y, flist, qlist, data_type)
        else:
            vi, qa = _openimagedatafiles_(x_map, y_map, x, y, flist, qlist, data_type)

        print('--- start TIMESAT processing ---' + '  starttime: ' +
              str(datetime.datetime.now()))

        # scale and offset
        if scale != 0 or offset != 0:
            vi = vi * scale + offset

        if para_check > 0:
            # vi_id = ray.put(vi)
            # qa_id = ray.put(qa)

            @ray.remote
            def runtimesat(vi_temp, qa_temp):
                vpp_para, vppqa, nseason_para, yfit_para, yfitqa, seasonfit, tseq = timesat.tsfprocess(
                    yr, vi_temp, qa_temp, timevector, p_outindex,
                    p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
                    p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
                    1, x, z, p_outindex_num)
                vpp_para = vpp_para[0, :, :]
                yfit_para = yfit_para[0, :, :]
                nseason_para = nseason_para[0, :]
                return vpp_para, yfit_para, nseason_para

            futures = [runtimesat.remote(np.expand_dims(vi[i, :, :], axis=0), np.expand_dims(qa[i, :, :], axis=0)) for i
                       in range(y)]
            futures_out = ray.get(futures)
            vpp = np.stack([item[0] for item in futures_out], axis=0)
            yfit = np.stack([item[1] for item in futures_out], axis=0)
            nseason = np.stack([item[2] for item in futures_out], axis=0)
            futures_out = None

        else:
            vpp, vppqa, nseason, yfit, yfitqa, seasonfit, tseq = timesat.tsfprocess(
                yr, vi, qa, timevector, p_outindex,
                p_ignoreday, p_ylu, p_a, p_printflag, p_fitmethod, p_nodata, p_davailwin, p_outlier, p_nenvi, p_wfactnum,
                p_startmethod, p_startcutoff, p_low_percentile, p_fillbase, p_hrvppformat, p_seasonmethod, p_seapar,
                y, x, z, p_outindex_num)

        vpp = np.moveaxis(vpp, -1, 0)
        if scale == 0 and offset == 0:
            yfit = np.moveaxis(yfit, -1, 0).astype(img_profile['dtype'])
        else:
            yfit = np.moveaxis(yfit, -1, 0).astype('float32')

        if imgprocessing:
            print('--- start writing geotif ---' + '  starttime: ' +
                  str(datetime.datetime.now()))
            if para_check > 0:
                @ray.remote
                def write_outputs_vpp(nlayer, arr):
                    with rasterio.open(nlayer, 'r+', **img_profile_vpp) as outfile:
                        outfile.write(arr, window=Window(x_map, y_map, x, y), indexes=1)

                [write_outputs_vpp.remote(outvppfn[i - 1], arr) for i, arr in enumerate(vpp, 1)]
                @ray.remote
                def write_outputs_st(nlayer, arr):
                    with rasterio.open(nlayer, 'r+', **img_profile_st) as outfile:
                        outfile.write(arr, window=Window(x_map, y_map, x, y), indexes=1)

                [write_outputs_st.remote(outyfitfn[i - 1], arr) for i, arr in enumerate(yfit, 1)]
            else:
                for i, arr in enumerate(vpp, 1):
                    with rasterio.open('{}'.format(outvppfn[i - 1]), 'r+', **img_profile_vpp) as outvppfile:
                        outvppfile.write(arr, window=Window(x_map, y_map, x, y), indexes=1)
                for i, arr in enumerate(yfit, 1):
                    with rasterio.open('{}'.format(outyfitfn[i - 1]), 'r+', **img_profile_st) as outstfile:
                        outstfile.write(arr, window=Window(x_map, y_map, x, y), indexes=1)

            with rasterio.open(outnsfn, 'r+', **img_profile_ns) as outnsfile:
                outnsfile.write(nseason, window=Window(x_map, y_map, x, y), indexes=1)

            print('Block: ' + str(iblock + 1) + '/' + str(num_block) + '  finishedtime: ' +
                  str(datetime.datetime.now()))

    return

