from django.shortcuts import render, redirect
from django.http import JsonResponse
# Create your views here.
from job import models
import re
from psutil import *
from numpy import *
from job import tools
from job import job_recommend
from django.db import connection
from job import salary_prediction
import json
from django.views.decorators.csrf import csrf_exempt
import os  # 添加os模块导入

spider_code = 0  # 定义全局变量，用来识别爬虫的状态，0空闲，1繁忙

# 创建薪资预测器实例
salary_predictor = salary_prediction.SalaryPredictor()

# python manage.py inspectdb > job/models.py
# 使用此命令可以将数据库表导入models生成数据模型


def login(request):
    if request.method == "POST":
        user = request.POST.get('user')
        pass_word = request.POST.get('password')
        
        # 确保user是字符串类型
        user = str(user)
        print(f'登录用户ID: {user} (类型: {type(user)})')
        
        users_list = list(models.UserList.objects.all().values("user_id"))
        users_id = [str(x['user_id']) for x in users_list]  # 确保列表中的ID也是字符串
        print(f'数据库中的用户ID列表: {users_id}')
        
        ret = models.UserList.objects.filter(user_id=user, pass_word=pass_word)
        if user not in users_id:
            return JsonResponse({'code': 1, 'msg': '该账号不存在！'})
        elif ret:
            # 有此用户 -->> 跳转到首页
            # 登录成功后，将用户名和昵称保存到session 中，
            request.session['user_id'] = user  # 存储字符串类型的用户ID
            user_obj = ret.last()
            if user_obj:  # 检查用户对象是否存在
                user_name = user_obj.user_name
                request.session['user_name'] = user_name
                # 显式保存会话，确保数据被立即写入
                request.session.save()
                print(f'登录成功，用户ID: {user}, 用户名: {user_name}')
                return JsonResponse({'code': 0, 'msg': '登录成功！', 'user_name': user_name})
        else:
            return JsonResponse({'code': 1, 'msg': '密码错误！'})
    else:
        return render(request, "login.html")


def register(request):
    if request.method == "POST":
        user = request.POST.get('user')
        pass_word = request.POST.get('password')
        
        # 确保user是字符串类型
        user = str(user)
        print(f'注册用户ID: {user} (类型: {type(user)})')
        
        users_list = list(models.UserList.objects.all().values("user_id"))
        users_id = [str(x['user_id']) for x in users_list]  # 确保列表中的ID也是字符串
        print(f'数据库中的用户ID列表: {users_id}')
        
        if user in users_id:
            return JsonResponse({'code': 1, 'msg': '该账号已存在！'})
        else:
            # 使用用户名作为显示名称
            user_name = user
            models.UserList.objects.create(user_id=user, user_name=user_name, pass_word=pass_word)
            request.session['user_id'] = user  # 存储字符串类型的用户ID
            request.session['user_name'] = user_name
            # 显式保存会话，确保数据被立即写入
            request.session.save()
            print(f'注册成功，用户ID: {user}, 用户名: {user_name}')
            return JsonResponse({'code': 0, 'msg': '注册成功！'})
    else:
        return render(request, "register.html")


# 退出(登出)
def logout(request):
    # 1. 将session中的用户名、昵称删除
    request.session.flush()
    # 2. 重定向到 登录界面
    return redirect('login')


def index(request):
    """此函数用于返回主页，主页包括头部，左侧菜单"""
    # 检查用户是否已登录
    if 'user_id' not in request.session or 'user_name' not in request.session:
        # 如果会话中没有用户信息，重定向到登录页面
        print("用户未登录或会话已过期，重定向到登录页面")
        return redirect('login')
    
    # 打印当前会话中的用户信息，用于调试
    print(f"访问首页，当前用户ID: {request.session.get('user_id')}, 用户名: {request.session.get('user_name')}")
    
    return render(request, "index.html")


def welcome(request):
    """此函数用于处理控制台页面"""
    # 检查用户是否已登录
    if 'user_id' not in request.session or 'user_name' not in request.session:
        # 如果会话中没有用户信息，重定向到登录页面
        print("访问控制台页面时，用户未登录或会话已过期，重定向到登录页面")
        return redirect('login')
    
    # 获取当前用户信息
    user_id = request.session.get('user_id')
    user_name = request.session.get('user_name')
    print(f"访问控制台页面，当前用户ID: {user_id}, 用户名: {user_name}")
    
    job_data = models.JobData.objects.all().values()  # 查询所有的职位信息
    all_job = len(job_data)  # 职位信息总数
    list_1 = []  # 定义一个空列表
    for job in list(job_data):  # 使用循环处理最高哦薪资
        try:  # 使用try...except检验最高薪资的提取，如果提取不到则加入0
            salary_1 = float(re.findall(r'-(\d+)k', job['salary'])[0])  # 使用正则提取最高薪资
            job['salary_1'] = salary_1  # 添加一个最高薪资
            list_1.append(salary_1)  # 把最高薪资添加到list_1用来计算平均薪资
        except Exception as e:
            # print(e)
            job['salary_1'] = 0
            list_1.append(0)
    job_data = sorted(list(job_data), key=lambda x: x['salary_1'], reverse=True)  # 反向排序所有职位信息的最高薪资
    # print(job_data)
    job_data_10 = job_data[0:10]  # 取最高薪资前10用来渲染top—10表格
    # print(job_data[0:10])
    job_data_1 = job_data[0]  # 取出最高薪资的职位信息
    mean_salary = int(mean(list_1))  # 计算平均薪资
    spider_info = models.SpiderInfo.objects.filter(spider_id=1).first()  # 查询爬虫程序运行的数据记录
    # print(spider_info)
    return render(request, "welcome.html", locals())


def spiders(request):
    global spider_code
    # print(spider_code)
    spider_code_1 = spider_code
    return render(request, "spiders.html", locals())


def start_spider(request):
    if request.method == "POST":
        key_word = request.POST.get("key_word")
        city = request.POST.get("city")
        page = request.POST.get("page")
        role = request.POST.get("role")
        spider_code = 1  # 改变爬虫状态
        spider_model = models.SpiderInfo.objects.filter(spider_id=1).first()
        # print(spider_model)
        spider_model.count += 1  # 给次数+1
        spider_model.page += int(page)  # 给爬取页数加上选择的页数
        spider_model.save()
        if role == '猎聘网':
            # print(key_word,city,page)
            spider_code = tools.lieSpider(key_word=key_word, city=city, all_page=page)
        return JsonResponse({"code": 0, "msg": "爬取完毕!"})
    else:
        return JsonResponse({"code": 1, "msg": "请使用POST请求"})


def job_list(request):
    return render(request, "job_list.html", locals())


