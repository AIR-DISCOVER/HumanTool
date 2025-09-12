import requests
import json

url = "https://api.gptplus5.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer sk-quBjWaFrfCyP8NFp75Bd90C46e96425a8756545dC5Ee386f"
}
data = {
    "model": "gpt-4o",
    "stream": False,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    # 处理非流式响应
    print(response.json()['choices'][0]['message']['content'])
else:
    print(f"Error: {response.status_code}, {response.text}")