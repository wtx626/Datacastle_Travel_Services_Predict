#!/home/sunnymarkliu/softwares/anaconda3/bin/python
# _*_ coding: utf-8 _*_

"""
@author: SunnyMarkLiu
@time  : 17-12-22 下午7:23
"""
from __future__ import absolute_import, division, print_function

import os
import sys

module_path = os.path.abspath(os.path.join('..'))
sys.path.append(module_path)

# remove warnings
import warnings

warnings.filterwarnings('ignore')

import datetime
import numpy as np
import pandas as pd
from pypinyin import lazy_pinyin
from sklearn.preprocessing import LabelEncoder
from conf.configure import Configure
from utils import data_utils


def check_last_time_order_info(uid, userid_grouped, flag, check_name):
    """ 最近的一次交易的具体信息 check_name """
    if flag == 0:
        return 2

    df = userid_grouped[uid]
    if df.shape[0] == 0:
        return 2
    else:
        return df.iloc[-1][check_name]


def pre_days_order_count(uid, userid_grouped, flag, days):
    """ 往前 days 的 order 数量 """
    if flag == 0:
        return 2

    df = userid_grouped[uid]
    if df.shape[0] == 0:
        return 2
    else:
        df = df.loc[df['days_from_now'] < days]
        return df.shape[0]


def pre_days_count(uid, userid_grouped, flag, days, check_name):
    """ 往前 days 的 order 的 check_name 数量 """
    if flag == 0:
        return 2

    df = userid_grouped[uid]
    if df.shape[0] == 0:
        return 2
    else:
        df = df.loc[df['days_from_now'] < days]
        if df.shape[0] == 0:
            return 0
        else:
            return len(df[check_name].unique())


def build_order_history_features(df, history):
    features = pd.DataFrame({'userid': df['userid']})

    df_ids = history['userid'].unique()
    userid_grouped = dict(list(history.groupby('userid')))

    #给trade表打标签，若id在login表中，则打标签为1，否则为0
    features['has_history_flag'] = features['userid'].map(lambda uid: uid in df_ids).astype(int)

    "基本特征"
    # 最近的一次交易的 orderType
    features['last_time_orderType'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'orderType'), axis=1)
    # 最近的一次交易的 days_from_now, order_year, order_month, order_day, order_weekofyear, order_weekday
    features['last_time_days_from_now'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'days_from_now'), axis=1)
    features['last_time_order_year'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'order_year'), axis=1)
    features['last_time_order_month'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'order_month'), axis=1)
    features['last_time_order_day'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'order_day'), axis=1)
    features['last_time_order_weekofyear'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'order_weekofyear'), axis=1)
    features['last_time_order_weekday'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'order_weekday'), axis=1)
    features['last_time_continent'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'continent'), axis=1)
    features['last_time_country'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'country'), axis=1)
    features['last_time_city'] = features.apply(lambda row: check_last_time_order_info(row['userid'], userid_grouped, row['has_history_flag'], 'city'), axis=1)

    "计数特征"
    # 往前 90days 的计数特征
    features['pre_90days_order_count'] = features.apply(lambda row: pre_days_order_count(row['userid'], userid_grouped, row['has_history_flag'], 90), axis=1)
    features['pre_90days_order_continent_count'] = features.apply(lambda row: pre_days_count(row['userid'], userid_grouped, row['has_history_flag'], 90, 'continent'), axis=1)
    features['pre_90days_order_country_count'] = features.apply(lambda row: pre_days_count(row['userid'], userid_grouped, row['has_history_flag'], 90, 'country'), axis=1)
    features['pre_90days_order_city_count'] = features.apply(lambda row: pre_days_count(row['userid'], userid_grouped, row['has_history_flag'], 90, 'city'), axis=1)

    return features


def build_time_category_encode(history):
    history['orderTime'] = pd.to_datetime(history['orderTime'], unit='s')

    # 训练集和测试集最后一天是 2017-09-11
    now = datetime.datetime(2017, 9, 12)
    history['days_from_now'] = history['orderTime'].map(lambda order: (now - order).days)
    history['order_year'] = history['orderTime'].dt.year
    history['order_month'] = history['orderTime'].dt.month
    history['order_day'] = history['orderTime'].dt.day
    history['order_weekofyear'] = history['orderTime'].dt.weekofyear
    history['order_weekday'] = history['orderTime'].dt.weekday
    history['order_hour'] = history['orderTime'].dt.hour
    history['order_minute'] = history['orderTime'].dt.minute
    history['order_is_weekend'] = history['orderTime'].map(lambda d: 1 if (d == 0) | (d == 6) else 0)
    history['order_week_hour'] = history['order_weekday'] * 24 + history['order_hour']
    # 按照时间排序
    history = history.sort_values(by='orderTime')

    history['continent'] = history['continent'].map(lambda c: '_'.join(lazy_pinyin(c)) if c == c else 'None')
    history['country'] = history['country'].map(lambda c: '_'.join(lazy_pinyin(c)) if c == c else 'None')
    history['city'] = history['city'].map(lambda c: '_'.join(lazy_pinyin(c)) if c == c else 'None')

    le = LabelEncoder()
    le.fit(history['continent'].values)
    history['continent'] = le.transform(history['continent'])
    le = LabelEncoder()
    le.fit(history['country'].values)
    history['country'] = le.transform(history['country'])
    le = LabelEncoder()
    le.fit(history['city'].values)
    history['city'] = le.transform(history['city'])

    return history


def main():
    feature_name = 'user_order_history_features'
    # if data_utils.is_feature_created(feature_name):
    #     return

    # 待预测订单的数据 （原始训练集和测试集）
    train = pd.read_csv(Configure.base_path + 'train/orderFuture_train.csv', encoding='utf8')
    test = pd.read_csv(Configure.base_path + 'test/orderFuture_test.csv', encoding='utf8')


    orderHistory_train = pd.read_csv(Configure.base_path + 'train/orderHistory_train.csv', encoding='utf8')
    orderHistory_test = pd.read_csv(Configure.base_path + 'test/orderHistory_test.csv', encoding='utf8')

    orderHistory_train = build_time_category_encode(orderHistory_train)
    orderHistory_test = build_time_category_encode(orderHistory_test)

    train_features = build_order_history_features(train, orderHistory_train)
    test_features = build_order_history_features(test, orderHistory_test)

    print('save ', feature_name)
    data_utils.save_features(train_features, test_features, feature_name)


if __name__ == "__main__":
    print("========== 构造用户历史订单特征 ==========")
    main()
