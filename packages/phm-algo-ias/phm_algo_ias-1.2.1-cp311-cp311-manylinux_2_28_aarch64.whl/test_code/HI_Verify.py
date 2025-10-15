# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 14:19:40 2023

@author: yunghua.chang
"""

import os
import numpy as np
import pandas as pd
#import scipy.stats as st
import datetime
#from glob import glob
#from matplotlib import pyplot as plt
#from sklearn.preprocessing import StandardScaler
#from sklearn.decomposition import PCA
#from scipy.stats import f, skew
#import matplotlib.ticker as ticker
#import pickle
import sys
#from types import SimpleNamespace

sys.path.append(os.getcwd())
from algo.HI import HI
from algo.RUL import RUL
from datetime import timedelta

import matplotlib.pyplot as plt
import pickle   

def plot(health, target):

    health = health.copy()
    health = health.sort_index()

    # 用 datetime index 轉為字串來當作 x 軸標籤
    health["TimeLabel"] = health.index.strftime("%Y-%m-%d %H:%M")

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(health["TimeLabel"], health["Score"], marker="o", color="#3A8FB7", label="Score")
    ax.axhline(0.9 * 100, linestyle="--", color="#F26D5A", label="Threshold")

    ax.set_title("Health Index - " + target, fontsize=20)
    ax.set_ylabel("Score", fontsize=15)
    ax.set_ylim(0, 100)

    # 控制 x 軸顯示密度
    step = max(len(health) // 12, 1)  # 至少每 12 個點顯示一次
    ax.set_xticks(health["TimeLabel"][::step])
    ax.set_xticklabels(health["TimeLabel"][::step], rotation=15, fontsize=10)

    plt.yticks(fontsize=12)
    plt.subplots_adjust(bottom=0.25)
    plt.legend()
    
    plt.show()


def drop_time_ranges(df, time_col="_time", ranges=None, fmt=None):
    """
    將 df 中 time_col 落在 ranges 內的列刪除（含起訖）。
    ranges: [("YYYY/MM/DD HH:MM:SS", "YYYY/MM/DD HH:MM:SS"), ...]
    fmt: 若你的時間字串有固定格式可填，否則留 None 讓 pandas 自動判斷
    """
    if ranges is None or len(ranges) == 0:
        return df

    out = df.copy()
    # 轉成 datetime
    out[time_col] = pd.to_datetime(out[time_col], format=fmt, errors="coerce")

    for start, end in ranges:
        start_dt = pd.to_datetime(start, format=fmt, errors="coerce")
        end_dt   = pd.to_datetime(end,   format=fmt, errors="coerce")
        mask = (out[time_col] >= start_dt) & (out[time_col] <= end_dt)
        out = out.loc[~mask]

    # 如果你後續還要把 Time 當 index 用：
    # out = out.set_index(time_col).sort_index()

    return out

#----------------------------------- 改欄位名稱 -------------------------------------------------------------
def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    將輸入的 DataFrame 欄位依照對應表改名
    Input: df (pandas.DataFrame)
    Output: df (pandas.DataFrame, 欄位已改名)
    """
    # 先去掉欄位名稱前後空白
    df.columns = df.columns.str.strip()

    mapping_dict = {
        "Time": "_time",
        "RPM": "RPM",
        "X-Overall": "X_Overall",
        "Y-Overall": "Y_Overall",
        "Z-Overall": "Z_Overall",
        "X-Peak": "X_Peak",
        "Y-Peak": "Y_Peak",
        "Z-Peak": "Z_Peak",
        "X-Peak to Peak": "X_Peak_to_Peak",
        "Y-Peak to Peak": "Y_Peak_to_Peak",
        "Z-Peak to Peak": "Z_Peak_to_Peak",
        "X-Crest Factor": "X_Crest_Factor",
        "Y-Crest Factor": "Y_Crest_Factor",
        "Z-Crest Factor": "Z_Crest_Factor",

        "X-Power in Band 01": "X_Power_in_Band_01",
        "X-Power in Band 02": "X_Power_in_Band_02",
        "X-Power in Band 03": "X_Power_in_Band_03",
        "X-Power in Band 04": "X_Power_in_Band_04",
        "X-Power in Band 05": "X_Power_in_Band_05",
        "X-Power in Band 06": "X_Power_in_Band_06",
        "X-Power in Band 07": "X_Power_in_Band_07",
        "X-Power in Band 08": "X_Power_in_Band_08",
        "X-Power in Band 09": "X_Power_in_Band_09",
        "X-Power in Band 10": "X_Power_in_Band_10",

        "Y-Power in Band 01": "Y_Power_in_Band_01",
        "Y-Power in Band 02": "Y_Power_in_Band_02",
        "Y-Power in Band 03": "Y_Power_in_Band_03",
        "Y-Power in Band 04": "Y_Power_in_Band_04",
        "Y-Power in Band 05": "Y_Power_in_Band_05",
        "Y-Power in Band 06": "Y_Power_in_Band_06",
        "Y-Power in Band 07": "Y_Power_in_Band_07",
        "Y-Power in Band 08": "Y_Power_in_Band_08",
        "Y-Power in Band 09": "Y_Power_in_Band_09",
        "Y-Power in Band 10": "Y_Power_in_Band_10",

        "Z-Power in Band 01": "Z_Power_in_Band_01",
        "Z-Power in Band 02": "Z_Power_in_Band_02",
        "Z-Power in Band 03": "Z_Power_in_Band_03",
        "Z-Power in Band 04": "Z_Power_in_Band_04",
        "Z-Power in Band 05": "Z_Power_in_Band_05",
        "Z-Power in Band 06": "Z_Power_in_Band_06",
        "Z-Power in Band 07": "Z_Power_in_Band_07",
        "Z-Power in Band 08": "Z_Power_in_Band_08",
        "Z-Power in Band 09": "Z_Power_in_Band_09",
        "Z-Power in Band 10": "Z_Power_in_Band_10",

        "Bearing": "Bearing",
        "Looseness": "Looseness",
        "Misalignment": "Misalignment",
        "Imbalance": "Imbalance",
        "Gear_mesh": "Gear_mesh",
        "Van_Pass": "Van_Pass",

        "Bearing %": "Bearing_percentage",
        "Looseness %": "Looseness_percentage",
        "Misalignment %": "Misalignment_percentage",
        "Imbalance %": "Imbalance_percentage",
        "Gear_mesh %": "Gear_mesh_percentage",
        "Van_Pass %": "Van_Pass_percentage",

        "Temperature": "Temperature",
        "X-Overall QC": "X_Overall_QC",
        "Y-Overall QC": "Y_Overall_QC",
        "Z-Overall QC": "Z_Overall_QC",
    }

    df = df.rename(columns=mapping_dict, errors="ignore")
    return df

