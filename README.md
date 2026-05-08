# 基于Python的招聘数据分析推荐系统

## 项目简介

本系统是一个基于 Django + MySQL 的招聘数据分析与职位推荐系统，集成了数据采集、数据处理、可视化分析和智能推荐等功能。

## 目录结构
 
```
├── JobRecommend/                # Django 项目配置目录
│   ├── settings.py             # 项目配置文件（数据库、静态文件等）
│   ├── urls.py                 # 主路由配置
│   ├── wsgi.py                 # WSGI 部署配置
│   └── asgi.py                 # ASGI 部署配置
│
├── job/                        # 核心应用目录
│   ├── views.py                # 视图函数（业务逻辑）
│   ├── urls.py                 # 应用路由配置
│   ├── models.py               # 数据模型定义
│   ├── tools.py                # 爬虫工具（猎聘网数据采集）
│   ├── job_recommend.py        # 职位推荐算法（协同过滤）
│   ├── salary_prediction.py    # 薪资预测模型（机器学习）
│   ├── admin.py                # 后台管理配置
│   ├── city_data.json          # 城市代码数据
│   ├── chromedriver.exe        # Chrome 浏览器驱动
│   ├── models/                 # 训练好的机器学习模型
│   │   ├── random_forest_*.pkl
│   │   └── gradient_boosting_*.pkl
│   ├── exports/                # 爬虫导出的 CSV 文件
│   └── migrations/             # 数据库迁移文件
│
├── templates/                  # HTML 模板目录
│   ├── index.html              # 主页框架
│   ├── login.html              # 登录页面
│   ├── register.html           # 注册页面
│   ├── welcome.html            # 控制台页面
│   ├── job_list.html           # 职位列表页面
│   ├── recommend.html          # 职位推荐页面
│   ├── data_visualization.html # 数据可视化分析页面
│   ├── salary_prediction.html  # 薪资预测页面
│   ├── skill_heatmap.html      # 技能热度地图
│   ├── 可视化大屏.html          # 可视化大屏展示
│   └── ...                     # 其他页面模板
│
├── static/                     # 静态资源目录
│   ├── css/                    # 样式文件
│   ├── js/                     # JavaScript 文件
│   ├── images/                 # 图片资源
│   ├── layuiadmin/             # Layui 管理后台框架
│   └── echarts.min.js          # ECharts 图表库
│
├── manage.py                   # Django 管理脚本
├── requirements.txt            # Python 依赖包列表
├── recommend_job.sql           # 数据库初始化 SQL 文件
└── train_and_test_model.py     # 模型训练测试脚本
```

## 功能模块

### 1. 数据采集模块
- 使用 Selenium + ChromeDriver 爬取猎聘网招聘数据
- 支持按关键词、城市、页数进行数据采集
- 采集字段：职位名称、薪资、地点、学历、经验、公司信息等
- 支持导出 CSV 文件

### 2. 数据集成模块
- Django ORM 管理 MySQL 数据库
- 基于物品的协同过滤推荐算法
- 机器学习薪资预测模型（随机森林、梯度提升、岭回归等）

### 3. 数据展示模块
- 控制台：职位统计、薪资 TOP10、系统监控
- 数据可视化：薪资分布、学历分布、职位关键词、城市分布
- 技能热度地图
- 可视化大屏
- 职位推荐与薪资预测

---

## 数据采集实现详解

### 采集流程概述

```
用户输入参数 → 生成URL列表 → 多线程爬取 → 解析HTML → 存入数据库 → 导出CSV
```

### 核心代码分析（job/tools.py）

#### 1. 爬虫入口函数

