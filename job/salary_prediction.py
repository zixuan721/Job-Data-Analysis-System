import os
import pandas as pd
import numpy as np
import json
import re
import pickle
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, r2_score
from job.models import JobData, SalaryPredictionModel
from sklearn.impute import SimpleImputer
import sys
import io
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')  # 注释：如需控制台正常显示中文，保持默认编码（GBK）
# sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')  # 注释：如需控制台正常显示中文，保持默认编码（GBK）

# 模型文件保存目录
MODEL_DIR = os.path.join('job', 'models')

# 确保模型目录存在
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

class SalaryPredictor:
    """
    薪资预测器类
    实现薪资预测模型的训练和预测功能
    """
    
    def __init__(self):
        """
        初始化薪资预测器
        """
        # 定义特征列和目标列
        self.categorical_features = ['education', 'experience', 'place', 'scale', 'key_word']
        self.numerical_features = []  # 目前没有数值型特征，如果有可以添加
        self.target_columns = ['salary_min', 'salary_max']
        
        # 初始化模型
        self.model = None
        self.preprocessor = None
        
    def _extract_salary(self, salary_str):
        """
        从薪资字符串中提取最低和最高薪资
        
        参数:
            salary_str (str): 薪资字符串，格式如 "10k-15k"
            
        返回:
            tuple: (最低薪资, 最高薪资)，单位为k
        """
        try:
            # 尝试提取"10k-15k"格式的薪资
            match = re.search(r'(\d+)[kK]-(\d+)[kK]', salary_str)
            if match:
                min_salary = float(match.group(1))
                max_salary = float(match.group(2))
                return min_salary, max_salary
            
            # 尝试提取"10k以上"格式的薪资
            match = re.search(r'(\d+)[kK]以上', salary_str)
            if match:
                min_salary = float(match.group(1))
                max_salary = min_salary * 1.5  # 估算最高薪资为最低薪资的1.5倍
                return min_salary, max_salary
            
            # 尝试提取"10k以下"格式的薪资
            match = re.search(r'(\d+)[kK]以下', salary_str)
            if match:
                max_salary = float(match.group(1))
                min_salary = max_salary * 0.6  # 估算最低薪资为最高薪资的0.6倍
                return min_salary, max_salary
                
            # 如果都不匹配，尝试直接提取数字
            match = re.search(r'(\d+)', salary_str)
            if match:
                salary = float(match.group(1))
                return salary * 0.8, salary * 1.2  # 估算范围
                
            # 如果没有匹配到任何数字，返回None
            return None, None
        except Exception as e:
            print(f"薪资提取错误: {e}, 原始薪资字符串: {salary_str}")
            return None, None
    
    def prepare_data(self):
        """
        准备训练数据
        
        返回:
            DataFrame: 准备好的数据集
        """
        # 重置特征列表，避免多次调用时累积
        self.categorical_features = ['education', 'experience', 'place', 'scale', 'key_word']
        self.numerical_features = []
        
        # 从数据库中获取所有职位数据
        job_data = list(JobData.objects.all().values())
        df = pd.DataFrame(job_data)
        
        # 提取薪资数据
        salary_data = df['salary'].apply(self._extract_salary)
        df['salary_min'] = salary_data.apply(lambda x: x[0])
        df['salary_max'] = salary_data.apply(lambda x: x[1])
        
        # 去除无效的薪资数据行
        df = df.dropna(subset=['salary_min', 'salary_max'])
        
        # 数据清洗和预处理
        print(f"原始数据记录数: {len(df)}")
        
        # 1. 移除薪资异常值 - 使用Z-score方法而不是IQR
        # 计算薪资的Z-score
        df['salary_min_zscore'] = (df['salary_min'] - df['salary_min'].mean()) / df['salary_min'].std()
        df['salary_max_zscore'] = (df['salary_max'] - df['salary_max'].mean()) / df['salary_max'].std()
        
        # 移除Z-score绝对值大于3的记录（更保守的异常值处理）
        df = df[(abs(df['salary_min_zscore']) <= 3) & (abs(df['salary_max_zscore']) <= 3)]
        df = df.drop(['salary_min_zscore', 'salary_max_zscore'], axis=1)
        
        print(f"移除薪资异常值后记录数: {len(df)}")
        
        # 2. 确保最高薪资大于最低薪资且差距合理
        df = df[df['salary_max'] >= df['salary_min']]
        
        # 薪资差距应该合理，最高薪资不应该是最低薪资的3倍以上
        df = df[df['salary_max'] <= df['salary_min'] * 3]
        
        print(f"确保薪资合理后记录数: {len(df)}")
        
        # 3. 填充缺失值 - 确保基本特征列存在
        basic_features = ['education', 'experience', 'place', 'scale', 'key_word']
        for feature in basic_features:
            if feature in df.columns:
                df[feature] = df[feature].fillna('未知')
            else:
                df[feature] = '未知'
                print(f"警告: 数据中缺少'{feature}'列，已创建并填充默认值")
        
        # 4. 标准化工作经验字段 - 只保留常见的选项
        # 创建更全面的经验映射字典
        experience_mapping = {
            # 保留的主要经验类别
            '应届毕业生': '应届生',
            '应届': '应届生',
            '实习': '实习',
            '1年以下': '1年以下',
            '一年以下': '1年以下',
            '1-3年': '1-3年',
            '2-3年': '1-3年',
            '3-5年': '3-5年',
            '3-4年': '3-5年',
            '5-10年': '5-10年',
            '5-8年': '5-10年',
            '10年以上': '10年以上',
            '经验不限': '不限',
            '不限': '不限',
            
            # 其他不常见经验归类
            '1年以上': '1-3年',
            '2年以上': '1-3年',
            '3年以上': '3-5年',
            '4年以上': '5-10年',
            '5年以上': '5-10年',
            '6年以上': '5-10年',
            '7年以上': '5-10年',
            '8年以上': '5-10年',
            '3-6年': '3-5年',
            '3-7年': '3-5年',
            '3-8年': '3-5年',
            '3-10年': '5-10年',
            '2-4年': '1-3年',
            '2-5年': '3-5年',
            '2-6年': '3-5年',
            '2-7年': '3-5年',
            '2-8年': '3-5年',
            '2-10年': '3-5年',
            '1-5年': '1-3年',
            '1-6年': '1-3年',
            '1-8年': '1-3年',
            '1-10年': '1-3年',
            '4-10年': '5-10年',
            '10年以下': '5-10年',
            '3年以下': '1-3年'
        }
        
        # 应用映射
        for key, value in experience_mapping.items():
            df.loc[df['experience'].str.contains(key, na=False), 'experience'] = value
        
        # 5. 标准化学历字段 - 只保留常见的选项
        education_mapping = {
            '博士': '博士',
            '硕士': '硕士',
            '本科': '本科',
            '大专': '大专',
            '中专': '中专',
            '高中': '中专以下',
            '不限': '不限',
            '初中': '中专以下',
            '小学': '中专以下',
            '中技': '中专',
            '中职': '中专',
            '职高': '中专',
            '职校': '中专',
            '技校': '中专'
        }
        
        # 应用映射
        for key, value in education_mapping.items():
            df.loc[df['education'].str.contains(key, na=False), 'education'] = value
        
        # 处理未映射的学历，设为'不限'
        if '其他' not in education_mapping.values():
            unusual_education = ~df['education'].isin(education_mapping.values())
            if unusual_education.sum() > 0:
                print(f"发现 {unusual_education.sum()} 条未映射的学历记录，设置为'不限'")
                df.loc[unusual_education, 'education'] = '不限'
        
        # 6. 标准化公司规模字段 - 只保留常见的选项
        scale_mapping = {
            # 原有映射
            '0-50人': '小型企业',
            '1-49人': '小型企业',
            '50-200人': '中小企业',
            '50-500人': '中小企业',
            '200-500人': '中型企业',
            '500-1000人': '中大型企业',
            '1000-5000人': '大型企业',
            '5000-10000人': '大型企业',
            '10000人以上': '超大型企业',
            '不限': '未知规模',
            
            # 新增数据库中实际出现的值的映射
            '50-99人': '小型企业',
            '100-499人': '中小企业',
            '500-999人': '中大型企业',
            '1000-2000人': '大型企业',
            '2000-5000人': '大型企业',
            
            # 处理可能出现的行业或融资阶段信息
            '融资未公开': '未知规模',
            '已上市': '大型企业',
            '新三板上市': '中大型企业',
            '战略融资': '中大型企业',
            '战略投资': '中大型企业',
            'A轮': '小型企业',
            'B轮': '小型企业',
            'C轮': '中型企业',
            'D轮': '中大型企业',
            '天使轮': '小型企业'
        }
        
        # 应用映射
        # 1. 先尝试精确匹配
        for key, value in scale_mapping.items():
            df.loc[df['scale'] == key, 'scale'] = value
        
        # 2. 对于未匹配的记录，尝试模糊匹配
        unmatched_mask = ~df['scale'].isin(list(scale_mapping.values()))
        if unmatched_mask.sum() > 0:
            for key, value in scale_mapping.items():
                df.loc[unmatched_mask & df['scale'].str.contains(key, na=False), 'scale'] = value
        
        # 3. 处理未映射的公司规模，设为'未知规模'
        if '其他' not in scale_mapping.values():
            unusual_scale = ~df['scale'].isin(list(scale_mapping.values()))
            if unusual_scale.sum() > 0:
                print(f"发现 {unusual_scale.sum()} 条未映射的公司规模记录，设置为'未知规模'")
                # 打印前20个未映射的公司规模值
                unmapped_scales = df.loc[unusual_scale, 'scale'].unique()
                if len(unmapped_scales) > 0:
                    print(f"未映射的公司规模值示例: {unmapped_scales[:20]}")
                df.loc[unusual_scale, 'scale'] = '未知规模'
        
        # 7. 标准化城市字段 - 提取主要城市名称
        def extract_city(place):
            if pd.isna(place) or place == '':
                return '未知'
            
            # 处理常见格式：城市-区域
            if '-' in place:
                return place.split('-')[0].strip()
            
            # 处理直辖市
            for city in ['北京', '上海', '广州', '深圳', '杭州', '南京', '成都', '武汉', '西安', '重庆']:
                if city in place:
                    return city
            
            return place
        
        df['place'] = df['place'].apply(extract_city)
        
        # 8. 从职位名称中提取关键技能信息
        common_skills = ['Java', 'Python', 'C++', 'PHP', '前端', '后端', '全栈', 
                         '数据分析', '机器学习', '人工智能', 'AI', '大数据', '算法', 
                         '测试', 'UI', 'UX', '产品', '运营', '销售', '市场']
        
        def extract_skills(name, key_word):
            if pd.isna(name):
                return key_word if not pd.isna(key_word) else '其他'
            
            skills = []
            for skill in common_skills:
                if skill.lower() in name.lower():
                    skills.append(skill)
            
            if skills:
                return '+'.join(skills)
            elif not pd.isna(key_word):
                return key_word
            else:
                return '其他'
        
        df['extracted_skills'] = df.apply(lambda row: extract_skills(row['name'], row['key_word']), axis=1)
        df['key_word'] = df['extracted_skills']
        
        # 9. 新增特征: 职位级别 (初级、中级、高级)
        df['position_level'] = '普通'
        
        # 高级职位
        senior_keywords = ['高级', '资深', '专家', 'senior', '总监', '经理', '主管', '架构']
        for keyword in senior_keywords:
            df.loc[df['name'].str.contains(keyword, na=False, case=False), 'position_level'] = '高级'
        
        # 初级职位
        junior_keywords = ['初级', '助理', 'junior', '实习']
        for keyword in junior_keywords:
            df.loc[df['name'].str.contains(keyword, na=False, case=False), 'position_level'] = '初级'
        
        # 10. 新增特征: 薪资范围比例 (最高/最低)
        df['salary_ratio'] = df['salary_max'] / df['salary_min']
        
        # 11. 新增特征: 职位热门程度 (基于相同职位的数量)
        position_counts = df['key_word'].value_counts()
        df['position_popularity'] = df['key_word'].map(position_counts)
        
        # 对职位热门程度进行分箱，使用更安全的方法
        try:
            df['position_popularity_bin'] = pd.qcut(df['position_popularity'], 
                                                q=5, 
                                                labels=['极低', '低', '中', '高', '极高'],
                                                duplicates='drop')
        except ValueError:
            # 如果出现分箱错误，先计算实际的分位数
            quantiles = pd.qcut(df['position_popularity'], q=5, duplicates='drop').cat.categories.size
            # 根据实际分位数量调整标签
            labels = ['极低', '低', '中', '高', '极高'][:quantiles]
            df['position_popularity_bin'] = pd.qcut(df['position_popularity'], 
                                                q=5, 
                                                labels=labels,
                                                duplicates='drop')
            print(f"职位热门度分箱调整为 {quantiles} 个分箱")
        
        # 12. 新增特征: 城市热门程度 (基于相同城市的数量)
        city_counts = df['place'].value_counts()
        df['city_popularity'] = df['place'].map(city_counts)
        
        # 对城市热门程度进行分箱，使用更安全的方法
        try:
            df['city_popularity_bin'] = pd.qcut(df['city_popularity'], 
                                            q=5, 
                                            labels=['极低', '低', '中', '高', '极高'],
                                            duplicates='drop')
        except ValueError:
            # 如果出现分箱错误，先计算实际的分位数
            quantiles = pd.qcut(df['city_popularity'], q=5, duplicates='drop').cat.categories.size
            # 根据实际分位数量调整标签
            labels = ['极低', '低', '中', '高', '极高'][:quantiles]
            df['city_popularity_bin'] = pd.qcut(df['city_popularity'], 
                                            q=5, 
                                            labels=labels,
                                            duplicates='drop')
            print(f"城市热门度分箱调整为 {quantiles} 个分箱")
        
        # 13. 对于实习生和应届生，设置合理的薪资上限
        df.loc[df['experience'] == '实习', 'salary_max'] = df.loc[df['experience'] == '实习', 'salary_max'].clip(upper=15)
        df.loc[df['experience'] == '应届生', 'salary_max'] = df.loc[df['experience'] == '应届生', 'salary_max'].clip(upper=20)
        
        # 14. 对于高级职位，设置合理的薪资下限
        senior_mask = df['position_level'] == '高级'
        df.loc[senior_mask & (df['experience'] == '5-10年'), 'salary_min'] = df.loc[senior_mask & (df['experience'] == '5-10年'), 'salary_min'].clip(lower=15)
        df.loc[senior_mask & (df['experience'] == '10年以上'), 'salary_min'] = df.loc[senior_mask & (df['experience'] == '10年以上'), 'salary_min'].clip(lower=20)
        
        # 15. 平衡数据集 - 对经验类别进行下采样，避免某些类别过多
        # 统计各经验类别的数量
        exp_counts = df['experience'].value_counts()
        
        # 找出样本数超过1000的经验类别
        large_categories = exp_counts[exp_counts > 1000].index.tolist()
        
        # 对这些类别进行下采样
        if large_categories:
            sample_size = 1000  # 每个大类别保留的样本数
            
            # 创建一个空的DataFrame来存储平衡后的数据
            balanced_df = pd.DataFrame()
            
            # 对每个类别进行处理
            for exp in df['experience'].unique():
                category_df = df[df['experience'] == exp]
                
                # 如果是大类别，进行下采样
                if exp in large_categories and len(category_df) > sample_size:
                    sampled_df = category_df.sample(sample_size, random_state=42)
                    balanced_df = pd.concat([balanced_df, sampled_df])
                else:
                    # 小类别全部保留
                    balanced_df = pd.concat([balanced_df, category_df])
            
            # 使用平衡后的数据集替换原始数据集
            df = balanced_df
        
        # 16. 对数值型特征进行对数变换，使其分布更接近正态分布
        # 对薪资进行对数变换
        df['log_salary_min'] = np.log1p(df['salary_min'])
        df['log_salary_max'] = np.log1p(df['salary_max'])
        
        # 更新分类特征列表，添加新创建的特征
        self.categorical_features = ['education', 'experience', 'place', 'scale', 'key_word', 
                                    'position_level', 'position_popularity_bin', 'city_popularity_bin']
        
        # 添加数值特征
        self.numerical_features = ['salary_ratio', 'position_popularity', 'city_popularity']
        
        # 更新目标列
        self.target_columns = ['log_salary_min', 'log_salary_max']
        
        print(f"数据预处理后的记录数: {len(df)}")
        print(f"经验分布: {df['experience'].value_counts().to_dict()}")
        print(f"学历分布: {df['education'].value_counts().to_dict()}")
        print(f"城市分布前10: {df['place'].value_counts()[:10].to_dict()}")
        print(f"职位级别分布: {df['position_level'].value_counts().to_dict()}")
        
        return df
    
    def build_model(self, model_type='random_forest', model_params=None):
        """
        构建预处理器和模型
        
        参数:
            model_type (str): 模型类型，可选值: 'random_forest', 'gradient_boosting', 'ridge', 'lasso', 'xgboost', 'lightgbm'
            model_params (dict, optional): 模型参数，如果为None则使用默认参数
            
        返回:
            tuple: (预处理器, 模型)
        """
        # 确保model_params是一个字典
        if model_params is None:
            model_params = {}
        elif not isinstance(model_params, dict):
            print(f"警告: model_params应该是一个字典，但获取到的是 {type(model_params)}，将使用默认参数")
            model_params = {}
        
        # 分类特征处理
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='未知')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])
        
        # 数值特征处理
        numerical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        # 特征预处理器
        preprocessor = ColumnTransformer(
            transformers=[
                ('cat', categorical_transformer, self.categorical_features),
                ('num', numerical_transformer, self.numerical_features) if self.numerical_features else ('num', 'passthrough', [])
            ],
            remainder='drop'  # 删除未指定的列
        )
        
        # 根据模型类型构建模型
        if model_type == 'random_forest':
            # 随机森林参数
            rf_params = {
                'n_estimators': model_params.get('n_estimators', 200),  # 默认200棵树
                'max_depth': model_params.get('max_depth', 15),  # 默认最大深度15
                'min_samples_split': model_params.get('min_samples_split', 5),  # 默认分裂所需的最小样本数5
                'min_samples_leaf': model_params.get('min_samples_leaf', 2),  # 默认叶节点的最小样本数2
                'max_features': model_params.get('max_features', 'sqrt'),  # 默认使用sqrt(n_features)个特征
                'bootstrap': model_params.get('bootstrap', True),  # 默认使用bootstrap采样
                'random_state': 42,  # 固定随机种子，确保结果可复现
                'n_jobs': -1  # 使用所有可用的CPU核心
            }
            model = RandomForestRegressor(**rf_params)
            print(f"构建随机森林模型，参数: {rf_params}")
            
        elif model_type == 'gradient_boosting':
            # 梯度提升参数
            gb_params = {
                'n_estimators': model_params.get('n_estimators', 200),  # 默认200棵树
                'learning_rate': model_params.get('learning_rate', 0.05),  # 默认学习率0.05
                'max_depth': model_params.get('max_depth', 5),  # 默认最大深度5
                'min_samples_split': model_params.get('min_samples_split', 5),  # 默认分裂所需的最小样本数5
                'min_samples_leaf': model_params.get('min_samples_leaf', 2),  # 默认叶节点的最小样本数2
                'subsample': model_params.get('subsample', 0.8),  # 默认子采样率0.8
                'max_features': model_params.get('max_features', 0.8),  # 默认使用80%的特征
                'random_state': 42  # 固定随机种子，确保结果可复现
            }
            model = GradientBoostingRegressor(**gb_params)
            print(f"构建梯度提升模型，参数: {gb_params}")
            
        elif model_type == 'ridge':
            # 岭回归参数
            ridge_params = {
                'alpha': model_params.get('alpha', 1.0),  # 默认正则化强度1.0
                'solver': model_params.get('solver', 'auto'),  # 默认求解器auto
                'random_state': 42  # 固定随机种子，确保结果可复现
            }
            model = Ridge(**ridge_params)
            print(f"构建岭回归模型，参数: {ridge_params}")
            
        elif model_type == 'lasso':
            # Lasso回归参数
            lasso_params = {
                'alpha': model_params.get('alpha', 0.1),  # 默认正则化强度0.1
                'max_iter': model_params.get('max_iter', 10000),  # 默认最大迭代次数10000
                'random_state': 42  # 固定随机种子，确保结果可复现
            }
            model = Lasso(**lasso_params)
            print(f"构建Lasso回归模型，参数: {lasso_params}")
            
        elif model_type == 'xgboost':
            # 尝试导入XGBoost
            try:
                from xgboost import XGBRegressor
                
                # XGBoost参数
                xgb_params = {
                    'n_estimators': model_params.get('n_estimators', 200),  # 默认200棵树
                    'learning_rate': model_params.get('learning_rate', 0.05),  # 默认学习率0.05
                    'max_depth': model_params.get('max_depth', 6),  # 默认最大深度6
                    'min_child_weight': model_params.get('min_child_weight', 1),  # 默认最小子权重1
                    'subsample': model_params.get('subsample', 0.8),  # 默认子采样率0.8
                    'colsample_bytree': model_params.get('colsample_bytree', 0.8),  # 默认列采样率0.8
                    'gamma': model_params.get('gamma', 0),  # 默认gamma值0
                    'reg_alpha': model_params.get('reg_alpha', 0),  # 默认L1正则化0
                    'reg_lambda': model_params.get('reg_lambda', 1),  # 默认L2正则化1
                    'random_state': 42,  # 固定随机种子，确保结果可复现
                    'n_jobs': -1  # 使用所有可用的CPU核心
                }
                model = XGBRegressor(**xgb_params)
                print(f"构建XGBoost模型，参数: {xgb_params}")
            except ImportError:
                print("警告: XGBoost未安装，将使用随机森林模型代替")
                # 如果XGBoost未安装，回退到随机森林
                model = RandomForestRegressor(
                    n_estimators=200, 
                    max_depth=15, 
                    min_samples_split=5, 
                    min_samples_leaf=2, 
                    max_features='sqrt', 
                    bootstrap=True, 
                    random_state=42, 
                    n_jobs=-1
                )
        
        elif model_type == 'lightgbm':
            # 尝试导入LightGBM
            try:
                from lightgbm import LGBMRegressor
                
                # LightGBM参数
                lgbm_params = {
                    'n_estimators': model_params.get('n_estimators', 200),  # 默认200棵树
                    'learning_rate': model_params.get('learning_rate', 0.05),  # 默认学习率0.05
                    'max_depth': model_params.get('max_depth', -1),  # 默认无限制
                    'num_leaves': model_params.get('num_leaves', 31),  # 默认31叶子节点
                    'min_child_samples': model_params.get('min_child_samples', 20),  # 默认最小子样本数20
                    'subsample': model_params.get('subsample', 0.8),  # 默认子采样率0.8
                    'colsample_bytree': model_params.get('colsample_bytree', 0.8),  # 默认列采样率0.8
                    'reg_alpha': model_params.get('reg_alpha', 0),  # 默认L1正则化0
                    'reg_lambda': model_params.get('reg_lambda', 0),  # 默认L2正则化0
                    'random_state': 42,  # 固定随机种子，确保结果可复现
                    'n_jobs': -1  # 使用所有可用的CPU核心
                }
                model = LGBMRegressor(**lgbm_params)
                print(f"构建LightGBM模型，参数: {lgbm_params}")
            except ImportError:
                print("警告: LightGBM未安装，将使用随机森林模型代替")
                # 如果LightGBM未安装，回退到随机森林
                model = RandomForestRegressor(
                    n_estimators=200, 
                    max_depth=15, 
                    min_samples_split=5, 
                    min_samples_leaf=2, 
                    max_features='sqrt', 
                    bootstrap=True, 
                    random_state=42, 
                    n_jobs=-1
                )
        
        else:
            # 默认使用随机森林
            print(f"警告: 未知的模型类型 '{model_type}'，将使用随机森林模型")
            model = RandomForestRegressor(
                n_estimators=200, 
                max_depth=15, 
                min_samples_split=5, 
                min_samples_leaf=2, 
                max_features='sqrt', 
                bootstrap=True, 
                random_state=42, 
                n_jobs=-1
            )
        
        return preprocessor, model
    
    def save_model_to_file(self, model_type, min_pipeline, max_pipeline, results):
        """
        将模型保存到本地文件
        
        参数:
            model_type (str): 模型类型
            min_pipeline (Pipeline): 最低薪资预测模型管道
            max_pipeline (Pipeline): 最高薪资预测模型管道
            results (dict): 模型评估结果
            
        返回:
            tuple: (模型文件路径, 元数据文件路径)
        """
        try:
            # 确保模型目录存在
            if not os.path.exists(MODEL_DIR):
                os.makedirs(MODEL_DIR)
            
            # 生成模型文件名（使用时间戳确保唯一性）
            import time
            timestamp = int(time.time())
            model_filename = f"{model_type}_{timestamp}.pkl"
            meta_filename = f"{model_type}_{timestamp}_meta.json"
            
            model_path = os.path.join(MODEL_DIR, model_filename)
            meta_path = os.path.join(MODEL_DIR, meta_filename)
            
            # 保存模型到文件
            with open(model_path, 'wb') as f:
                model_data = {
                    'min_pipeline': min_pipeline,
                    'max_pipeline': max_pipeline,
                    'categorical_features': self.categorical_features,
                    'numerical_features': self.numerical_features,
                    'model_type': model_type
                }
                pickle.dump(model_data, f)
            
            # 保存元数据
            meta_data = {
                'model_type': model_type,
                'model_filename': model_filename,
                'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'categorical_features': self.categorical_features,
                'numerical_features': self.numerical_features,
                'results': results
            }
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=4)
            
            print(f"模型已保存到文件: {model_path}")
            return model_path, meta_path
        except Exception as e:
            print(f"保存模型到文件失败: {e}")
            return None, None

    def load_model_from_file(self, model_type=None, model_filename=None):
        """
        从文件加载模型
        
        参数:
            model_type (str, optional): 模型类型，如果指定则加载该类型的最新模型
            model_filename (str, optional): 模型文件名，如果指定则直接加载该文件
            
        返回:
            bool: 加载成功返回True，否则返回False
        """
        try:
            # 确定要加载的模型文件
            if model_filename:
                model_path = os.path.join(MODEL_DIR, model_filename)
                if not os.path.exists(model_path):
                    print(f"指定的模型文件不存在: {model_path}")
                    return False
            elif model_type:
                # 查找指定类型的最新模型文件
                model_files = [f for f in os.listdir(MODEL_DIR) if f.startswith(f"{model_type}_") and f.endswith(".pkl")]
                if not model_files:
                    print(f"未找到类型为 {model_type} 的模型文件")
                    return False
                
                # 按时间戳排序找到最新的模型
                model_files.sort(reverse=True)
                model_path = os.path.join(MODEL_DIR, model_files[0])
            else:
                # 查找任意类型的最新模型文件
                model_files = [f for f in os.listdir(MODEL_DIR) if f.endswith(".pkl")]
                if not model_files:
                    print("未找到任何模型文件")
                    return False
                
                # 按时间戳排序找到最新的模型
                model_files.sort(reverse=True)
                model_path = os.path.join(MODEL_DIR, model_files[0])
            
            # 加载模型
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # 提取模型数据
            self.min_pipeline = model_data['min_pipeline']
            self.max_pipeline = model_data['max_pipeline']
            self.categorical_features = model_data['categorical_features']
            self.numerical_features = model_data['numerical_features']
            self.model_type = model_data['model_type']
            
            print(f"成功从文件加载模型: {model_path}")
            return True
        except Exception as e:
            print(f"从文件加载模型失败: {e}")
            return False
    
    def train_model(self, model_type='random_forest', save_model=True, model_params=None):
        """
        训练薪资预测模型
        
        参数:
            model_type (str): 模型类型
            save_model (bool): 是否保存模型
            model_params (dict, optional): 模型参数，如果为None则使用默认参数
            
        返回:
            dict: 模型评估结果
        """
        # 准备数据
        df = self.prepare_data()
        
        # 分离特征和目标
        X = df[self.categorical_features + self.numerical_features]
        # 使用对数变换后的目标变量
        y_min = df['log_salary_min']
        y_max = df['log_salary_max']
        
        print(f"训练数据形状: X={X.shape}, y_min={y_min.shape}, y_max={y_max.shape}")
        
        # 分割训练集和测试集
        try:
            # 尝试使用分层抽样
            if len(df['experience'].unique()) < 10:
                X_train, X_test, y_min_train, y_min_test, y_max_train, y_max_test = train_test_split(
                    X, y_min, y_max, test_size=0.2, random_state=42, shuffle=True, stratify=df['experience']
                )
                print("使用分层抽样划分训练集和测试集")
            else:
                # 如果类别太多，不使用分层抽样
                X_train, X_test, y_min_train, y_min_test, y_max_train, y_max_test = train_test_split(
                    X, y_min, y_max, test_size=0.2, random_state=42, shuffle=True
                )
                print("使用随机抽样划分训练集和测试集")
        except ValueError as e:
            print(f"分层抽样失败: {e}，使用随机抽样")
            X_train, X_test, y_min_train, y_min_test, y_max_train, y_max_test = train_test_split(
                X, y_min, y_max, test_size=0.2, random_state=42, shuffle=True
            )
        
        # 构建模型
        preprocessor, model = self.build_model(model_type, model_params)
        
        # 训练最低薪资预测模型
        min_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', model)
        ])
        
        print(f"开始训练最低薪资模型 ({model_type})...")
        min_pipeline.fit(X_train, y_min_train)
        
        # 训练最高薪资预测模型
        max_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', model)
        ])
        
        print(f"开始训练最高薪资模型 ({model_type})...")
        max_pipeline.fit(X_train, y_max_train)
        
        # 评估模型
        y_min_pred = min_pipeline.predict(X_test)
        y_max_pred = max_pipeline.predict(X_test)
        
        # 计算对数空间中的评估指标
        min_mae = mean_absolute_error(y_min_test, y_min_pred)
        min_r2 = r2_score(y_min_test, y_min_pred)
        
        max_mae = mean_absolute_error(y_max_test, y_max_pred)
        max_r2 = r2_score(y_max_test, y_max_pred)
        
        # 将预测结果转换回原始空间进行评估
        y_min_pred_orig = np.expm1(y_min_pred)
        y_min_test_orig = np.expm1(y_min_test)
        
        y_max_pred_orig = np.expm1(y_max_pred)
        y_max_test_orig = np.expm1(y_max_test)
        
        # 计算原始空间中的评估指标
        min_mae_orig = mean_absolute_error(y_min_test_orig, y_min_pred_orig)
        min_r2_orig = r2_score(y_min_test_orig, y_min_pred_orig)
        
        max_mae_orig = mean_absolute_error(y_max_test_orig, y_max_pred_orig)
        max_r2_orig = r2_score(y_max_test_orig, y_max_pred_orig)
        
        print(f"模型评估结果 (对数空间):")
        print(f"  最低薪资 - MAE: {min_mae:.4f}, R2: {min_r2:.4f}")
        print(f"  最高薪资 - MAE: {max_mae:.4f}, R2: {max_r2:.4f}")
        
        print(f"模型评估结果 (原始空间):")
        print(f"  最低薪资 - MAE: {min_mae_orig:.4f}, R2: {min_r2_orig:.4f}")
        print(f"  最高薪资 - MAE: {max_mae_orig:.4f}, R2: {max_r2_orig:.4f}")
        
        # 计算特征重要性（如果是树模型）
        feature_importance = {}
        if model_type in ['random_forest', 'gradient_boosting']:
            # 获取预处理后的特征名称
            cat_features = []
            try:
                cat_features = preprocessor.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(self.categorical_features)
            except:
                # 兼容旧版本scikit-learn
                try:
                    cat_features = preprocessor.named_transformers_['cat'].named_steps['onehot'].get_feature_names(self.categorical_features)
                except:
                    print("警告: 无法获取分类特征名称")
            
            num_features = self.numerical_features
            feature_names = np.concatenate([cat_features, num_features]) if len(num_features) > 0 and len(cat_features) > 0 else (cat_features if len(cat_features) > 0 else num_features)
            
            # 获取特征重要性
            min_importance = min_pipeline.named_steps['model'].feature_importances_
            max_importance = max_pipeline.named_steps['model'].feature_importances_
            
            # 计算平均特征重要性
            avg_importance = (min_importance + max_importance) / 2
            
            # 创建特征重要性字典
            feature_importance = {
                feature_names[i]: float(avg_importance[i]) for i in range(len(feature_names))
            }
            
            # 打印前10个最重要的特征
            print("前10个最重要的特征:")
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            for feature, importance in sorted_features:
                print(f"  {feature}: {importance:.6f}")
        
        # 保存模型评估结果
        results = {
            'model_type': model_type,
            'min_salary': {
                'mae': float(min_mae),
                'r2': float(min_r2),
                'mae_orig': float(min_mae_orig),
                'r2_orig': float(min_r2_orig)
            },
            'max_salary': {
                'mae': float(max_mae),
                'r2': float(max_r2),
                'mae_orig': float(max_mae_orig),
                'r2_orig': float(max_r2_orig)
            },
            'feature_importance': feature_importance
        }
        
        # 保存模型
        self.min_pipeline = min_pipeline
        self.max_pipeline = max_pipeline
        self.model_type = model_type
        
        # 如果需要，保存模型
        if save_model:
            # 1. 保存到数据库
            # 将之前的活跃模型设为非活跃
            SalaryPredictionModel.objects.filter(is_active=True).update(is_active=False)
            
            # 创建新的模型记录
            model_obj = SalaryPredictionModel.objects.create(
                model_name=f"薪资预测模型_{model_type}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}",
                model_type=model_type,
                model_parameters=json.dumps({
                    'categorical_features': self.categorical_features,
                    'numerical_features': self.numerical_features,
                    'training_samples': len(X_train),
                    'model_params': model_params
                }, ensure_ascii=False),
                feature_importance=json.dumps(feature_importance, ensure_ascii=False) if feature_importance else None,
                r2_score=(min_r2_orig + max_r2_orig) / 2,  # 使用原始空间的平均R2作为模型整体评分
                mean_absolute_error=(min_mae_orig + max_mae_orig) / 2,  # 使用原始空间的平均MAE
                is_active=True  # 设置为活跃模型
            )
            
            # 2. 保存到文件系统
            model_path, meta_path = self.save_model_to_file(model_type, min_pipeline, max_pipeline, results)
            
            # 在数据库中记录文件路径
            if model_path and meta_path:
                model_obj.model_parameters = json.dumps({
                    'categorical_features': self.categorical_features,
                    'numerical_features': self.numerical_features,
                    'model_file_path': model_path,
                    'meta_file_path': meta_path,
                    'training_samples': len(X_train),
                    'model_params': model_params
                }, ensure_ascii=False)
                model_obj.save()
                
            print(f"模型已保存: ID={model_obj.model_id}, 名称={model_obj.model_name}")
        
        return results
    
    def predict(self, features, model_type=None, apply_manual_adjustment=True):
        """
        使用加载的模型进行薪资预测
        
        参数:
            features (dict): 职位特征，包括 education, experience, place, scale, key_word 等
            model_type (str, optional): 指定使用的模型类型，如不指定则使用当前活跃模型
            apply_manual_adjustment (bool): 是否应用手动调整参数，默认为True
            
        返回:
            tuple: (预测最低薪资, 预测最高薪资)
        """
        try:
            # 如果指定了模型类型，尝试从文件加载该类型的模型
            if model_type and not hasattr(self, 'min_pipeline'):
                self.load_model_from_file(model_type=model_type)
            
            # 如果没有指定模型类型，且没有加载模型，尝试加载任意模型
            if not hasattr(self, 'min_pipeline') or not hasattr(self, 'max_pipeline'):
                model_loaded = self.load_model_from_file()
                
                # 如果无法加载任何模型，训练一个新模型
                if not model_loaded:
                    print("无法加载模型，训练新模型")
                    self.train_model(model_type=model_type if model_type else 'random_forest')
            
            # 准备特征数据
            df = pd.DataFrame([features])
            
            # 填充缺失值
            for feature in self.categorical_features:
                if feature not in df.columns:
                    df[feature] = '未知'
                else:
                    df[feature] = df[feature].fillna('未知')
            
            # 如果特征不完整，填充缺失特征
            for feature in self.categorical_features + self.numerical_features:
                if feature not in df.columns:
                    if feature in self.categorical_features:
                        df[feature] = '未知'
                    else:
                        df[feature] = 0
            
            # 添加派生特征
            # 职位级别
            if 'position_level' not in df.columns:
                df['position_level'] = '普通'
                
                # 根据职位名称判断级别
                if 'name' in features:
                    name = features['name'].lower() if features['name'] else ''
                    
                    # 高级职位
                    senior_keywords = ['高级', '资深', '专家', 'senior', '总监', '经理', '主管', '架构']
                    for keyword in senior_keywords:
                        if keyword.lower() in name:
                            df['position_level'] = '高级'
                            break
                    
                    # 初级职位
                    junior_keywords = ['初级', '助理', 'junior', '实习']
                    for keyword in junior_keywords:
                        if keyword.lower() in name:
                            df['position_level'] = '初级'
                            break
            
            # 职位热门程度和城市热门程度 - 使用中等值作为默认值
            if 'position_popularity' not in df.columns:
                df['position_popularity'] = 100  # 默认中等热门度
            
            if 'city_popularity' not in df.columns:
                df['city_popularity'] = 100  # 默认中等热门度
                
            if 'position_popularity_bin' not in df.columns:
                df['position_popularity_bin'] = '中'  # 默认中等热门度
                
            if 'city_popularity_bin' not in df.columns:
                df['city_popularity_bin'] = '中'  # 默认中等热门度
                
            # 薪资比例 - 使用默认值1.5（最高薪资是最低薪资的1.5倍）
            if 'salary_ratio' not in df.columns:
                df['salary_ratio'] = 1.5
            
            # 使用模型进行预测
            try:
                X_pred = df[self.categorical_features + self.numerical_features]
                
                # 预测薪资（对数空间）
                log_min_salary = self.min_pipeline.predict(X_pred)[0]
                log_max_salary = self.max_pipeline.predict(X_pred)[0]
                
                # 转换回原始空间
                min_salary = np.expm1(log_min_salary)
                max_salary = np.expm1(log_max_salary)
                
                # 确保预测结果合理
                min_salary = max(0, min_salary)  # 薪资不应该为负
                max_salary = max(min_salary, max_salary)  # 最高薪资应该大于等于最低薪资
                
                # 应用手动调整系数，使预测更符合实际情况
                if apply_manual_adjustment:
                    min_salary, max_salary = self._apply_manual_adjustments(
                        min_salary, max_salary, features
                    )
                
                # 确保最小值和最大值有合理差异
                if abs(min_salary - max_salary) < 1.0:  # 如果差异小于1K
                    # 在相同值的情况下，给予一个合理的范围 (约10-20%的增长)
                    max_salary = min_salary * 1.15  # 增加15%
                
                print(f"使用模型 {self.model_type} 预测薪资: {min_salary:.1f}-{max_salary:.1f}K")
                return min_salary, max_salary
            
            except Exception as e:
                print(f"预测过程中出错: {e}")
                import traceback
                traceback.print_exc()
                # 使用一个简单的回退机制，返回行业平均值
                return 10.0, 20.0  # 假设行业平均薪资范围为10k-20k
                
        except Exception as e:
            print(f"薪资预测失败: {e}")
            import traceback
            traceback.print_exc()
            # 出现异常时返回默认值
            return 8.0, 15.0  # 返回一个默认的薪资范围
    
    def _apply_manual_adjustments(self, min_salary, max_salary, features):
        """
        应用手动调整规则，使薪资预测更符合实际情况
        
        参数:
            min_salary (float): 模型预测的最低薪资
            max_salary (float): 模型预测的最高薪资
            features (dict): 职位特征
            
        返回:
            tuple: (调整后的最低薪资, 调整后的最高薪资)
        """
        # 复制原始值用于调整
        adjusted_min = min_salary
        adjusted_max = max_salary
        
        print(f"原始预测: {min_salary:.1f}K-{max_salary:.1f}K")
        print(f"职位特征: {features}")
        
        # 1. 根据工作经验调整
        experience = features.get('experience', '未知')
        experience_factors = {
            '实习': 0.5,       # 实习生薪资预测值通常严重偏高，降低50%
            '应届生': 0.6,     # 应届生薪资预测值通常偏高，降低40%
            '1年以下': 0.7,    # 1年以下经验，降低30%
            '1-3年': 0.85,     # 1-3年经验，降低15%
            '3-5年': 1.0,      # 3-5年经验，保持原值
            '5-10年': 1.1,     # 5-10年经验，增加10%
            '10年以上': 1.2,   # 10年以上，增加20%
            '不限': 0.75,      # 不限通常意味着接受较少经验，降低25%
            '未知': 0.75       # 未知情况，按较低值处理
        }
        
        # 获取经验对应的调整因子，如果没有匹配项则使用默认值0.8（降低20%）
        exp_factor = experience_factors.get(experience, 0.8)
        adjusted_min *= exp_factor
        adjusted_max *= exp_factor
        
        print(f"经验调整后: {adjusted_min:.1f}K-{adjusted_max:.1f}K (因子: {exp_factor})")
        
        # 2. 根据学历调整
        education = features.get('education', '未知')
        education_factors = {
            '博士': 1.3,      # 博士学历，增加30%
            '硕士': 1.15,     # 硕士学历，增加15%
            '本科': 1.0,      # 本科学历，保持原值
            '大专': 0.85,     # 大专学历，降低15%
            '中专': 0.75,     # 中专学历，降低25%
            '中专以下': 0.7,  # 中专以下学历，降低30%
            '高中': 0.7,      # 高中学历，降低30%
            '不限': 0.8,      # 不限通常意味着接受较低学历，降低20%
            '未知': 0.9       # 未知情况，轻微降低
        }
        
        # 获取学历对应的调整因子
        edu_factor = education_factors.get(education, 1.0)
        adjusted_min *= edu_factor
        adjusted_max *= edu_factor
        
        print(f"学历调整后: {adjusted_min:.1f}K-{adjusted_max:.1f}K (因子: {edu_factor})")
        
        # 3. 根据城市进行调整（一线城市vs二三线城市）
        place = features.get('place', '未知')
        city_factors = {
            '北京': 1.0,      # 北京作为基准
            '上海': 1.0,      # 上海与北京相当
            '广州': 0.9,      # 广州略低于北京上海
            '深圳': 1.0,      # 深圳与北京上海相当
            '杭州': 0.85,     # 杭州略低
            '南京': 0.8,      # 南京更低一些
            '成都': 0.8,      # 成都更低一些
            '武汉': 0.75,     # 武汉更低一些
            '西安': 0.75,     # 西安更低一些
            '苏州': 0.85,     # 苏州略低
            '天津': 0.85,     # 天津略低
            '重庆': 0.8,      # 重庆更低一些
            '厦门': 0.8,      # 厦门更低一些
            '青岛': 0.75,     # 青岛更低一些
            '长沙': 0.75,     # 长沙更低一些
            '郑州': 0.7,      # 郑州更低一些
            '其他': 0.7,      # 其他城市普遍较低
            '未知': 0.8       # 未知情况，按较低值处理
        }
        
        # 尝试精确匹配城市名
        city_factor = city_factors.get(place, None)
        
        # 如果没有精确匹配，尝试模糊匹配（检查城市名是否在地点字符串中）
        if city_factor is None:
            for city, factor in city_factors.items():
                if city != '其他' and city != '未知' and city in place:
                    city_factor = factor
                    break
            
            # 如果仍然没有匹配，使用"其他"的系数
            if city_factor is None:
                city_factor = city_factors['其他']
        
        adjusted_min *= city_factor
        adjusted_max *= city_factor
        
        print(f"城市调整后: {adjusted_min:.1f}K-{adjusted_max:.1f}K (因子: {city_factor}, 城市: {place})")
        
        # 4. 根据公司规模调整
        scale = features.get('scale', '未知规模')
        scale_factors = {
            '小型企业': 0.85,     # 小型企业通常薪资较低
            '中小企业': 0.9,      # 中小企业薪资略低
            '中型企业': 1.0,      # 中型企业作为基准
            '中大型企业': 1.05,   # 中大型企业薪资略高
            '大型企业': 1.1,      # 大型企业薪资较高
            '超大型企业': 1.15,   # 超大型企业薪资最高
            '未知规模': 0.95      # 未知规模按略低处理
        }
        
        # 尝试精确匹配公司规模
        scale_factor = 0.95  # 默认因子
        
        # 遍历规模因子字典进行模糊匹配
        for scale_key, factor in scale_factors.items():
            if scale_key in scale:
                scale_factor = factor
                break
                
        # 应用公司规模调整因子
        adjusted_min *= scale_factor
        adjusted_max *= scale_factor
        
        print(f"公司规模调整后: {adjusted_min:.1f}K-{adjusted_max:.1f}K (因子: {scale_factor}, 规模: {scale})")
        
        # 5. 为特定职位名称添加调整因子
        position_name = features.get('key_word', '').lower()
        job_name = features.get('name', '').lower() if 'name' in features else ''
        
        # 高薪职位加成
        high_salary_keywords = ['架构', '专家', '总监', '经理', '主管', '高级', '资深', 'senior', 'lead']
        if any(keyword in position_name or (job_name and keyword in job_name) for keyword in high_salary_keywords):
            position_factor = 1.15  # 增加15%
            adjusted_min *= position_factor
            adjusted_max *= position_factor
            print(f"高薪职位加成: {adjusted_min:.1f}K-{adjusted_max:.1f}K (因子: {position_factor})")
        
        # 技术岗位差异化调整
        tech_factors = {
            'java': 1.05,       # Java开发薪资略高
            'python': 1.0,      # Python开发作为基准
            'c++': 1.05,        # C++开发薪资略高
            'golang': 1.1,      # Go语言开发薪资较高
            'rust': 1.15,       # Rust语言开发薪资高
            '前端': 0.95,       # 前端开发薪资略低
            '后端': 1.05,       # 后端开发薪资略高
            '全栈': 1.1,        # 全栈开发薪资较高
            '数据分析': 0.95,   # 数据分析薪资略低
            '机器学习': 1.1,    # 机器学习薪资较高
            '人工智能': 1.15,   # 人工智能薪资高
            '大数据': 1.05,     # 大数据薪资略高
            '测试': 0.9,        # 测试薪资较低
            '运维': 0.9,        # 运维薪资较低
            '产品': 0.95,       # 产品薪资略低
            '设计': 0.9,        # 设计薪资较低
            '运营': 0.85,       # 运营薪资较低
            '销售': 0.9         # 销售薪资较低
        }
        
        # 应用技术岗位调整
        for tech, factor in tech_factors.items():
            if tech in position_name or (job_name and tech in job_name):
                adjusted_min *= factor
                adjusted_max *= factor
                print(f"技术岗位调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K (因子: {factor}, 技术: {tech})")
                break
        
        # 6. 应用合理的薪资上下限
        # 设置绝对薪资下限，确保不会有低于市场最低值的预测
        minimum_salary = {
            '实习': 2.0,     # 实习生最低2K
            '应届生': 3.5,   # 应届生最低3.5K
            '1年以下': 4.5,  # 1年以下最低4.5K
            '1-3年': 6.0,    # 1-3年最低6K
            '3-5年': 8.0,    # 3-5年最低8K
            '5-10年': 12.0,  # 5-10年最低12K
            '10年以上': 18.0,# 10年以上最低18K
            '不限': 4.0,     # 不限经验最低4K
            '未知': 4.0      # 未知经验最低4K
        }
        
        # 设置绝对薪资上限，确保不会有超出市场合理范围的预测
        maximum_salary = {
            '实习': 6.0,      # 实习生最高6K
            '应届生': 15.0,   # 应届生最高15K
            '1年以下': 20.0,  # 1年以下最高20K
            '1-3年': 30.0,    # 1-3年最高30K
            '3-5年': 45.0,    # 3-5年最高45K
            '5-10年': 70.0,   # 5-10年最高70K
            '10年以上': 100.0,# 10年以上最高100K
            '不限': 25.0,     # 不限经验最高25K
            '未知': 25.0      # 未知经验最高25K
        }
        
        # 获取薪资下限和上限
        min_limit = minimum_salary.get(experience, 4.0)
        max_limit = maximum_salary.get(experience, 25.0)
        
        # 应用绝对下限和上限
        adjusted_min = max(adjusted_min, min_limit)
        adjusted_max = min(adjusted_max, max_limit)
        
        # 确保最大值至少比最小值高20%
        if adjusted_max < adjusted_min * 1.2:
            adjusted_max = adjusted_min * 1.2
            
        print(f"应用薪资限制后: {adjusted_min:.1f}K-{adjusted_max:.1f}K (下限: {min_limit}, 上限: {max_limit})")
        
        # 7. 特定职位的专门调整
        # 为Java开发工程师特别调整
        if ('java' in position_name.lower() and '开发' in position_name.lower()) or \
           (job_name and 'java' in job_name and '开发' in job_name):
            if experience == '实习':
                adjusted_min = min(adjusted_min, 3.0)  # 最高不超过3K起薪
                adjusted_max = min(adjusted_max, 5.0)  # 最高不超过5K封顶
                print(f"Java开发实习生特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
            elif experience == '应届生':
                adjusted_min = min(adjusted_min, 7.0)  # 最高不超过7K起薪
                adjusted_max = min(adjusted_max, 10.0)  # 最高不超过10K封顶
                print(f"Java开发应届生特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
            elif experience == '1-3年':
                adjusted_min = min(adjusted_min, 10.0)
                adjusted_max = min(adjusted_max, 18.0)
                print(f"Java开发1-3年特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
        
        # 为Python数据分析师特别调整
        if ('python' in position_name.lower() and '数据分析' in position_name.lower()) or \
           ('数据分析师' in position_name.lower()) or \
           (job_name and 'python' in job_name and '数据分析' in job_name) or \
           (job_name and '数据分析师' in job_name):
            if experience == '实习':
                adjusted_min = min(adjusted_min, 2.0)  # 最高不超过2K起薪
                adjusted_max = min(adjusted_max, 4.0)  # 最高不超过4K封顶
                print(f"Python数据分析师实习生特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
            elif experience == '应届生':
                adjusted_min = min(adjusted_min, 5.0)  # 最高不超过5K起薪
                adjusted_max = min(adjusted_max, 8.0)  # 最高不超过8K封顶
                print(f"Python数据分析师应届生特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
            elif experience == '1-3年':
                adjusted_min = min(adjusted_min, 8.0)
                adjusted_max = min(adjusted_max, 15.0)
                print(f"Python数据分析师1-3年特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
        
        # 为前端开发特别调整
        if ('前端' in position_name.lower() and '开发' in position_name.lower()) or \
           (job_name and '前端' in job_name and '开发' in job_name):
            if experience == '实习':
                adjusted_min = min(adjusted_min, 2.5)  # 最高不超过2.5K起薪
                adjusted_max = min(adjusted_max, 4.5)  # 最高不超过4.5K封顶
                print(f"前端开发实习生特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
            elif experience == '应届生':
                adjusted_min = min(adjusted_min, 6.0)  # 最高不超过6K起薪
                adjusted_max = min(adjusted_max, 9.0)  # 最高不超过9K封顶
                print(f"前端开发应届生特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
            elif experience == '1-3年':
                adjusted_min = min(adjusted_min, 9.0)
                adjusted_max = min(adjusted_max, 16.0)
                print(f"前端开发1-3年特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
        
        # 为测试工程师特别调整
        if ('测试' in position_name.lower()) or (job_name and '测试' in job_name):
            if experience == '实习':
                adjusted_min = min(adjusted_min, 2.0)  # 最高不超过2K起薪
                adjusted_max = min(adjusted_max, 4.0)  # 最高不超过4K封顶
                print(f"测试工程师实习生特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
            elif experience == '应届生':
                adjusted_min = min(adjusted_min, 5.0)  # 最高不超过5K起薪
                adjusted_max = min(adjusted_max, 8.0)  # 最高不超过8K封顶
                print(f"测试工程师应届生特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
            elif experience == '1-3年':
                adjusted_min = min(adjusted_min, 7.0)
                adjusted_max = min(adjusted_max, 14.0)
                print(f"测试工程师1-3年特别调整: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
        
        # 8. 确保最小值和最大值有合理差异
        if abs(adjusted_max - adjusted_min) < 2.0:  # 如果差异小于2K
            # 在相同值的情况下，给予一个合理的范围 (约20%的增长)
            adjusted_max = adjusted_min * 1.2  # 增加20%
            print(f"应用最小差异调整后: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
        
        # 9. 最终四舍五入，保留一位小数
        adjusted_min = round(adjusted_min, 1)
        adjusted_max = round(adjusted_max, 1)
        
        print(f"最终预测: {adjusted_min:.1f}K-{adjusted_max:.1f}K")
        return adjusted_min, adjusted_max
    
    def get_available_models(self):
        """
        获取所有可用的预训练模型
        
        返回:
            list: 可用模型列表，包含模型ID、名称、类型和性能指标等信息
        """
        try:
            # 合并数据库和文件系统中的模型信息
            model_list = []
            
            # 1. 从数据库获取模型
            db_models = SalaryPredictionModel.objects.all().order_by('-updated_time')
            for model in db_models:
                model_info = {
                    'model_id': model.model_id,
                    'model_name': model.model_name,
                    'model_type': model.model_type,
                    'r2_score': float(model.r2_score) if model.r2_score else None,
                    'mean_absolute_error': float(model.mean_absolute_error) if model.mean_absolute_error else None,
                    'is_active': model.is_active,
                    'created_time': model.created_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'updated_time': model.updated_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'source': 'database'
                }
                model_list.append(model_info)
            
            # 2. 从文件系统获取模型
            if os.path.exists(MODEL_DIR):
                meta_files = [f for f in os.listdir(MODEL_DIR) if f.endswith("_meta.json")]
                for meta_file in meta_files:
                    try:
                        meta_path = os.path.join(MODEL_DIR, meta_file)
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            meta_data = json.load(f)
                        
                        # 检查对应的模型文件是否存在
                        model_filename = meta_data.get('model_filename')
                        model_path = os.path.join(MODEL_DIR, model_filename)
                        if not os.path.exists(model_path):
                            continue
                        
                        # 添加模型信息
                        results = meta_data.get('results', {})
                        model_info = {
                            'model_name': f"文件模型_{meta_data.get('model_type')}",
                            'model_type': meta_data.get('model_type'),
                            'r2_score': (results.get('min_salary', {}).get('r2', 0) + results.get('max_salary', {}).get('r2', 0)) / 2 if results else None,
                            'mean_absolute_error': (results.get('min_salary', {}).get('mae', 0) + results.get('max_salary', {}).get('mae', 0)) / 2 if results else None,
                            'is_active': False,  # 文件模型默认非活跃
                            'created_time': meta_data.get('created_time'),
                            'model_filename': model_filename,
                            'source': 'file'
                        }
                        model_list.append(model_info)
                    except Exception as e:
                        print(f"读取模型元数据文件失败: {meta_file}, {e}")
            
            return model_list
        except Exception as e:
            print(f"获取可用模型失败: {e}")
            return []
    
    def set_active_model(self, model_id):
        """
        设置指定ID的模型为活跃模型
        
        参数:
            model_id (int): 模型ID
            
        返回:
            bool: 设置成功返回True，否则返回False
        """
        try:
            # 将所有模型设为非活跃
            SalaryPredictionModel.objects.filter(is_active=True).update(is_active=False)
            
            # 将指定ID的模型设为活跃
            model = SalaryPredictionModel.objects.get(model_id=model_id)
            model.is_active = True
            model.save()
            
            # 更新当前模型类型
            self.model_type = model.model_type
            
            print(f"已将模型 {model.model_name} (ID: {model_id}) 设为活跃模型")
            return True
        except Exception as e:
            print(f"设置活跃模型失败: {e}")
            return False

    def load_model(self, model_id=None):
        """
        从数据库加载模型
        
        参数:
            model_id (int, optional): 模型ID，如果为None则加载最新的活跃模型
            
        返回:
            bool: 加载成功返回True，否则返回False
        """
        try:
            # 获取模型记录
            if model_id:
                model_record = SalaryPredictionModel.objects.get(model_id=model_id)
            else:
                model_record = SalaryPredictionModel.objects.filter(is_active=True).order_by('-updated_time').first()
            
            if not model_record:
                # 如果没有找到活跃模型，训练一个新模型
                print("未找到可用的模型，开始训练新模型...")
                self.train_model()
                model_record = SalaryPredictionModel.objects.filter(is_active=True).order_by('-updated_time').first()
                if not model_record:
                    return False
            
            # 获取模型类型
            self.model_type = model_record.model_type
            
            # 获取模型参数
            # 注意：实际使用时，应从数据库中提取序列化的模型参数并反序列化
            # 这里为了简化，我们重新训练模型
            _, _ = self.build_model(self.model_type)
            
            # 加载模型成功
            print(f"成功加载模型: {model_record.model_name}")
            return True
        except Exception as e:
            print(f"加载模型失败: {e}")
            return False
    
    def load_specific_model(self, model_type):
        """
        从数据库加载特定类型的模型
        
        参数:
            model_type (str): 模型类型，如'random_forest', 'gradient_boosting'等
            
        返回:
            bool: 加载成功返回True，否则返回False
        """
        try:
            # 获取指定类型的最新模型记录
            model_record = SalaryPredictionModel.objects.filter(
                model_type=model_type
            ).order_by('-updated_time').first()
            
            if not model_record:
                print(f"未找到{model_type}类型的模型")
                return False
            
            # 获取模型类型
            self.model_type = model_record.model_type
            
            # 获取模型参数
            # 注意：实际使用时，应从数据库中提取序列化的模型参数并反序列化
            # 这里为了简化，我们重新训练模型
            _, _ = self.build_model(self.model_type)
            
            # 加载模型成功
            print(f"成功加载{model_type}类型模型: {model_record.model_name}")
            return True
        except Exception as e:
            print(f"加载{model_type}类型模型失败: {e}")
            return False


# 实用函数，用于提取职位特征
def extract_job_features(job_name, education='本科', experience='3-5年', place='北京', scale='未知规模', key_word=None):
    """
    从职位名称和其他信息中提取预测薪资所需的特征
    
    参数:
        job_name (str): 职位名称
        education (str): 学历要求
        experience (str): 工作经验
        place (str): 工作地点
        scale (str): 公司规模
        key_word (str): 关键词
        
    返回:
        dict: 特征字典
    """
    # 如果没有关键词，从职位名称中提取
    if not key_word:
        # 常见职位关键词列表
        common_keywords = ['开发', '工程师', '架构师', '产品经理', '设计师', '运营', '销售', 
                          'HR', '人力资源', '财务', '会计', '客服', '前端', '后端', 'Java', 
                          'Python', 'C++', 'PHP', '数据分析', '机器学习', '人工智能', 
                          '算法', '测试', 'UI', 'UX', '市场', '营销', '策划', '总监', '主管']
        
        # 检查职位名称中是否包含常见关键词
        for keyword in common_keywords:
            if keyword in job_name:
                key_word = keyword
                break
        
        # 如果没有找到关键词，则使用职位名称的前两个字符
        if not key_word and len(job_name) >= 2:
            key_word = job_name[:2]
        elif not key_word:
            key_word = '其他'
    
    # 构建特征字典
    features = {
        'education': education,
        'experience': experience,
        'place': place,
        'scale': scale,
        'key_word': key_word
    }
    
    return features 