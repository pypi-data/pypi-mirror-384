#encoding:utf-8
import os.path

import pandas as pd
from sklearn.metrics import roc_auc_score


def check_auc(sub_path, label_path):
    # 检查文件是否存在
    if not os.path.exists(sub_path):
        print(f"警告: 预测文件不存在 {sub_path}")
        return
    if not os.path.exists(label_path):
        print(f"警告: 标签文件不存在 {label_path}")
        return

    try:
        sub_pred_set = pd.read_csv(sub_path)
        label_set = pd.read_csv(label_path)
        y_true = label_set['label']
        y_pred = sub_pred_set['label']
        auc_l = roc_auc_score(y_true, y_pred)
        print('from', sub_path, 'auc', auc_l)
    except Exception as e:
        print(f"计算AUC时出错: {e}")


if __name__ == '__main__':
    # 使用更灵活的路径处理
    base_dir = '../fake_init_data/初赛B榜数据集/test/'
    result_dir = '../fake_result/'

    label_path = os.path.join(base_dir, 'testB_label.csv')

    for sub_file in ['1_result.csv', '2_result.csv', '3_result.csv', 'result.csv']:
        sub_path = os.path.join(result_dir, sub_file)
        print(sub_file)
        check_auc(sub_path, label_path)
# 1_result.csv
# from ../fake_result/1_result.csv auc 0.6960865711394153
# 2_result.csv
# from ../fake_result/2_result.csv auc 0.6883708616058656
# 3_result.csv
# from ../fake_result/3_result.csv auc 0.6984852246724575
# result.csv
# from ../fake_result/result.csv auc 0.6967246666621931