def get_job_list(request):
    """此函数用来渲染职位信息列表"""
    page = int(request.GET.get("page", ""))  # 获取请求地址中页码
    limit = int(request.GET.get("limit", ""))  # 获取请求地址中的每页数据数量
    keyword = request.GET.get("keyword", "")
    price_min = request.GET.get("price_min", "")
    price_max = request.GET.get("price_max", "")
    edu = request.GET.get("edu", "")
    city = request.GET.get("city", "")
    job_data_list = list(models.JobData.objects.filter(name__icontains=keyword, education__icontains=edu,
                                                       place__icontains=city).values())  # 查询所有的职位信息
    job_data = []
    if price_min != "" or price_max != "":
        for job in job_data_list:
            try:
                salary_1 = '薪资' + job['salary']
                max_salary = float(re.findall(r'-(\d+)k', salary_1)[0])  # 使用正则提取最高薪资
                min_salary = float(re.findall(r'薪资(\d+)', salary_1)[0])  # 使用正则提取最低薪资
                if price_min == "" and price_max != "":
                    if max_salary <= float(price_max):
                        job_data.append(job)
                elif price_min != "" and price_max == "":
                    if min_salary >= float(price_min):
                        job_data.append(job)
                else:
                    if min_salary >= float(price_min) and float(price_max) >= max_salary:
                        job_data.append(job)
            except Exception as e:  # 如果筛选不出就跳过
                continue
    else:
        job_data = job_data_list
    job_data_1 = job_data[(page - 1) * limit:limit * page]
    
    # 获取当前用户ID
    user_id = request.session.get("user_id")
    
    for job in job_data_1:
        # 检查是否已投递
        job['send_key'] = 1 if models.SendList.objects.filter(user_id=user_id, job_id=job['job_id']).exists() else 0
        
        # 使用原生SQL获取收藏状态和评分
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT rating, is_favorite FROM user_job_interaction 
                WHERE user_id = %s AND job_id = %s
            """, [user_id, job['job_id']])
            
            interaction = cursor.fetchone()
            
            if interaction:
                job['rating'] = interaction[0] if interaction[0] else 0
                job['is_favorite'] = 1 if interaction[1] else 0  # 将布尔值转换为整数，与get_job_list函数保持一致
            else:
                job['rating'] = 0
                job['is_favorite'] = 0  # 使用整数0而不是布尔值
    
    # print(job_data_1)
    if len(job_data) == 0 or len(job_data_list) == 0:
        return JsonResponse(
            {"code": 1, "msg": "没找到需要查询的数据！", "count": "{}".format(len(job_data)), "data": job_data_1})
    return JsonResponse({"code": 0, "msg": "success", "count": "{}".format(len(job_data)), "data": job_data_1})


def get_psutil(request):
    """此函数用于读取cpu使用率和内存占用率"""
    # cpu_percent()可以获取cpu的使用率，参数interval是获取的间隔
    # virtual_memory()[2]可以获取内存的使用率
    return JsonResponse({'cpu_data': cpu_percent(interval=1), 'memory_data': virtual_memory()[2]})


def get_pie(request):
    """此函数用于渲染控制台饼图的数据,要求学历的数据和薪资待遇的数据"""
    edu_list = ['博士', '硕士', '本科', '大专', '不限']
    edu_data = []
    for edu in edu_list:
        edu_count = len(models.JobData.objects.filter(education__icontains=edu))  # 使用for循环，查询字段education包含这些学历的职位信息
        edu_data.append({'name': edu, "value": edu_count})  # 添加到学历的数据列表中
    # print(edu_data)
    list_5 = []
    list_10 = []
    list_15 = []
    list_20 = []
    list_30 = []
    list_50 = []
    list_51 = []
    job_data = models.JobData.objects.all().values()  # 查询所有的职位信息
    for job in list(job_data):
        try:
            salary_1 = float(re.findall(r'-(\d+)k', job['salary'])[0])  # 提取薪资待遇的最高薪资要求
            if salary_1 <= 5:  # 小于5K则加入list_5
                list_5.append(salary_1)
            elif 10 >= salary_1 > 5:  # 在5K和10K之间，加入list_10
                list_10.append(salary_1)
            elif 15 >= salary_1 > 10:  # 10K-15K加入list_15
                list_15.append(salary_1)
            elif 20 >= salary_1 > 15:  # 15K-20K加入list_20
                list_20.append(salary_1)
            elif 30 >= salary_1 > 20:  # 20K-30K 加list_30
                list_30.append(salary_1)
            elif 50 >= salary_1 > 30:  # 30K-50K加入list_50
                list_50.append(salary_1)
            elif salary_1 > 50:  # 大于50K加入list_51
                list_51.append(salary_1)
        except Exception as e:
            job['salary_1'] = 0
    salary_data = [{'name': '5K及以下', 'value': len(list_5)},  # 生成薪资待遇各个阶段的数据字典，value是里面职位信息的数量
                   {'name': '5-10K', 'value': len(list_10)},
                   {'name': '10K-15K', 'value': len(list_15)},
                   {'name': '15K-20K', 'value': len(list_20)},
                   {'name': '20K-30K', 'value': len(list_30)},
                   {'name': '30-50K', 'value': len(list_50)},
                   {'name': '50K以上', 'value': len(list_51)}]
    # print(edu_data)
    return JsonResponse({'edu_data': edu_data, 'salary_data': salary_data})


def send_job(request):
    """此函数用于投递职位和取消投递"""
    if request.method == "POST":
        user_id = request.session.get("user_id")
        job_id = request.POST.get("job_id")
        send_key = request.POST.get("send_key")
        
        # 确保user_id是字符串类型
        user_id = str(user_id)
        
        if int(send_key) == 1:
            models.SendList.objects.filter(user_id=user_id, job_id=job_id).delete()
            print(f"用户 {user_id} 取消投递职位 {job_id}")
        else:
            models.SendList.objects.create(user_id=user_id, job_id=job_id)
            print(f"用户 {user_id} 投递职位 {job_id}")
        return JsonResponse({"Code": 0, "msg": "操作成功"})


def job_expect(request):
    if request.method == "POST":
        job_name = request.POST.get("key_word")
        city = request.POST.get("city")
        
        # 获取用户ID并确保是字符串类型
        user_id = str(request.session.get("user_id"))
        
        ret = models.UserExpect.objects.filter(user=user_id)
        # print(ret)
        if ret:
            ret.update(key_word=job_name, place=city)
            print(f"用户 {user_id} 更新职位意向: {job_name}, 地点: {city}")
        else:
            user_obj = models.UserList.objects.filter(user_id=user_id).first()
            models.UserExpect.objects.create(user=user_obj, key_word=job_name, place=city)
            print(f"用户 {user_id} 创建职位意向: {job_name}, 地点: {city}")
        return JsonResponse({"Code": 0, "msg": "操作成功"})
    else:
        # 获取用户ID并确保是字符串类型
        user_id = str(request.session.get("user_id"))
        
        ret = models.UserExpect.objects.filter(user=user_id).values()
        # print(ret)
        if len(ret) != 0:
            keyword = ret[0]['key_word']
            place = ret[0]['place']
        else:
            keyword = ''
            place = ''
        return render(request, "expect.html", locals())


def get_recommend(request):
    # 获取当前用户ID
    user_id = request.session.get("user_id")
    
    # 检查session是否存在用户ID
    if not user_id:
        # 如果没有用户ID，重定向到登录页面
        return redirect('login')
    
    # 确保user_id是字符串类型
    user_id = str(user_id)
    print(f"视图函数中的用户ID: {user_id} (类型: {type(user_id)})")
    
    # 检查用户是否存在于数据库中
    try:
        user_obj = models.UserList.objects.get(user_id=user_id)
        print(f"视图函数中找到用户: {user_obj.user_name}")
    except models.UserList.DoesNotExist:
        # 用户ID在session中存在，但在数据库中不存在
        # 可能是数据库中的用户被删除，但session仍然保留
        # 清除session并重定向到登录页面
        print(f"视图函数中用户ID {user_id} 在数据库中不存在")
        request.session.flush()
        return redirect('login')
    
    try:
        # 获取推荐列表
        recommend_list = job_recommend.recommend_by_item_id(user_id, 9)
        
        # 获取每个推荐职位的收藏状态和评分
        for job in recommend_list:
            # 使用原生SQL获取收藏状态和评分
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT rating, is_favorite FROM user_job_interaction 
                    WHERE user_id = %s AND job_id = %s
                """, [user_id, job['job_id']])
                
                interaction = cursor.fetchone()
                
                if interaction:
                    job['rating'] = interaction[0] if interaction[0] else 0
                    job['is_favorite'] = 1 if interaction[1] else 0  # 将布尔值转换为整数，与get_job_list函数保持一致
                else:
                    job['rating'] = 0
                    job['is_favorite'] = 0  # 使用整数0而不是布尔值
                    
            # 获取投递状态
            job['is_sent'] = 1 if models.SendList.objects.filter(user_id=user_id, job_id=job['job_id']).exists() else 0  # 转换为整数
        
        return render(request, "recommend.html", {'recommend_list': recommend_list, 'user_id': user_id})
    except Exception as e:
        # 记录错误信息
        print(f"推荐系统错误: {str(e)}")
        # 返回一个错误页面
        return render(request, "recommend.html", {'error': '获取推荐失败，请稍后再试', 'recommend_list': []})


def send_page(request):
    return render(request, "send_list.html")


def send_list(request):
    # 获取用户ID并确保是字符串类型
    user_id = str(request.session.get("user_id"))
    print(f"获取用户 {user_id} 的投递列表")
    
    send_list = list(models.JobData.objects.filter(sendlist__user=user_id).values())
    for send in send_list:
        send['send_key'] = 1
    
    if len(send_list) == 0:
        print(f"用户 {user_id} 没有投递记录")
        return JsonResponse(
            {"code": 1, "msg": "没找到需要查询的数据！", "count": "{}".format(len(send_list)), "data": []})
    else:
        print(f"用户 {user_id} 有 {len(send_list)} 条投递记录")
        return JsonResponse({"code": 0, "msg": "success", "count": "{}".format(len(send_list)), "data": send_list})


def pass_page(request):
    user_obj = models.UserList.objects.filter(user_id=request.session.get("user_id")).first()
    return render(request, "pass_page.html", locals())


def up_info(request):
    if request.method == "POST":
        user_name = request.POST.get("user_name")
        old_pass = request.POST.get("old_pass")
        pass_word = request.POST.get("pass_word")
        user_obj = models.UserList.objects.filter(user_id=request.session.get("user_id")).first()
        if old_pass != user_obj.pass_word:
            return JsonResponse({"Code": 0, "msg": "原密码错误"})
        else:
            models.UserList.objects.filter(user_id=request.session.get("user_id")).update(user_name=user_name,
                                                                                          pass_word=pass_word)
            return JsonResponse({"Code": 0, "msg": "密码修改成功"})


def salary(request):
    return render(request, "salary.html")


def edu(request):
    return render(request, "edu.html")


def bar_page(request):
    return render(request, "bar_page.html")


def bar(request):
    """获取职位关键字统计数据，按数量从大到小排序"""
    try:
        # 获取所有非空的关键字
        key_list = [x['key_word'] for x in models.JobData.objects.exclude(key_word__isnull=True).exclude(key_word='').values("key_word")]
        
        # 统计每个关键字出现的次数
        key_count = {}
        for key in key_list:
            key = key.strip()  # 去除前后空格
            if not key:  # 跳过空字符串
                continue
            
            if key in key_count:
                key_count[key] += 1
            else:
                key_count[key] = 1
        
        # 按照数量从大到小排序
        sorted_keys = sorted(key_count.items(), key=lambda x: x[1], reverse=True)
        
        # 提取排序后的关键字和对应的数量
        bar_x = [item[0] for item in sorted_keys]
        bar_y = [item[1] for item in sorted_keys]
        
        print(f"职位关键字排序结果(前10个): {sorted_keys[:10] if len(sorted_keys) >= 10 else sorted_keys}")
        print(f"总共统计了 {len(sorted_keys)} 个不同的关键字")
        
        return JsonResponse({
            "code": 0, 
            "msg": "success", 
            "bar_x": bar_x, 
            "bar_y": bar_y,
            "total": len(sorted_keys)
        })
    except Exception as e:
        print(f"获取职位关键字统计数据出错: {str(e)}")
        # 返回空数据
        return JsonResponse({
            "code": 1, 
            "msg": f"获取数据失败: {str(e)}", 
            "bar_x": [], 
            "bar_y": [],
            "total": 0
        })


def data_visualization(request):
    """统一的数据可视化页面，支持动态筛选"""
    return render(request, "data_visualization.html")


