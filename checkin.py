import requests
import os  # 新增：用于读取环境变量
from lxml import etree

# --- 配置参数 ---
login_url = "https://vip.ioshashiqi.com/aspx3/mobile/login.aspx"
qiandao_url = "https://vip.ioshashiqi.com/aspx3/mobile/qiandao.aspx?action=list&s=&no="
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

# 从环境变量获取用户名和密码（GitHub Actions 中配置）
USERNAME = os.getenv("CHECKIN_USERNAME")  # 环境变量名自定义，需和 Secrets 一致
PASSWORD = os.getenv("CHECKIN_PASSWORD")

# 通用请求头
common_headers = {
    "Accept-Language": "zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "User-Agent": user_agent,
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

session = requests.Session()  # 使用 Session 保持会话和 Cookies

# ================== 第一步：执行登录操作 ==================
print("--- 执行登录操作 ---")
# 1.1 获取登录页面
login_page_response = session.get(login_url, headers=common_headers)
login_page_parser = etree.HTML(login_page_response.text)

# 1.2 提取登录表单所需隐藏字段和控件名称
get_xpath_value = lambda parser, xpath_str, default='': \
    (result := parser.xpath(xpath_str)) and result[0] or default

viewstate = get_xpath_value(login_page_parser, '//input[@name="__VIEWSTATE"]/@value')
eventvalidation = get_xpath_value(login_page_parser, '//input[@name="__EVENTVALIDATION"]/@value')
user_name_attr = get_xpath_value(login_page_parser, '//*[@id="txtUser_sign_in"]/@name', 'txtUser_sign_in')
pass_name_attr = get_xpath_value(login_page_parser, '//*[@id="txtPwd_sign_in"]/@name', 'txtPwd_sign_in')
login_button_name = get_xpath_value(login_page_parser, '//input[@type="submit" and @value="登 录"]/@name', 'btnLogin')
login_button_value = get_xpath_value(login_page_parser, f'//input[@name="{login_button_name}"]/@value', '登 录')

# 1.3 构建登录 POST 数据
login_post_data = {
    "__VIEWSTATE": viewstate,
    "__EVENTVALIDATION": eventvalidation,
    user_name_attr: USERNAME,
    pass_name_attr: PASSWORD,
    login_button_name: login_button_value,
}

# 1.4 设置 POST 请求头
login_post_headers = {
    **common_headers,
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": login_url
}

# 1.5 发送登录 POST 请求
login_result_response = session.post(login_url, headers=login_post_headers, data=login_post_data, allow_redirects=False)

# 1.6 验证登录是否成功
if login_result_response.status_code == 302 and 'location' in login_result_response.headers:
    print(f"登录成功！重定向至: {login_result_response.headers['location']}")
else:
    print("登录可能失败，请检查用户名、密码或表单提交参数。")
    print("登录响应状态码:", login_result_response.status_code)
    print("登录响应内容 (部分):", login_result_response.text[:500])
    exit("登录失败，程序终止。")


# ================== 第二步：访问签到页面并模拟点击签到按钮 ==================
print("\n--- 访问签到页面并模拟点击签到 ---")

# 2.1 获取签到页面
qiandao_page_response = session.get(qiandao_url, headers=common_headers)
qiandao_page_parser = etree.HTML(qiandao_page_response.text)

# 2.2 提取签到页面所需的隐藏字段和按钮信息
qiandao_viewstate = get_xpath_value(qiandao_page_parser, '//input[@name="__VIEWSTATE"]/@value')
qiandao_eventvalidation = get_xpath_value(qiandao_page_parser, '//input[@name="__EVENTVALIDATION"]/@value')
qiandao_button_name = get_xpath_value(qiandao_page_parser, '//input[@type="submit" and @value="签到"]/@name', 'btnSign')
qiandao_button_value = get_xpath_value(qiandao_page_parser, f'//input[@name="{qiandao_button_name}"]/@value', '签到')

print(f"签到页面 __VIEWSTATE: {qiandao_viewstate[:30]}...")
print(f"签到页面 __EVENTVALIDATION: {qiandao_eventvalidation[:30]}..." if qiandao_eventvalidation else "签到页面 __EVENTVALIDATION 未找到")
print(f"签到按钮 name: {qiandao_button_name}, value: {qiandao_button_value}")


# 2.3 构建点击签到按钮的 POST 数据
qiandao_post_data = {
    "__VIEWSTATE": qiandao_viewstate,
    "__EVENTVALIDATION": qiandao_eventvalidation,
    qiandao_button_name: qiandao_button_value,
}

# 2.4 设置 POST 请求头
qiandao_post_headers = {
    **common_headers,
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": qiandao_url
}

# 2.5 发送点击签到按钮的 POST 请求
qiandao_result_response = session.post(qiandao_url, headers=qiandao_post_headers, data=qiandao_post_data, allow_redirects=True)

print("\n--- 点击签到按钮后的页面内容 ---")
print(qiandao_result_response.text[:1000])

# 检查签到是否成功
if "签到成功" in qiandao_result_response.text or "您已签到" in qiandao_result_response.text:
    print("\n>>> 自动签到可能成功！ <<<")
else:
    print("\n>>> 自动签到结果待确认，请手动检查页面内容。 <<<")
