#!/usr/bin/env python
# coding: utf-8
import pickle
import warnings

import joblib
from lightgbm import LGBMClassifier

import logging

logging.getLogger("lightgbm").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")


import numpy as np
import re
import gc
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression
import pandas as pd
from lightgbm import LGBMClassifier

pd.set_option('display.max_columns', 200)
# ----------------------------
# 全局参数
# ----------------------------
TOP_K = 3
N_SPLITS = 5
SEED = 42
RARE_THR = 20
TE_SMOOTH = 50
MAX_EARLY_STOP = 200
LGB_ROUNDS = 2000
XGB_ROUNDS = 2000
CTB_ROUNDS = 2000

# 模型开关
HAS_XGB = True
HAS_CTB = True
HAS_RF = True
HAS_AUTO_ENGINEERING = True
verbose = False
verbose_int = 1 if verbose else 0
# 创建目录
import os

# os.makedirs("models", exist_ok=True)
#
# TRAIN_PATH = r"data/train.csv"
# TEST_PATH = r"data/testB.csv"
# SUB_PATH = r"data/submitB_xiefeng_0701_v1.csv"


# ----------------------------
# 数据读取与预处理函数
# ----------------------------
def load_data(train_path, test_path):
    """读取训练和测试数据"""
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    return train, test


# ----------------------------
# 自动特征生成函数
# ----------------------------
class HorizongtalFeature(object):

    def __init__(self):
        pass

    # 1. 对类别型特征，先进行计数和排序（每个特征横向衍生两列特征）value_counts和LabelEncoder
    @staticmethod
    def get_feats_vcrank(df, feat='', return_labelencoder=False):
        # 只能一列列进来
        # 0.1 计数特征 value_counts
        ftr_ = df[feat].value_counts()
        ftr_ = pd.DataFrame(list(zip(ftr_.index, ftr_.values)), columns=[feat, feat + '_' + 'vcounts'])
        df = df.merge(ftr_, 'left', on=feat)
        # 0.2 排序特征
        le = LabelEncoder()
        ftr_ = le.fit_transform(df[feat])
        df[feat + '_' + 'rank'] = ftr_
        if return_labelencoder:
            return le, df  # 返回的le可以对测试数据进行transform
        return df

    # 2. 针对同类特征群（比如消费，浏览记录等）横向扩展，计算一些统计量作为特征
    @staticmethod
    def get_feats_syndrome(df, syndrome_num=0, feat_cols=None):  # 有多个特征群的时候会用到syndrome_num编号
        df = df.copy()
        _df = df[feat_cols]

        buildin_funcs = ['count', 'min', 'mean', 'median', 'max', 'sum', 'std', 'var', 'sem', 'skew']
        for f in buildin_funcs:
            df['horz' + str(syndrome_num) + '_' + f] = _df.__getattr__(f)(axis=1)
        if len(feat_cols) > 3:  # 从公式来看峰度n要大于3
            df['horz' + str(syndrome_num) + '_' + 'kurt'] = _df.kurt(axis=1)
        df['horz' + str(syndrome_num) + '_' + 'q1'] = _df.quantile(0.25, axis=1)
        df['horz' + str(syndrome_num) + '_' + 'q3'] = _df.quantile(0.75, axis=1)
        df['horz' + str(syndrome_num) + '_' + 'q3_q1'] = df['horz' + str(syndrome_num) + '_' + 'q3'] - df[
            'horz' + str(syndrome_num) + '_' + 'q1']
        df['horz' + str(syndrome_num) + '_' + 'max_min'] = df['horz' + str(syndrome_num) + '_' + 'max'] - df[
            'horz' + str(syndrome_num) + '_' + 'min']
        df['horz' + str(syndrome_num) + '_' + 'COV'] = df['horz' + str(syndrome_num) + '_' + 'std'] / (
                df['horz' + str(syndrome_num) + '_' + 'mean'] + 10 ** -8)  # 变异系数C.O.V
        df['horz' + str(syndrome_num) + '_' + 'COV_reciprocal'] = df['horz' + str(syndrome_num) + '_' + 'mean'] / (
                df['horz' + str(syndrome_num) + '_' + 'std'] + 10 ** -8)
        return df

    # 3. 多项式特征Polynomial
    @staticmethod
    def get_feats_poly(data, feats=None, degree=2, return_df=True, return_poly=False):
        """PolynomialFeatures
        :param data: np.array or pd.DataFrame, dataframe should be reindexed from 0 TO n
        :param feats: columns names
        :param degree:
        :return: df
        """
        df = data.copy()
        poly = PolynomialFeatures(degree, include_bias=False)
        df = poly.fit_transform(df[feats])

        if return_df:
            df = pd.DataFrame(df, columns=poly.get_feature_names_out(feats))
            df.drop(feats, axis=1, inplace=True)
            data = pd.concat([data, df], axis=1)
        if return_poly:
            return poly, data
        return data

    # 4. 组合特征
    @staticmethod
    def get_numeric_feats_comb(df, operations=['add', 'sub', 'mul', 'div'], feature_for_polyAndcomb=None):
        from itertools import combinations
        df = df.copy()
        # 加减乘除
        add = lambda a, b: a + b
        sub = lambda a, b: a - b
        mul = lambda a, b: a * b
        div = lambda a, b: a / (b + 10 ** -8)
        for oper in tqdm(operations):
            for f1, f2 in combinations(feature_for_polyAndcomb, 2):
                col_name = f1 + oper + f2
                df[col_name] = eval(oper)(df[f1], df[f2])
        return df

    # 5. Grougby类别型特征（比如时间，性别等）计算其他数值型特征的均值，方差等等（交叉特征，特征表征）
    @staticmethod
    def create_fts_from_catgroup(data, feats=None, by='ts', standardize=False):
        data = data.copy()
        q1_func = lambda x: x.quantile(0.25)
        q3_func = lambda x: x.quantile(0.75)
        get_max_min = lambda x: np.max(x) - np.min(x)
        get_q3_q1 = lambda x: x.quantile(0.75) - x.quantile(0.25)
        get_cov = lambda x: np.var(x) * 1.0 / (np.mean(x) + 10 ** -8)
        get_cov_reciprocal = lambda x: np.mean(x) * 1.0 / (np.var(x) + 10 ** -8)
        func_list = [('count', 'count'),
                     ('mean', 'mean'),
                     ('std', 'std'),
                     ('var', 'var'),
                     ('min', 'min'),
                     ('max', 'max'),
                     ('median', 'median'),
                     ('q1_func', q1_func),
                     ('q3_func', q3_func),
                     ('q3_q1', get_q3_q1),
                     ('max_min', get_max_min),
                     ('get_cov', get_cov),
                     ('get_cov_reciprocal', get_cov_reciprocal)]
        if feats is not None:  # 对时间特征可用数值特征平均编码
            print("%s_encoding ..." % by)
            new_feats = []
            gr = data.groupby(by)
            for ft in tqdm(feats):
                for func_name, func in func_list:
                    new_feat = '{}_{}_encoding_'.format(by, func_name) + ft
                    data[new_feat] = gr[ft].transform(func)
                    new_feats.append(new_feat)
        if standardize:
            sdsr = StandardScaler()
            data[new_feats] = sdsr.fit_transform(data[new_feats])
            return data, sdsr  # sdsr不一定用得到如果数据是训练和测试拼接完后放进来的
        return data