def get_chart_data(request):
    """处理图表数据请求，支持动态筛选"""
    # 获取筛选参数
    keyword = request.GET.get("keyword", "")
    city = request.GET.get("city", "")
    education = request.GET.get("education", "")
    scale = request.GET.get("scale", "")
    
    print(f"筛选参数: keyword={keyword}, city={city}, education={education}, scale={scale}")
    
    # 构建基本查询条件
    filter_conditions = {}
    if keyword:
        filter_conditions["name__icontains"] = keyword
    if city:
        # 直接从数据库查询筛选后的总数
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM job_data WHERE place LIKE %s",
                ['%' + city + '%']
            )
            filtered_count = cursor.fetchone()[0]
            print(f"SQL 查询 '{city}' 的结果:", filtered_count)
        
        # 使用和SQL查询相同的方式：LIKE '%上海%'
        filter_conditions["place__icontains"] = city
    if education:
        filter_conditions["education__icontains"] = education
    if scale:
        filter_conditions["scale__icontains"] = scale
    
    print(f"查询条件: {filter_conditions}")
    
    # 获取符合条件的职位数据
    job_data = models.JobData.objects.filter(**filter_conditions).values()
    
    print(f"查询到的数据量: {len(job_data)}")
    
    # 没有数据时返回空结果
    if not job_data:
        return JsonResponse({
            "code": 0,
            "msg": "没有找到符合条件的数据",
            "salary_data": [],
            "edu_data": [],
            "keyword_data": {"x": [], "y": []},
            "city_data": {"x": [], "y": []}
        })
    
    # 处理薪资分布数据
    list_5 = []      # 5K及以下
    list_10 = []     # 5-10K
    list_15 = []     # 10K-15K
    list_20 = []     # 15K-20K
    list_30 = []     # 20K-30K
    list_50 = []     # 30-50K
    list_51 = []     # 50K以上
    
    for job in job_data:
        try:
            salary_1 = float(re.findall(r'-(\d+)k', job['salary'])[0])  # 提取薪资待遇的最高薪资要求
            if salary_1 <= 5:  # 小于5K则加入list_5
                list_5.append(salary_1)
            elif 10 >= salary_1 > 5:  # 在5K和10K之间，加入list_10
                list_10.append(salary_1)
            elif 15 >= salary_1 > 10:  # 10K-15K加入list_15
                list_15.append(salary_1)
            elif 20 >= salary_1 > 15:  # 15K-20K加入list_20
                list_20.append(salary_1)
            elif 30 >= salary_1 > 20:  # 20K-30K 加list_30
                list_30.append(salary_1)
            elif 50 >= salary_1 > 30:  # 30K-50K加入list_50
                list_50.append(salary_1)
            elif salary_1 > 50:  # 大于50K加入list_51
                list_51.append(salary_1)
        except Exception as e:
            pass
    
    salary_data = [
        {'name': '5K及以下', 'value': len(list_5)},
        {'name': '5-10K', 'value': len(list_10)},
        {'name': '10K-15K', 'value': len(list_15)},
        {'name': '15K-20K', 'value': len(list_20)},
        {'name': '20K-30K', 'value': len(list_30)},
        {'name': '30-50K', 'value': len(list_50)},
        {'name': '50K以上', 'value': len(list_51)}
    ]
    
    # 处理学历分布数据
    edu_list = ['博士', '硕士', '本科', '大专', '中专', '不限']
    edu_data = []
    
    for edu in edu_list:
        # 在当前筛选结果中统计学历要求
        edu_count = len([job for job in job_data if edu in job['education']])
        edu_data.append({'name': edu, 'value': edu_count})
    
    # 处理职位关键词数据
    keyword_count = {}
    for job in job_data:
        if job['key_word']:
            # 标准化关键词：去除首尾空格并转为小写
            keyword = job['key_word'].strip().lower()
            if keyword in keyword_count:
                keyword_count[keyword] += 1
            else:
                keyword_count[keyword] = 1
    
    # 只取前15个关键词，按数量降序排序
    sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:15]
    keyword_data = {
        "x": [item[0] for item in sorted_keywords],
        "y": [item[1] for item in sorted_keywords]
    }
    
    # 处理城市分布数据 - 全局数据，不受筛选条件影响
    city_count = {}
    
    # 使用原生SQL直接计算城市数量，确保完全匹配SQL查询
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN place LIKE '%-%' THEN SUBSTRING(place, 1, POSITION('-' IN place) - 1)
                    ELSE place
                END AS city_name,
                COUNT(*) as count
            FROM job_data
            GROUP BY city_name
            ORDER BY count DESC
            LIMIT 10
        """)
        city_results = cursor.fetchall()
        
    # 转换为前端需要的格式
    city_data = {
        "x": [item[0].replace('市', '') for item in city_results],
        "y": [item[1] for item in city_results]
    }
    
    # 无论是否有城市筛选条件，都返回全局的城市分布数据
    return JsonResponse({
        "code": 0,
        "msg": "success",
        "total_count": len(job_data),  # 添加总数据量字段
        "salary_data": salary_data,
        "edu_data": edu_data,
        "keyword_data": keyword_data,
        "city_data": city_data
    })


def job_rate(request):
    """此函数用于处理用户对职位的评分"""
    if request.method == "POST":
        user_id = request.session.get("user_id")  # 获取当前登录用户ID
        job_id = request.POST.get("job_id")  # 获取职位ID
        rating = request.POST.get("rating")  # 获取评分值
        
        if not user_id or not job_id:
            return JsonResponse({"code": 1, "msg": "用户或职位不存在"})
        
        # 检查评分是否在有效范围内（1-5）
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({"code": 1, "msg": "评分必须在1-5之间"})
        except:
            return JsonResponse({"code": 1, "msg": "评分格式不正确"})
        
        # 使用原生SQL更新或插入评分
        with connection.cursor() as cursor:
            # 先检查记录是否存在
            cursor.execute("""
                SELECT interaction_id FROM user_job_interaction 
                WHERE user_id = %s AND job_id = %s
            """, [user_id, job_id])
            
            interaction = cursor.fetchone()
            
            if interaction:
                # 如果记录存在，更新评分
                cursor.execute("""
                    UPDATE user_job_interaction 
                    SET rating = %s, updated_time = NOW(6)
                    WHERE user_id = %s AND job_id = %s
                """, [rating, user_id, job_id])
            else:
                # 如果记录不存在，创建新记录
                cursor.execute("""
                    INSERT INTO user_job_interaction 
                    (user_id, job_id, rating, is_favorite, created_time, updated_time)
                    VALUES (%s, %s, %s, 0, NOW(6), NOW(6))
                """, [user_id, job_id, rating])
            
        return JsonResponse({"code": 0, "msg": "评分成功"})
    else:
        return JsonResponse({"code": 1, "msg": "请使用POST请求"})


def toggle_favorite(request):
    """此函数用于切换职位收藏状态"""
    if request.method == "POST":
        user_id = request.session.get("user_id")  # 获取当前登录用户ID
        job_id = request.POST.get("job_id")  # 获取职位ID
        
        if not user_id or not job_id:
            return JsonResponse({"code": 1, "msg": "用户或职位不存在"})
        
        # 使用原生SQL实现收藏功能
        with connection.cursor() as cursor:
            # 先检查记录是否存在
            cursor.execute("""
                SELECT interaction_id, is_favorite FROM user_job_interaction 
                WHERE user_id = %s AND job_id = %s
            """, [user_id, job_id])
            
            interaction = cursor.fetchone()
            
            if interaction:
                # 记录存在，切换收藏状态
                is_favorite = not bool(interaction[1])
                cursor.execute("""
                    UPDATE user_job_interaction 
                    SET is_favorite = %s, updated_time = NOW(6)
                    WHERE user_id = %s AND job_id = %s
                """, [is_favorite, user_id, job_id])
            else:
                # 记录不存在，创建新记录并设为收藏
                is_favorite = True
                cursor.execute("""
                    INSERT INTO user_job_interaction 
                    (user_id, job_id, rating, is_favorite, created_time, updated_time)
                    VALUES (%s, %s, NULL, 1, NOW(6), NOW(6))
                """, [user_id, job_id])
        
        # 返回更新后的状态
        msg = "收藏成功" if is_favorite else "取消收藏"
        return JsonResponse({
            "code": 0, 
            "msg": msg, 
            "is_favorite": 1 if is_favorite else 0  # 返回整数而非布尔值
        })
    else:
        return JsonResponse({"code": 1, "msg": "请使用POST请求"})


def favorite_jobs(request):
    """此函数用于显示用户收藏的职位列表页面"""
    return render(request, "favorite_jobs.html")


def get_favorite_jobs(request):
    """此函数用于获取用户收藏的职位列表数据"""
    # 查询当前用户收藏的所有职位
    user_id = request.session.get("user_id")
    
    # 由于我们使用了原生SQL创建表，需要直接使用SQL查询
    # 使用raw SQL查询获取收藏的职位ID列表
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT job_id FROM user_job_interaction 
            WHERE user_id = %s AND is_favorite = 1
        """, [user_id])
        favorite_job_ids = [row[0] for row in cursor.fetchall()]
    
    # 使用职位ID列表获取职位详细信息
    favorite_jobs = []
    if favorite_job_ids:
        favorite_jobs = list(models.JobData.objects.filter(job_id__in=favorite_job_ids).values())
        
        # 获取职位的收藏状态和评分
        for job in favorite_jobs:
            # 使用原生SQL查询获取职位评分
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT rating, is_favorite FROM user_job_interaction 
                    WHERE user_id = %s AND job_id = %s
                """, [user_id, job['job_id']])
                interaction = cursor.fetchone()
                
                job['is_favorite'] = True  # 这里已经是收藏的职位
                job['rating'] = interaction[0] if interaction and interaction[0] else 0
                job['send_key'] = 1 if models.SendList.objects.filter(user_id=user_id, job_id=job['job_id']).exists() else 0
    
    if len(favorite_jobs) == 0:
        return JsonResponse({
            "code": 1, 
            "msg": "您还没有收藏任何职位", 
            "count": 0, 
            "data": []
        })
    else:
        return JsonResponse({
            "code": 0, 
            "msg": "success", 
            "count": len(favorite_jobs), 
            "data": favorite_jobs
        })


def skill_heatmap_page(request):
    """技能热度地图页面"""
    return render(request, "skill_heatmap.html")


def get_skill_heatmap_data(request):
    """获取技能热度地图数据
    
    根据不同地区对技能的需求程度，生成热度地图数据
    """
    try:
        # 获取查询参数
        skill = request.GET.get("skill", "")  # 技能关键词，如果为空则查询所有技能
        
        print(f"查询技能热度地图数据，技能关键词: {skill}")
        
        # 使用原生SQL查询不同地区的技能需求
        with connection.cursor() as cursor:
            if skill:
                # 查询特定技能在不同地区的需求数量
                # 使用参数化查询，避免SQL注入和%字符问题
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN place LIKE CONCAT('%%', '-', '%%') THEN SUBSTRING(place, 1, LOCATE('-', place) - 1)
                            ELSE place
                        END AS city_name,
                        COUNT(*) as count
                    FROM job_data
                    WHERE key_word LIKE CONCAT('%%', %s, '%%') OR name LIKE CONCAT('%%', %s, '%%')
                    GROUP BY city_name
                    ORDER BY count DESC
                """, [skill, skill])
            else:
                # 查询所有职位在不同地区的分布
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN place LIKE CONCAT('%%', '-', '%%') THEN SUBSTRING(place, 1, LOCATE('-', place) - 1)
                            ELSE place
                        END AS city_name,
                        COUNT(*) as count
                    FROM job_data
                    GROUP BY city_name
                    ORDER BY count DESC
                """)
            
            city_results = cursor.fetchall()
        
        # 查询热门技能列表（用于前端筛选）
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    key_word,
                    COUNT(*) as count
                FROM job_data
                WHERE key_word IS NOT NULL AND key_word != ''
                GROUP BY key_word
                ORDER BY count DESC
                LIMIT 20
            """)
            
            skill_results = cursor.fetchall()
        
        # 定义城市到省份的映射关系
        city_to_province = {
            # 直辖市
            '北京': '北京',
            '上海': '上海',
            '天津': '天津',
            '重庆': '重庆',
            
            # 华北地区
            '石家庄': '河北', '唐山': '河北', '秦皇岛': '河北', '邯郸': '河北', '邢台': '河北',
            '保定': '河北', '张家口': '河北', '承德': '河北', '沧州': '河北', '廊坊': '河北', '衡水': '河北',
            
            '太原': '山西', '大同': '山西', '阳泉': '山西', '长治': '山西', '晋城': '山西',
            '朔州': '山西', '晋中': '山西', '运城': '山西', '忻州': '山西', '临汾': '山西', '吕梁': '山西',
            
            '呼和浩特': '内蒙古', '包头': '内蒙古', '乌海': '内蒙古', '赤峰': '内蒙古', '通辽': '内蒙古',
            '鄂尔多斯': '内蒙古', '呼伦贝尔': '内蒙古', '巴彦淖尔': '内蒙古', '乌兰察布': '内蒙古',
            
            # 东北地区
            '沈阳': '辽宁', '大连': '辽宁', '鞍山': '辽宁', '抚顺': '辽宁', '本溪': '辽宁',
            '丹东': '辽宁', '锦州': '辽宁', '营口': '辽宁', '阜新': '辽宁', '辽阳': '辽宁',
            '盘锦': '辽宁', '铁岭': '辽宁', '朝阳': '辽宁', '葫芦岛': '辽宁',
            
            '长春': '吉林', '吉林': '吉林', '四平': '吉林', '辽源': '吉林', '通化': '吉林',
            '白山': '吉林', '松原': '吉林', '白城': '吉林',
            
            '哈尔滨': '黑龙江', '齐齐哈尔': '黑龙江', '鸡西': '黑龙江', '鹤岗': '黑龙江', '双鸭山': '黑龙江',
            '大庆': '黑龙江', '伊春': '黑龙江', '佳木斯': '黑龙江', '七台河': '黑龙江', '牡丹江': '黑龙江',
            '黑河': '黑龙江', '绥化': '黑龙江',
            
            # 华东地区
            '南京': '江苏', '无锡': '江苏', '徐州': '江苏', '常州': '江苏', '苏州': '江苏',
            '南通': '江苏', '连云港': '江苏', '淮安': '江苏', '盐城': '江苏', '扬州': '江苏',
            '镇江': '江苏', '泰州': '江苏', '宿迁': '江苏',
            
            '杭州': '浙江', '宁波': '浙江', '温州': '浙江', '嘉兴': '浙江', '湖州': '浙江',
            '绍兴': '浙江', '金华': '浙江', '衢州': '浙江', '舟山': '浙江', '台州': '浙江', '丽水': '浙江',
            
            '合肥': '安徽', '芜湖': '安徽', '蚌埠': '安徽', '淮南': '安徽', '马鞍山': '安徽',
            '淮北': '安徽', '铜陵': '安徽', '安庆': '安徽', '黄山': '安徽', '滁州': '安徽',
            '阜阳': '安徽', '宿州': '安徽', '六安': '安徽', '亳州': '安徽', '池州': '安徽', '宣城': '安徽',
            
            '福州': '福建', '厦门': '福建', '莆田': '福建', '三明': '福建', '泉州': '福建',
            '漳州': '福建', '南平': '福建', '龙岩': '福建', '宁德': '福建',
            
            '南昌': '江西', '景德镇': '江西', '萍乡': '江西', '九江': '江西', '新余': '江西',
            '鹰潭': '江西', '赣州': '江西', '吉安': '江西', '宜春': '江西', '抚州': '江西', '上饶': '江西',
            
            '济南': '山东', '青岛': '山东', '淄博': '山东', '枣庄': '山东', '东营': '山东',
            '烟台': '山东', '潍坊': '山东', '济宁': '山东', '泰安': '山东', '威海': '山东',
            '日照': '山东', '临沂': '山东', '德州': '山东', '聊城': '山东', '滨州': '山东', '菏泽': '山东',
            
            # 中南地区
            '郑州': '河南', '开封': '河南', '洛阳': '河南', '平顶山': '河南', '安阳': '河南',
            '鹤壁': '河南', '新乡': '河南', '焦作': '河南', '濮阳': '河南', '许昌': '河南',
            '漯河': '河南', '三门峡': '河南', '南阳': '河南', '商丘': '河南', '信阳': '河南',
            '周口': '河南', '驻马店': '河南',
            
            '武汉': '湖北', '黄石': '湖北', '十堰': '湖北', '宜昌': '湖北', '襄阳': '湖北',
            '鄂州': '湖北', '荆门': '湖北', '孝感': '湖北', '荆州': '湖北', '黄冈': '湖北',
            '咸宁': '湖北', '随州': '湖北',
            
            '长沙': '湖南', '株洲': '湖南', '湘潭': '湖南', '衡阳': '湖南', '邵阳': '湖南',
            '岳阳': '湖南', '常德': '湖南', '张家界': '湖南', '益阳': '湖南', '郴州': '湖南',
            '永州': '湖南', '怀化': '湖南', '娄底': '湖南',
            
            '广州': '广东', '韶关': '广东', '深圳': '广东', '珠海': '广东', '汕头': '广东',
            '佛山': '广东', '江门': '广东', '湛江': '广东', '茂名': '广东', '肇庆': '广东',
            '惠州': '广东', '梅州': '广东', '汕尾': '广东', '河源': '广东', '阳江': '广东',
            '清远': '广东', '东莞': '广东', '中山': '广东', '潮州': '广东', '揭阳': '广东', '云浮': '广东',
            
            '南宁': '广西', '柳州': '广西', '桂林': '广西', '梧州': '广西', '北海': '广西',
            '防城港': '广西', '钦州': '广西', '贵港': '广西', '玉林': '广西', '百色': '广西',
            '贺州': '广西', '河池': '广西', '来宾': '广西', '崇左': '广西',
            
            '海口': '海南', '三亚': '海南', '三沙': '海南', '儋州': '海南',
            
            # 西南地区
            '成都': '四川', '自贡': '四川', '攀枝花': '四川', '泸州': '四川', '德阳': '四川',
            '绵阳': '四川', '广元': '四川', '遂宁': '四川', '内江': '四川', '乐山': '四川',
            '南充': '四川', '眉山': '四川', '宜宾': '四川', '广安': '四川', '达州': '四川',
            '雅安': '四川', '巴中': '四川', '资阳': '四川',
            
            '贵阳': '贵州', '六盘水': '贵州', '遵义': '贵州', '安顺': '贵州', '毕节': '贵州', '铜仁': '贵州',
            
            '昆明': '云南', '曲靖': '云南', '玉溪': '云南', '保山': '云南', '昭通': '云南',
            '丽江': '云南', '普洱': '云南', '临沧': '云南',
            
            '拉萨': '西藏', '日喀则': '西藏', '昌都': '西藏', '林芝': '西藏', '山南': '西藏', '那曲': '西藏', '阿里': '西藏',
            
            # 西北地区
            '西安': '陕西', '铜川': '陕西', '宝鸡': '陕西', '咸阳': '陕西', '渭南': '陕西',
            '延安': '陕西', '汉中': '陕西', '榆林': '陕西', '安康': '陕西', '商洛': '陕西',
            
            '兰州': '甘肃', '嘉峪关': '甘肃', '金昌': '甘肃', '白银': '甘肃', '天水': '甘肃',
            '武威': '甘肃', '张掖': '甘肃', '平凉': '甘肃', '酒泉': '甘肃', '庆阳': '甘肃',
            '定西': '甘肃', '陇南': '甘肃',
            
            '西宁': '青海', '海东': '青海',
            
            '银川': '宁夏', '石嘴山': '宁夏', '吴忠': '宁夏', '固原': '宁夏', '中卫': '宁夏',
            
            '乌鲁木齐': '新疆', '克拉玛依': '新疆', '吐鲁番': '新疆', '哈密': '新疆',
            
            # 特别行政区
            '香港': '香港',
            '澳门': '澳门',
            '台北': '台湾', '高雄': '台湾', '台中': '台湾', '台南': '台湾'
        }
        
        # 处理城市数据，移除"市"字并计算最大值和最小值
        city_data = []
        province_data = {}  # 用于累计省份数据
        max_count = 0  # 初始化最大值
        min_count = float('inf')  # 初始化最小值为无穷大
        
        for city, count in city_results:
            if not city:  # 跳过空城市名
                continue
                
            # 处理城市名称，使其与地图匹配
            city_name = city.strip()
            if '市' in city_name:
                city_name = city_name.replace('市', '')
            if '省' in city_name:
                city_name = city_name.replace('省', '')
            if '自治区' in city_name:
                city_name = city_name.replace('自治区', '')
            if '特别行政区' in city_name:
                city_name = city_name.replace('特别行政区', '')
            
            # 确保count是整数
            count = int(count)
            
            # 处理直辖市
            if city_name in ['北京', '上海', '天津', '重庆']:
                city_data.append({
                    'name': city_name,
                    'value': count
                })
            else:
                # 尝试将城市映射到省份
                province = city_to_province.get(city_name)
                if province:
                    # 累加到省份数据
                    if province in province_data:
                        province_data[province] += count
                    else:
                        province_data[province] = count
                else:
                    # 如果没有映射，直接使用城市名称
                    city_data.append({
                        'name': city_name,
                        'value': count
                    })
            
            # 更新最大值和最小值
            if count > max_count:
                max_count = count
            if count < min_count:
                min_count = count
        
        # 将省份数据添加到结果中
        for province, count in province_data.items():
            city_data.append({
                'name': province,
                'value': count
            })
            
            # 更新最大值
            if count > max_count:
                max_count = count
        
        # 如果没有数据，设置最小值为0
        if min_count == float('inf'):
            min_count = 0
        
        # 处理技能列表数据
        skill_list = []
        for skill_name, count in skill_results:
            if skill_name:
                skill_list.append({
                    'name': skill_name,
                    'count': count
                })
        
        print(f"查询到 {len(city_data)} 个地区数据，{len(skill_list)} 个技能数据")
        print(f"最大值: {max_count}, 最小值: {min_count}")
        
        return JsonResponse({
            "code": 0,
            "msg": "success",
            "data": city_data,
            "max": max_count,
            "min": min_count,
            "skill_list": skill_list,
            "current_skill": skill
        })
    except Exception as e:
        import traceback
        print(f"获取技能热度地图数据出错: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            "code": 1,
            "msg": f"获取数据失败: {str(e)}",
            "data": [],
            "skill_list": []
        })


