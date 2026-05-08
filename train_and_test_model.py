#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
薪资预测模型训练和测试脚本

此脚本用于训练薪资预测模型并测试其预测效果。
可以训练不同类型的模型，包括随机森林、梯度提升、岭回归等，并比较它们的性能。
"""

import sys
import io 
import os
import time
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score

# 强制使用 UTF-8 编码
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"  # 强制 Python 使用 UTF-8


# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JobRecommend.settings')
import django
django.setup()

# 导入薪资预测器
from job.salary_prediction import SalaryPredictor, extract_job_features

def train_models():
    """
    训练不同类型的薪资预测模型并评估它们的性能
    """
    print("=" * 80)
    print("开始训练薪资预测模型")
    print("=" * 80)
    
    models = {}
    
    # 训练随机森林模型
    print("\n训练随机森林模型...")
    rf_predictor = SalaryPredictor()
    rf_results = rf_predictor.train_model(model_type='random_forest', save_model=True, model_params={
        'n_estimators': 300,
        'max_depth': 20,
        'min_samples_split': 5,
        'min_samples_leaf': 2
    })
    models['随机森林'] = rf_results
    
    # 训练梯度提升模型
    print("\n训练梯度提升模型...")
    gb_predictor = SalaryPredictor()
    gb_results = gb_predictor.train_model(model_type='gradient_boosting', save_model=True, model_params={
        'n_estimators': 300,
        'learning_rate': 0.05,
        'max_depth': 6,
        'subsample': 0.8
    })
    models['梯度提升'] = gb_results
    
    # 训练岭回归模型
    print("\n训练岭回归模型...")
    ridge_predictor = SalaryPredictor()
    ridge_results = ridge_predictor.train_model(model_type='ridge', save_model=True, model_params={
        'alpha': 1.0
    })
    models['岭回归'] = ridge_results
    
    # 打印评估结果
    print("\n" + "=" * 80)
    print("模型评估结果对比")
    print("=" * 80)
    
    print("\n最低薪资预测 (原始空间):")
    print(f"{'模型类型':<10} | {'MAE':<10} | {'R²':<10}")
    print("-" * 35)
    for model_name, results in models.items():
        mae = results['min_salary']['mae_orig']
        r2 = results['min_salary']['r2_orig']
        print(f"{model_name:<10} | {mae:<10.4f} | {r2:<10.4f}")
    
    print("\n最高薪资预测 (原始空间):")
    print(f"{'模型类型':<10} | {'MAE':<10} | {'R²':<10}")
    print("-" * 35)
    for model_name, results in models.items():
        mae = results['max_salary']['mae_orig']
        r2 = results['max_salary']['r2_orig']
        print(f"{model_name:<10} | {mae:<10.4f} | {r2:<10.4f}")
    
    # 返回最佳模型类型
    best_model = max(models.items(), key=lambda x: (x[1]['min_salary']['r2_orig'] + x[1]['max_salary']['r2_orig']) / 2)
    print(f"\n最佳模型: {best_model[0]}")
    
    return best_model[0]

def test_predictions():
    """
    测试薪资预测效果
    """
    print("\n" + "=" * 80)
    print("测试薪资预测效果")
    print("=" * 80)
    
    # 创建薪资预测器
    predictor = SalaryPredictor()
    
    # 测试案例
    test_cases = [
        {
            'name': 'Python数据分析师（实习）',
            'education': '大专',
            'experience': '实习',
            'place': '北京',
            'scale': '中型企业',
            'key_word': 'Python'
        },
        {
            'name': 'Python数据分析师（应届生）',
            'education': '本科',
            'experience': '应届生',
            'place': '北京',
            'scale': '中型企业',
            'key_word': 'Python'
        },
        {
            'name': 'Python数据分析师（1-3年）',
            'education': '本科',
            'experience': '1-3年',
            'place': '北京',
            'scale': '中型企业',
            'key_word': 'Python'
        },
        {
            'name': 'Java后端开发工程师（实习）',
            'education': '本科',
            'experience': '实习',
            'place': '上海',
            'scale': '大型企业',
            'key_word': 'Java'
        },
        {
            'name': 'Java后端开发工程师（应届生）',
            'education': '本科',
            'experience': '应届生',
            'place': '上海',
            'scale': '大型企业',
            'key_word': 'Java'
        },
        {
            'name': 'Java后端开发工程师（1-3年）',
            'education': '本科',
            'experience': '1-3年',
            'place': '上海',
            'scale': '大型企业',
            'key_word': 'Java'
        },
        {
            'name': '前端开发工程师（实习）',
            'education': '大专',
            'experience': '实习',
            'place': '杭州',
            'scale': '中小企业',
            'key_word': '前端'
        },
        {
            'name': '前端开发工程师（应届生）',
            'education': '本科',
            'experience': '应届生',
            'place': '杭州',
            'scale': '中小企业',
            'key_word': '前端'
        },
        {
            'name': '前端开发工程师（1-3年）',
            'education': '本科',
            'experience': '1-3年',
            'place': '杭州',
            'scale': '中小企业',
            'key_word': '前端'
        },
        {
            'name': '高级Java架构师',
            'education': '本科',
            'experience': '5-10年',
            'place': '北京',
            'scale': '大型企业',
            'key_word': 'Java'
        },
        {
            'name': '资深Python工程师',
            'education': '硕士',
            'experience': '5-10年',
            'place': '上海',
            'scale': '大型企业',
            'key_word': 'Python'
        },
        {
            'name': '测试工程师（实习）',
            'education': '大专',
            'experience': '实习',
            'place': '成都',
            'scale': '中型企业',
            'key_word': '测试'
        }
    ]
    
    # 打印表头
    print(f"\n{'职位名称':<25} | {'原始预测':<15} | {'调整后预测':<15}")
    print("-" * 60)
    
    # 对每个测试案例进行预测
    for case in test_cases:
        # 原始预测（不应用手动调整）
        raw_min, raw_max = predictor.predict(case, apply_manual_adjustment=False)
        
        # 调整后预测（应用手动调整）
        adj_min, adj_max = predictor.predict(case, apply_manual_adjustment=True)
        
        # 打印结果
        print(f"{case['name']:<25} | {raw_min:.1f}-{raw_max:.1f}K | {adj_min:.1f}-{adj_max:.1f}K")
    
    print("\n注: 调整后预测应用了手动调整规则，使预测结果更符合实际情况。")

if __name__ == "__main__":
    start_time = time.time()
    
    # 训练模型
    best_model = train_models()
    
    # 测试预测
    test_predictions()
    
    end_time = time.time()
    print(f"\n总耗时: {end_time - start_time:.2f} 秒") 