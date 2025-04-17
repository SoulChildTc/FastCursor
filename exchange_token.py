import requests
from utils import PKCEInfo
import jwt
import time
from logger import logging

def get_sub_from_jwt(token, secret=None, algorithms=None, verify=False):
    try:
        # 解码 token
        payload = jwt.decode(
            token,
            key=secret if verify else None,
            algorithms=algorithms if verify else None,
            options={"verify_signature": verify}
        )
        # 提取 sub
        return payload.get('sub')
    
    except jwt.InvalidTokenError as e:
        print(f"无效的 Token: {e}")
        return None

# 判断jwt token 过期时间是否大于 500 天
def is_old_token(token):
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload.get('exp') > time.time() + 500 * 24 * 60 * 60

def get_pkce_info():
    return PKCEInfo.generate()

def exchange_token(uuid, verifier, challenge, token):

    headers={
        "accept": "*/*",
        "accept-language": "zh-CN",
        "content-type": "application/json",
        "cookie": f"WorkosCursorSessionToken={get_sub_from_jwt(token)}%3A%3A{token}",
        "dnt": "1",
        "origin": "https://www.cursor.com",
        "priority": "u=1, i",
        "referer": f"https://www.cursor.com/cn/loginDeepControl?challenge={challenge}&uuid={uuid}&mode=login",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
        "sec-ch-ua-mobile": "?0",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
    }
    
    # 提交
    response=requests.post(
        url="https://www.cursor.com/api/auth/loginDeepCallbackControl",
        headers=headers,
        json={"uuid":uuid,"challenge":challenge}
    )

    if response.status_code!=200:
        logging.info(response.text)
        raise Exception(f"交换 token 提交失败: {response.text}")
    
    
    response=requests.get(
        url=f"https://api2.cursor.sh/auth/poll?uuid={uuid}&verifier={verifier}",
        headers=headers
    )
    if response.status_code!=200:
        logging.info(response.text)
        raise Exception(f"交换 token 失败: {response.text}")
    
    return response.json().get("accessToken")

def get_new_token(token):
    
    # 如果token 过期大于 500 天，可能是老的永久 token , 直接返回
    if is_old_token(token):
        return token
    
    logging.info(f"开始交换新token")
    code_uuid,code_verifier,code_challenge=get_pkce_info()
    return exchange_token(code_uuid,code_verifier,code_challenge,token)

if __name__=="__main__":
    print(get_new_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdXRoMHx1c2VyXzAxSlJZVzRRNTVKWEE1RDlCTjBIUEgzVDAwIiwidGltZSI6IjE3NDQ4NzA2MDYiLCJyYW5kb21uZXNzIjoiMTcyNzY1ZTQtM2ZmMi00ZGE0IiwiZXhwIjoxNzQ0ODc2MDA2LCJpc3MiOiJodHRwczovL2F1dGhlbnRpY2F0aW9uLmN1cnNvci5zaCIsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwgb2ZmbGluZV9hY2Nlc3MiLCJhdWQiOiJodHRwczovL2N1cnNvci5jb20ifQ.KJ4kCQB4HcCxQace6VcKB27USGmdnJ7deAMQuYQmh8I"))

