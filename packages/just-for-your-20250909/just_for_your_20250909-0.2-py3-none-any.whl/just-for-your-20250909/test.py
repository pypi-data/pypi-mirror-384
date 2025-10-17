# encoding:utf-8
import argparse
import os.path

import pandas as pd


def main_1(train_dir, test_dir, result_dir, model_dir):
    from train_testB_auc0690 import (load_data,
                                     feature_engineering,
                                     auto_feature_engineering,
                                     train_models,
                                     ensemble_predictions_train,
                                     ensemble_predictions_test,
                                     predict_models,
                                     HAS_AUTO_ENGINEERING)
    train_path = os.path.join(train_dir, "train.csv")
    test_path = os.path.join(test_dir, "testB.csv")
    sub_example_path = os.path.join(test_dir, "submit_exampleB.csv")

    # 读取数据
    train, test = load_data(train_path, test_path)

    # 划分训练集和验证集
    X_train, X_test, y_train = train, test, train["label"].copy()
    test_ids = X_test["id"].copy()
    ori_test_T = X_test.copy()
    # 自动特征
    auto_import_features = ['region_vcounts', 'daysaddx19', 'conditionaddV', 'conditionaddx15', 'conditionaddx19', 'conditionaddw1',
                            'conditionsubV', 'conditionsubx0', 'conditionsubx19', 'conditionsubw2', 'x0subx16', 'x1subx9', 'x1subx15',
                            'daysmulcc', 'daysmulcondition', 'daysmulV', 'daysmulx10', 'daysmulx17', 'daysmulx19', 'daysmulage_range', 'daysmulw2',
                            'conditionmulV', 'conditionmulx19', 'conditionmulmax_g', 'Vmulx10', 'x0mulx10', 'x6mulx20', 'x7mulx16', 'x14mulx16',
                            'daysdivcondition', 'daysdivx17', 'daysdivx19', 'daysdivage_range', 'conditiondivage_range', 'conditiondivw2', 'x0divx6',
                            'x2divx18', 'region_max_min_encoding_x14', 'region_mean_encoding_x16',
                            'region_max_encoding_x20', 't3_mean_encoding_x2', 't3_median_encoding_x4', 't3_max_min_encoding_x12',
                            'source_q3_q1_encoding_condition']
    if HAS_AUTO_ENGINEERING:
        train_2, test_2, important_feats = auto_feature_engineering(X_train, X_test,auto_import_features)

    # 手动特征
    X_processed, T_processed, features, cat_cols = feature_engineering(X_train, X_test, y_train)

    ################addaddadd################
    print(sorted(features))
    if HAS_AUTO_ENGINEERING:
        print(sorted(important_feats))
        features = features + important_feats
        X_processed = pd.concat([X_processed, train_2[important_feats]], axis=1)
        T_processed = pd.concat([T_processed, test_2[important_feats].reset_index(drop=True)], axis=1)


    #预测
    pred_lgb, pred_xgb, pred_ctb, pred_rf = predict_models(T_processed,model_dir)
    pred_list = [pred_lgb, pred_xgb, pred_ctb, pred_rf]
    final_pred = ensemble_predictions_test(pred_list,model_dir)

    submission = pd.read_csv(sub_example_path)
    submission['label'] = final_pred
    print('sub data size', len(submission))
    print(submission.head(10))

    sub_path = os.path.join(result_dir, "1_result.csv")
    submission.to_csv(sub_path, index=False)
    print('main_1 finished.')