# ----------------------------
# 特征选择函数
# ----------------------------
def train_model(X, y, X_test, cv, cv_seed, lgb_seed):
    params = {
        'boosting': 'gbdt',  # 'rf', 'dart', 'goss'
        'application': 'binary',
        # 'application': 'multiclass', 'num_class': 3, # multiclass=softmax, multiclassova=ova  One-vs-All
        'learning_rate': 0.01,
        'max_depth': -1,
        'num_leaves': 2 ** 7 - 1,
        'max_bin': 255,
        'metric_freq': 10,
        'min_split_gain': 0,
        'min_child_weight': 1,
        'bagging_fraction': 0.8,
        'feature_fraction': 0.8,
        'bagging_freq': 5,
        'min_data_in_leaf': 1000,
        'min_sum_hessian_in_leaf': 5.0,
        'lambda_l1': 0,
        'lambda_l2': 1,
        'scale_pos_weight': 1,
        'metric': 'auc',
        'verbosity': -1,
        'num_threads': 32,
    }

    clf = LGBMClassifier(**params)

    oof_preds = np.zeros(X.shape[0])
    sub_preds = np.zeros((X_test.shape[0], cv))
    for n_fold, (train_idx, valid_idx) in enumerate(
            StratifiedKFold(n_splits=cv, shuffle=True, random_state=cv_seed).split(X, y), 1):
        X_train, y_train = X[train_idx], y[train_idx]
        X_valid, y_valid = X[valid_idx], y[valid_idx]

        clf.fit(X_train, y_train,
                eval_set=[(X_train, y_train), (X_valid, y_valid)],
                eval_metric='auc',
                # early_stopping_rounds=300,
                # verbose=0
                )
        oof_preds[valid_idx] = clf.predict_proba(X_valid)[:, 1]
        sub_preds[:, n_fold - 1] = clf.predict_proba(X_test)[:, 1]
    sub_preds = sub_preds.mean(1)
    print('OOF AUC:', roc_auc_score(y, oof_preds))
    return clf, sub_preds


# _horizongtalFeature
import pandas as pd
from tqdm import tqdm
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import PolynomialFeatures
from sklearn.preprocessing import StandardScaler


def auto_feature_engineering(train, test,auto_import_features=None):
    """主函数"""
    # 1. 数据读取与预处理
    train, test = train.copy(), test.copy()
    print(train.shape)
    print(test.shape)
    num_train_ = train.shape[0]

    train['is_train'] = 1
    test['is_train'] = 0

    cate_feat = ['month', 'region', 't3', 'code', 'source', 'grades', 'version']
    # num_feat = list(set(train.columns) - set(cate_feat + ['id', 'label', 'is_train']))
    num_feat = [item for item in train.columns if item not in cate_feat + ['id', 'label', 'is_train']]
    train.condition.fillna(0, inplace=True)
    test.condition.fillna(0, inplace=True)

    y_true = train.label

    del train['label']
    data = pd.concat([train, test])

    # 做一些通用的处理
    data['t3_'] = data.t3.map(lambda x: x[-1])
    data['source_car'] = data.source.map(lambda x: x.split('|')[0])
    data['source_eng'] = data.source.map(lambda x: x.split('|')[-1])

    data['t3_int'] = data.t3.map(lambda x: float(x[:-1]))
    data['source_int_1'] = data.source.map(lambda x: int(x.split('|')[0].replace('CAR_', '')))
    data['source_int_2'] = data.source.map(lambda x: int(x.split('|')[1].replace('ENG_', '')))

    cate_feat = cate_feat + ['t3_', 'source_car', 'source_eng']

    print('cate_feat', cate_feat)

    hf = HorizongtalFeature()
    # cate feats
    for i in tqdm(cate_feat):
        data = hf.get_feats_vcrank(data, feat=i)
    # num feats
    data = hf.get_feats_syndrome(data, feat_cols=num_feat)
    # data = hf.get_feats_poly(data, feats=num_feat)
    data = hf.get_numeric_feats_comb(data, feature_for_polyAndcomb=num_feat)
    for i in tqdm(cate_feat):
        data = hf.create_fts_from_catgroup(data, feats=num_feat, by=i)
    for i in cate_feat + ['id']:
        del data[i]

    train_2 = data[data.is_train == 1]
    del train_2['is_train']
    test_2 = data[data.is_train == 0]
    del test_2['is_train']
    # 孤立森林
    from sklearn.ensemble import IsolationForest
    isof = IsolationForest(n_jobs=40)
    isof.fit(data)
    data['isof'] = isof.predict(data)
    # kmeans
    km = KMeans(n_clusters=10, random_state=19)
    tmp = km.fit_transform(data)
    data['km_feature'] = tmp.argmax(axis=1)
    # train_2 = data.iloc[:21328]
    # test_2 = data.iloc[21328:]
    train_2 = data.iloc[:num_train_]
    test_2 = data.iloc[num_train_:]
    if auto_import_features is None:
        model, res = train_model(train_2.values, y_true.values, test_2.values, 5, 19, 19)
        indices = [index for index, value in enumerate(model.feature_importances_) if value > 4]
        important_feats = [train_2.columns[i] for i in indices]

    else:
        important_feats = auto_import_features
    print(important_feats)

    # 返回处理后的数据和特征
    return train_2, test_2, important_feats