```python
def lieSpider(key_word, city, all_page, export_to_csv=True):
    """
    主函数，用于启动爬虫
    :param key_word: 搜索关键词（如 'java', 'python'）
    :param city: 城市名称（如 '北京', '上海'）
    :param all_page: 需要爬取的页数
    :param export_to_csv: 是否导出到CSV文件
    """
    # 1. 获取城市代码（猎聘网使用城市代码而非城市名）
    city_code = get_city_code(city)
    
    # 2. 生成需要爬取的URL列表
    urls_list = get_urls(key_word, all_page, city_code)
    
    # 3. 使用线程池进行多线程爬取（2个线程，避免被封IP）
    pool = Pool(2)
    results = pool.map(lambda url: get_pages(url, collect_jobs=True), urls_list)
    pool.close()
    pool.join()
    
    # 4. 收集所有爬取到的职位信息
    all_jobs = []
    for result in results:
        if result:
            all_jobs.extend(result)
    
    # 5. 导出到CSV文件
    if export_to_csv and all_jobs:
        export_jobs_to_csv(all_jobs, key_word, city)
    
    return all_jobs
```

#### 2. URL生成规则

```python
def get_urls(key_word, all_page, city_code):
    """
    生成猎聘网搜索URL列表
    URL格式: https://www.liepin.com/zhaopin/?city={城市代码}&currentPage={页码}&key={关键词}
    """
    urls_list = []
    for page in range(1, int(all_page) + 1):
        url = f'https://www.liepin.com/zhaopin/?city={city_code}&dq={city_code}&currentPage={page}&pageSize=40&key={key_word}'
        urls_list.append(url)
    return urls_list
```

#### 3. 页面解析与数据提取

```python
def get_pages(url, collect_jobs=False):
    """
    爬取单个页面的职位信息
    使用 Selenium 加载动态页面，lxml 解析 HTML
    """
    # 配置 Chrome 浏览器选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式，不显示浏览器窗口
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    # 添加 User-Agent 避免被检测为爬虫
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)...')
    
    # 启动浏览器并访问页面
    driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
    driver.get(url)
    time.sleep(5)  # 等待页面加载完成
    
    # 使用 lxml 解析 HTML
    req_html = etree.HTML(driver.page_source)
    
    # 使用 XPath 提取职位信息
    name = req_html.xpath('//div[@class="ellipsis-1"]/@title')           # 职位名称
    salary = req_html.xpath('//span[@class="_40108E8PWS"]/text()')       # 薪资
    address = req_html.xpath('//div[@class="_40108__9nJ"]/span[@class="ellipsis-1"]/text()')  # 地点
    experience = req_html.xpath('//div[@class="_40108KeJJy"]/span[@class="_40108hJbMl"][1]/text()')  # 经验
    education = req_html.xpath('//div[@class="_40108KeJJy"]/span[@class="_40108hJbMl"][2]/text()')   # 学历
    com_name = req_html.xpath('//span[@class="_40108K6Y1c ellipsis-1"]/text()')  # 公司名称
    tag_list = req_html.xpath('//div[@class="_40108hFeAm ellipsis-1"]')  # 公司标签
    href_list = req_html.xpath('//a[@data-nick="job-detail-job-info"]/@href')   # 职位链接
    
    # ... 数据处理和存储
```

#### 4. 数据存储（MySQL）

```python
# 连接数据库
conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    passwd='123456',
    database='recommend_job',
    charset='utf8mb4'
)

# 检查数据是否已存在（去重）
select_sql = 'SELECT href FROM job_data'
cur.execute(select_sql)
href_list_mysql = [x[0] for x in cur.fetchall()]

# 插入新数据
insert_sql = '''INSERT INTO job_data(name, salary, place, education, experience, 
                company, label, scale, href, key_word) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

for i in range(min_length):
    href = href_list[i].split('?')[0]
    if href not in href_list_mysql:  # 去重判断
        data = (name[i], salary[i], address[i], education[i], experience[i], 
               com_name[i], label_list[i], scale_list[i], href, key_word)
        cur.execute(insert_sql, data)
        conn.commit()
```

#### 5. 城市代码管理

```python
def get_city_code(city_name):
    """根据城市名称获取城市代码"""
    # 从 city_data.json 文件加载城市数据
    city_data_path = os.path.join(current_dir, 'city_data.json')
    with open(city_data_path, 'r', encoding='utf-8') as f:
        city_list = json.load(f)
    
    # 查找匹配的城市
    for name, code in city_list:
        if name == city_name:
            return code
    
    return '410'  # 默认返回"全国"代码
```

