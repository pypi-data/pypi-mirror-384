import requests


def llm_chat(user_content: str, url: str = None, key: str = None, model_name: str = None, temper: float = None,
             payload: dict = None):
    """
    调用 openai 格式 大模型
    :param user_content:
    :param url:
    :param key:
    :param model_name:
    :param temper:
    :param payload:
    :return:
    """

    headers = {
        "Authorization": f"Bear {key}",
        "Content-type": "application/json"
    }

    # 支持自定义payload
    if not payload:
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            "temperature": temper
        }

    try:
        response = requests.post(
            f"{url}/chat/completions", headers=headers, json=payload, timeout=600
        )
        if response.status_code == 200:
            response_data = response.json()
            reply = response_data["choices"][0]["message"]["content"]
            return reply, response_data["usage"]
        return {"error": response.status_code}, 0
    except Exception as e:
        return {"exception": e}, 0