# ----------------------------手动特征--

# ----------------------------
# 特征转换函数
# ----------------------------
def parse_t3(v):
    """将 '5.34P' / '4.72E' / 纯数值 等解析为 (float, unit)"""
    if pd.isna(v):
        return np.nan, "NONE"
    s = str(v).strip()
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]+)?$", s)
    if m:
        num = float(m.group(1))
        unit = (m.group(2) or "NONE").upper()
        return num, unit
    try:
        return float(s), "NONE"
    except:
        return np.nan, "NONE"


def month_to_idx(v):
    """将 'M0'..'M12' 转成数字；非此格式则试图转int，否则返回-1"""
    if pd.isna(v): return -1
    s = str(v).strip().upper()
    m = re.match(r"^M(\d+)$", s)
    if m:
        return int(m.group(1))
    try:
        return int(float(s))
    except:
        return -1


def float_to_str(v):
    """将浮点数转换为字符串表示"""
    if v == np.inf:
        return 'inf'
    elif v == -np.inf:
        return '-inf'
    elif np.isnan(v):
        return 'nan'
    else:
        return f"{v:.2f}"


def tulple_float_to_str(v):
    """处理 pandas Interval 对象"""
    if hasattr(v, 'left') and hasattr(v, 'right'):
        v_1, v_2 = v.left, v.right
    else:
        v_1, v_2 = v

    v_1 = float_to_str(v_1)
    v_2 = float_to_str(v_2)

    return f"{v_1}_{v_2}"


def process_source_feature(df):
    """处理source特征"""
    source_parts = df['source'].str.split('|', expand=True)
    df['CAR_type'] = source_parts[0].str.replace('CAR_', '').astype(int)
    df['ENG_type'] = source_parts[1].str.replace('ENG_', '').astype(int)
    return df


def process_grades_feature(df):
    # grades 为 s/ss/sss 时做有序映射（保留原列，新增一个）
    order_map = {'s': 1, 'ss': 2, 'sss': 3}
    df['grades_ord'] = df['grades'].map(order_map).fillna(0).astype(int)


# ----------------------------
# 数值特征处理函数
# ----------------------------
def log1p_cols(df, cols):
    """对指定列应用 log1p 转换"""
    for c in cols:
        if c in df.columns:
            df[c] = np.log1p(df[c].astype(float))
    return df


def add_row_stats(df, xcols):
    """添加行级统计特征"""
    X = df[xcols].astype(float)
    df["x_mean"] = X.mean(axis=1)
    df["x_std"] = X.std(axis=1).fillna(0.0)
    df["x_max"] = X.max(axis=1)
    df["x_min"] = X.min(axis=1)
    df["x_abs_sum"] = np.abs(X).sum(axis=1)
    df["x_pos_cnt"] = (X > 0).sum(axis=1)
    df["x_neg_cnt"] = (X < 0).sum(axis=1)
    df["x_energy"] = (X ** 2).sum(axis=1)
    return df


def add_binary_sums(df, bin_cols):
    """添加二进制列的和"""
    cols = [c for c in bin_cols if c in df.columns]
    if cols:
        df["flag_sum"] = df[cols].sum(axis=1)
    return df


def add_days_features(df):
    df['log_days'] = np.log1p(df['days'])
    df['norm_days'] = 11 - df['days']
    df['region_norm_days'] = df.groupby('region')['norm_days'].transform("mean")


# zzq
def add_agg_features(df):
    code_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
    df['code'] = df.groupby('source')['code'].transform(lambda x: x.mode()[0])
    df['code_ord'] = df['code'].map(code_map).fillna(0).astype(int)
    order_map = {'s': 1, 'ss': 2, 'sss': 3}
    df['grades_ord'] = df['grades'].map(order_map).fillna(0).astype(int)
    df['t3_numeric_agg'] = df.groupby('source')['t3_numeric'].transform('mean')
    df['grades_agg'] = df.groupby('source')['grades'].transform(lambda x: x.mode()[0])
    df['livability_agg'] = df.groupby('region')['livability'].transform('mean')
    df['cc_agg'] = df.groupby('source')['cc'].transform('mean')
    df['V_agg'] = df.groupby('source')['V'].transform('mean')
    df['max_g_agg'] = df.groupby('source')['max_g'].transform('mean')
    df['car_mul'] = df['t3_numeric_agg'] * df['cc_agg'] * df['V_agg'] * df['max_g_agg'] * df['grades_ord'] * df[
        'code_ord']
    df['all_age'] = df['condition'] * df['age_range'] * df['days']
    df['car_env'] = df['car_mul'] * df['all_age'] * df['livability_agg']
    df['trcw'] = df['t1'] * df['t2'] * df['r1'] * df['r2'] * df['c1'] * df['c2'] * df['w1'] * df['w2']
    df['all_env'] = df['car_mul'] * df['all_age'] * df['car_env']
    # 时间
    df['days_age'] = 28 + (df['age_range']) * 5 - df['days'] / 10000
    df['condition_age'] = 28 + (df['age_range']) * 5 - df['condition'] * 4000 / 365
    # 离散特征
    df['t'] = df['t1'] * df['t2']
    df['r'] = df['r1'] * df['r2']
    df['c'] = df['c1'] * df['c2']
    df['w'] = df['w1'] * df['w2']
    # month处理
    df['month_agg'] = df.groupby('source')['month'].transform(lambda x: x.mode()[0])
    df['month_agg'] = df['month_agg'].apply(month_to_idx)
    # chatgpt
    df['days_condition'] = df['days'] / (df['condition'] + 1e-5)
    df['condition'] = df['condition'] * df['grades']
    df['age_code'] = df['age_range'] * df['code_ord']

    return df