### 采集数据字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| name | 职位名称 | Java开发工程师 |
| salary | 薪资范围 | 15-25k |
| place | 工作地点 | 北京-海淀区 |
| education | 学历要求 | 本科 |
| experience | 经验要求 | 3-5年 |
| company | 公司名称 | 阿里巴巴 |
| label | 公司行业 | 互联网 |
| scale | 公司规模 | 10000人以上 |
| href | 职位链接 | https://www.liepin.com/job/xxx |
| key_word | 搜索关键词 | java |

---

## 数据集成实现详解

### 集成架构

```
                    ┌─────────────────┐
                    │   MySQL 数据库   │
                    │  recommend_job  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Django ORM   │   │  推荐算法模块  │   │  预测模型模块  │
│  数据模型管理  │   │  协同过滤推荐  │   │  薪资预测     │
└───────────────┘   └───────────────┘   └───────────────┘
```

### 1. 数据模型定义（job/models.py）

```python
class JobData(models.Model):
    """招聘信息数据模型"""
    job_id = models.AutoField('职位ID', primary_key=True)
    name = models.CharField('职位名称', max_length=255)
    salary = models.CharField('薪资', max_length=255)
    place = models.CharField('工作地点', max_length=255)
    education = models.CharField('学历要求', max_length=255)
    experience = models.CharField('工作经验', max_length=255)
    company = models.CharField('公司名称', max_length=255)
    label = models.CharField('职位标签', max_length=255)
    scale = models.CharField('公司规模', max_length=255)
    href = models.CharField('职位链接', max_length=255)
    key_word = models.CharField('关键词', max_length=255)

    class Meta:
        db_table = 'job_data'


class UserList(models.Model):
    """用户信息模型"""
    user_id = models.CharField('用户ID', primary_key=True, max_length=11)
    user_name = models.CharField('用户名', max_length=255)
    pass_word = models.CharField('密码', max_length=255)

    class Meta:
        db_table = 'user_list'


class SendList(models.Model):
    """用户投递记录模型"""
    send_id = models.AutoField(primary_key=True)
    job = models.ForeignKey(JobData, models.DO_NOTHING)  # 关联职位
    user = models.ForeignKey(UserList, models.DO_NOTHING)  # 关联用户

    class Meta:
        db_table = 'send_list'


class UserExpect(models.Model):
    """用户求职意向模型"""
    expect_id = models.AutoField(primary_key=True)
    key_word = models.CharField('期望职位', max_length=255)
    place = models.CharField('期望城市', max_length=255)
    user = models.ForeignKey(UserList, models.DO_NOTHING)

    class Meta:
        db_table = 'user_expect'


class UserJobInteraction(models.Model):
    """用户职位交互记录（评分、收藏）"""
    interaction_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(UserList, models.CASCADE)
    job = models.ForeignKey(JobData, models.CASCADE)
    rating = models.IntegerField('评分')  # 1-5星
    is_favorite = models.BooleanField('是否收藏', default=False)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_job_interaction'
        unique_together = ('user', 'job')  # 联合唯一约束
```

### 2. 职位推荐算法（job/job_recommend.py）

#### 算法原理：基于物品的协同过滤

```
用户A投递了职位1、职位2
用户B投递了职位1、职位3
→ 职位1和职位2相似，职位1和职位3相似
→ 给用户A推荐职位3，给用户B推荐职位2
```

#### 核心实现

