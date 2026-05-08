"""JobRecommend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from job import views

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('^$', views.login),
    path('login/', views.login, name="login"),  # 登入
    path('register/', views.register, name="register"),  # 注册
    path('logout/', views.logout, name="logout"),  # 登出
    path('index/', views.index, name="index"),  # 主页
    path('welcome/', views.welcome, name="welcome"),
    path('spiders/', views.spiders, name="spiders"),
    path('start_spider/', views.start_spider, name="start_spider"),  # 启动爬虫接口
    path('job_list/', views.job_list, name="job_list"),
    re_path(r'^get_job_list/$', views.get_job_list, name="get_job_list"),
    path('get_psutil/', views.get_psutil, name="get_psutil"),
    path('get_pie/', views.get_pie, name="get_pie"),
    path('send_job/', views.send_job, name="send_job"),  # 投递或取消
    path('job_expect/', views.job_expect, name="job_expect"),  # 求职意向
    path('get_recommend/', views.get_recommend, name="get_recommend"),  # 职位推荐
    path('send_list/', views.send_list, name="send_list"),  # 已投递列表
    path('send_page/', views.send_page, name="send_page"),  # 已投递列表
    path('pass_page/', views.pass_page, name="pass_page"),
    path('up_info/', views.up_info, name="up_info"),  # 修改信息
    path('salary/', views.salary, name="salary"),
    path('edu/', views.edu, name="edu"),
    path('bar_page/', views.bar_page, name="bar_page"),
    path('bar/', views.bar, name="bar"),
    
    # 新增的用户-职位交互路由
    path('job_rate/', views.job_rate, name="job_rate"),  # 职位评分
    path('toggle_favorite/', views.toggle_favorite, name="toggle_favorite"),  # 切换收藏状态
    path('favorite_jobs/', views.favorite_jobs, name="favorite_jobs"),  # 收藏职位页面
    path('get_favorite_jobs/', views.get_favorite_jobs, name="get_favorite_jobs"),  # 获取收藏职位数据
    
    # 新增的数据可视化路由
    path('data_visualization/', views.data_visualization, name="data_visualization"),  # 数据可视化统一页面
    path('get_chart_data/', views.get_chart_data, name="get_chart_data"),  # 获取图表数据
    
    # 新增的技能热度地图路由
    path('skill_heatmap/', views.skill_heatmap_page, name="skill_heatmap"),  # 技能热度地图页面
    path('get_skill_heatmap_data/', views.get_skill_heatmap_data, name="get_skill_heatmap_data"),  # 获取技能热度地图数据
    
    # 新增的可视化大屏路由
    path('visualization_dashboard/', views.visualization_dashboard, name="visualization_dashboard"),  # 可视化大屏页面
    
    # 新增的薪资预测路由
    path('salary_prediction/', views.salary_prediction_page, name="salary_prediction"),  # 薪资预测页面
    path('train_salary_model/', views.train_salary_model, name="train_salary_model"),  # 训练薪资预测模型
    path('predict_salary/', views.predict_salary, name="predict_salary"),  # 预测薪资
    path('get_prediction_history/', views.get_prediction_history, name="get_prediction_history"),  # 获取预测历史
    path('get_model_info/', views.get_model_info, name="get_model_info"),  # 获取模型信息
    path('get_available_models/', views.get_available_models, name="get_available_models"),  # 获取可用模型列表
    path('set_active_model/', views.set_active_model, name="set_active_model"),  # 设置活跃模型
]
