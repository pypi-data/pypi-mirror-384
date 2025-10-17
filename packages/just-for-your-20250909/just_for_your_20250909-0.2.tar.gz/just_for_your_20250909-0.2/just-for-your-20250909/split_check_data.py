#encoding:utf-8
import pandas as pd
from sklearn.model_selection import train_test_split
import os

# 读取原始训练数据
TRAIN_PATH = "../init_data/初赛B榜数据集/train/train.csv"
train = pd.read_csv(TRAIN_PATH)


# 分离特征和目标变量
y = train["label"].astype(int)
X = train

# 分层抽样分割训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 重新组合训练集和测试集（包含id和label）
train_set = X_train


# 创建提交示例文件（仅包含id和预测标签的模板）
submission_example = X_test[["id", "label"]].copy()
submission_example.columns = ["id", "label"]
submission_example['label'] = 0.5

test_set = X_test.drop(columns=["label"])


# 定义输出目录和文件路径
train_dir = "../fake_init_data/初赛B榜数据集/train"  # 替换为你的训练集输出目录
test_dir = "../fake_init_data/初赛B榜数据集/test"    # 替换为你的测试集输出目录
os.makedirs(train_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)

train_path = os.path.join(train_dir, "train.csv")
test_path = os.path.join(test_dir, "testB.csv")
sub_example_path = os.path.join(test_dir, "submit_exampleB.csv")

test_label_set = X_test[["id", "label"]].copy()
test_label_path = os.path.join(test_dir, "testB_label.csv")

# 保存文件
train_set.to_csv(train_path, index=False)
test_set.to_csv(test_path, index=False)
submission_example.to_csv(sub_example_path, index=False)
test_label_set.to_csv(test_label_path, index=False)

print(f"训练集已保存至: {train_path}")
print(f"测试集已保存至: {test_path}")
print(f"提交示例已保存至: {sub_example_path}")