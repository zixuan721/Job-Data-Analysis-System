from django.contrib import admin

from job.models import JobData, UserList, UserJobInteraction, SalaryPredictionModel, UserSalaryPrediction

# 后台里面的认证和授权 可以隐藏掉
from django.contrib import admin
from django.contrib.auth.models import User, Group

# 取消注册 User 和 Group 模型
admin.site.unregister(User)
admin.site.unregister(Group)

# 设置管理后台的头部标题
admin.site.site_header = '招聘后台管理'
# 设置管理后台在浏览器标签页中显示的标题
admin.site.site_title = '招聘后台管理'
# 设置管理后台主页的标题
admin.site.index_title = '招聘后台管理'



 

class UserListAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'user_name', 'pass_word')  # 列表中显示的字段
    search_fields = ('user_id', 'user_name')  # 可搜索的字段
    # 设置默认的排序方式，这里按照 id 字段进行排序
    ordering = ['user_id']

admin.site.register(UserList, UserListAdmin)


# Register your models here.
class JobDataAdmin(admin.ModelAdmin):
    list_display = (
    'job_id', 'name', 'salary', 'place', 'education', 'experience', 'company', 'label', 'scale', 'href', 'key_word')
    search_fields = ('name', 'company', 'place')
    list_filter = ('education', 'experience', 'scale')
    # 设置默认的排序方式，这里按照 id 字段进行排序
    ordering = ['job_id']


admin.site.register(JobData, JobDataAdmin)


class UserJobInteractionAdmin(admin.ModelAdmin):
    list_display = ('interaction_id', 'user', 'job', 'rating', 'is_favorite', 'created_time', 'updated_time')  # 列表中显示的字段
    search_fields = ('user__user_id', 'user__user_name', 'job__name')  # 可搜索的字段
    list_filter = ('rating', 'is_favorite')  # 可筛选的字段
    ordering = ['-updated_time']  # 按更新时间降序排序

admin.site.register(UserJobInteraction, UserJobInteractionAdmin)


# 薪资预测模型管理
class SalaryPredictionModelAdmin(admin.ModelAdmin):
    list_display = ('model_id', 'model_name', 'model_type', 'r2_score', 'mean_absolute_error', 'is_active', 'created_time', 'updated_time')
    search_fields = ('model_name', 'model_type')
    list_filter = ('model_type', 'is_active')
    ordering = ['-updated_time']
    readonly_fields = ('model_id', 'created_time', 'updated_time')
    list_editable = ('is_active',)  # 允许直接在列表页修改是否激活

admin.site.register(SalaryPredictionModel, SalaryPredictionModelAdmin)


# 用户薪资预测记录管理
class UserSalaryPredictionAdmin(admin.ModelAdmin):
    list_display = ('prediction_id', 'user', 'position_name', 'education', 'experience', 'city', 
                   'predicted_salary_min', 'predicted_salary_max', 'prediction_date', 'model_used')
    search_fields = ('user__user_name', 'position_name', 'city')
    list_filter = ('education', 'experience', 'model_used__model_type')
    ordering = ['-prediction_date']
    readonly_fields = ('prediction_id', 'prediction_date')

admin.site.register(UserSalaryPrediction, UserSalaryPredictionAdmin)