```python
def similarity(job1_id, job2_id):
    """
    计算两个职位的相似度（余弦相似度）
    基于投递这两个职位的用户重合度
    """
    # 投递职位1的用户集合
    job1_set = models.SendList.objects.filter(job=job1_id)
    job1_sum = job1_set.count()
    
    # 投递职位2的用户数量
    job2_sum = models.SendList.objects.filter(job=job2_id).count()
    
    # 同时投递两个职位的用户数量（交集）
    common = models.SendList.objects.filter(
        user__in=Subquery(job1_set.values('user')), 
        job=job2_id
    ).values('user').count()
    
    # 余弦相似度计算
    if job1_sum == 0 or job2_sum == 0:
        return 0
    similar_value = common / sqrt(job1_sum * job2_sum)
    return similar_value


def recommend_by_item_id(user_id, k=9):
    """
    为用户推荐职位
    :param user_id: 用户ID
    :param k: 推荐数量
    :return: 推荐职位列表
    """
    # 1. 获取用户投递过的职位
    jobs_id = models.SendList.objects.filter(user_id=user_id).values('job_id')
    
    # 2. 分析用户偏好（投递最多的职位关键词）
    key_word_list = []
    for job in jobs_id:
        key_word_list.append(models.JobData.objects.get(job_id=job['job_id']).key_word)
    
    # 统计关键词频率，取前3个作为用户偏好
    user_prefer = sorted(set(key_word_list), key=key_word_list.count, reverse=True)[:3]
    
    # 3. 如果用户没有投递记录，使用求职意向推荐
    if len(jobs_id) == 0:
        user_expect = models.UserExpect.objects.filter(user=user_id).first()
        if user_expect:
            # 根据意向关键词和城市筛选职位
            job_list = models.JobData.objects.filter(
                name__icontains=user_expect.key_word,
                place__icontains=user_expect.place
            ).values()
            return random.sample(list(job_list), min(k, len(job_list)))
        else:
            # 随机推荐
            return random.sample(list(models.JobData.objects.all().values()), k)
    
    # 4. 获取用户未投递的、符合偏好的职位（随机取30个）
    un_send = models.JobData.objects.filter(
        ~Q(sendlist__user=user_id),  # 排除已投递的
        key_word__in=user_prefer      # 符合用户偏好
    ).order_by('?').values()[:30]
    
    # 5. 计算相似度并排序
    distances = []
    for un_send_job in un_send:
        for send_job in jobs_id:
            sim = similarity(un_send_job['job_id'], send_job['job_id'])
            distances.append((sim, un_send_job))
    
    # 按相似度降序排序
    distances.sort(key=lambda x: x[0], reverse=True)
    
    # 6. 返回前k个推荐结果
    recommend_list = []
    for mark, job in distances:
        if len(recommend_list) >= k:
            break
        if job not in recommend_list:
            recommend_list.append(job)
    
    return recommend_list
```

### 3. 薪资预测模型（job/salary_prediction.py）

#### 模型架构

```
原始数据 → 数据清洗 → 特征工程 → 模型训练 → 模型保存 → 在线预测
```

#### 数据预处理

```python
def prepare_data(self):
    """准备训练数据"""
    # 1. 从数据库获取所有职位数据
    job_data = list(JobData.objects.all().values())
    df = pd.DataFrame(job_data)
    
    # 2. 提取薪资数值（从 "10k-15k" 提取 10 和 15）
    def extract_salary(salary_str):
        match = re.search(r'(\d+)[kK]-(\d+)[kK]', salary_str)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None
    
    salary_data = df['salary'].apply(extract_salary)
    df['salary_min'] = salary_data.apply(lambda x: x[0])
    df['salary_max'] = salary_data.apply(lambda x: x[1])
    
    # 3. 数据清洗 - 移除异常值
    df = df.dropna(subset=['salary_min', 'salary_max'])
    df = df[(df['salary_max'] >= df['salary_min'])]
    df = df[df['salary_max'] <= df['salary_min'] * 3]  # 薪资差距不超过3倍
    
    # 4. 特征标准化
    # 学历映射
    education_mapping = {
        '博士': '博士', '硕士': '硕士', '本科': '本科',
        '大专': '大专', '不限': '不限'
    }
    
    # 经验映射
    experience_mapping = {
        '应届毕业生': '应届生', '1-3年': '1-3年', '3-5年': '3-5年',
        '5-10年': '5-10年', '10年以上': '10年以上', '不限': '不限'
    }
    
    # 5. 特征工程 - 提取职位级别
    df['position_level'] = '普通'
    senior_keywords = ['高级', '资深', '专家', 'senior', '总监', '经理']
    for keyword in senior_keywords:
        df.loc[df['name'].str.contains(keyword, na=False), 'position_level'] = '高级'
    
    return df
```