# ----------------------------
# 分箱函数
# ----------------------------
def numeric_binning(train, test, num_feat=''):
    """数值型分箱"""
    from sklearn.tree import DecisionTreeClassifier

    # 预定义的叶子节点数量
    __d = {'days': 6, 'cc': 7, 'V': 9, 'x19': 7, 'x20': 8, 'max_g': 15}
    if num_feat not in __d:
        return train, test

    dt_binner = DecisionTreeClassifier(max_leaf_nodes=__d.get(num_feat), random_state=__d.get(num_feat))
    if 'label' in test.columns:
        train_test_cat = pd.concat([train[[num_feat] + ['label']], test[[num_feat] + ['label']]], axis=0)
        dt_binner.fit(train_test_cat[num_feat].values.reshape(-1, 1), train_test_cat['label'].values)
    else:
        dt_binner.fit(train[num_feat].values.reshape(-1, 1), train['label'].values)

    thresholds = dt_binner.tree_.threshold
    bin_edges = sorted(list(set(thresholds[thresholds != -2])))
    bin_edges = [-np.inf] + bin_edges + [np.inf]

    train[f'{num_feat}_bin'] = pd.cut(train[num_feat], bins=bin_edges, include_lowest=True, right=False).apply(
        tulple_float_to_str)
    test[f'{num_feat}_bin'] = pd.cut(test[num_feat], bins=bin_edges, include_lowest=True, right=False).apply(
        tulple_float_to_str)

    del dt_binner
    gc.collect()
    return train, test


# ----------------------------
# 类别特征处理函数
# ----------------------------
def rare_merge(series, thr=RARE_THR):
    """合并稀有类别"""
    vc = series.value_counts()
    rare = vc[vc < thr].index
    return series.where(~series.isin(rare), "__RARE__")


def kfold_target_encoding(train_df, test_df, col, y, n_splits=5, smooth=50, seed=42):
    """KFold Target Encoding（防泄露版）"""
    print('TE encoding', col)
    assert col in train_df.columns, f"[TE] 列 {col} 不在 train_df 中"
    global_mean = y.mean()

    train_te = np.zeros(len(train_df), dtype=np.float64)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    for tr_idx, val_idx in skf.split(train_df, y):
        tr_col = train_df[col].iloc[tr_idx]
        val_col = train_df[col].iloc[val_idx]
        y_tr = y.iloc[tr_idx]

        stats = y_tr.groupby(tr_col).agg(["sum", "count"])
        stats["te"] = (stats["sum"] + global_mean * smooth) / (stats["count"] + smooth)

        train_te[val_idx] = val_col.map(stats["te"]).fillna(global_mean).values

    # test 使用全量统计
    full = y.groupby(train_df[col]).agg(["sum", "count"])
    full["te"] = (full["sum"] + global_mean * smooth) / (full["count"] + smooth)
    test_te = test_df[col].map(full["te"]).fillna(global_mean).values

    return train_te, test_te


def add_frequency_feature(df_train, df_test, column_name):
    """添加频率特征"""
    if column_name not in df_train.columns:
        print(f"警告: 列 '{column_name}' 不存在于数据集中")
        return df_train, df_test

    X_T_concat = pd.concat([df_train, df_test], axis=0)
    column_name_freq = X_T_concat[column_name].value_counts(normalize=True).rename('{column_name}_freq')

    df_train[f'{column_name}_freq'] = df_train[column_name].map(column_name_freq)
    df_test[f'{column_name}_freq'] = df_test[column_name].map(column_name_freq)

    print(f"已添加 '{column_name}_freq' 特征")
    return df_train, df_test


# ----------------------------
# 复合特征生成函数
# ----------------------------

def process_region_livability(df):
    """处理region-livability特征"""
    df['ratio'] = df.groupby('region')['livability'].transform(
        lambda x: x.map(x.value_counts(normalize=True))
    )
    df['livability_new'] = (df['ratio'] < 0.03).astype(int)
    return df


def add_numeric_interactions(df):
    """添加数值交互特征"""
    if 'age_range' in df.columns and 'cc' in df.columns:
        df['age_cc_inter'] = df['age_range'] * df['cc']

    if 'age_range' in df.columns and 'CAR_type' in df.columns:
        df['age_car_inter'] = df['age_range'] * df['CAR_type']

    if 'livability' in df.columns and 'cc' in df.columns:
        df['livability_cc_inter'] = df['livability'] * df['cc']

    if 'x1' in df.columns and 'x20' in df.columns:
        df['x1_x20_inter'] = np.log1p(df['x1'].astype(float)) * np.log1p(df['x20'].astype(float))

    if 'cc' in df.columns:
        df['cc_squared'] = df['cc'] ** 2

    if set(['cc', 'V']).issubset(df.columns):
        df['cc_x_V'] = df['cc'] * df['V']
    if set(['condition', 'age_range']).issubset(df.columns):
        df['cond_x_age'] = df['condition'] * df['age_range']

    if "t3_numeric" in df.columns:
        eps = 1e-6
        if "cc" in df.columns:
            df["t3_per_cc"] = df["t3_numeric"] / (df["cc"] + eps)
        if "V" in df.columns:
            df["t3_per_V"] = df["t3_numeric"] / (df["V"] + eps)

    return df


def add_categorical_cross(df):
    """添加类别交叉特征"""

    df['region_age_cat'] = df['region'].astype(str) + '_' + df['age_range'].astype(str)

    df['region_month'] = df['region'].astype(str) + '|' + df['month_idx'].astype(str)

    df['code_grades'] = df['code'].astype(str) + '|' + df['grades'].astype(str)

    df['region_new_type_x19'] = df['region'].astype(str) + '|' + df['new_type_x19'].astype(str)

    df['region_new_type_livability'] = df['region'].astype(str) + '|' + df['new_type_livability'].astype(str)

    df['region_age_range'] = df['region'].astype(str) + '|' + df['age_range'].astype(str)

    return df


def add_condition_features(df):
    df['condition'].fillna(0, inplace=True)
    """添加风险相关特征"""
    if 'condition' in df.columns and 'log_days' in df.columns:
        df['condition_abs_age_ratio'] = df['condition'].abs() / (df['log_days'] / 365.25 + 1e-5)  # 很奇怪
        print(df['condition_abs_age_ratio'].head(5))

    if 'region' in df.columns and 'condition_abs_age_ratio' in df.columns:
        df['region_days_log_condition_abs'] = df['condition_abs_age_ratio'] - df.groupby('region')[
            'condition_abs_age_ratio'].transform("mean")
    if 'cc' in df.columns and 'V' in df.columns and 'condition' in df.columns:
        df['cc_x_V_condition_ratio'] = df['cc'] * df['V'] / (df['condition'] + 1e-6)

    return df