def main_2(train_dir, test_dir,result_dir, model_dir):
    from train_testB_auc0688 import (load_data,
                                     feature_engineering,
                                     auto_feature_engineering,
                                     train_models,
                                     ensemble_predictions_train,
                                     predict_models,
                                     ensemble_predictions_test,
                                     HAS_AUTO_ENGINEERING)
    # 读取数据
    train_path = os.path.join(train_dir, "train.csv")
    test_path = os.path.join(test_dir, "testB.csv")
    sub_example_path = os.path.join(test_dir, "submit_exampleB.csv")

    # 读取数据
    train, test = load_data(train_path, test_path)

    # 划分训练集和验证集
    X_train, X_test, y_train = train, test, train["label"].copy()
    test_ids = X_test["id"].copy()
    ori_test_T = X_test.copy()
    auto_import_features = ['region_vcounts', 'daysaddx19', 'conditionaddV', 'conditionaddx15', 'conditionaddx19', 'conditionaddw1', 'conditionsubV',
                            'conditionsubx0', 'conditionsubx19', 'conditionsubw2', 'x0subx16', 'x1subx9', 'x1subx15', 'daysmulcc', 'daysmulcondition',
                            'daysmulV', 'daysmulx10', 'daysmulx17', 'daysmulx19', 'daysmulage_range', 'daysmulw2', 'conditionmulV', 'conditionmulx19',
                            'conditionmulmax_g', 'Vmulx10', 'x0mulx10', 'x6mulx20', 'x7mulx16', 'x14mulx16', 'daysdivcondition', 'daysdivx17', 'daysdivx19',
                            'daysdivage_range', 'conditiondivage_range', 'conditiondivw2', 'x0divx6', 'x2divx18', 'region_max_min_encoding_x14',
                            'region_mean_encoding_x16', 'region_max_encoding_x20', 't3_mean_encoding_x2', 't3_median_encoding_x4', 't3_max_min_encoding_x12',
                            'source_q3_q1_encoding_condition']
    # 自动特征
    if HAS_AUTO_ENGINEERING:
        train_2, test_2, important_feats = auto_feature_engineering(X_train, X_test,auto_import_features)

    # 手动特征
    X_processed, T_processed, features, cat_cols = feature_engineering(X_train, X_test, y_train)

    ################addaddadd################
    print(sorted(features))
    if HAS_AUTO_ENGINEERING:
        print(sorted(important_feats))
        features = features + important_feats
        X_processed = pd.concat([X_processed, train_2[important_feats]], axis=1)
        T_processed = pd.concat([T_processed, test_2[important_feats].reset_index(drop=True)], axis=1)

    # 预测
    pred_lgb, pred_xgb, pred_ctb, pred_rf = predict_models(T_processed, model_dir)
    pred_list = [pred_lgb, pred_xgb, pred_ctb, pred_rf]
    final_pred = ensemble_predictions_test(pred_list, model_dir)

    submission = pd.read_csv(sub_example_path)
    submission['label'] = final_pred
    print('sub data size', len(submission))
    print(submission.head(10))

    sub_path = os.path.join(result_dir, "2_result.csv")
    submission.to_csv(sub_path, index=False)
    print('main_2 finished.')


def main_3(train_dir, test_dir, temp_dir, result_dir,model_dir):
    from train_testB_auc0690_for_fusion_ssl import (load_data,
                                                    feature_engineering,
                                                    auto_feature_engineering,
                                                    train_models,
                                                    ensemble_predictions_train,
                                                    get_semi_data,
                                                    predict_models,
                                                    ensemble_predictions_test,
                                                    HAS_AUTO_ENGINEERING)
    train_path = os.path.join(train_dir, "train.csv")
    test_path = os.path.join(test_dir, "testB.csv")
    sub_1_path = os.path.join(temp_dir, "1_result.csv")
    sub_example_path = os.path.join(test_dir, "submit_exampleB.csv")
    # 读取数据
    train, test = load_data(train_path, test_path)
    test_semi = get_semi_data(test_path, sub_1_path)
    train = pd.concat([train, test_semi], axis=0, ignore_index=True)

    # 划分训练集和验证集
    X_train, X_test, y_train = train, test, train["label"].copy()
    test_ids = X_test["id"].copy()
    ori_test_T = X_test.copy()
    # 自动特征
    auto_import_features = ['daysaddx19', 'conditionaddV', 'conditionaddx19', 'conditionaddlivability', 'conditionaddw1', 'x4addx16', 'x7addx16', 'x10addw1',
                            'x18addage_range', 'dayssubcc', 'conditionsubV', 'conditionsubx19', 'conditionsubw2', 'x7subx17', 'daysmulcc', 'daysmulcondition', 'daysmulx10',
                            'daysmulx17', 'daysmulx19', 'daysmulw2', 'conditionmulV', 'conditionmulmax_g', 'x1mulx10', 'x2mulx18', 'x6mulx12', 'x10mulx20', 'x16mulx18',
                            'x19mulx20', 'daysdivcc', 'daysdivcondition', 'daysdivx5', 'daysdivx17', 'daysdivx19', 'daysdivc2', 'daysdivw1', 'daysdivw2', 'ccdivx9',
                            'conditiondivx19', 'conditiondivage_range', 'conditiondivw2', 'Vdivage_range', 'x2divx18', 'x6divx20', 'region_max_encoding_condition',
                            'region_max_min_encoding_x14', 'region_mean_encoding_x16', 'region_max_encoding_x20', 't3_get_cov_encoding_x0',
                            't3_median_encoding_x3', 't3_max_encoding_x8', 't3_median_encoding_x16', 'source_q3_q1_encoding_condition', 'source_median_encoding_x6']
    if HAS_AUTO_ENGINEERING:
        train_2, test_2, important_feats = auto_feature_engineering(X_train, X_test,auto_import_features)

    # 手动特征
    X_processed, T_processed, features, cat_cols = feature_engineering(X_train, X_test, y_train)

    ################addaddadd################
    print(sorted(features))
    if HAS_AUTO_ENGINEERING:
        print(sorted(important_feats))
        features = features + important_feats
        X_processed = pd.concat([X_processed, train_2[important_feats]], axis=1)
        T_processed = pd.concat([T_processed, test_2[important_feats].reset_index(drop=True)], axis=1)

        # 预测
    pred_lgb, pred_xgb, pred_ctb, pred_rf = predict_models(T_processed, model_dir)
    pred_list = [pred_lgb, pred_xgb, pred_ctb, pred_rf]
    final_pred = ensemble_predictions_test(pred_list, model_dir)

    submission = pd.read_csv(sub_example_path)
    submission['label'] = final_pred
    print('sub data size', len(submission))
    print(submission.head(10))

    sub_path = os.path.join(result_dir, "3_result.csv")
    submission.to_csv(sub_path, index=False)
    print('main_3 finished.')

