# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 14:19:40 2023

@author: yunghua.chang
"""

import os
import numpy as np
import pandas as pd
import scipy.stats as st
import datetime
from glob import glob
from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import f, skew
import matplotlib.ticker as ticker

#%% Health Index計算
def health_modeling(df, score, alpha=0.05):
    # 標準化
    scaler = StandardScaler()
    scaler.fit(df)
    df_scaled = scaler.transform(df)

    # 進行主成份分析降維
    pca = PCA(n_components=0.9)
    pca.fit(df_scaled)
    df_pca = pca.transform(df_scaled)

    # 計算模型的 mu & sigma
    model_mu = df_pca.mean(axis=0)
    model_cov = np.cov(df_pca.T)

    # 計算模型的UCL
    m = df_pca.shape[0]
    p = df_pca.shape[1]
    fscore = f.ppf(1 - alpha, p, m - p)
    ucl = (p * (m - 1)) / (m - p) * fscore

    ## 計算分數
    df_health = Health_Index(df_pca, model_mu, model_cov, ucl, df.index, score)

    return df_health, model_mu, model_cov, ucl, scaler, pca


def health_testing(df, model_mu, model_cov, ucl, scaler, pca):

    # 以模型平均&標準差進行標準
    df_scaled = scaler.transform(df)
    # 進行主成份分析降維
    df_pca = pca.transform(df_scaled)
    ## 計算分數
    df_health = Health_Index(df_pca, model_mu, model_cov, ucl, df.index, score)

    return df_health


def score_ewma(df_health, score):
    ## EWMA部分
    grade_rolling = df_health["Score"].ewm(span=3, adjust=False).mean()
    index = grade_rolling[df_health["Score"] < score * 100].index
    df_health.loc[index, "Score"] = grade_rolling[
        df_health["Score"] < score * 100
    ]
    return df_health


def CalTSquare(data_pca, i, mu, sigma):
    x = data_pca[i]
    bias = x - mu
    tsquare = bias.dot(np.linalg.pinv(sigma)).dot(np.transpose(bias))
    return tsquare


def CalScore(tsquare, ucl, score):

    score_ = np.exp(np.log(score) * ((tsquare) / ucl)) * 100

    return score_


def Health_Index(data_pca, model_mu, model_cov, ucl, index, score):

    df = pd.DataFrame(index=index)
    df["Tsquare"] = list(
        map(
            lambda x: CalTSquare(data_pca, x, model_mu, model_cov),
            np.arange(len(data_pca)),
        )
    )
    df["Score"] = df["Tsquare"].apply(lambda x: CalScore(x, ucl, score))

    return df


def plot(health, target):

    tick_spacing = 15
    fig, ax = plt.subplots(figsize=(20, 5))
    ax.plot(health.index, health["Score"], marker="o")
    ax.axhline(score * 100, color="r")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
    plt.title(" Health Index ," + target, fontsize=25)
    plt.yticks(fontsize=20)
    plt.xticks(rotation=15, fontsize=20)
    plt.ylim(0, 100)
    plt.show()



#%% 參數設定
score = 0.9
modeling_start_time = "2024-09-30 16:00:00"
modeling_end_time = "2024-10-21 23:59:59"

file_path = r"C:\Users\chiyu.hong\Desktop\T7_TLRB0100_00_00001_____9_2_edc_raw_data.csv"

df = pd.read_csv(file_path) 

df["txn_dttm"] = pd.to_datetime(df["txn_dttm"], errors="coerce")
df = df.set_index("txn_dttm")

indicator_name = [
    "X-OA_MAX~_X",	
    "Y-OA_MAX~_X",	
    "Z-B01_MAX~_X",	
    "Z-OA_MAX~_X",	
    "Y-B03_MAX~_X",	
    "X-B03_MAX~_X",	
    "TSquare~_X",	
    "Y-B01_MAX~_X",	
    "Z-B02_MAX~_X",	
    "X-B01_MAX~_X",	
    "Z-B03_MAX~_X",	
    "Y-B02_MAX~_X",	
    "X-B02_MAX~_X"
]

#%%
std_name = list(map(lambda x: x + "_std", indicator_name))
mean_name = list(map(lambda x: x + "_mean", indicator_name))

#%%
df_copy = df.copy()
df = df_copy[indicator_name].resample("H").max()
df = df.dropna(axis="index", how="any")
df[mean_name] = df_copy[indicator_name].resample("H").mean()
df[std_name] = df_copy[indicator_name].resample("H").std()

df = df.dropna(axis="index", how="any")

    

if __name__ == "__main__":
    target = "Train"

    (df_health_train, mu, cov, ucl, scaler, pca) = health_modeling(
        df.loc[modeling_start_time:modeling_end_time], score
    )

    df_health_train = df_health_train.rolling("3H").mean()

    # Health_train = plot(df_health_train, target)

#%%
## Test
if __name__ == "__main__":
    target = "Test"
    df_health_test = health_testing(
        df.loc[modeling_end_time:], mu, cov, ucl, scaler, pca
    )

    df_health_test = df_health_test.rolling("3H").mean()

    Health_test = plot(df_health_test, target)

