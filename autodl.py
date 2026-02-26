import requests
import hashlib
import logging
import time
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ========== 配置区域 ==========
USERNAME = ""          # 手机号
PASSWORD = ""          # 密码
PHONE_AREA = "+86"
TOKEN=""
#
LOGIN_URL = "https://www.autodl.com/api/v1/new_login"          # 第1步：登录接口
PASSPORT_URL = "https://www.autodl.com/api/v1/passport"        # 第2步：获取 token 接口（POST，负载ticket）
INSTANCE_URL = "https://www.autodl.com/api/v1/instance"         # 第3步：实例列表接口（需带token）
# ==============================

def hash_password(password):
    """SHA1哈希密码"""
    return hashlib.sha1(password.encode()).hexdigest()

def login_and_get_ticket(session):
    """第1步：登录，返回 ticket"""
    login_data = {
        "phone": USERNAME,
        "password": hash_password(PASSWORD),
        "v_code": "",
        "phone_area": PHONE_AREA,
        "picture_id": None
    }
    try:
        resp = session.post(LOGIN_URL, json=login_data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        logging.debug(f"登录响应: {result}")
        if result.get('code') == 'Success':
            # 从响应中提取 ticket，字段名可能是 'ticket'，也可能是 'access_token'，请根据实际调整
            ticket = result.get('data', {}).get('ticket')
            if not ticket:
                logging.error("未找到 ticket 字段")
                return None
            logging.info("登录成功")

            return ticket
        else:
            logging.error(f"登录失败: {result}")
            return None
    except Exception as e:
        logging.error(f"登录异常: {e}")
        return None

def get_token_with_ticket(session, ticket):
    """第2步：使用 ticket 获取 token（POST请求，负载为ticket）"""
    # 根据抓包信息，这里是 POST 请求，负载是 {"ticket": "..."}
    payload = {"ticket": ticket}
    # 可以添加 appversion 等请求头（可选）
    session.headers.update({
        'appversion': 'v6.15.0',
        'content-type': 'application/json;charset=UTF-8',
        # 其他头部如 accept 等 session 已有默认值
    })
    try:
        resp = session.post(PASSPORT_URL, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        logging.debug(f"passport响应: {result}")
        if result.get('code') == 'Success':
            # 提取 token，字段名可能是 'token'、'access_token' 等，请根据实际调整
            token = result.get('data', {}).get('token')
            if not token:
                logging.error("passport返回成功但未找到 token 字段")
                return None
            logging.info("获取 token 成功")
            return token
        else:
            logging.error(f"获取 token 失败: {result}")
            return None
    except Exception as e:
        logging.error(f"passport请求异常: {e}")
        return None

def get_instance_info(session, token):
    """第3步：使用 token 和 cookie 获取实例信息"""
    # 将 token 放入 Authorization 头（根据你之前的经验，需要这个头）
    if token:
        session.headers.update({'authorization': token})
    # 构造请求参数（根据实例列表接口的要求，通常是 POST 带分页参数）
    payload = {
        "page_index": 1,
        "page_size": 10,
        "status": [],
        "charge_type": [],
        "sub_name": ""
    }
    try:
        # 使用 POST 方法，JSON 格式
        resp = session.post(INSTANCE_URL, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get('code') != 'Success':
            logging.error(f"实例接口返回错误: {result}")
            return None
        instances = result.get('data', {}).get('list', [])
        if not instances:
            logging.info("没有实例")
            return None
        # 取实例的 GPU 信息
        logging.info("实例信息如下：")
        logging.info("*************************************************************")
        for instance in instances:
            gpu_all = instance.get('gpu_all_num')
            gpu_idle = instance.get('gpu_idle_num')
            alias = instance.get('machine_alias')
            if  gpu_idle:
                message(alias)
            logging.info(f"实例 {alias}: 空闲 {gpu_idle}/{gpu_all}")
        logging.info("*************************************************************")
        return 1
    except Exception as e:
        logging.error(f"实例请求异常: {e}")
        return None

def message(machine):
    if TOKEN!="":
        headers = {"Authorization": TOKEN}
        requests.post("https://www.autodl.com/api/v1/wechat/message/send",
                             json={
                                 "title": "来自autodl",
                                 "name": str(machine)+"----存在空闲GPU通知",
                                 "content": "存在空闲GPU"
                             }, headers=headers)

def main():
    session = requests.Session()
    # 设置基础请求头（模拟浏览器）
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
        'Referer': 'https://www.autodl.com/login',
        'Origin': 'https://www.autodl.com',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'sec-ch-ua': '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
    })

    # 第1步：登录获取 ticket
    ticket = login_and_get_ticket(session)
    if not ticket:
        print("❌ 登录失败，无法继续")
        return

    # 第2步：用 ticket 获取 token
    token = get_token_with_ticket(session, ticket)
    if not token:
        print("❌ 获取 token 失败，无法继续")
        return

    # 第3步：获取实例信息
    result = get_instance_info(session, token)
    if not result:
        print("❌ 获取实例信息失败")


if __name__ == "__main__":
    while True:
        main()
        time.sleep(1800)

