# -*- coding: utf-8 -*-

from workflow import Workflow3
import sentry_sdk
import os
import json
import uuid
import hashlib
import time
import sys
import random

YOUDAO_URL = 'https://openapi.youdao.com/api'
# APP_KEY = 'APP_KEY'
# APP_SECRET = 'APP_SECRET'

ERRORCODE_DICT = {
    "20": "要翻译的文本过长",
    "30": "无法进行有效的翻译",
    "40": "不支持的语言类型",
    "50": "无效的key",
    "60": "无词典结果，仅在获取词典结果生效",
    "101": "缺少必填的参数，出现这个情况还可能是et的值和实际加密方式不对应",
    "102": "不支持的语言类型",
    "103": "翻译文本过长",
    "104": "不支持的API类型",
    "105": "不支持的签名类型",
    "106": "不支持的响应类型",
    "107": "不支持的传输加密类型",
    "108": "appKey无效，注册账号， 登录后台创建应用和实例并完成绑定，\
        可获得应用ID和密钥等信息，其中应用ID就是appKey（注意不是应用密钥）",
    "109": "batchLog格式不正确",
    "110": "无相关服务的有效实例",
    "111": "开发者账号无效",
    "113": "q不能为空",
    "201": "解密失败，可能为DES,BASE64,URLDecode的错误",
    "202": "签名检验失败",
    "203": "访问IP地址不在可访问IP列表",
    "205": "请求的接口与应用的平台类型不一致，如有疑问请参考[入门指南]",
    "206": "因为时间戳无效导致签名校验失败",
    "207": "重放请求",
    "301": "辞典查询失败",
    "302": "翻译查询失败",
    "303": "服务端的其它异常",
    "401": "账户已经欠费停",
    "411": "访问频率受限,请稍后访问",
    "412": "长请求过于频繁，请稍后访问",
    "500": "有道翻译失败"
}

ICON_DEFAULT = 'icon.png'
ICON_PHONETIC = 'icon_phonetic.png'
ICON_BASIC = 'icon_basic.png'
ICON_WEB = 'icon_web.png'
ICON_UPDATE = 'icon_update.png'
ICON_ERROR = 'icon_error.png'

QUERY_LANGUAGE = 'EN2zh-CHS'


def init_sentry():
    # 收集错误信息
    if os.getenv('sentry', 'False').strip():
        sentry_sdk.init(
            "https://4d5a5b1f2e68484da9edd9076b86e9b7@sentry.io/1500348")
        with sentry_sdk.configure_scope() as scope:
            user_id = get_user_id()
            scope.user = {"id": user_id}
            scope.set_tag("version", str(wf.version))


def get_user_id():
    user_id = wf.stored_data('user__id')
    if user_id == None:
        user_id = str(uuid.uuid1())
    wf.store_data('user__id', user_id)
    return user_id


def sentry_message(errorCode, msg):
    if os.getenv('sentry', 'False').strip():
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("errorCode", errorCode)
        sentry_sdk.capture_message(msg)

def get_youdao_old_url(query, youdao_keyfrom, youdao_key):
    import urllib.parse

    query = urllib.parse.quote(str(query))
    url = 'http://fanyi.youdao.com/openapi.do?' + \
        'keyfrom=' + str(youdao_keyfrom) + \
        '&key=' + str(youdao_key) + \
        '&type=data&doctype=json&version=1.1&q=' + query
    return url


def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()

def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()


def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

# def do_request(data):
#     headers = {'Content-Type': 'application/x-www-form-urlencoded'}
#     return requests.post(YOUDAO_URL, data=data, headers=headers)

def format_data(query):
    q = query or "待输入的文字"

    data = {}
    data['from'] = '源语言'
    data['to'] = '目标语言'
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['q'] = q
    data['salt'] = salt
    data['sign'] = sign

    return data

def fetch_translation(query):
    from urllib import request, parse
    
    data = parse.urlencode(format_data(query)).encode()
    req =  request.Request(YOUDAO_URL, data=data)
    # 设置请求方法为 POST
    req.method = 'POST'

    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    with request.urlopen(req) as response:
        result = response.read()

    wf.logger.debug(YOUDAO_URL)

    try:
        rt = json.loads(result)
        return rt
    except:
        rt = {}
        rt['errorCode'] = "500"
        return rt
    else:
        rt = {}
        rt['errorCode'] = "500"
        return rt


def save_history_data(query, title, arg, ICON_DEFAULT):
    jsonData = '{"title": "%s", "subtitle": "%s", "arg": "%s", \
        "icon": "%s"}\n' % (query, title, arg, ICON_DEFAULT)
    with open('history.log', 'a') as file:
        file.write(jsonData)