def entropy(s):
    """计算熵"""
    p = s.value_counts(normalize=True)
    return -np.sum(p * np.log(p + 1e-10))


def add_entropy_features(X, T):
    """添加熵特征"""
    X_T_concat = pd.concat([X[['region', 'livability', 'new_type_x19']].copy(),
                            T[['region', 'livability', 'new_type_x19']].copy()], axis=0)

    region_entropy = X_T_concat.groupby('region')['livability'].apply(entropy).rename('region_entropy')
    region_entropy_2 = X_T_concat.groupby('region')['new_type_x19'].apply(entropy).rename('region_entropy_2')

    for df in [X, T]:
        df['region_r1_mean'] = df.groupby('region')['r1'].transform("mean")
        df['region_t1_mean'] = df.groupby('region')['t1'].transform("mean")
        df['region_entropy'] = df['region'].map(region_entropy)
        df['region_entropy_2'] = df['region'].map(region_entropy_2)
        df['region_entropy'].fillna(region_entropy.mean(), inplace=True)
        df['region_entropy_2'].fillna(region_entropy_2.mean(), inplace=True)

    return X, T


# ----------------------------
# 特征工程主函数
# ----------------------------
def feature_engineering(X, T, y):
    """执行完整的特征工程流程"""

    # month → month_idx
    for df in [X, T]:
        if "month" in df.columns:
            df["month_idx"] = df["month"].apply(month_to_idx)

    # 分箱处理
    num_feats2bin = []
    for i in ['days', 'cc', 'V', 'x19', 'x20', 'max_g']:
        X, T = numeric_binning(X, T, i)
        num_feats2bin.append(f'{i}_bin')

    # 添加变换新特征
    for df in [X, T]:
        add_days_features(df)
        process_grades_feature(df)
        process_region_livability(df)
        if "t3" in df.columns:
            out = df["t3"].apply(parse_t3)
            df["t3_numeric"] = out.apply(lambda x: x[0])
            df["t3_unit"] = out.apply(lambda x: x[1])
    # 数值转字符串
    float_to_str_cols = ['x19', 'livability']
    for df in [X, T]:
        for c in float_to_str_cols:
            if c in df.columns:
                df[f'new_type_{c}'] = df[c].apply(float_to_str)
    # 处理source特征
    X = process_source_feature(X)
    T = process_source_feature(T)

    # 添加数值交互特征
    X = add_numeric_interactions(X)
    T = add_numeric_interactions(T)

    # 添加类别交叉特征
    X = add_categorical_cross(X)
    T = add_categorical_cross(T)

    # 添加condition特征
    X = add_condition_features(X)
    T = add_condition_features(T)

    # 添加熵特征
    X, T = add_entropy_features(X, T)

    # 添加频率特征
    columns_for_freq = ['region', 'region_grades', 'region_month', 'region_age_range',
                        'region_age_range_grades', 'region_new_type_x19', 'region_new_type_x20',
                        'region_new_type_livability']

    for col in columns_for_freq:
        if col in X.columns:
            X, T = add_frequency_feature(X, T, col)

    # 类别列定义
    cat_cols_raw = (["month", "region", "code", "age_range", "source", "grades", "version", "t3_unit"]
                    + ['grades_ord', 'region_month', 'code_grades']
                    + ['region_age_range']
                    + ['region_age_cat']
                    + ['new_type_x19']
                    + ['region_new_type_x19']
                    + num_feats2bin
                    + ['new_type_livability', 'region_new_type_livability'])

    cat_cols_raw = [c for c in cat_cols_raw if c in X.columns]

    # 获取数值型和对象型特征
    numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
    print('manual cat_cols_raw', len(cat_cols_raw), cat_cols_raw)
    print('X number cols', len(numeric_features), numeric_features)
    print('X cat cols', len(categorical_features), categorical_features)
    print('manual cat cols not in X.columns', [c for c in categorical_features if c not in cat_cols_raw])
    # 稀有合并 + LabelEncoding
    le_map = {}
    for c in cat_cols_raw:
        X[c] = rare_merge(X[c].astype(str), RARE_THR)
        T[c] = T[c].astype(str)

        known = set(np.concatenate([X[c].unique(), T[c].unique()]))
        T[c] = T[c].where(T[c].isin(known), "__UNK__")

        le = LabelEncoder()
        all_vals = list(known | {"__UNK__"})
        le.fit(all_vals)
        X[c] = le.transform(X[c])
        T[c] = le.transform(T[c])
        le_map[c] = le

    # 目标编码
    te_cols = [c for c in ["region", "code", "grades", "t3_unit", "new_type_x19"] + num_feats2bin if c in X.columns]
    for c in te_cols:
        tr_te, te_te = kfold_target_encoding(pd.DataFrame({c: X[c]}),
                                             pd.DataFrame({c: T[c]}),
                                             c, y, n_splits=N_SPLITS, smooth=TE_SMOOTH, seed=SEED)
        X[f"{c}_te"] = tr_te
        T[f"{c}_te"] = te_te

    # 缺失值处理
    X = X.replace([np.inf, -np.inf], np.nan).fillna(-999)
    T = T.replace([np.inf, -np.inf], np.nan).fillna(-999)
    # 聚合特征
    all_data = pd.concat([X, T], axis=0)
    all_data = add_agg_features(all_data)
    X = all_data[:len(X)]
    T = all_data[len(X):].drop(columns=['label'])
    # X = add_agg_features(X)
    # T = add_agg_features(T) # zzq
    exclude_cols = ["id", "label", "t1", "t2", "t3",
                    "x1", "x4", "x6", "x7", "x9", "x11", "x12", "x13", "x14",
                    "x15", "x17", "x18", "x19", "x20",
                    "ratio",
                    "days"  # old days去除,保留log_days
                    ]
    # 特征列最终确定
    features = sorted([c for c in X.columns if
                       c not in exclude_cols])

    # 类别列（给LightGBM使用）
    cat_cols = [c for c in cat_cols_raw if c in features]

    return X, T, features, cat_cols


