import os
import re
import json
import time
import sys
import requests
from multiprocessing import Pool, Manager

# 多个账户请使用空格隔开
USERNAME = os.environ.get('FREENOM_USERNAME')
PASSWORD = os.environ.get('FREENOM_PASSWORD')

# 推送信息
TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
TG_USER_ID = os.environ.get('TG_USER_ID')

# 定义一些变量
desp = ""

# 保持连接,重复利用
ss = requests.session()
# 全局基础请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
}

def unix_time_to_date(t):
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)))

def log(info: str):
    print(info)
    global desp
    desp = desp + info + "\n"

def telegram():
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TG_USER_ID,
            'text': f"Freenom 域名续期日志\n{desp}",
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        if response.status_code != 200:
            log('Telegram Bot 推送失败')
        else:
            log('Telegram Bot 推送成功')
    except Exception as e:
        log(f"Telegram推送时出错: {str(e)}")

def process_wrapper(func, args):
    try:
        func(*args)
    except Exception as e:
        handle_exception(e,args[0])

def handle_exception(e,i):
    log(f"[{ck['name']}] 账号{i+1} 程序出现异常:", e)

def freenom(i,ck,shared_desp):
    domain = "https://my.freenom.com"
    headers["referer"] = "https://my.freenom.com/clientarea.php"
    # 重试次数
    check_count = 32
    # 等待时间
    sleep_time = 30
    def renew(user):
        nonlocal shared_desp
        result = ss.get(domain+"/domains.php?a=renewals",headers=headers).text
        if "logout.php" in result:
            shared_desp += (f"[{ck['name']}] 登陆状态验证成功!\n")
            token = re.findall('name="token" value="(.*?)"',result)
            if token != []:
                shared_desp += (f"[{ck['name']}] 获取账号Token成功!\n")
                domains = re.findall(r'<tr><td>(.*?)</td><td>[^<]+</td><td>[^<]+<span class="[^<]+>(\d+?).Days</span>[^&]+&domain=(\d+?)">.*?</tr>', result)
                if domains != []:
                    shared_desp += (f"[{ck['name']}] 获取域名成功!\n")
                    tips = "\n"
                    for do, days, renewal_id in domains:
                        if int(days) < 14:
                            headers["referer"] =  f"https://my.freenom.com/domains.php?a=renewdomain&domain={renewal_id}"
                            data={"token": token, "renewalid": renewal_id, f"renewalperiod[{renewal_id}]": "12M", "paymentmethod": "credit" }
                            result = ss.post(domain + "/domains.php?submitrenewals=true",data=data).text
                            if result.find("Order Confirmation") != -1:
                                tips += f"[{ck['name']}] 域名:{do}续期成功!\n"
                            else:
                                tips += f"[{ck['name']}] 域名:{do}续期失败!\n"
                        else:
                            tips += f"[{ck['name']}] 域名:{do} 剩余:{days} 天续期!\n"
                    shared_desp += (f"[{ck['name']}] 续期结果: {tips}")

            else:
                shared_desp += (f"[{ck['name']}] 获取账号Token失败!\n")
            return True
        else:
            shared_desp += (f"[{ck['name']}] 登陆状态验证失败!\n")
            return False
    data = {"username": ck['username'], "password": ck['password']}
    token = requests.get("http://dt.lieren.link/token").json()['token']
    cookies = {'aws-waf-token': token}
    theaders = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://my.freenom.com/clientarea.php',
        'authority': 'my.freenom.com',
    }
    result = ss.get("https://my.freenom.com/clientarea.php",headers=theaders,cookies=cookies)
    result = ss.post(domain+"/dologin.php",headers=headers ,cookies=cookies,data=data)
    for count in range(check_count):
        shared_desp += (f"[{ck['name']}] 正在处理第{i+1}个账号 {ck['username']})\n")
        if result.status_code == 405:
            shared_desp += (f"[{ck['name']}] 人机验证拦截,30秒后开始重新尝试! 当前[{count+1}/{check_count}]\n")
        elif result.status_code == 200:
            shared_desp += (f"[{ck['name']}] 登陆成功!\n")
            renew(ck)
            break
        else:
            shared_desp += (f"[{ck['name']}] 未知异常:{result}!\n")
        time.sleep(sleep_time)
        
    
if __name__ == "__main__":
    # 参数判断
    if not USERNAME or not PASSWORD:
        log("[Freenom] 需要设置2个必要参数:USERNAME,PASSWORD")
        sys.exit(1)

    user_list = USERNAME.strip().split()
    passwd_list = PASSWORD.strip().split()

    if not len(user_list) == len(passwd_list):
        log("[Freenom] The number of usernames and passwords do not match!")
        sys.exit(1)

    # 处理账户信息为列表
    freenom_accounts = []
    for user, pwd in zip(user_list, passwd_list):
        freenom_accounts.append({"name": "Freenom", "username": user, "password": pwd})
    
    # 创建进程池
    with Pool() as pool, Manager() as manager:
        # 拼接日志
        shared_desp = manager.list()
        shared_desp += "\n" + "*" * 40 + "\n"
        shared_desp += "本次执行时间：" + unix_time_to_date(time.time()) + "\n"
        # 处理续期
        pool.starmap(process_wrapper, [(freenom, (i, ck, shared_desp)) for i, ck in enumerate(freenom_accounts)])
        # log处理
        log("".join(shared_desp))
        # 关闭进程池
        pool.close()
        # 等待所有子进程执行完毕
        pool.join()
        # 关闭连接
        ss.close()

    # 消息推送
    if TG_BOT_TOKEN and TG_USER_ID and len(desp) > 0:
        telegram()
        sys.exit(0)
