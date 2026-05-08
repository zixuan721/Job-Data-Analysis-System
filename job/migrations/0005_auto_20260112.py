
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0004_auto_20250601_1217'),
    ]

    operations = [
        # 第一步：创建 salary_prediction_model 表（无外键依赖）
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS `salary_prediction_model` (
              `model_id` int(11) NOT NULL AUTO_INCREMENT,
              `model_name` varchar(255) NOT NULL,
              `model_type` varchar(255) NOT NULL,
              `model_parameters` longtext,
              `feature_importance` longtext,
              `r2_score` double DEFAULT NULL,
              `mean_absolute_error` double DEFAULT NULL,
              `created_time` datetime(6) NOT NULL,
              `updated_time` datetime(6) NOT NULL,
              `is_active` tinyint(1) NOT NULL,
              `min_pipeline` longblob DEFAULT NULL,
              `max_pipeline` longblob DEFAULT NULL,
              PRIMARY KEY (`model_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            "DROP TABLE IF EXISTS `salary_prediction_model`;"
        ),
        
        # 第二步：创建 user_salary_prediction 表（无外键约束）
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS `user_salary_prediction` (
              `prediction_id` int(11) NOT NULL AUTO_INCREMENT,
              `position_name` varchar(255) NOT NULL,
              `education` varchar(255) NOT NULL,
              `experience` varchar(255) NOT NULL,
              `city` varchar(255) NOT NULL,
              `company_scale` varchar(255) DEFAULT NULL,
              `skills` longtext,
              `predicted_salary_min` double NOT NULL,
              `predicted_salary_max` double NOT NULL,
              `prediction_date` datetime(6) NOT NULL,
              `model_used_id` int(11) NOT NULL,
              `user_id` varchar(11) DEFAULT NULL,
              PRIMARY KEY (`prediction_id`),
              KEY `user_salary_prediction_model_used_id` (`model_used_id`),
              KEY `user_salary_prediction_user_id` (`user_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            "DROP TABLE IF EXISTS `user_salary_prediction`;"
        ),
    ]