def main_4(test_dir,result_dir):
    # 对3个预测文件结果融合
    main_1_sub = os.path.join(result_dir,'1_result.csv')
    main_2_sub = os.path.join(result_dir,'2_result.csv')
    main_3_sub = os.path.join(result_dir,'3_result.csv')

    main_1_sub_set = pd.read_csv(main_1_sub)
    main_2_sub_set = pd.read_csv(main_2_sub)
    main_3_sub_set = pd.read_csv(main_3_sub)

    sub_example_path = os.path.join(test_dir, "submit_exampleB.csv")
    submission = pd.read_csv(sub_example_path)
    submission['label'] = (main_1_sub_set['label']+main_2_sub_set['label']+main_3_sub_set['label'])/3
    print('sub data size', len(submission))
    print(submission.head(10))

    sub_path = os.path.join(result_dir, "result.csv")
    submission.to_csv(sub_path, index=False)
    print('main_4 finished.')


if __name__ == '__main__':
    # train_dir, test_dir, temp_dir, model_dir = r'../init_data/初赛B榜数据集/train', r'../init_data/初赛B榜数据集/test', r'../temp_data/', r'./model/'
    # result_dir = r'../result/'
    parser = argparse.ArgumentParser()
    parser.add_argument('trainSetDir', type=str, help='训练数据加载根路径')
    parser.add_argument('testSetDir', type=str, help='测试数据加载根路径')
    parser.add_argument('tempDir', type=str, help='临时文件存放根路径')
    parser.add_argument('modelDir', type=str, help='模型存放根路径')
    parser.add_argument('resultDir', type=str, help='结果文件存放根路径')
    args = parser.parse_args()
    print('args',args)
    #python test.py ../init_data/初赛B榜数据集/train ../init_data/初赛B榜数据集/test ../temp_data/ ./model/ ../result/

    train_dir = args.trainSetDir
    test_dir = args.testSetDir
    temp_dir = args.tempDir
    model_dir = args.modelDir
    result_dir = args.resultDir

    # train_dir, test_dir, temp_dir, model_dir = r'../fake_init_data/初赛B榜数据集/train', r'../fake_init_data/初赛B榜数据集/test', r'../fake_temp_data/', r'./fake_model/'
    # result_dir = r'../fake_result/'
    os.makedirs(model_dir,exist_ok=True)
    os.makedirs(result_dir,exist_ok=True)
    main_1_model_dir = os.path.join(model_dir,'main_1')
    os.makedirs(main_1_model_dir,exist_ok=True)
    main_2_model_dir = os.path.join(model_dir,'main_2')
    os.makedirs(main_2_model_dir, exist_ok=True)
    main_3_model_dir = os.path.join(model_dir,'main_3')
    os.makedirs(main_3_model_dir, exist_ok=True)
    # auc 0.690
    main_1(train_dir, test_dir, result_dir, main_1_model_dir)
    # auc 0.688
    main_2(train_dir, test_dir,result_dir, main_2_model_dir)
    # 基于auc 0.690的半监督
    main_3(train_dir, test_dir, temp_dir,result_dir, main_3_model_dir)

    # 三个结果文件融合
    main_4(test_dir,result_dir)