# 添加薪资预测相关的视图函数
def salary_prediction_page(request):
    """薪资预测页面"""
    # 检查是否存在薪资预测模型表
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'salary_prediction_model'
                AND table_schema = DATABASE()
            """)
            if cursor.fetchone()[0] == 0:
                print("salary_prediction_model表不存在，需要应用数据库迁移")
                # 如果表不存在，显示提示信息
                return render(request, "salary_prediction.html", {
                    'init_error': '数据库初始化未完成，请确保已应用所有迁移'
                })
    except Exception as e:
        print(f"检查表存在时出错: {e}")
    
    # 检查是否存在随机森林模型，如果没有则训练一个
    try:
        # 首先检查是否有随机森林模型
        rf_model_exists = models.SalaryPredictionModel.objects.filter(model_type='random_forest').exists()
        
        # 如果没有随机森林模型，检查是否有任何活跃模型
        if not rf_model_exists:
            active_model_exists = models.SalaryPredictionModel.objects.filter(is_active=True).exists()
            
            if not active_model_exists:
                print("系统中没有可用的随机森林模型，开始训练初始模型...")
                try:
                    # 训练随机森林模型
                    predictor = salary_prediction.SalaryPredictor()
                    results = predictor.train_model(model_type="random_forest", save_model=True)
                    print(f"初始随机森林模型训练完成: {results}")
                    
                    # 获取表单选项数据
                    context = get_prediction_form_options()
                    context['init_message'] = '系统已自动训练了一个随机森林模型，您可以开始使用薪资预测功能'
                    return render(request, "salary_prediction.html", context)
                except Exception as e:
                    print(f"初始模型训练失败: {e}")
                    return render(request, "salary_prediction.html", {
                        'init_error': f'初始模型训练失败: {str(e)}'
                    })
    except Exception as e:
        print(f"检查模型状态时出错: {e}")
        return render(request, "salary_prediction.html", {
            'init_error': f'检查模型状态时出错: {str(e)}'
        })
    
    # 获取表单选项数据
    context = get_prediction_form_options()
    return render(request, "salary_prediction.html", context)


def get_prediction_form_options():
    """
    从数据库获取薪资预测表单所需的选项数据
    """
    try:
        # 定义标准化的学历选项
        standard_education = ['博士', '硕士', '本科', '大专', '中专', '中专以下', '不限']
        
        # 定义标准化的工作经验选项
        standard_experience = ['实习', '应届生', '1年以下', '1-3年', '3-5年', '5-10年', '10年以上', '不限']
        
        # 定义标准化的公司规模选项
        standard_scale = ['小型企业', '中小企业', '中型企业', '中大型企业', '大型企业', '超大型企业', '未知规模']
        
        # 获取唯一的城市
        city_values = models.JobData.objects.exclude(place__isnull=True).exclude(place='').values_list('place', flat=True).distinct()
        
        # 提取城市名称（去除区域信息）
        city_options = []
        for place in city_values:
            city = place.split('-')[0].strip() if '-' in place else place.strip()
            if city and city not in city_options:
                city_options.append(city)
        
        # 添加常见城市，确保它们存在
        common_cities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '西安', '其他']
        for city in common_cities:
            if city not in city_options:
                city_options.append(city)
        
        city_options = sorted(city_options)
        
        return {
            'education_options': standard_education,
            'experience_options': standard_experience,
            'city_options': city_options,
            'scale_options': standard_scale
        }
    except Exception as e:
        print(f"获取表单选项数据失败: {e}")
        # 返回默认选项
        return {
            'education_options': ['博士', '硕士', '本科', '大专', '中专', '中专以下', '不限'],
            'experience_options': ['实习', '应届生', '1年以下', '1-3年', '3-5年', '5-10年', '10年以上', '不限'],
            'city_options': ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '南京', '西安', '其他'],
            'scale_options': ['小型企业', '中小企业', '中型企业', '中大型企业', '大型企业', '超大型企业', '未知规模']
        }


@csrf_exempt
def train_salary_model(request):
    """
    手动训练特定类型的薪资预测模型并保存
    """
    # 强制设置Python环境变量为UTF-8，防止Windows下编码报错
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    try:
        if request.method == 'POST':
            # 获取模型类型参数
            model_type = request.POST.get('model_type', 'random_forest')
            
            # 获取模型训练参数
            model_params = {}
            
            # 根据模型类型获取相应的参数
            if model_type == 'random_forest':
                # 随机森林参数
                if 'n_estimators' in request.POST:
                    model_params['n_estimators'] = int(request.POST.get('n_estimators'))
                if 'max_depth' in request.POST:
                    model_params['max_depth'] = int(request.POST.get('max_depth'))
                if 'min_samples_split' in request.POST:
                    model_params['min_samples_split'] = int(request.POST.get('min_samples_split'))
                if 'min_samples_leaf' in request.POST:
                    model_params['min_samples_leaf'] = int(request.POST.get('min_samples_leaf'))
            
            elif model_type == 'gradient_boosting':
                # 梯度提升树参数
                if 'n_estimators' in request.POST:
                    model_params['n_estimators'] = int(request.POST.get('n_estimators'))
                if 'learning_rate' in request.POST:
                    model_params['learning_rate'] = float(request.POST.get('learning_rate'))
                if 'max_depth' in request.POST:
                    model_params['max_depth'] = int(request.POST.get('max_depth'))
            
            elif model_type in ['ridge', 'lasso']:
                # 岭回归和Lasso回归参数
                if 'alpha' in request.POST:
                    model_params['alpha'] = float(request.POST.get('alpha'))
            
            # 创建薪资预测器实例
            predictor = salary_prediction.SalaryPredictor()
            
            # 训练模型，传入参数
            results = predictor.train_model(model_type=model_type, save_model=True, model_params=model_params)
            
            return JsonResponse({
                'code': 0,
                'msg': f'成功训练{model_type}模型',
                'data': results
            })
        else:
            return JsonResponse({
                'code': 1,
                'msg': '请使用POST方法请求'
            })
    except Exception as e:
        print(f"训练模型出错: {e}")
        return JsonResponse({
            'code': 1,
            'msg': f'训练模型失败: {str(e)}'
        })


@csrf_exempt
def predict_salary(request):
    """
    预测薪资
    """
    try:
        if request.method == 'POST':
            # 获取职位信息
            position_name = request.POST.get('position_name', '')
            education = request.POST.get('education', '本科')
            experience = request.POST.get('experience', '3-5年')
            city = request.POST.get('city', '北京')
            company_scale = request.POST.get('company_scale', '未知规模')
            skills = request.POST.get('skills', '')
            # 获取模型类型
            model_type = request.POST.get('model_type', 'random_forest')
            # 智能调整始终启用
            apply_adjustment = True
            
            # 提取特征
            features = salary_prediction.extract_job_features(
                position_name, 
                education=education,
                experience=experience,
                place=city,
                scale=company_scale,
                key_word=skills
            )
            
            # 创建薪资预测器实例
            predictor = salary_prediction.SalaryPredictor()
            
            # 尝试加载指定类型的模型
            model_loaded = predictor.load_specific_model(model_type)
            
            if not model_loaded:
                # 检查是否有任何模型
                any_model_exists = models.SalaryPredictionModel.objects.exists()
                
                if not any_model_exists:
                    # 如果没有找到任何模型，先训练一个初始模型
                    print(f"没有找到任何训练好的模型，正在训练初始{model_type}模型...")
                    results = predictor.train_model(model_type=model_type, save_model=True)
                    print(f"初始模型训练完成: {results}")
                    model_loaded = True
                else:
                    # 如果有其他类型的模型但没有指定类型的模型
                    return JsonResponse({
                        'code': 1,
                        'msg': f'没有找到{model_type}类型的模型，请先训练该类型的模型或选择其他可用的模型类型'
                    })
            
            # 进行预测，传入手动调整参数
            min_salary, max_salary = predictor.predict(
                features, 
                apply_manual_adjustment=apply_adjustment
            )
            
            # 保留一位小数
            min_salary = round(min_salary, 1)
            max_salary = round(max_salary, 1)
            
            # 确保最小值和最大值不相同，如果相同则最大值加上合理的范围
            if abs(min_salary - max_salary) < 0.1:  # 几乎相同
                # 给最大值添加合理的范围 (约10-20%的增长)
                max_salary = round(min_salary * 1.15, 1)  # 增加15%并保留一位小数
            
            # 获取当前用户ID
            user_id = request.session.get("user_id")
            
            # 获取使用的模型对象
            try:
                model_obj = models.SalaryPredictionModel.objects.filter(
                    model_type=model_type
                ).order_by('-updated_time').first()
                
                # 如果用户已登录且找到了模型对象，保存预测历史
                if user_id and model_obj:
                    try:
                        # 保存预测历史
                        models.UserSalaryPrediction.objects.create(
                            user_id=user_id,
                            position_name=position_name,
                            education=education,
                            experience=experience,
                            city=city,
                            company_scale=company_scale,
                            skills=skills,
                            predicted_salary_min=min_salary,
                            predicted_salary_max=max_salary,
                            model_used=model_obj
                        )
                        print(f"已保存用户 {user_id} 的薪资预测历史")
                    except Exception as e:
                        print(f"保存预测历史时出错: {e}")
            except Exception as e:
                print(f"获取模型对象时出错: {e}")
            
            # 返回预测结果
            return JsonResponse({
                'code': 0,
                'msg': '预测成功',
                'data': {
                    'position_name': position_name,
                    'education': education,
                    'experience': experience,
                    'city': city,
                    'company_scale': company_scale,
                    'skills': skills,
                    'min_salary': min_salary,
                    'max_salary': max_salary,
                    'model_type': model_type,
                    'adjustment_applied': apply_adjustment
                }
            })
        else:
            return JsonResponse({
                'code': 1,
                'msg': '请使用POST方法请求'
            })
    except Exception as e:
        print(f"预测薪资出错: {e}")
        return JsonResponse({
            'code': 1,
            'msg': f'预测失败: {str(e)}'
        })


def get_prediction_history(request):
    """获取用户的薪资预测历史记录"""
    # 获取用户ID
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({
            "code": 1,
            "msg": "请先登录"
        })
    
    try:
        # 检查表是否存在
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'user_salary_prediction'
                AND table_schema = DATABASE()
            """)
            if cursor.fetchone()[0] == 0:
                print("user_salary_prediction表不存在")
                return JsonResponse({
                    "code": 1,
                    "msg": "薪资预测历史表不存在，请确保数据库迁移已正确应用",
                    "count": 0,
                    "data": []
                })
        
        # 获取分页参数
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))
        
        # 查询用户的预测历史记录
        history_query = models.UserSalaryPrediction.objects.filter(user_id=user_id).order_by('-prediction_date')
        
        # 计算总记录数
        total = history_query.count()
        
        if total == 0:
            return JsonResponse({
                "code": 0,
                "msg": "没有找到预测历史记录",
                "count": 0,
                "data": []
            })
        
        # 分页查询
        history = history_query[(page - 1) * limit:page * limit]
        
        # 构建响应数据
        history_data = []
        for item in history:
            try:
                history_data.append({
                    "prediction_id": item.prediction_id,
                    "position_name": item.position_name,
                    "education": item.education,
                    "experience": item.experience,
                    "city": item.city,
                    "company_scale": item.company_scale if item.company_scale else "未知规模",
                    "skills": item.skills if item.skills else "",
                    "predicted_salary_min": round(item.predicted_salary_min, 1),
                    "predicted_salary_max": round(item.predicted_salary_max, 1),
                    "prediction_date": item.prediction_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "model_type": item.model_used.model_type
                })
            except Exception as e:
                print(f"处理历史记录项时出错: {e}")
                # 跳过有错误的记录，继续处理其他记录
                continue
        
        return JsonResponse({
            "code": 0,
            "msg": "获取历史记录成功",
            "count": total,
            "data": history_data
        })
    except Exception as e:
        print(f"获取历史记录失败: {e}")
        return JsonResponse({
            "code": 1,
            "msg": f"获取历史记录失败: {str(e)}",
            "count": 0,
            "data": []
        })


