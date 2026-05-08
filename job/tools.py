# -*- coding: utf-8 -*-
# @File: tools.py
# @IDE: PyCharm

import time
from lxml import etree
from multiprocessing.dummy import Pool
import pymysql
import csv
import datetime
import random
import re
from functools import wraps

import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ========== 注释：数据库连接池（已移除） ==========
# 由于虚拟环境中DBUtils.PooledDB未安装，已移除数据库连接池实现
# 回退到原始数据库连接方式

# ========== 新增：重试机制装饰器 ==========
def retry(max_retries=3, delay=2, backoff=2, exceptions=(Exception,)):
    """
    重试装饰器
    :param max_retries: 最大重试次数
    :param delay: 初始延迟时间（秒）
    :param backoff: 延迟倍数
    :param exceptions: 需要重试的异常类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries == max_retries:
                        print(f"函数 {func.__name__} 重试 {max_retries} 次后失败: {e}")
                        raise
                    print(f"函数 {func.__name__} 第 {retries} 次失败，{current_delay}秒后重试: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

# ========== 新增：数据清洗函数 ==========
def clean_salary(salary_str):
    """
    清洗薪资数据（已去除复杂清洗，仅保留基本处理）
    :param salary_str: 原始薪资字符串
    :return: 处理后的薪资字符串
    """
    if not salary_str or not isinstance(salary_str, str):
        return "面议"
    
    # 仅去除首尾空格，保留原始格式
    return salary_str.strip()

def clean_experience(exp_str):
    """
    清洗经验要求
    :param exp_str: 原始经验字符串
    :return: 清洗后的经验字符串
    """
    if not exp_str or not isinstance(exp_str, str):
        return "经验不限"
    
    exp_str = exp_str.strip()
    
    # 标准化经验描述
    exp_mapping = {
        '在校生': '应届生',
        '应届': '应届生',
        '1年以内': '1年以下',
        '1年以下': '1年以下',
        '1-3年': '1-3年',
        '3-5年': '3-5年',
        '5-10年': '5-10年',
        '10年以上': '10年以上',
        '经验不限': '经验不限',
        '无经验': '经验不限'
    }
    
    for key, value in exp_mapping.items():
        if key in exp_str:
            return value
    
    return exp_str

def clean_education(edu_str):
    """
    清洗学历要求
    :param edu_str: 原始学历字符串
    :return: 清洗后的学历字符串
    """
    if not edu_str or not isinstance(edu_str, str):
        return "学历不限"
    
    edu_str = edu_str.strip()
    
    # 标准化学历描述
    edu_mapping = {
        '大专': '大专',
        '本科': '本科',
        '硕士': '硕士',
        '博士': '博士',
        '中专': '中专',
        '高中': '高中',
        '初中': '初中',
        '学历不限': '学历不限',
        '不限': '学历不限'
    }
    
    for key, value in edu_mapping.items():
        if key in edu_str:
            return value
    
    return edu_str

def clean_company_scale(scale_str):
    """
    清洗公司规模数据（已去除复杂清洗，仅保留基本处理）
    :param scale_str: 原始公司规模字符串
    :return: 处理后的公司规模字符串
    """
    if not scale_str or not isinstance(scale_str, str):
        return "规模未知"
    
    # 仅去除首尾空格，保留原始格式
    return scale_str.strip()

# ========== 新增：随机等待时间 ==========
def random_wait(min_time=3, max_time=8):
    """
    随机等待时间
    :param min_time: 最小等待时间（秒）
    :param max_time: 最大等待时间（秒）
    """
    wait_time = random.uniform(min_time, max_time)
    time.sleep(wait_time)
    return wait_time

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 指定 chromedriver 的路径
driver_path = os.path.join(current_dir, 'chromedriver.exe')  # 确保 chromedriver 文件名是正确的
# 城市数据文件路径
city_data_path = os.path.join(current_dir, 'city_data.json')
# 导出数据的目录
export_dir = os.path.join(current_dir, 'exports')
if not os.path.exists(export_dir):
    os.makedirs(export_dir)

# city, all_page, spider_code
def lieSpider(key_word, city, all_page, export_to_csv=True):
    """
    主函数，用于启动爬虫
    :param key_word: 搜索关键词
    :param city: 城市名称
    :param all_page: 需要爬取的页数
    :param export_to_csv: 是否导出到CSV文件
    """
    # 使用get_city_code函数获取城市代码，如果找不到则使用默认值'410'（全国）
    city_code = get_city_code(city)
    if not city_code:
        print(f"未找到城市 '{city}' 的代码，使用默认值'410'（全国）")
        city_code = '410'
    else:
        print(f"获取到城市 '{city}' 的代码: {city_code}")
    
    # 生成需要爬取的URL列表
    urls_list = get_urls(key_word, all_page, city_code)
    print(f"将爬取 {len(urls_list)} 个页面，关键词: {key_word}，城市: {city}({city_code})")
    
    # 创建一个共享的列表，用于收集所有爬取到的职位信息
    all_jobs = []
    
    # 使用线程池进行多线程爬取
    pool = Pool(2)  # 适当增加线程数，但不宜过多以免被封IP
    results = pool.map(lambda url: get_pages(url, collect_jobs=True), urls_list)
    pool.close()
    pool.join()
    
    # 收集所有爬取到的职位信息
    for result in results:
        if result:
            all_jobs.extend(result)
    
    print(f"爬虫执行完成，共获取 {len(all_jobs)} 条职位信息")
    
    # 如果需要导出到CSV文件
    if export_to_csv and all_jobs:
        export_jobs_to_csv(all_jobs, key_word, city)
    
    return all_jobs


def get_urls(key_word, all_page, city_code):
    """
    生成需要爬取的URL列表
    :param key_word: 搜索关键词
    :param all_page: 需要爬取的页数
    :param city_code: 城市代码
    :return: URL列表
    """
    urls_list = []
    for page in range(1, int(all_page) + 1):
        url = f'https://www.liepin.com/zhaopin/?city={city_code}&dq={city_code}&currentPage={page}&pageSize=40&key={key_word}'
        urls_list.append(url)
    return urls_list


def get_city():
    """
    抓取城市列表及其对应的代码
    :return: 城市列表，每个元素为[城市名称, 城市代码]
    """
    # 检查是否已有缓存的城市数据
    if os.path.exists(city_data_path):
        try:
            with open(city_data_path, 'r', encoding='utf-8') as f:
                city_list = json.load(f)
                print(f"从缓存加载了 {len(city_list)} 个城市数据")
                return city_list
        except Exception as e:
            print(f"加载缓存的城市数据失败: {e}")
    
    print('开始抓取城市列表...')

    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1920,1080')  # 设置窗口大小，确保元素可见

    # 使用 Service 指定 chromedriver 路径
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # 访问猎聘网职位搜索页面
        driver.get('https://www.liepin.com/zhaopin/?inputFrom=head_navigation&scene=init&workYearCode=0&ckId=ayvlgrooqq8e4w2b3yoae69sd91dmbq9')
        print("页面加载中...")
        time.sleep(5)  # 增加等待时间，确保页面完全加载
        
        # 创建一个包含所有城市和对应代码的列表
        all_city_list = []
        
        # 先点击"其他"按钮以展开更多城市选项
        try:
            print("尝试定位'其他'按钮...")
            
            # 尝试多种定位方式
            try:
                # 方法1：使用ID直接定位
                other_city_btn = driver.find_element('id', 'filter-option-other-city')
                print("通过ID找到'其他'按钮")
            except:
                try:
                    # 方法2：使用完整XPath定位
                    other_city_btn = driver.find_element('xpath', "//li[@class='options-item' and @id='filter-option-other-city']")
                    print("通过完整XPath找到'其他'按钮")
                except:
                    # 方法3：使用包含文本"其他"的元素定位
                    other_city_btn = driver.find_element('xpath', "//li[contains(@class, 'options-item')]//span[text()='其他']/parent::li")
                    print("通过文本内容找到'其他'按钮")
            
            # 打印按钮信息以便调试
            print(f"找到'其他'按钮: {other_city_btn.get_attribute('outerHTML')}")
            
            # 尝试多种点击方式
            try:
                # 方法1：直接点击
                other_city_btn.click()
                print("直接点击'其他'按钮")
            except:
                try:
                    # 方法2：使用JavaScript点击
                    driver.execute_script("arguments[0].click();", other_city_btn)
                    print("使用JavaScript点击'其他'按钮")
                except:
                    # 方法3：使用Actions链
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(other_city_btn).click().perform()
                    print("使用Actions链点击'其他'按钮")
            
            print("点击'其他'按钮后等待...")
            time.sleep(3)  # 等待展开动画完成
            
            # 截图保存，便于调试
            driver.save_screenshot('after_click_other.png')
            print(f"截图已保存到: {os.path.abspath('after_click_other.png')}")
            
            # 检查是否成功展开省份列表
            province_elements = driver.find_elements('xpath', '//ul[contains(@class, "ant-menu")]/li')
            print(f"找到 {len(province_elements)} 个省份元素")
            
            if len(province_elements) > 0:
                # 处理省份和城市
                for province_element in province_elements:
                    try:
                        # 获取省份名称和代码
                        province_name = province_element.find_element('xpath', './/span[contains(@class, "ant-menu-text")]').text
                        province_code = province_element.get_attribute('data-code')
                        print(f"处理省份: {province_name}, 代码: {province_code}")
                        
                        # 点击省份以显示其下属城市
                        driver.execute_script("arguments[0].click();", province_element)
                        time.sleep(2)  # 增加等待时间
                        
                        # 获取该省份下所有城市
                        city_elements = driver.find_elements('xpath', '//div[contains(@class, "data-list")]/ul/li')
                        print(f"在 {province_name} 下找到 {len(city_elements)} 个城市")
                        
                        if len(city_elements) > 0:
                            # 添加省份本身
                            all_city_list.append([province_name, province_code])
                            
                            # 添加该省份下的所有城市
                            for city_element in city_elements:
                                try:
                                    city_id = city_element.get_attribute('id')
                                    city_name = city_element.text
                                    
                                    # 如果有id属性，说明是具体城市而非"全XX省"选项
                                    if city_id and city_id.startswith('code_'):
                                        city_code = city_id.replace('code_', '')    #数据清洗
                                        all_city_list.append([city_name, city_code])
                                        print(f"添加城市: {city_name}, 代码: {city_code}")
                                except Exception as e:
                                    print(f"处理城市元素时出错: {e}")
                    except Exception as e:
                        print(f"处理省份元素时出错: {e}")
            else:
                print("未找到省份列表，可能点击'其他'按钮失败")
                
        except Exception as e:
            print(f"点击'其他'按钮或获取城市失败: {e}")
            
            # 如果上面的方法失败，尝试使用原来的方法获取一些基本城市
            print("尝试使用备用方法获取城市列表...")
            req_html = etree.HTML(driver.page_source)
            code_list = req_html.xpath('//li[@data-key="dq"]/@data-code')
            name_list = req_html.xpath('//li[@data-key="dq"]/@data-name')
            all_city_list = [[name, code] for name, code in zip(name_list, code_list)]
            print(f"使用备用方法找到 {len(all_city_list)} 个城市")
        
        print('抓取到的城市列表:', all_city_list)
        
        # 在函数结尾，成功获取数据后保存到文件
        try:
            # 保存城市列表到JSON文件
            save_city_list(all_city_list)
            print(f"城市数据已保存到: {os.path.abspath(city_data_path)}")
        except Exception as e:
            print(f"保存城市数据失败: {e}")
        
        return all_city_list
    except Exception as e:
        print('抓取城市列表失败:', e)
        return []
    finally:
        driver.quit()


def save_city_list(city_list):
    """
    将城市列表保存到JSON文件
    :param city_list: 城市列表，每个元素为[城市名称, 城市代码]
    """
    with open(city_data_path, 'w', encoding='utf-8') as f:
        json.dump(city_list, f, ensure_ascii=False, indent=4)


def load_city_list():
    """
    从JSON文件加载城市列表
    :return: 城市列表，每个元素为[城市名称, 城市代码]，如果文件不存在则返回空列表
    """
    if not os.path.exists(city_data_path):
        print(f"城市数据文件不存在: {city_data_path}")
        return []
        
    try:
        with open(city_data_path, 'r', encoding='utf-8') as f:
            city_list = json.load(f)
            print(f"成功加载了 {len(city_list)} 个城市数据")
            return city_list
    except Exception as e:
        print(f"加载城市数据失败: {e}")
        return []


def get_city_dict():
    """
    获取城市代码字典，格式为 {城市名称: 城市代码}
    处理重复城市名称的问题，优先使用省级城市代码
    :return: 城市代码字典
    """
    city_list = load_city_list()
    city_dict = {}
    
    # 首先添加所有城市
    for city_name, city_code in city_list:
        # 如果城市名称已存在且当前代码更短（通常省级城市代码更短），则更新
        if city_name in city_dict:
            # 优先使用较短的代码（通常是省级城市代码）
            if len(city_code) < len(city_dict[city_name]):
                city_dict[city_name] = city_code
        else:
            city_dict[city_name] = city_code
    
    # 添加特殊城市代码
    city_dict['全国'] = '410'  # 确保全国代码存在
    
    return city_dict


def get_city_code(city_name):
    """
    根据城市名称获取城市代码
    :param city_name: 城市名称
    :return: 城市代码，如果不存在则返回None
    """
    city_dict = get_city_dict()
    return city_dict.get(city_name)


def export_jobs_to_csv(jobs, key_word, city):
    """
    将爬取到的职位信息导出到CSV文件
    :param jobs: 职位信息列表
    :param key_word: 搜索关键词
    :param city: 城市名称
    """
    if not jobs:
        print("没有职位信息可导出")
        return
    
    # 生成文件名，包含关键词、城市和时间戳
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{key_word}_{city}_{timestamp}.csv"
    filepath = os.path.join(export_dir, filename)
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:  # 使用utf-8-sig编码，支持Excel打开
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(['职位名称', '薪资待遇', '工作地点', '学历要求', '经验要求', 
                            '公司名称', '公司行业', '公司规模', '详情链接', '搜索关键词', '城市'])
            
            # 写入数据
            for job in jobs:
                writer.writerow([
                    job['name'], job['salary'], job['address'], job['education'],
                    job['experience'], job['company'], job['label'], job['scale'],
                    job['href'], job['key_word'], job['city_name']
                ])
        
        print(f"职位信息已导出到: {filepath}")
    except Exception as e:
        print(f"导出职位信息失败: {e}")


@retry(max_retries=3, delay=3, backoff=2, exceptions=(Exception,))
def get_pages(url, collect_jobs=False):
    """
    爬取单个页面的职位信息并存储到数据库
    :param url: 需要爬取的页面URL
    :param collect_jobs: 是否收集职位信息并返回
    :return: 如果collect_jobs为True，则返回职位信息列表，否则返回None
    """
    # ========== 新增：加强错误处理和数据验证 ==========
    try:
        # 从URL中提取城市代码和关键词
        import re
        city_code_match = re.search(r'city=([^&]+)', url)
        key_word_match = re.search(r'key=([^&]+)', url)
        
        city_code = city_code_match.group(1) if city_code_match else '410'
        key_word = key_word_match.group(1) if key_word_match else ''
        
        # 验证城市代码和关键词
        if not city_code or not isinstance(city_code, str):
            print(f"警告: 无效的城市代码: {city_code}")
            city_code = '410'
        
        if not key_word or not isinstance(key_word, str):
            print(f"警告: 无效的关键词: {key_word}")
            key_word = ''
        
        # 获取城市名称（仅用于日志显示，不存入数据库）
        city_name = get_city_name(city_code) or '未知城市'
        
        print(f'开始爬取 {url}...')
        print(f'城市: {city_name}({city_code}), 关键词: {key_word}')

        # ========== 修改：加强数据库连接错误处理 ==========
        mysql_conn = get_mysql()
        if not mysql_conn:
            print("错误: 数据库连接失败，无法继续爬取")
            return [] if collect_jobs else None
        
        conn = mysql_conn[0]
        cur = mysql_conn[1]
        
        if not conn or not cur:
            print("错误: 数据库连接或游标获取失败")
            return [] if collect_jobs else None

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        # 添加user-agent避免被检测
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        # 添加更多反检测选项
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(driver_path)
        driver = None
        
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            # 执行CDP命令避免检测
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
        except Exception as e:
            print(f"Chrome驱动初始化失败: {e}")
            if conn:
                cur.close()
                conn.close()
            return [] if collect_jobs else None
        
        # 用于收集职位信息的列表
        jobs_list = [] if collect_jobs else None

        # 移除内层try块，将代码直接放在这里
        driver.get(url)
        # ========== 修改：使用随机等待时间替换固定等待 ==========
        wait_time = random_wait(4, 7)  # 随机等待4-7秒
        print(f"页面加载完成，随机等待 {wait_time:.2f} 秒...")
        
        req_html = etree.HTML(driver.page_source)

        # 使用新的XPath选择器提取职位信息
        # 职位名称（从title属性获取完整名称）
        name = req_html.xpath('//div[@class="ellipsis-1"]/@title')
        if not name:
            # 如果没有title属性，直接获取文本
            name = req_html.xpath('//div[@class="ellipsis-1"]/text()')
        
        # 薪资（包含急聘标签的span）
        salary = req_html.xpath('//span[@class="_40108E8PWS"]/text()')
        
        # 地点（在职位信息区域的span）
        address = req_html.xpath('//div[@class="_40108__9nJ"]/span[@class="ellipsis-1"]/text()')
        
        # 经验和学历（在job-labels区域）
        experience = req_html.xpath('//div[@class="_40108KeJJy"]/span[@class="_40108hJbMl"][1]/text()')
        education = req_html.xpath('//div[@class="_40108KeJJy"]/span[@class="_40108hJbMl"][2]/text()')
        
        # 公司名称
        com_name = req_html.xpath('//span[@class="_40108K6Y1c ellipsis-1"]/text()')
        
        # 公司标签（行业、融资、规模等）
        tag_list = req_html.xpath('//div[@class="_40108hFeAm ellipsis-1"]')
        
        # 职位链接
        href_list = req_html.xpath('//a[@data-nick="job-detail-job-info"]/@href')

        # 处理公司标签信息
        label_list = []
        scale_list = []
        for tag in tag_list:
            span_list = tag.xpath('./span/text()')
            if span_list:
                # 第一个是行业，最后一个是规模
                label_list.append(span_list[0] if len(span_list) > 0 else '')
                scale_list.append(span_list[-1] if len(span_list) > 0 else '')
            else:
                label_list.append('')
                scale_list.append('')

        # 确保所有列表长度一致，取最小长度
        lists = [name, salary, address, education, experience, com_name, label_list, scale_list, href_list]
        min_length = min(len(lst) for lst in lists if lst)  #数据对齐
        
        if min_length == 0:
            print('未抓取到任何数据，可能页面结构已变化或需要登录')
            return [] if collect_jobs else None

        # 截取所有列表到相同长度
        name = name[:min_length]
        salary = salary[:min_length]
        address = address[:min_length]
        education = education[:min_length]
        experience = experience[:min_length]
        com_name = com_name[:min_length]
        label_list = label_list[:min_length]
        scale_list = scale_list[:min_length]
        href_list = href_list[:min_length]

        print(f"获取到 {min_length} 条职位信息")
        print("-" * 80)

        # ========== 修改：数据去重优化 ==========
        # 优化数据库查询，只查询当前批次的href，避免全表查询
        href_list_str = "','".join([href.split('?')[0] for href in href_list])
        select_sql = f"SELECT href FROM job_data WHERE href IN ('{href_list_str}')"
        try:
            cur.execute(select_sql)
            href_list_mysql = [x[0] for x in cur.fetchall()]
        except Exception as e:
            print(f"查询数据库失败，使用全表查询: {e}")
            # 如果查询失败，回退到全表查询
            select_sql = 'SELECT href FROM job_data'
            cur.execute(select_sql)
            href_list_mysql = [x[0] for x in cur.fetchall()]

        # 使用原始的插入语句，不添加city_code和city_name字段
        insert_sql = '''INSERT INTO job_data(name, salary, place, education, experience, company, label, scale, href, key_word) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        inserted_count = 0
        for i in range(min_length):
            href = href_list[i].split('?')[0]
            
            # ========== 新增：数据清洗 ==========
            cleaned_salary = clean_salary(salary[i] if i < len(salary) else '')
            cleaned_experience = clean_experience(experience[i] if i < len(experience) else '')
            cleaned_education = clean_education(education[i] if i < len(education) else '')
            cleaned_scale = clean_company_scale(scale_list[i] if i < len(scale_list) else '')
            
            # 数据验证
            if not name[i] or not isinstance(name[i], str) or len(name[i].strip()) == 0:
                print(f"警告: 第{i+1}条数据职位名称为空或无效，跳过")
                continue
            
            if not href or not isinstance(href, str) or len(href.strip()) == 0:
                print(f"警告: 第{i+1}条数据链接为空或无效，跳过")
                continue
            
            # 输出每个岗位的详细信息
            print(f"岗位 {i+1}/{min_length}:")
            print(f"  职位名称: {name[i]}")
            
            # 薪资待遇：只有当清洗后的数据与原始数据不同时才显示箭头
            original_salary = salary[i] if i < len(salary) else ''
            if original_salary != cleaned_salary:
                print(f"  薪资待遇: {original_salary} -> {cleaned_salary}")
            else:
                print(f"  薪资待遇: {original_salary}")
            
            # 工作地点：没有清洗函数，直接输出
            print(f"  工作地点: {address[i] if i < len(address) else ''}")
            
            # 学历要求：只有当清洗后的数据与原始数据不同时才显示箭头
            original_education = education[i] if i < len(education) else ''
            if original_education != cleaned_education:
                print(f"  学历要求: {original_education} -> {cleaned_education}")
            else:
                print(f"  学历要求: {original_education}")
            
            # 经验要求：只有当清洗后的数据与原始数据不同时才显示箭头
            original_experience = experience[i] if i < len(experience) else ''
            if original_experience != cleaned_experience:
                print(f"  经验要求: {original_experience} -> {cleaned_experience}")
            else:
                print(f"  经验要求: {original_experience}")
            
            # 公司名称：没有清洗函数，直接输出
            print(f"  公司名称: {com_name[i] if i < len(com_name) else ''}")
            
            # 公司行业：没有清洗函数，直接输出
            print(f"  公司行业: {label_list[i] if i < len(label_list) else ''}")
            
            # 公司规模：只有当清洗后的数据与原始数据不同时才显示箭头
            original_scale = scale_list[i] if i < len(scale_list) else ''
            if original_scale != cleaned_scale:
                print(f"  公司规模: {original_scale} -> {cleaned_scale}")
            else:
                print(f"  公司规模: {original_scale}")
            
            print(f"  详情链接: {href}")
            print(f"  搜索关键词: {key_word}")
            print(f"  城市: {city_name}")
            print("-" * 50)
            
            # 如果需要收集职位信息，则添加到列表中
            if collect_jobs:
                job_info = {
                    'name': name[i],
                    'salary': cleaned_salary,  # 使用清洗后的薪资
                    'address': address[i] if i < len(address) else '',
                    'education': cleaned_education,  # 使用清洗后的学历
                    'experience': cleaned_experience,  # 使用清洗后的经验
                    'company': com_name[i] if i < len(com_name) else '',
                    'label': label_list[i] if i < len(label_list) else '',
                    'scale': cleaned_scale,  # 使用清洗后的规模
                    'href': href,
                    'key_word': key_word,
                    'city_name': city_name,
                    'city_code': city_code
                }
                jobs_list.append(job_info)
            
            if href not in href_list_mysql:
                # 使用清洗后的数据插入数据库
                data = (name[i], cleaned_salary, 
                        address[i] if i < len(address) else '', 
                        cleaned_education, 
                        cleaned_experience, 
                        com_name[i] if i < len(com_name) else '', 
                        label_list[i] if i < len(label_list) else '', 
                        cleaned_scale, 
                        href, key_word)
                try:
                    cur.execute(insert_sql, data)
                    conn.commit()
                    inserted_count += 1
                    print(f"  状态: 已插入数据库（使用清洗后数据）")
                except Exception as e:
                    print(f"  状态: 插入数据库失败: {e}")
                    conn.rollback()
            else:
                print(f"  状态: 数据已存在，跳过")
                print("-" * 50)
    
        print(f"成功插入 {inserted_count} 条新职位数据")
        return jobs_list

    except Exception as e:
        print(f'爬取页面 {url} 失败: {e}')
        return [] if collect_jobs else None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        if driver:
            driver.quit()


# ========== 修改：数据库连接（原始版本） ==========
def get_mysql():
    """
    连接MySQL数据库（原始连接方式）
    :return: 数据库连接和游标
    """
    try:
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='123456',
            database='recommend_job',
            autocommit=True,
            charset='utf8mb4'
        )
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f'连接数据库失败: {e}')
        return None, None


def get_city_name(city_code):
    """
    根据城市代码获取城市名称
    :param city_code: 城市代码
    :return: 城市名称，如果不存在则返回None
    """
    city_list = load_city_list()
    for city_name, code in city_list:
        if code == city_code:
            return city_name
    return None


def get_city_info():
    """
    获取所有城市信息，返回两个字典：
    1. 城市名称到代码的映射
    2. 城市代码到名称的映射
    :return: (name_to_code_dict, code_to_name_dict)
    """
    city_list = load_city_list()
    name_to_code = {}
    code_to_name = {}
    
    # 处理所有城市
    for city_name, city_code in city_list:
        # 名称到代码的映射（优先使用较短的代码）
        if city_name in name_to_code:
            if len(city_code) < len(name_to_code[city_name]):
                name_to_code[city_name] = city_code
        else:
            name_to_code[city_name] = city_code
        
        # 代码到名称的映射（优先使用较短的名称）
        if city_code in code_to_name:
            if len(city_name) < len(code_to_name[city_code]):
                code_to_name[city_code] = city_name
        else:
            code_to_name[city_code] = city_name
    
    # 添加特殊城市代码
    name_to_code['全国'] = '410'
    code_to_name['410'] = '全国'
    
    return name_to_code, code_to_name


if __name__ == '__main__':
    # 设置爬取参数
    keyword = 'python'  # 搜索关键词
    city_name = '广州'  # 城市名称
    pages = '1'  # 爬取页数
    
    # 获取城市代码
    code = get_city_code(city_name)
    if not code:
        print(f"未找到城市 '{city_name}' 的代码，使用默认值'410'（全国）")
        city_name = '全国'
    else:
        print(f"城市 '{city_name}' 的代码是: {code}")
    
    # 执行爬虫并导出到CSV
    print(f"开始爬取 '{keyword}' 在 '{city_name}' 的职位信息，共 {pages} 页...")
    jobs = lieSpider(keyword, city_name, pages, export_to_csv=True)
    print(f"爬取完成，共获取到 {len(jobs)} 条职位信息")
