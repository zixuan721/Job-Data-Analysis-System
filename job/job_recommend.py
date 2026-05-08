#!/usr/bin/python3.9.10
# -*- coding: utf-8 -*-
# @Time    : 2023/2/18 9:41
# @File    : job_recommend.py
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "JobRecommend.settings"
import django

django.setup()
from job import models
from math import sqrt, pow
import operator
from django.db.models import Subquery, Q, Count
import random


# 计算相似度
def similarity(job1_id, job2_id):
    job1_set = models.SendList.objects.filter(job=job1_id)
    # job1的投递用户数
    job1_sum = job1_set.count()
    # job2的打分用户数
    job2_sum = models.SendList.objects.filter(job=job2_id).count()
    # 两者的交集
    common = models.SendList.objects.filter(user__in=Subquery(job1_set.values('user')), job=job2_id).values(
        'user').count()
    # 没有人投递当前职位
    if job1_sum == 0 or job2_sum == 0:
        return 0
    similar_value = common / sqrt(job1_sum * job2_sum)  # 余弦计算相似度
    return similar_value


# 基于物品
def recommend_by_item_id(user_id, k=9):
    # 检查用户ID是否为空
    if not user_id:
        # 用户未登录，返回随机推荐
        job_list = list(models.JobData.objects.all().values())  # 从全部的职位中选
        try:
            job_list = random.sample(job_list, k)
        except ValueError:
            # 如果职位数量不足k个，返回所有职位
            job_list = job_list[:]
        return job_list
    
    # 确保user_id是字符串类型
    user_id = str(user_id)
    print(f"正在为用户ID: {user_id} (类型: {type(user_id)}) 生成推荐")
        
    # 检查用户是否存在
    try:
        current_user = models.UserList.objects.get(user_id=user_id)
        print(f"找到用户: {current_user.user_name}")
    except models.UserList.DoesNotExist:
        # 用户不存在，返回随机推荐
        print(f"用户ID {user_id} 在数据库中不存在")
        job_list = list(models.JobData.objects.all().values())  # 从全部的职位中选
        try:
            job_list = random.sample(job_list, k)
        except ValueError:
            # 如果职位数量不足k个，返回所有职位
            job_list = job_list[:]
        return job_list
    
    # 投递简历最多的前三keyword
    jobs_id = models.SendList.objects.filter(user_id=user_id).values('job_id')  # 先找出用户投过的简历
    print(f"用户 {user_id} 投递的职位数量: {len(jobs_id)}")
    
    key_word_list = []  # 找出用户投递的职位关键字
    for job in jobs_id:
        key_word_list.append(models.JobData.objects.get(job_id=job['job_id']).key_word)
    # print(key_word_list)
    key_word_list_1 = list(set(key_word_list))
    user_prefer = []
    for key_word in key_word_list_1:
        user_prefer.append([key_word, key_word_list.count(key_word)])
    user_prefer = sorted(user_prefer, key=lambda x: x[1], reverse=True)  # 排序
    user_prefer = [x[0] for x in user_prefer[0:3]]  # 找出最多的3个投递简历的key_word
    # print(user_prefer)
    
    # 如果当前用户没有投递过简历,则看是否选择过意向职位，选过的话，就从意向中找，没选过就随机推荐
    if current_user.sendlist_set.count() == 0:
        print(f"用户 {user_id} 没有投递过简历")
        if current_user.userexpect_set.count() != 0:
            print(f"用户 {user_id} 有设置职位意向")
            user_expect = list(models.UserExpect.objects.filter(user=user_id).values("key_word", "place"))[0]
            # print(user_expect)
            job_list = list(models.JobData.objects.filter(name__icontains=user_expect['key_word'],
                                                          place__icontains=user_expect['place']).values())  # 从用户设置的意向中选
            try:
                job_list = random.sample(job_list, k)
            except ValueError:
                job_list = job_list[:]  # 或者其他适当的处理方式
                print(f"从意向中选择的职位数量不足 {k} 个，返回全部 {len(job_list)} 个")
        else:
            print(f"用户 {user_id} 没有设置职位意向，返回随机推荐")
            job_list = list(models.JobData.objects.all().values())  # 从全部的职位中选
            try:
                job_list = random.sample(job_list, k)
            except ValueError:
                job_list = job_list[:]  # 或者其他适当的处理方式
        # print('from here')
        # print(job_list)
        return job_list
    # # most_tags = Tags.objects.annotate(tags_sum=Count('name')).order_by('-tags_sum').filter(movie__rate__user_id=user_id).order_by('-tags_sum')
    # 选用户投递简历最多的职位的标签，再随机选择30个没有投递过的简历的职位，计算距离最近
    print(f"用户 {user_id} 有投递简历，使用基于物品的协同过滤")
    un_send = list(
        models.JobData.objects.filter(~Q(sendlist__user=user_id), key_word__in=user_prefer).order_by('?').values())[
              :30]  # 没有投过的简历
    # un_send = random.sample(un_send, 30)
    # print(un_send)
    send = []  # 找出用户投递的职位关键字
    for job in jobs_id:
        send.append(models.JobData.objects.filter(job_id=job['job_id']).values()[0])
    # print(send)
    distances = []
    names = []
    # 在未投过的简历的职位中找到
    for un_send_job in un_send:
        for send_job in send:
            if un_send_job not in names:
                names.append(un_send_job)
                distances.append((similarity(un_send_job['job_id'], send_job['job_id']) * send_job['job_id'],
                                  un_send_job))  # 加入相似的职位列表
    distances.sort(key=lambda x: x[0], reverse=True)
    # print('this is distances', distances[:15])
    recommend_list = []
    for mark, job in distances:
        if len(recommend_list) >= k:
            break
        if job not in recommend_list:
            recommend_list.append(job)
    # print('this is recommend list', recommend_list)
    # 如果得不到有效数量的推荐 按照未投递的简历中的职位进行填充
    # print('recommend list', recommend_list)
    print(f"为用户 {user_id} 生成了 {len(recommend_list)} 个推荐职位")
    return recommend_list


if __name__ == '__main__':
    # similarity(2003, 2008)
    recommend_by_item_id(1)