def get_model_info(request):
    """
    获取当前活跃模型的信息
    """
    try:
        # 获取请求中的模型类型参数
        model_type = request.GET.get('model_type', None)
        
        # 如果指定了模型类型，获取该类型的最新模型
        if model_type:
            model = models.SalaryPredictionModel.objects.filter(
                model_type=model_type
            ).order_by('-updated_time').first()
        else:
            # 否则获取当前活跃的模型
            model = models.SalaryPredictionModel.objects.filter(
                is_active=True
            ).order_by('-updated_time').first()
            
            # 如果没有活跃模型，尝试获取随机森林模型
            if not model:
                model = models.SalaryPredictionModel.objects.filter(
                    model_type='random_forest'
                ).order_by('-updated_time').first()
        
        if model:
            # 解析特征重要性
            feature_importance = json.loads(model.feature_importance) if model.feature_importance else {}
            
            return JsonResponse({
                'code': 0,
                'msg': '获取模型信息成功',
                'data': {
                    'model_name': model.model_name,
                    'model_type': model.model_type,
                    'r2_score': round(model.r2_score, 4),
                    'mean_absolute_error': round(model.mean_absolute_error, 4),
                    'created_time': model.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_time': model.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'feature_importance': feature_importance
                }
            })
        else:
            return JsonResponse({
                'code': 1,
                'msg': '没有找到可用的模型，请先训练一个模型',
                'data': {}
            })
    except Exception as e:
        print(f"获取模型信息出错: {e}")
        return JsonResponse({
            'code': 1,
            'msg': f'获取模型信息失败: {str(e)}',
            'data': {}
        })


