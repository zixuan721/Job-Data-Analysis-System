
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0006_auto_20250601_1254'),
    ]

    operations = [
        migrations.RunSQL(
            """
            DROP TABLE IF EXISTS `salary_prediction_model`;
            CREATE TABLE `salary_prediction_model` (
              `model_id` int(11) NOT NULL AUTO_INCREMENT,
              `model_name` varchar(255) NOT NULL,
              `model_type` varchar(255) NOT NULL,
              `model_parameters` longtext,
              `feature_importance` longtext,
              `r2_score` double DEFAULT NULL,
              `mean_absolute_error` double DEFAULT NULL,
              `created_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
              `updated_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
              `is_active` tinyint(1) NOT NULL DEFAULT 0,
              `min_pipeline` longblob DEFAULT NULL,
              `max_pipeline` longblob DEFAULT NULL,
              PRIMARY KEY (`model_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            "DROP TABLE IF EXISTS `salary_prediction_model`;"
        ),
        migrations.RunSQL(
            """
            DROP TABLE IF EXISTS `user_salary_prediction`;
            CREATE TABLE `user_salary_prediction` (
              `prediction_id` int(11) NOT NULL AUTO_INCREMENT,
              `position_name` varchar(255) NOT NULL,
              `education` varchar(255) NOT NULL,
              `experience` varchar(255) NOT NULL,
              `city` varchar(255) NOT NULL,
              `company_scale` varchar(255) DEFAULT NULL,
              `skills` longtext,
              `predicted_salary_min` double NOT NULL,
              `predicted_salary_max` double NOT NULL,
              `prediction_date` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
              `model_used_id` int(11) NOT NULL,
              `user_id` varchar(11) DEFAULT NULL,
              PRIMARY KEY (`prediction_id`),
              KEY `model_used_id_index` (`model_used_id`),
              KEY `user_id_index` (`user_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            "DROP TABLE IF EXISTS `user_salary_prediction`;"
        ),
    ]
