import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
import openai

# 加载配置
load_dotenv()

# ======================================
# 1. 获取微信公众号 access_token
# ======================================
def get_access_token():
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": os.getenv("WECHAT_APPID"),
        "secret": os.getenv("WECHAT_APPSECRET")
    }
    resp = requests.get(url, params=params).json()
    
    if "access_token" in resp:
        print("✅ 获取 access_token 成功")
        return resp["access_token"]
    else:
        print("❌ 获取 token 失败：", resp)
        return None

# ======================================
# 2. AI Agent 自动生成文章（你的行业专属）
# ======================================
def ai_generate_article():
    client = openai.OpenAI(
        api_key=os.getenv("AI_API_KEY"),
        base_url=os.getenv("AI_BASE_URL")
    )

    # 为 诚塬商务 定制的专业写作指令
    prompt = """
    你是【诚塬商务 CYBusinessAI】的专业 AI 内容创作 Agent，
    请生成一篇适合企业服务号的技术文章，主题从以下随机选 1 个：
    1. AI Agent 企业落地应用
    2. AIGC 最新技术动态
    3. 大数据、数据同步、数据传输
    4. 信创政策、国产数据库（达梦、人大金仓、GaussDB）
    5. AI 行业政策解读(可以偏向医疗健康行业）

    输出要求：
    1. 标题专业、正式、有吸引力
    2. 正文 800-1000 字
    3. 纯文本，适配微信公众号，自带分段、小标题
    4. 语言正式、企业级、无表情、无特殊符号
    5. 第一行必须是标题，从第二行开始是正文
    """

    response = client.chat.completions.create(
        model="doubao-lite",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content.strip()
    
    # 自动拆分标题和正文
    lines = content.split("\n")
    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip()
    
    print(f"📝 生成文章：{title}")
    return {"title": title, "content": body}

# ======================================
# 3. 上传文章到公众号草稿
# ======================================
def create_draft(access_token, title, content):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    data = {
        "articles": [
            {
                "title": title,
                "content": content,
                "author": "诚塬商务",
                "show_cover_pic": 1
            }
        ]
    }
    resp = requests.post(url, json=data).json()
    
    if "media_id" in resp:
        print("✅ 草稿创建成功")
        return resp["media_id"]
    else:
        print("❌ 草稿创建失败：", resp)
        return None

# ======================================
# 4. 设置 20:00 定时发布
# ======================================
def publish_draft(access_token, media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={access_token}"
    data = {
        "media_id": media_id,
        "publish_time": "20:00"
    }
    resp = requests.post(url, json=data).json()
    print("✅ 定时发布结果：", resp)
    return resp

# ======================================
# 主流程：一键全自动
# ======================================
if __name__ == "__main__":
    print("===== 诚塬商务 AI 自动发文启动 =====")
    
    # 1. 生成文章
    article = ai_generate_article()
    
    # 2. 获取凭证
    token = get_access_token()
    if not token:
        exit()
    
    # 3. 创建草稿
    media_id = create_draft(token, article["title"], article["content"])
    if not media_id:
        exit()
    
    # 4. 定时发布
    publish_draft(token, media_id)
    
    print("===== 今日任务完成，20:00 自动推送 =====")
