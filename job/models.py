# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models





from django.db import models

class JobData(models.Model):
    job_id = models.AutoField('职位ID', primary_key=True)  # 职位ID，自动增长主键
    name = models.CharField('职位名称', max_length=255, blank=True, null=True)  # 职位名称
    salary = models.CharField('薪资', max_length=255, blank=True, null=True)  # 薪资
    place = models.CharField('工作地点', max_length=255, blank=True, null=True)  # 工作地点
    education = models.CharField('学历要求', max_length=255, blank=True, null=True)  # 学历要求
    experience = models.CharField('工作经验', max_length=255, blank=True, null=True)  # 工作经验
    company = models.CharField('公司名称', max_length=255, blank=True, null=True)  # 公司名称
    label = models.CharField('职位标签', max_length=255, blank=True, null=True)  # 职位标签
    scale = models.CharField('公司规模', max_length=255, blank=True, null=True)  # 公司规模
    href = models.CharField('职位链接', max_length=255, blank=True, null=True)  # 职位链接
    key_word = models.CharField('关键词', max_length=255, blank=True, null=True)  # 关键词

    class Meta:
        managed = True  # 是否由Django管理
        db_table = 'job_data'  # 数据库表名
        verbose_name = "招聘信息"
        verbose_name_plural = "招聘信息"


class SendList(models.Model):
    send_id = models.AutoField(primary_key=True)
    job = models.ForeignKey(JobData, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('UserList', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'send_list'


class SpiderInfo(models.Model):
    spider_id = models.AutoField(primary_key=True)
    spider_name = models.CharField(max_length=255, blank=True, null=True)
    count = models.IntegerField(blank=True, null=True)
    page = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'spider_info'


class UserExpect(models.Model):
    expect_id = models.AutoField(primary_key=True)
    key_word = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey('UserList', models.DO_NOTHING, blank=True, null=True)
    place = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'user_expect'



class UserList(models.Model):
    user_id = models.CharField('用户ID', primary_key=True, max_length=11)  # 用户ID，主键
    user_name = models.CharField('用户名', max_length=255, blank=True, null=True)  # 用户名
    pass_word = models.CharField('密码', max_length=255, blank=True, null=True)  # 密码

    class Meta:
        managed = True  # 是否由Django管理
        db_table = 'user_list'  # 数据库表名
        verbose_name = "前台用户"
        verbose_name_plural = "前台用户"


class UserJobInteraction(models.Model):
    interaction_id = models.AutoField('交互ID', primary_key=True)  # 交互ID，自动增长主键
    user = models.ForeignKey('UserList', models.CASCADE, blank=True, null=True, verbose_name='用户')  # 用户外键
    job = models.ForeignKey(JobData, models.CASCADE, blank=True, null=True, verbose_name='职位')  # 职位外键
    rating = models.IntegerField('评分', blank=True, null=True)  # 用户对职位的评分（1-5星）
    is_favorite = models.BooleanField('是否收藏', default=False)  # 是否被用户收藏
    created_time = models.DateTimeField('创建时间', auto_now_add=True)  # 记录创建时间
    updated_time = models.DateTimeField('更新时间', auto_now=True)  # 记录更新时间

    class Meta:
        managed = True  # 是否由Django管理
        db_table = 'user_job_interaction'  # 数据库表名
        verbose_name = "用户职位交互"
        verbose_name_plural = "用户职位交互"
        unique_together = ('user', 'job')  # 确保每个用户对每个职位只有一条交互记录


class SalaryPredictionModel(models.Model):
    """
    薪资预测模型参数存储
    用于存储训练好的薪资预测模型参数
    """
    model_id = models.AutoField('模型ID', primary_key=True)  # 模型ID，自动增长主键
    model_name = models.CharField('模型名称', max_length=255)  # 模型名称
    model_type = models.CharField('模型类型', max_length=255)  # 模型类型（如线性回归、随机森林等）
    model_parameters = models.TextField('模型参数', blank=True, null=True)  # 模型参数，JSON格式存储
    feature_importance = models.TextField('特征重要性', blank=True, null=True)  # 特征重要性，JSON格式存储
    r2_score = models.FloatField('R2得分', blank=True, null=True)  # 模型R2得分
    mean_absolute_error = models.FloatField('平均绝对误差', blank=True, null=True)  # 平均绝对误差
    created_time = models.DateTimeField('创建时间', auto_now_add=True)  # 记录创建时间
    updated_time = models.DateTimeField('更新时间', auto_now=True)  # 记录更新时间
    is_active = models.BooleanField('是否激活', default=True)  # 是否是当前激活的模型
    # 添加二进制字段存储序列化模型
    min_pipeline = models.BinaryField('最低薪资预测模型', blank=True, null=True)  # 序列化的最低薪资预测模型
    max_pipeline = models.BinaryField('最高薪资预测模型', blank=True, null=True)  # 序列化的最高薪资预测模型

    class Meta:
        managed = True  # 是否由Django管理
        db_table = 'salary_prediction_model'  # 数据库表名
        verbose_name = "薪资预测模型"
        verbose_name_plural = "薪资预测模型"


class UserSalaryPrediction(models.Model):
    """
    用户薪资预测记录
    记录用户进行的薪资预测历史
    """
    prediction_id = models.AutoField('预测ID', primary_key=True)  # 预测ID，自动增长主键
    user = models.ForeignKey('UserList', models.CASCADE, blank=True, null=True, verbose_name='用户')  # 用户外键
    position_name = models.CharField('职位名称', max_length=255)  # 职位名称
    education = models.CharField('学历', max_length=255)  # 学历
    experience = models.CharField('工作经验', max_length=255)  # 工作经验
    city = models.CharField('城市', max_length=255)  # 城市
    company_scale = models.CharField('公司规模', max_length=255, blank=True, null=True)  # 公司规模
    skills = models.TextField('技能要求', blank=True, null=True)  # 技能要求
    predicted_salary_min = models.FloatField('预测最低薪资')  # 预测最低薪资
    predicted_salary_max = models.FloatField('预测最高薪资')  # 预测最高薪资
    prediction_date = models.DateTimeField('预测日期', auto_now_add=True)  # 预测日期
    model_used = models.ForeignKey('SalaryPredictionModel', models.CASCADE, verbose_name='使用的模型')  # 使用的模型

    class Meta:
        managed = True  # 是否由Django管理
        db_table = 'user_salary_prediction'  # 数据库表名
        verbose_name = "用户薪资预测"
        verbose_name_plural = "用户薪资预测"