def get_available_models(request):
    """
    获取所有可用的模型类型及其信息
    """
    try:
        # 检查表是否存在
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'salary_prediction_model'
                AND table_schema = DATABASE()
            """)
            if cursor.fetchone()[0] == 0:
                print("salary_prediction_model表不存在")
                return JsonResponse({
                    'code': 1,
                    'msg': '薪资预测模型表不存在，请确保数据库迁移已正确应用',
                    'data': []
                })

        # 按模型类型分组，获取每种类型的最新模型
        model_types = models.SalaryPredictionModel.objects.values('model_type').distinct()
        
        if not model_types.exists():
            print("没有找到任何训练好的模型")
            return JsonResponse({
                'code': 1,
                'msg': '还没有训练好的模型，请先训练一个模型',
                'data': []
            })
        
        available_models = []
        for type_obj in model_types:
            model_type = type_obj['model_type']
            model = models.SalaryPredictionModel.objects.filter(
                model_type=model_type
            ).order_by('-updated_time').first()
            
            if model:
                available_models.append({
                    'model_type': model_type,
                    'model_name': model.model_name,
                    'r2_score': round(model.r2_score, 4),
                    'mean_absolute_error': round(model.mean_absolute_error, 4),
                    'updated_time': model.updated_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'is_active': model.is_active
                })
        
        return JsonResponse({
            'code': 0,
            'msg': '获取可用模型成功',
            'data': available_models
        })
    except Exception as e:
        print(f"获取可用模型出错: {e}")
        return JsonResponse({
            'code': 1,
            'msg': f'获取可用模型失败: {str(e)}',
            'data': []
        })


def set_active_model(request):
    """设置活跃模型"""
    if request.method == "POST":
        try:
            model_id = request.POST.get("model_id")
            if not model_id:
                return JsonResponse({
                    "code": 1,
                    "msg": "请提供模型ID"
                })
            
            # 设置活跃模型
            success = salary_predictor.set_active_model(model_id)
            
            if success:
                return JsonResponse({
                    "code": 0,
                    "msg": "设置活跃模型成功"
                })
            else:
                return JsonResponse({
                    "code": 1,
                    "msg": "设置活跃模型失败"
                })
        except Exception as e:
            print(f"设置活跃模型失败: {e}")
            return JsonResponse({
                "code": 1,
                "msg": f"设置活跃模型失败: {str(e)}"
            })
    else:
        return JsonResponse({
            "code": 1,
            "msg": "请使用POST请求"
        })

def visualization_dashboard(request):
    """
    可视化大屏页面
    展示计算机行业就业情况的可视化数据
    """
    # 获取职位数据总数
    job_data = list(models.JobData.objects.all().values())  # 使用.values()将查询结果转为字典列表
    lendata = len(job_data)
    
    # 获取不同职位类型的数量
    unique_job_count = len(set([job['key_word'] for job in job_data if job['key_word']]))
    
    # 获取各城市的职位数量
    city_counts = {}
    for job in job_data:
        if job['place']:
            # 提取城市名称（去掉区县信息）
            city = job['place'].split('-')[0] if '-' in job['place'] else job['place']
            city = city.replace('市', '')  # 移除"市"字
            if city in city_counts:
                city_counts[city] += 1
            else:
                city_counts[city] = 1
    
    # 获取前10个城市
    top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    city_names = [city for city, _ in top_cities]  # 城市名称
    city_counts_list = [count for _, count in top_cities]  # 对应的职位数量
    
    # 打印城市数据，用于验证
    print("城市名称列表:", city_names)
    print("城市职位数量列表:", city_counts_list)
    
    # 准备地理数据
    data2 = []
    
    # 定义城市到省份的映射关系
    city_to_province = {
        # 直辖市
        '北京': '北京',
        '上海': '上海',
        '天津': '天津',
        '重庆': '重庆',
        
        # 华北地区
        '石家庄': '河北', '唐山': '河北', '秦皇岛': '河北', '邯郸': '河北', '邢台': '河北',
        '保定': '河北', '张家口': '河北', '承德': '河北', '沧州': '河北', '廊坊': '河北', '衡水': '河北',
        
        '太原': '山西', '大同': '山西', '阳泉': '山西', '长治': '山西', '晋城': '山西',
        '朔州': '山西', '晋中': '山西', '运城': '山西', '忻州': '山西', '临汾': '山西', '吕梁': '山西',
        
        '呼和浩特': '内蒙古', '包头': '内蒙古', '乌海': '内蒙古', '赤峰': '内蒙古', '通辽': '内蒙古',
        '鄂尔多斯': '内蒙古', '呼伦贝尔': '内蒙古', '巴彦淖尔': '内蒙古', '乌兰察布': '内蒙古',
        
        # 东北地区
        '沈阳': '辽宁', '大连': '辽宁', '鞍山': '辽宁', '抚顺': '辽宁', '本溪': '辽宁',
        '丹东': '辽宁', '锦州': '辽宁', '营口': '辽宁', '阜新': '辽宁', '辽阳': '辽宁',
        '盘锦': '辽宁', '铁岭': '辽宁', '朝阳': '辽宁', '葫芦岛': '辽宁',
        
        '长春': '吉林', '吉林': '吉林', '四平': '吉林', '辽源': '吉林', '通化': '吉林',
        '白山': '吉林', '松原': '吉林', '白城': '吉林',
        
        '哈尔滨': '黑龙江', '齐齐哈尔': '黑龙江', '鸡西': '黑龙江', '鹤岗': '黑龙江', '双鸭山': '黑龙江',
        '大庆': '黑龙江', '伊春': '黑龙江', '佳木斯': '黑龙江', '七台河': '黑龙江', '牡丹江': '黑龙江',
        '黑河': '黑龙江', '绥化': '黑龙江',
        
        # 华东地区
        '南京': '江苏', '无锡': '江苏', '徐州': '江苏', '常州': '江苏', '苏州': '江苏',
        '南通': '江苏', '连云港': '江苏', '淮安': '江苏', '盐城': '江苏', '扬州': '江苏',
        '镇江': '江苏', '泰州': '江苏', '宿迁': '江苏',
        
        '杭州': '浙江', '宁波': '浙江', '温州': '浙江', '嘉兴': '浙江', '湖州': '浙江',
        '绍兴': '浙江', '金华': '浙江', '衢州': '浙江', '舟山': '浙江', '台州': '浙江', '丽水': '浙江',
        
        '合肥': '安徽', '芜湖': '安徽', '蚌埠': '安徽', '淮南': '安徽', '马鞍山': '安徽',
        '淮北': '安徽', '铜陵': '安徽', '安庆': '安徽', '黄山': '安徽', '滁州': '安徽',
        '阜阳': '安徽', '宿州': '安徽', '六安': '安徽', '亳州': '安徽', '池州': '安徽', '宣城': '安徽',
        
        '福州': '福建', '厦门': '福建', '莆田': '福建', '三明': '福建', '泉州': '福建',
        '漳州': '福建', '南平': '福建', '龙岩': '福建', '宁德': '福建',
        
        '南昌': '江西', '景德镇': '江西', '萍乡': '江西', '九江': '江西', '新余': '江西',
        '鹰潭': '江西', '赣州': '江西', '吉安': '江西', '宜春': '江西', '抚州': '江西', '上饶': '江西',
        
        '济南': '山东', '青岛': '山东', '淄博': '山东', '枣庄': '山东', '东营': '山东',
        '烟台': '山东', '潍坊': '山东', '济宁': '山东', '泰安': '山东', '威海': '山东',
        '日照': '山东', '临沂': '山东', '德州': '山东', '聊城': '山东', '滨州': '山东', '菏泽': '山东',
        
        # 中南地区
        '郑州': '河南', '开封': '河南', '洛阳': '河南', '平顶山': '河南', '安阳': '河南',
        '鹤壁': '河南', '新乡': '河南', '焦作': '河南', '濮阳': '河南', '许昌': '河南',
        '漯河': '河南', '三门峡': '河南', '南阳': '河南', '商丘': '河南', '信阳': '河南',
        '周口': '河南', '驻马店': '河南',
        
        '武汉': '湖北', '黄石': '湖北', '十堰': '湖北', '宜昌': '湖北', '襄阳': '湖北',
        '鄂州': '湖北', '荆门': '湖北', '孝感': '湖北', '荆州': '湖北', '黄冈': '湖北',
        '咸宁': '湖北', '随州': '湖北',
        
        '长沙': '湖南', '株洲': '湖南', '湘潭': '湖南', '衡阳': '湖南', '邵阳': '湖南',
        '岳阳': '湖南', '常德': '湖南', '张家界': '湖南', '益阳': '湖南', '郴州': '湖南',
        '永州': '湖南', '怀化': '湖南', '娄底': '湖南',
        
        '广州': '广东', '韶关': '广东', '深圳': '广东', '珠海': '广东', '汕头': '广东',
        '佛山': '广东', '江门': '广东', '湛江': '广东', '茂名': '广东', '肇庆': '广东',
        '惠州': '广东', '梅州': '广东', '汕尾': '广东', '河源': '广东', '阳江': '广东',
        '清远': '广东', '东莞': '广东', '中山': '广东', '潮州': '广东', '揭阳': '广东', '云浮': '广东',
        
        '南宁': '广西', '柳州': '广西', '桂林': '广西', '梧州': '广西', '北海': '广西',
        '防城港': '广西', '钦州': '广西', '贵港': '广西', '玉林': '广西', '百色': '广西',
        '贺州': '广西', '河池': '广西', '来宾': '广西', '崇左': '广西',
        
        '海口': '海南', '三亚': '海南', '三沙': '海南', '儋州': '海南',
        
        # 西南地区
        '成都': '四川', '自贡': '四川', '攀枝花': '四川', '泸州': '四川', '德阳': '四川',
        '绵阳': '四川', '广元': '四川', '遂宁': '四川', '内江': '四川', '乐山': '四川',
        '南充': '四川', '眉山': '四川', '宜宾': '四川', '广安': '四川', '达州': '四川',
        '雅安': '四川', '巴中': '四川', '资阳': '四川',
        
        '贵阳': '贵州', '六盘水': '贵州', '遵义': '贵州', '安顺': '贵州', '毕节': '贵州', '铜仁': '贵州',
        
        '昆明': '云南', '曲靖': '云南', '玉溪': '云南', '保山': '云南', '昭通': '云南',
        '丽江': '云南', '普洱': '云南', '临沧': '云南',
        
        '拉萨': '西藏', '日喀则': '西藏', '昌都': '西藏', '林芝': '西藏', '山南': '西藏', '那曲': '西藏', '阿里': '西藏',
        
        # 西北地区
        '西安': '陕西', '铜川': '陕西', '宝鸡': '陕西', '咸阳': '陕西', '渭南': '陕西',
        '延安': '陕西', '汉中': '陕西', '榆林': '陕西', '安康': '陕西', '商洛': '陕西',
        
        '兰州': '甘肃', '嘉峪关': '甘肃', '金昌': '甘肃', '白银': '甘肃', '天水': '甘肃',
        '武威': '甘肃', '张掖': '甘肃', '平凉': '甘肃', '酒泉': '甘肃', '庆阳': '甘肃',
        '定西': '甘肃', '陇南': '甘肃',
        
        '西宁': '青海', '海东': '青海',
        
        '银川': '宁夏', '石嘴山': '宁夏', '吴忠': '宁夏', '固原': '宁夏', '中卫': '宁夏',
        
        '乌鲁木齐': '新疆', '克拉玛依': '新疆', '吐鲁番': '新疆', '哈密': '新疆',
        
        # 特别行政区
        '香港': '香港',
        '澳门': '澳门',
        '台北': '台湾', '高雄': '台湾', '台中': '台湾', '台南': '台湾'
    }
    
    # 处理城市数据，移除"市"字并计算最大值和最小值
    province_data = {}  # 用于累计省份数据
    
    for city, count in city_counts.items():
        # 处理城市名称，使其与地图匹配
        city_name = city.strip()
        if '市' in city_name:
            city_name = city_name.replace('市', '')
        if '省' in city_name:
            city_name = city_name.replace('省', '')
        if '自治区' in city_name:
            city_name = city_name.replace('自治区', '')
        if '特别行政区' in city_name:
            city_name = city_name.replace('特别行政区', '')
        
        # 处理直辖市
        if city_name in ['北京', '上海', '天津', '重庆']:
            data2.append({
                'name': city_name,
                'value': count
            })
        else:
            # 尝试将城市映射到省份
            province = city_to_province.get(city_name)
            if province:
                # 累加到省份数据
                if province in province_data:
                    province_data[province] += count
                else:
                    province_data[province] = count
            else:
                # 如果没有映射，直接使用城市名称
                data2.append({
                    'name': city_name,
                    'value': count
                })
    
    # 将省份数据添加到结果中
    for province, count in province_data.items():
        data2.append({
            'name': province,
            'value': count
        })
    
    print(f"地图数据生成完成，共 {len(data2)} 条记录")
    
    # 获取不同学历的平均薪资
    education_types = ['博士', '硕士', '本科', '大专', '中专', '不限']
    job_price_index = education_types
    job_price = []
    
    print("开始计算不同学历的平均薪资...")
    for edu in education_types:
        # 获取该学历要求的职位
        edu_jobs = [job for job in job_data if edu in job['education']]
        if not edu_jobs:
            job_price.append(0)
            print(f"学历 '{edu}' 没有找到相关职位数据，设置平均薪资为0")
            continue
            
        # 计算平均薪资（同时考虑最低和最高薪资）
        total_salary = 0
        valid_count = 0
        for job in edu_jobs:
            try:
                # 提取最高薪资和最低薪资
                salary_max = float(re.findall(r'-(\d+)k', job['salary'])[0])
                salary_min = float(re.findall(r'(\d+)-', job['salary'])[0])
                # 计算平均薪资（最低和最高的平均值）
                avg = (salary_min + salary_max) / 2
                total_salary += avg
                valid_count += 1
            except Exception as e:
                # 如果提取失败，尝试只提取最高薪资
                try:
                    salary_max = float(re.findall(r'-(\d+)k', job['salary'])[0])
                    total_salary += salary_max
                    valid_count += 1
                except:
                    pass
                
        # 计算平均值
        avg_salary = round(total_salary / valid_count, 1) if valid_count > 0 else 0
        job_price.append(avg_salary)
        print(f"学历 '{edu}' 找到 {len(edu_jobs)} 个职位，有效数据 {valid_count} 个，平均薪资 {avg_salary}K")
    
    print("不同学历的平均薪资计算完成:", job_price)
    
    # 获取不同城市下各类职位的平均薪资
    # 使用所有top_cities_names而不是仅前5个
    top_cities_names = city_names  # 使用所有城市
    top_keywords = ['Java', 'Python', '前端', '算法']
    
    # 初始化各类职位在不同城市的平均薪资
    java_cities_price = []
    python_cities_price = []
    web_cities_price = []
    hadoop_cities_price = []  # 变量名保持不变，但实际存储算法岗位数据
    
    # 计算各类职位在不同城市的平均薪资
    for city in top_cities_names:
        # Java职位
        java_jobs = [job for job in job_data if city in job['place'] and 'java' in job['name'].lower()]
        java_avg = calculate_avg_salary_from_dict(java_jobs)
        java_cities_price.append(java_avg)
        
        # Python职位
        python_jobs = [job for job in job_data if city in job['place'] and 'python' in job['name'].lower()]
        python_avg = calculate_avg_salary_from_dict(python_jobs)
        python_cities_price.append(python_avg)
        
        # 前端职位
        web_jobs = [job for job in job_data if city in job['place'] and ('前端' in job['name'] or 'web' in job['name'].lower())]
        web_avg = calculate_avg_salary_from_dict(web_jobs)
        web_cities_price.append(web_avg)
        
        # 算法职位（替换原来的Hadoop职位）
        # 扩大匹配范围，包括"算法"、"AI"、"人工智能"、"机器学习"等关键词
        algorithm_jobs = [job for job in job_data if city in job['place'] and 
                         ('算法' in job['name'] or 
                          'AI' in job['name'] or 
                          '人工智能' in job['name'] or 
                          '机器学习' in job['name'] or
                          'algorithm' in job['name'].lower())]
        algorithm_avg = calculate_avg_salary_from_dict(algorithm_jobs)
        hadoop_cities_price.append(algorithm_avg)
    
    # 打印薪资数据，用于验证
    print("Java城市薪资:", java_cities_price)
    print("Python城市薪资:", python_cities_price)
    print("Web城市薪资:", web_cities_price)
    print("算法城市薪资:", hadoop_cities_price)
    
    # 获取北京地区各职位数量
    beijing_jobs = [job for job in job_data if '北京' in job['place']]
    print(f"北京地区职位总数: {len(beijing_jobs)}")
    
    beijing_job_counts = {}
    for job in beijing_jobs:
        if job['key_word'] and job['key_word'].strip():  # 确保key_word非空且非空白字符
            key = job['key_word'].strip()
            if key in beijing_job_counts:
                beijing_job_counts[key] += 1
            else:
                beijing_job_counts[key] = 1
    
    # 获取前10个职位类型
    top_job_titles = sorted(beijing_job_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"北京地区前10个职位类型: {top_job_titles}")
    
    # 如果没有足够的北京职位数据，使用全国数据作为备选
    if len(top_job_titles) < 5:
        print("北京地区职位数据不足，使用全国数据")
        all_job_counts = {}
        for job in job_data:
            if job['key_word'] and job['key_word'].strip():
                key = job['key_word'].strip()
                if key in all_job_counts:
                    all_job_counts[key] += 1
                else:
                    all_job_counts[key] = 1
        top_job_titles = sorted(all_job_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"全国前10个职位类型: {top_job_titles}")
    
    job_titles = [{"name": title, "value": count} for title, count in top_job_titles]
    
    # 获取各大公司招聘岗位数量top10
    company_counts = {}
    for job in job_data:
        if job['company']:
            if job['company'] in company_counts:
                company_counts[job['company']] += 1
            else:
                company_counts[job['company']] = 1
    
    top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ll = [f"{company}: {count}个岗位" for company, count in top_companies]
    
    # 获取职位所需能力/技能分布
    skills_data = {}
    # 添加技能薪资统计
    skill_salary_data = {}
    
    for job in job_data:
        if job['name']:
            # 提取常见技能关键词
            skills = extract_skills_from_name(job['name'])
            for skill in skills:
                # 统计技能出现次数
                if skill in skills_data:
                    skills_data[skill] += 1
                else:
                    skills_data[skill] = 1
                
                # 统计技能薪资
                try:
                    # 提取薪资范围
                    salary_max = float(re.findall(r'-(\d+)k', job['salary'])[0])
                    salary_min = float(re.findall(r'(\d+)-', job['salary'])[0])
                    avg_salary = (salary_min + salary_max) / 2
                    
                    if skill in skill_salary_data:
                        skill_salary_data[skill]['total'] += avg_salary
                        skill_salary_data[skill]['count'] += 1
                    else:
                        skill_salary_data[skill] = {'total': avg_salary, 'count': 1}
                except:
                    pass
    
    # 计算每种技能的平均薪资
    skill_avg_salary = {}
    for skill, data in skill_salary_data.items():
        if data['count'] > 0:
            skill_avg_salary[skill] = round(data['total'] / data['count'], 1)
    
    # 获取前10个技能（按出现次数排序）
    top_skills = sorted(skills_data.items(), key=lambda x: x[1], reverse=True)[:10]
    abi_name = [skill for skill, _ in top_skills]
    abi_snum = [count for _, count in top_skills]
    
    # 获取前8个技能的平均薪资（按薪资排序）
    top_salary_skills = sorted(skill_avg_salary.items(), key=lambda x: x[1], reverse=True)[:8]
    skill_names = [skill for skill, _ in top_salary_skills]
    skill_salaries = [salary for _, salary in top_salary_skills]
    
    print("技能平均薪资:", top_salary_skills)
    
    # 准备热力图数据
    filtered_data = []
    for i, city in enumerate(top_cities_names[:6]):  # 取前6个城市
        city_data = {
            "name": city,
            "value": job_price[i] if i < len(job_price) else 0
        }
        filtered_data.append(city_data)
    
    return render(request, "可视化大屏.html", {
        'job': json.dumps(city_names),  # 使用city_names代替job
        'job1': json.dumps(city_counts_list),  # 使用city_counts_list代替job1
        'data2': json.dumps(data2),
        'job_price_index': json.dumps(job_price_index),
        'job_price': json.dumps(job_price),
        'java_cities_price': json.dumps(java_cities_price),
        'python_cities_price': json.dumps(python_cities_price),
        'web_cities_price': json.dumps(web_cities_price),
        'hadoop_cities_price': json.dumps(hadoop_cities_price),
        'abi_name': json.dumps(abi_name),
        'abi_snum': json.dumps(abi_snum),
        'skill_names': json.dumps(skill_names),
        'skill_salaries': json.dumps(skill_salaries),
        'job_titles': json.dumps(job_titles),
        'filtered_data': json.dumps(filtered_data),
        'lendata': lendata,
        'unique_job_count': unique_job_count,
        'll': ll
    })

def calculate_avg_salary_from_dict(jobs):
    """
    计算职位字典列表的平均薪资
    """
    if not jobs:
        return 0  # 如果没有职位数据，返回0
        
    total_salary = 0
    valid_count = 0
    for job in jobs:
        try:
            # 提取最高薪资
            salary_max = float(re.findall(r'-(\d+)k', job['salary'])[0])
            total_salary += salary_max
            valid_count += 1
        except:
            pass
            
    # 计算平均值
    if valid_count > 0:
        return round(total_salary / valid_count, 1)
    else:
        # 如果没有有效的薪资数据，返回0
        return 0

def extract_skills_from_name(job_name):
    """
    从职位名称中提取技能关键词
    """
    skills = []
    common_skills = [
        'Java', 'Python', 'C++', 'C#', 'PHP', 'JavaScript', 'TypeScript', 
        'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'Spring', 
        'MySQL', 'Oracle', 'SQL Server', 'MongoDB', 'Redis', 'Docker', 
        'Kubernetes', 'AWS', 'Azure', 'GCP', 'Linux', 'Git', 'AI', 
        '机器学习', '深度学习', '数据分析', '大数据', 'Hadoop', 'Spark', 
        '前端', '后端', '全栈', '测试', '运维', '产品', 'UI', 'UX', '设计'
    ]
    
    for skill in common_skills:
        if skill.lower() in job_name.lower() or skill in job_name:
            skills.append(skill)
    
    return skills

def calculate_avg_salary(jobs):
    """
    计算职位列表的平均薪资
    """
    if not jobs:
        return 0
        
    total_salary = 0
    valid_count = 0
    for job in jobs:
        try:
            # 提取最高薪资
            salary_max = float(re.findall(r'-(\d+)k', job.salary)[0])
            total_salary += salary_max
            valid_count += 1
        except:
            pass
            
    # 计算平均值
    return round(total_salary / valid_count, 1) if valid_count > 0 else 0