#### 模型训练

```python
def train_model(self, model_type='random_forest'):
    """训练薪资预测模型"""
    # 1. 准备数据
    df = self.prepare_data()
    
    # 2. 定义特征和目标变量
    categorical_features = ['education', 'experience', 'place', 'scale', 'key_word', 'position_level']
    X = df[categorical_features]
    y_min = df['salary_min']
    y_max = df['salary_max']
    
    # 3. 划分训练集和测试集
    X_train, X_test, y_min_train, y_min_test, y_max_train, y_max_test = train_test_split(
        X, y_min, y_max, test_size=0.2, random_state=42
    )
    
    # 4. 构建预处理管道
    preprocessor = ColumnTransformer(transformers=[
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='未知')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ]), categorical_features)
    ])
    
    # 5. 选择模型
    if model_type == 'random_forest':
        model = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42)
    elif model_type == 'gradient_boosting':
        model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05)
    
    # 6. 训练模型（分别训练最低薪资和最高薪资预测模型）
    min_pipeline = Pipeline([('preprocessor', preprocessor), ('model', model)])
    max_pipeline = Pipeline([('preprocessor', preprocessor), ('model', model)])
    
    min_pipeline.fit(X_train, y_min_train)
    max_pipeline.fit(X_train, y_max_train)
    
    # 7. 评估模型
    y_min_pred = min_pipeline.predict(X_test)
    y_max_pred = max_pipeline.predict(X_test)
    
    results = {
        'min_r2': r2_score(y_min_test, y_min_pred),
        'max_r2': r2_score(y_max_test, y_max_pred),
        'min_mae': mean_absolute_error(y_min_test, y_min_pred),
        'max_mae': mean_absolute_error(y_max_test, y_max_pred)
    }
    
    # 8. 保存模型
    self.save_model_to_file(model_type, min_pipeline, max_pipeline, results)
    
    return results
```

#### 在线预测

```python
def predict(self, education, experience, city, scale, key_word):
    """
    预测薪资范围
    :return: (最低薪资, 最高薪资) 单位：k
    """
    # 1. 加载模型
    self.load_model_from_file()
    
    # 2. 构建输入数据
    input_data = pd.DataFrame([{
        'education': education,
        'experience': experience,
        'place': city,
        'scale': scale,
        'key_word': key_word,
        'position_level': '普通'
    }])
    
    # 3. 预测
    salary_min = self.min_pipeline.predict(input_data)[0]
    salary_max = self.max_pipeline.predict(input_data)[0]
    
    return round(salary_min, 1), round(salary_max, 1)
```

### 数据库表结构

