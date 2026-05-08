from django.apps import AppConfig
import os
 

class JobConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'job'
    verbose_name = '信息管理'
    
    def ready(self):
        """
        当 Django 启动时自动执行
        用于创建必要的目录和初始化资源
        """
        # 创建模型保存目录
        model_dir = os.path.join('job', 'models')
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
            print(f"已创建模型保存目录: {model_dir}")
            
        # 可以在这里添加其他初始化操作
        # 例如：检查默认模型是否存在等