def get_history_data():
    with open('history.log', 'r') as file:
        for line in file.readlines()[-1:-10:-1]:
            try:
                line = json.loads(line)
                wf.add_item(
                    title=line['title'], subtitle=line['subtitle'],
                    arg=line['arg'], valid=True, icon=line['icon'])
            except Exception as e:
                pass


def is_expired():
    # 检查更新，随机检测
    if random.random() < 0.01 and wf.update_available:
        arg = get_arg_str('', '', operation='update_now')
        wf.add_item(
            title='马上更新（点击后请打开 Alfred 的 Preference 完成更新）',
            subtitle='有新版本更新', arg=arg,
            valid=True, icon=ICON_UPDATE)

        arg = get_arg_str('', '', operation='update_with_url')
        wf.add_item(
            title='手动更新', subtitle='有新版本更新', arg=arg,
            valid=True, icon=ICON_ERROR)

        arg = get_arg_str('', '', operation='update_next_time')
        wf.add_item(
            title='暂不更新', subtitle='有新版本更新', arg=arg,
            valid=True, icon=ICON_ERROR)

        wf.send_feedback()
        return True
    return False


def get_query_language(query):
    import re
    global QUERY_LANGUAGE
    # 检查中文
    if re.search(r"[\u4e00-\u9fa5]+", query):
        QUERY_LANGUAGE = "zh-CHS2EN"
    # 检查韩语
    elif re.search(r"[\uAC00-\uD7A3]+", query):
        QUERY_LANGUAGE = "KO2zh-CHS"
    # 检查日语
    elif re.search(r"[\u0800-\u4e00]+", query):
        QUERY_LANGUAGE = "JA2zh-CHS"


def get_arg_str(query, result, pronounce='', operation='', query_language=''):
    if query_language == '':
        query_language = QUERY_LANGUAGE
    arg_array = [str(wf.version), query, result,
                 query_language, pronounce, operation]
    return '$%'.join(arg_array)


# def get_l(query, rt):
#     if u'l' in rt.keys():
#         if rt["l"] is not None:
#             QUERY_LANGUAGE = rt["l"]


def add_translation(query, rt):
    # 翻译结果
    subtitle = '翻译结果'
    translations = rt["translation"]
    for title in translations:
        arg = get_arg_str(query, title)
        save_history_data(query, title, arg, ICON_DEFAULT)

        wf.add_item(
            title=title, subtitle=subtitle, arg=arg,
            valid=True, icon=ICON_DEFAULT)

def add_explains(query, rt):
    # 简明释意
    if u'basic' in rt.keys():
        if rt["basic"] is not None:
            for i in range(len(rt["basic"]["explains"])):
                title = rt["basic"]["explains"][i]
                subtitle = '词义'
                arg = get_arg_str(query, title)

                wf.add_item(
                    title=title, subtitle=subtitle, arg=arg,
                    valid=True, icon=ICON_PHONETIC)

def add_web_translation(query, rt):
  # 网络翻译
    if u'web' in rt.keys():
        if rt["web"] is not None:
            for i in range(len(rt["web"])):
                values = rt["web"][i]["value"]
                for value in values:
                    title = value
                    key = rt["web"][i]["key"]
                    subtitle = '网络翻译: ' + key

                    if QUERY_LANGUAGE.split('2')[1] == 'EN':
                        arg = get_arg_str(query, title, pronounce=value)
                    else:
                        arg = get_arg_str(query, title, pronounce=key)

                    wf.add_item(
                        title=title, subtitle=subtitle,
                        arg=arg, valid=True, icon=ICON_WEB)


def main(wf):
    if is_expired():
        return

    query = wf.args[0].strip()

    if query == "*":
        get_history_data()
    else:
        get_query_language(query)
        rt = fetch_translation(query)
        errorCode = str(rt.get("errorCode"))

        if errorCode in ERRORCODE_DICT:
            if errorCode == "500":
                sentry_message(errorCode, ERRORCODE_DICT[errorCode])

            arg = get_arg_str('', '', operation='error')
            wf.add_item(
                title=errorCode + " " + ERRORCODE_DICT[errorCode],
                subtitle='', arg=arg,
                valid=True, icon=ICON_ERROR)

        elif errorCode == "0":
            add_translation(query, rt)
            add_explains(query, rt)
            add_web_translation(query, rt)

        else:
            sentry_message(errorCode, '有道也翻译不出来了')
            title = '有道也翻译不出来了'
            subtitle = '尝试一下去网站搜索'
            arg = get_arg_str(query, '')
            wf.add_item(
                title=title, subtitle=subtitle, arg=arg,
                valid=True, icon=ICON_DEFAULT)
    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3(update_settings={
        'github_slug': 'whyliam/whyliam.workflows.youdao',
        'frequency': 7
    })
    init_sentry()
    sys.exit(wf.run(main))
