
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0002_create_user_job_interaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalaryPredictionModel',
            fields=[
                ('model_id', models.AutoField(primary_key=True, serialize=False, verbose_name='模型ID')),
                ('model_name', models.CharField(max_length=255, verbose_name='模型名称')),
                ('model_type', models.CharField(max_length=255, verbose_name='模型类型')),
                ('model_parameters', models.TextField(blank=True, null=True, verbose_name='模型参数')),
                ('feature_importance', models.TextField(blank=True, null=True, verbose_name='特征重要性')),
                ('r2_score', models.FloatField(blank=True, null=True, verbose_name='R2得分')),
                ('mean_absolute_error', models.FloatField(blank=True, null=True, verbose_name='平均绝对误差')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
            ],
            options={
                'verbose_name': '薪资预测模型',
                'verbose_name_plural': '薪资预测模型',
                'db_table': 'salary_prediction_model',
                'managed': True,
            },
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='company',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='公司名称'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='education',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='学历要求'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='experience',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='工作经验'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='href',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='职位链接'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='job_id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='职位ID'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='key_word',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='关键词'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='label',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='职位标签'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='职位名称'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='place',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='工作地点'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='salary',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='薪资'),
        ),
        migrations.AlterField(
            model_name='jobdata',
            name='scale',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='公司规模'),
        ),
        migrations.AlterField(
            model_name='userlist',
            name='pass_word',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='密码'),
        ),
        migrations.AlterField(
            model_name='userlist',
            name='user_id',
            field=models.CharField(max_length=11, primary_key=True, serialize=False, verbose_name='用户ID'),
        ),
        migrations.AlterField(
            model_name='userlist',
            name='user_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='用户名'),
        ),
        migrations.CreateModel(
            name='UserSalaryPrediction',
            fields=[
                ('prediction_id', models.AutoField(primary_key=True, serialize=False, verbose_name='预测ID')),
                ('position_name', models.CharField(max_length=255, verbose_name='职位名称')),
                ('education', models.CharField(max_length=255, verbose_name='学历')),
                ('experience', models.CharField(max_length=255, verbose_name='工作经验')),
                ('city', models.CharField(max_length=255, verbose_name='城市')),
                ('company_scale', models.CharField(blank=True, max_length=255, null=True, verbose_name='公司规模')),
                ('skills', models.TextField(blank=True, null=True, verbose_name='技能要求')),
                ('predicted_salary_min', models.FloatField(verbose_name='预测最低薪资')),
                ('predicted_salary_max', models.FloatField(verbose_name='预测最高薪资')),
                ('prediction_date', models.DateTimeField(auto_now_add=True, verbose_name='预测日期')),
                ('model_used', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='job.salarypredictionmodel', verbose_name='使用的模型')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='job.userlist', verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户薪资预测',
                'verbose_name_plural': '用户薪资预测',
                'db_table': 'user_salary_prediction',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='UserJobInteraction',
            fields=[
                ('interaction_id', models.AutoField(primary_key=True, serialize=False, verbose_name='交互ID')),
                ('rating', models.IntegerField(blank=True, null=True, verbose_name='评分')),
                ('is_favorite', models.BooleanField(default=False, verbose_name='是否收藏')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='job.jobdata', verbose_name='职位')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='job.userlist', verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户职位交互',
                'verbose_name_plural': '用户职位交互',
                'db_table': 'user_job_interaction',
                'managed': True,
                'unique_together': {('user', 'job')},
            },
        ),
    ]