if __name__ == "__main__":
    #------------------------------- << Training Model >> ---------------------------------------------------------
    time_scale = "h" # 輸入時間維度 : "每小時"("h"), "每分鐘"("min")
    file_path = os.path.join(os.getcwd(), "data", "410_good_1.csv")
    df = pd.read_csv(file_path) 

    #df = df[["Time"] + df.select_dtypes(include="number").columns.tolist()]
    df = rename_columns(df) # 更改欄位名稱 (.CSV檔欄位名稱->系統欄位名稱)

    algo_config = "1, 0, 1, 3, 3, 1, 1, 3" # [時長維度, testing資料離處理, 低解析度特徵刪除, 特徵選擇, 資料正規化, 模型, rul_deadline, feature_extraction]
    #df = df.loc[:1800] ############################
    #df = pd.concat([df] * 23, ignore_index=True)
    result = HI.training_model(df, algo_config) # Training Model : "training_model_robust_index"(訓練模型指標分數), "training_model_robust_status"(verify:綠燈，warning:紅燈)
    print(result)

    # result_clean = HI.outlier_clean(df, result) # 測試資料清洗後的model
    # print(result_clean)

    Health_train = plot(result['HI_Score'], target="train") # 繪出HI圖

    #展覽pickle檔案輸出
    # pick_path = os.path.join(os.getcwd(), "uploaded_files", "model", "model.pkl")
    # to_save = dict(result)
    # #to_save["for_demo"] = "for_demo" # 展覽pickle輸出，給系統辨識
    # with open(pick_path, "wb") as f:
    #     pickle.dump(to_save, f)

    #----------------------------------------<<測試一好一壞算法>>---------------------------------------------------------
    # file_path_1 = os.path.join(os.getcwd(), "data", "410_good_1_all_feature.csv")
    # df_1 = pd.read_csv(file_path_1) 
    # df_1 = rename_columns(df_1)
    # file_path_2 = os.path.join(os.getcwd(), "data", "Robust_Bad.csv")
    # df_2 = pd.read_csv(file_path_2) 
    # df_2 = rename_columns(df_2)
    # good_bad_result = HI.training_model_GB_compare(df_1, df_2,  time_scale)

    #------------------------------- << Inference_HI & 嫌疑度變量 >> ---------------------------------------------------------
    file_path_test = os.path.join(os.getcwd(), "data", "410_good_1.csv")
    test_df = pd.read_csv(file_path_test) 
    #test_df = df.loc[:12000]
    test_df = rename_columns(test_df) # 更改欄位名稱 (.CSV檔欄位名稱->系統欄位名稱)
    test_result = HI.testing_model(test_df,result) # Inference : 輸出  "HI_Score"(HI分數), "suspicious_variable"(變量嫌疑度)
    print(test_result)

    #test_cleaned = HI.testing_model(test_df,result_clean) # 測試資料清洗後的model
    Health_test = plot(test_result['HI_Score'], target="test")

    #------------------------------------- << RUL >> ------------------------------------------------------------------------
    RUL_result = RUL.rul_calculation(test_result["T2"], result, 0.9) # Inference : 輸出 RUL
    print(RUL_result)

    #------------------------------- << HI_Score 異常時間區段 >> --------------------------------------------------------------
    fail_time = HI.detect_bad_HI_zone(test_result["HI_Score"],threshold=90)
    print(fail_time)