def train_models(X, y, features, cat_cols, model_dir):
    """训练多个模型并进行预测"""
    # 不均衡权重
    n_pos = y.sum()
    n_neg = len(y) - n_pos
    scale_pos_weight = max((n_neg / max(n_pos, 1)), 1.0)
    print(f"[Info] Pos={int(n_pos)}, Neg={int(n_neg)}, scale_pos_weight={scale_pos_weight:.3f}")

    # 5折 OOF 训练
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

    oof_lgb = np.zeros(len(X))
    oof_xgb = np.zeros(len(X)) if HAS_XGB else None
    oof_ctb = np.zeros(len(X)) if HAS_CTB else None
    oof_rf = np.zeros(len(X)) if HAS_RF else None

    # pred_lgb = np.zeros(len(T))
    # pred_xgb = np.zeros(len(T)) if HAS_XGB else None
    # pred_ctb = np.zeros(len(T)) if HAS_CTB else None
    # pred_rf = np.zeros(len(T)) if HAS_RF else None

    fi_list = []
    # dte_xgb = xgb.DMatrix(T[features], feature_names=features) if HAS_XGB else None

    # 存储所有模型的信息
    models_info = {
        'lgb': [], 'xgb': [], 'ctb': [], 'rf': [],
        'features': features, 'cat_cols': cat_cols
    }

    candidates_lgb = []
    candidates_xgb = []
    candidates_ctb = []
    candidates_rf = []

    for fold, (tr_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_tr, X_va = X.iloc[tr_idx][features], X.iloc[val_idx][features]
        y_tr, y_va = y.iloc[tr_idx], y.iloc[val_idx]
        print(f'fold x {fold}', len(X_tr), len(X_va), len(y_tr), len(y_va))

        # LightGBM
        lgb_params = dict(
            objective="binary",
            metric="auc",
            boosting_type="gbdt",
            learning_rate=0.01,
            num_leaves=64,
            max_depth=-1,
            min_data_in_leaf=50,
            feature_fraction=0.8,
            bagging_fraction=0.8,
            bagging_freq=1,
            lambda_l1=0.1,
            lambda_l2=2.0,
            verbose=-1,
            seed=SEED + fold,
            n_jobs=-1,
        )

        lgb_train = lgb.Dataset(X_tr, label=y_tr, categorical_feature=cat_cols or None, free_raw_data=False)
        lgb_valid = lgb.Dataset(X_va, label=y_va, categorical_feature=cat_cols or None, reference=lgb_train,
                                free_raw_data=False)

        lgb_model = lgb.train(
            lgb_params, lgb_train,
            num_boost_round=LGB_ROUNDS,
            valid_sets=[lgb_train, lgb_valid],
            callbacks=[lgb.early_stopping(stopping_rounds=MAX_EARLY_STOP, verbose=verbose)],
        )

        oof_lgb[val_idx] = lgb_model.predict(X_va, num_iteration=lgb_model.best_iteration)
        fi = pd.DataFrame({
            "feature": features,
            "importance": lgb_model.feature_importance(importance_type="gain"),
            "fold": fold
        })
        fi_list.append(fi)
        auc_l = roc_auc_score(y_va, oof_lgb[val_idx])
        candidates_lgb.append(("LGB", auc_l, fold, lgb_model))
        # 保存LGB模型
        lgb_model_path = os.path.join(model_dir, f'lgb_fold{fold}.txt')
        lgb_model.save_model(lgb_model_path)
        models_info['lgb'].append({
            'model_path': lgb_model_path,
            'auc': auc_l,
            'fold': fold
        })
        print('lgb_model_path', lgb_model_path)
        # XGBoost
        if HAS_XGB:
            xgb_params = dict(
                objective="binary:logistic",
                eval_metric="auc",
                tree_method="hist",
                learning_rate=0.008,
                max_depth=3,
                subsample=0.8,
                colsample_bytree=0.9,
                reg_alpha=0.1,
                reg_lambda=0.8,
                random_state=SEED + fold,
                nthread=-1,
            )

            dtr = xgb.DMatrix(X_tr, label=y_tr, feature_names=features)
            dva = xgb.DMatrix(X_va, label=y_va, feature_names=features)

            xgb_model = xgb.train(
                xgb_params, dtr, num_boost_round=XGB_ROUNDS,
                evals=[(dtr, "train"), (dva, "valid")],
                early_stopping_rounds=MAX_EARLY_STOP,
                verbose_eval=verbose
            )

            oof_xgb[val_idx] = xgb_model.predict(dva)
            auc_x = roc_auc_score(y_va, oof_xgb[val_idx])
            candidates_xgb.append(("XGB", auc_x, fold, xgb_model))
            # 保存XGB模型
            xgb_model_path = os.path.join(model_dir, f'xgb_fold{fold}.model')
            xgb_model.save_model(xgb_model_path)
            models_info['xgb'].append({
                'model_path': xgb_model_path,
                'auc': auc_x,
                'fold': fold
            })
            print('xgb_model_path', xgb_model_path)

        # CatBoost
        if HAS_CTB:
            cat_idx = [features.index(c) for c in cat_cols if c in features]
            ctb_model = CatBoostClassifier(
                loss_function="Logloss",
                eval_metric="AUC",
                learning_rate=0.03,
                depth=7,
                l2_leaf_reg=6.0,
                random_seed=SEED + fold,
                iterations=CTB_ROUNDS,
                od_type="Iter",
                od_wait=MAX_EARLY_STOP,
                verbose=verbose,
            )

            ctb_model.fit(
                X_tr, y_tr,
                eval_set=(X_va, y_va),
                cat_features=cat_idx,
                use_best_model=True
            )

            oof_ctb[val_idx] = ctb_model.predict_proba(X_va)[:, 1]
            auc_c = roc_auc_score(y_va, oof_ctb[val_idx])
            candidates_ctb.append(("CTB", auc_c, fold, ctb_model))
            # 保存CatBoost模型
            ctb_model_path = os.path.join(model_dir, f'ctb_fold{fold}.cbm')
            ctb_model.save_model(ctb_model_path)
            models_info['ctb'].append({
                'model_path': ctb_model_path,
                'auc': auc_c,
                'fold': fold
            })
            print('ctb_model_path', ctb_model_path)

        # Random Forest
        if HAS_RF:
            rf_model = RandomForestClassifier(
                n_estimators=500,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                max_features="sqrt",
                class_weight="balanced",
                oob_score=True,
                n_jobs=-1,
                random_state=SEED + fold,
                verbose=verbose_int
            )

            rf_model.fit(X_tr, y_tr)
            oof_rf[val_idx] = rf_model.predict_proba(X_va)[:, 1]
            auc_rf = roc_auc_score(y_va, oof_rf[val_idx])
            candidates_rf.append(("RF", auc_rf, fold, rf_model))
            # 保存Random Forest模型
            rf_model_path = os.path.join(model_dir, f'rf_fold{fold}.pkl')
            joblib.dump(rf_model, rf_model_path, compress=3)
            models_info['rf'].append({
                'model_path': rf_model_path,
                'auc': auc_rf,
                'fold': fold
            })
            print('rf_model_path', rf_model_path)

        msg = f"[Fold {fold}] LGB AUC={auc_l:.5f}"
        if HAS_XGB:
            msg += f", XGB AUC={auc_x:.5f}"
        if HAS_CTB:
            msg += f", CTB AUC={auc_c:.5f}"
        if HAS_RF:
            msg += f", RF AUC={auc_rf:.5f}"
        print(msg)

    # # 选择最佳模型进行预测
    # candidates_sorted_lgb = sorted(candidates_lgb, key=lambda x: x[1], reverse=True)
    # topk_lgb = candidates_sorted_lgb[:min(TOP_K, len(candidates_sorted_lgb))]
    #
    # lgb_preds = []
    # for family, auc, f, model in topk_lgb:
    #     lgb_preds.append(model.predict(T[features], num_iteration=model.best_iteration))
    # pred_lgb = np.mean(np.vstack(lgb_preds), axis=0)
    #
    # if HAS_XGB:
    #     candidates_sorted_xgb = sorted(candidates_xgb, key=lambda x: x[1], reverse=True)
    #     topk_xgb = candidates_sorted_xgb[:min(TOP_K, len(candidates_sorted_xgb))]
    #
    #     xgb_preds = []
    #     for family, auc, f, model in topk_xgb:
    #         xgb_preds.append(model.predict(dte_xgb))
    #     pred_xgb = np.mean(np.vstack(xgb_preds), axis=0)
    #
    # if HAS_CTB:
    #     candidates_sorted_ctb = sorted(candidates_ctb, key=lambda x: x[1], reverse=True)
    #     topk_ctb = candidates_sorted_ctb[:min(TOP_K, len(candidates_sorted_ctb))]
    #
    #     ctb_preds = []
    #     for family, auc, f, model in topk_ctb:
    #         ctb_preds.append(model.predict_proba(T[features])[:, 1])
    #     pred_ctb = np.mean(np.vstack(ctb_preds), axis=0)
    #
    # if HAS_RF:
    #     candidates_sorted_rf = sorted(candidates_rf, key=lambda x: x[1], reverse=True)
    #     topk_rf = candidates_sorted_rf[:min(TOP_K, len(candidates_sorted_rf))]
    #
    #     rf_preds = []
    #     for family, auc, f, model in topk_rf:
    #         rf_preds.append(model.predict_proba(T[features])[:, 1])
    #     pred_rf = np.mean(np.vstack(rf_preds), axis=0)

    # OOF 评估
    def pr_auc(name, oof):
        if oof is None: return None
        auc = roc_auc_score(y, oof)
        print(f"[OOF] {name} AUC = {auc:.6f}")
        return auc

    auc_l = pr_auc("LGB", oof_lgb)
    auc_x = pr_auc("XGB", oof_xgb) if HAS_XGB else None
    auc_c = pr_auc("CTB", oof_ctb) if HAS_CTB else None
    auc_rf = pr_auc("RF", oof_rf) if HAS_RF else None

    # 保存特征重要度
    fi_all = pd.concat(fi_list, ignore_index=True)
    fi_all = fi_all.groupby("feature", as_index=False)["importance"].mean().sort_values("importance", ascending=False)
    topk = fi_all.head(50)
    # topk.to_csv("models/feature_importance_top50_0686_bin.csv", index=False)
    print("\n[Feature Importance - Top 20]")
    print(topk.head(4))

    # 保存模型信息
    models_info_path = os.path.join(model_dir, "models_info.pkl")
    with open(models_info_path, 'wb') as f:
        pickle.dump(models_info, f)

    print(f"所有模型已保存到目录: {model_dir}\n{models_info}")

    return oof_lgb, oof_xgb, oof_ctb, oof_rf, models_info


def predict_models(T, model_dir="models"):
    models_info_path = os.path.join(model_dir, "models_info.pkl")
    with open(models_info_path, 'rb') as rf:
        models_info = pickle.load(rf)
    top_k = TOP_K
    """加载模型并进行预测"""
    features = models_info['features']
    cat_cols = models_info['cat_cols']

    pred_lgb = np.zeros(len(T))
    pred_xgb = np.zeros(len(T)) if HAS_XGB and models_info['xgb'] else None
    pred_ctb = np.zeros(len(T)) if HAS_CTB and models_info['ctb'] else None
    pred_rf = np.zeros(len(T)) if HAS_RF and models_info['rf'] else None

    # LightGBM预测
    if models_info['lgb']:
        lgb_models = []
        lgb_aucs = []
        for model_info in models_info['lgb']:
            lgb_model = lgb.Booster(model_file=model_info['model_path'])
            lgb_models.append(lgb_model)
            lgb_aucs.append(model_info['auc'])

        # 选择topk模型
        sorted_indices = np.argsort(lgb_aucs)[::-1][:min(top_k, len(lgb_models))]
        top_lgb_models = [lgb_models[i] for i in sorted_indices]

        lgb_preds = []
        for model in top_lgb_models:
            lgb_preds.append(model.predict(T[features]))
        pred_lgb = np.mean(np.vstack(lgb_preds), axis=0)

    # XGBoost预测
    if HAS_XGB and models_info['xgb']:
        xgb_models = []
        xgb_aucs = []
        for model_info in models_info['xgb']:
            xgb_model = xgb.Booster()
            xgb_model.load_model(model_info['model_path'])
            xgb_models.append(xgb_model)
            xgb_aucs.append(model_info['auc'])

        sorted_indices = np.argsort(xgb_aucs)[::-1][:min(top_k, len(xgb_models))]
        top_xgb_models = [xgb_models[i] for i in sorted_indices]

        dte_xgb = xgb.DMatrix(T[features], feature_names=features)
        xgb_preds = []
        for model in top_xgb_models:
            xgb_preds.append(model.predict(dte_xgb))
        pred_xgb = np.mean(np.vstack(xgb_preds), axis=0)

    # CatBoost预测
    if HAS_CTB and models_info['ctb']:
        ctb_models = []
        ctb_aucs = []
        for model_info in models_info['ctb']:
            ctb_model = CatBoostClassifier()
            ctb_model.load_model(model_info['model_path'])
            ctb_models.append(ctb_model)
            ctb_aucs.append(model_info['auc'])

        sorted_indices = np.argsort(ctb_aucs)[::-1][:min(top_k, len(ctb_models))]
        top_ctb_models = [ctb_models[i] for i in sorted_indices]

        ctb_preds = []
        for model in top_ctb_models:
            ctb_preds.append(model.predict_proba(T[features])[:, 1])
        pred_ctb = np.mean(np.vstack(ctb_preds), axis=0)

    # Random Forest预测
    if HAS_RF and models_info['rf']:
        rf_models = []
        rf_aucs = []
        for model_info in models_info['rf']:
            rf_model = joblib.load(model_info['model_path'])
            rf_models.append(rf_model)
            rf_aucs.append(model_info['auc'])

        sorted_indices = np.argsort(rf_aucs)[::-1][:min(top_k, len(rf_models))]
        top_rf_models = [rf_models[i] for i in sorted_indices]

        rf_preds = []
        for model in top_rf_models:
            rf_preds.append(model.predict_proba(T[features])[:, 1])
        pred_rf = np.mean(np.vstack(rf_preds), axis=0)

    return pred_lgb, pred_xgb, pred_ctb, pred_rf



def ensemble_predictions_train(oof_list,y,model_dir):
    """集成多个模型的预测结果"""
    # 过滤掉None值
    meta_features = [oof for oof in oof_list if oof is not None]

    META = np.vstack(meta_features).T

    # Logistic 回归二层
    meta_lr = LogisticRegression(
        solver="liblinear",
        class_weight="balanced",
        C=1.0,
        random_state=SEED
    )

    meta_lr.fit(META, y)
    oof_meta = meta_lr.predict_proba(META)[:, 1]
    auc_meta = roc_auc_score(y, oof_meta)
    print(f"[OOF] META-LR AUC = {auc_meta:.6f}")
    # 保存元学习器
    meta_lr_path = os.path.join(model_dir, "meta_lr.pkl")
    joblib.dump(meta_lr, meta_lr_path)
    print(f"元学习器已保存到: {meta_lr_path}")


    # Rank Averaging
    def rank_avg(preds: np.ndarray) -> np.ndarray:
        R = []
        for i in range(preds.shape[0]):
            r = pd.Series(preds[i]).rank(method="average") / preds.shape[1]
            R.append(r.values)
        R = np.vstack(R)
        return R.mean(axis=0)

    oof_stack = np.vstack(meta_features)
    oof_rank = rank_avg(oof_stack)
    auc_rank = roc_auc_score(y, oof_rank)
    print(f"[OOF] Rank-Average AUC = {auc_rank:.6f}")

def ensemble_predictions_test(pred_list,model_dir):
    """集成多个模型的预测结果"""
    # 过滤掉None值
    test_meta = [pred for pred in pred_list if pred is not None]

    TEST_META = np.vstack(test_meta).T
    # 加载元学习器
    meta_lr_path = os.path.join(model_dir, "meta_lr.pkl")
    if os.path.exists(meta_lr_path):
        meta_lr = joblib.load(meta_lr_path)
        pred_meta = meta_lr.predict_proba(TEST_META)[:, 1]
    else:
        print(f"警告: 未找到元学习器文件 {meta_lr_path}")
        pred_meta = np.zeros(len(TEST_META))

    # Rank Averaging
    def rank_avg(preds: np.ndarray) -> np.ndarray:
        R = []
        for i in range(preds.shape[0]):
            r = pd.Series(preds[i]).rank(method="average") / preds.shape[1]
            R.append(r.values)
        R = np.vstack(R)
        return R.mean(axis=0)


    test_rank = rank_avg(np.vstack(test_meta))

    # 最终融合
    final_pred = 0.5 * pred_meta + 0.5 * test_rank

    return final_pred

# # ----------------------------
# # 主函数
# # ----------------------------
# def main():
#     """主函数"""
#     # 读取数据
#     train, test = load_data(TRAIN_PATH, TEST_PATH)
#
#     # 划分训练集和验证集
#     X_train, X_test, y_train = train, test, train["label"].copy()
#     test_ids = X_test["id"].copy()
#     ori_test_T = X_test.copy()
#     # 自动特征
#     if HAS_AUTO_ENGINEERING:
#         train_2, test_2, important_feats = auto_feature_engineering(X_train, X_test)
#
#     # 手动特征
#     X_processed, T_processed, features, cat_cols = feature_engineering(X_train, X_test, y_train)
#
#     ################addaddadd################
#     print(sorted(features))
#     if HAS_AUTO_ENGINEERING:
#         print(sorted(important_feats))
#         features = features + important_feats
#         X_processed = pd.concat([X_processed, train_2[important_feats]], axis=1)
#         T_processed = pd.concat([T_processed, test_2[important_feats].reset_index(drop=True)], axis=1)
#
#     # 模型训练与预测
#     oof_lgb, oof_xgb, oof_ctb, oof_rf, pred_lgb, pred_xgb, pred_ctb, pred_rf = train_models(
#         X_processed, y_train, T_processed, features, cat_cols
#     )
#
#     # 模型集成
#     oof_list = [oof_lgb, oof_xgb, oof_ctb, oof_rf]
#     pred_list = [pred_lgb, pred_xgb, pred_ctb, pred_rf]
#     final_pred = ensemble_predictions(oof_list, pred_list, y_train)
#
#     submission = pd.read_csv('data/submit_exampleB.csv')
#     submission['label'] = final_pred
#     print('sub data size',len(submission))
#     print(submission.head(10))
#     submission.to_csv(SUB_PATH, index=False)
#
#
# if __name__ == "__main__":
#     main()