```sql
-- 职位数据表
CREATE TABLE job_data (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) COMMENT '职位名称',
    salary VARCHAR(255) COMMENT '薪资',
    place VARCHAR(255) COMMENT '工作地点',
    education VARCHAR(255) COMMENT '学历要求',
    experience VARCHAR(255) COMMENT '工作经验',
    company VARCHAR(255) COMMENT '公司名称',
    label VARCHAR(255) COMMENT '行业标签',
    scale VARCHAR(255) COMMENT '公司规模',
    href VARCHAR(255) COMMENT '职位链接',
    key_word VARCHAR(255) COMMENT '搜索关键词'
);

-- 用户表
CREATE TABLE user_list (
    user_id VARCHAR(11) PRIMARY KEY,
    user_name VARCHAR(255),
    pass_word VARCHAR(255)
);

-- 投递记录表
CREATE TABLE send_list (
    send_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT,
    user_id VARCHAR(11),
    FOREIGN KEY (job_id) REFERENCES job_data(job_id),
    FOREIGN KEY (user_id) REFERENCES user_list(user_id)
);

-- 用户求职意向表
CREATE TABLE user_expect (
    expect_id INT AUTO_INCREMENT PRIMARY KEY,
    key_word VARCHAR(255),
    place VARCHAR(255),
    user_id VARCHAR(11),
    FOREIGN KEY (user_id) REFERENCES user_list(user_id)
);

-- 用户职位交互表（评分、收藏）
CREATE TABLE user_job_interaction (
    interaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(11),
    job_id INT,
    rating INT,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_time DATETIME,
    updated_time DATETIME,
    UNIQUE KEY (user_id, job_id)
);

-- 薪资预测模型表
CREATE TABLE salary_prediction_model (
    model_id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(255),
    model_type VARCHAR(255),
    model_parameters TEXT,
    r2_score FLOAT,
    mean_absolute_error FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    created_time DATETIME,
    updated_time DATETIME
);
```

## 环境配置

### 1. 系统要求
- Python 3.9+
- MySQL 5.7+
- Chrome 浏览器（用于爬虫）

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

主要依赖包：
- Django==3.2.8
- PyMySQL==1.1.0
- selenium==4.15.2
- scikit-learn==1.4.0
- pandas==2.1.4
- numpy==1.26.4
- lxml==4.9.3
- psutil==5.9.6
- django-simpleui==2024.8.28

### 3. 配置数据库

1. 创建 MySQL 数据库：
```sql
CREATE DATABASE recommend_job CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 导入数据库结构和初始数据：
```bash
mysql -u root -p recommend_job < recommend_job.sql
```

3. 修改数据库配置（如需要）：

编辑 `JobRecommend/settings.py` 文件：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'recommend_job',
        'USER': 'root',
        'PASSWORD': '123456',  # 修改为你的密码
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 4. 配置 ChromeDriver（爬虫功能）

1. 查看 Chrome 浏览器版本
2. 下载对应版本的 ChromeDriver：https://chromedriver.chromium.org/downloads
3. 将 `chromedriver.exe` 放入 `job/` 目录

## 运行项目

### 1. 数据库迁移（首次运行）

```bash
python manage.py migrate
```

### 2. 创建管理员账号（可选）

```bash
python manage.py createsuperuser
```

### 3. 启动开发服务器

```bash
python manage.py runserver
```

### 4. 访问系统

- 前台系统：http://127.0.0.1:8000/
- 后台管理：http://127.0.0.1:8000/admin/

### 5. 默认账号

- 前台用户：账号 `1`，密码 `123456`
- 后台管理：账号 `1`，密码 `1`

## 使用说明

### 数据爬取
1. 登录系统后，进入「爬虫调度」→「数据爬取」
2. 输入搜索关键词、选择城市、设置爬取页数
3. 点击开始爬取，等待完成

### 数据可视化
1. 进入「数据管理」→「数据可视化」
2. 可查看薪资分布、学历分布、职位关键词、城市分布等图表
3. 支持按条件筛选数据

### 职位推荐
1. 进入「职位推荐」→「求职意向」设置期望职位和城市
2. 进入「职位推荐」→「职位推荐」查看个性化推荐

### 薪资预测
1. 进入「薪资预测」→「预测我的薪资」
2. 输入学历、经验、城市、技能等信息
3. 系统将预测薪资范围

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Django 3.2 |
| 数据库 | MySQL 5.7+ |
| 前端框架 | Layui + LayuiAdmin |
| 图表库 | ECharts |
| 爬虫 | Selenium + lxml |
| 机器学习 | scikit-learn |
| 数据处理 | Pandas + NumPy |

## 注意事项

1. 爬虫功能需要安装 Chrome 浏览器和对应版本的 ChromeDriver
2. 首次运行需要导入数据库 SQL 文件
3. 薪资预测功能需要先训练模型（系统已内置训练好的模型）
4. 推荐功能需要用户有投递记录或设置求职意向才能生效
