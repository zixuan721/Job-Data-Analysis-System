from django.db import migrations

 
class Migration(migrations.Migration):

    dependencies = [
        ('job', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS `user_job_interaction` (
              `interaction_id` int(11) NOT NULL AUTO_INCREMENT,
              `user_id` varchar(11) DEFAULT NULL,
              `job_id` int(11) DEFAULT NULL,
              `rating` int(11) DEFAULT NULL,
              `is_favorite` tinyint(1) NOT NULL DEFAULT '0',
              `created_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
              `updated_time` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
              PRIMARY KEY (`interaction_id`),
              UNIQUE KEY `user_job_unique` (`user_id`,`job_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            "DROP TABLE IF EXISTS `user_job_interaction`;"
        ),
        migrations.AlterModelOptions(
            name='jobdata',
            options={'managed': True, 'verbose_name': '招聘信息', 'verbose_name_plural': '招聘信息'},
        ),
        migrations.AlterModelOptions(
            name='userlist',
            options={'managed': True, 'verbose_name': '前台用户', 'verbose_name_plural': '前台用户'},
        ),
    ] 