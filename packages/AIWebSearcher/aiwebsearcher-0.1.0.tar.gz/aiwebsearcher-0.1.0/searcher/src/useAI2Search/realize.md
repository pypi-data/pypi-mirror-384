整体的实现路径是：
用户输入query
LLM根据query选择合适的searchPara调用Search工具
Search MCP接收到searchPara开始处理
    searchPara分并行分发给3个小模型（3-7B，或者是flash），分别搜索到5个结果(orderNum, title, url, abstract),小模型根据内容返回选择合适的orderNum
    系统根据orderNum从五个结果中取得合适的结果(orderNum, title, url, abstract)，这3个模型的处理结果重新编排orderNum交给主模型（这是个大模型，至少70B）。
    主模型根据输入，返回合适的Number，将结果（只有前三个内容带上content）返回。



执行信息抽取或结构化数据生成任务时，大模型可能返回多余文本（如 ```json）导致下游解析失败。开启结构化输出可以确保大模型输出标准格式的 JSON 字符串。

使用方式
设置response_format参数：在请求体中，将 response_format 参数设置为 {"type": "json_object"}。

提示词包含"JSON"关键词：System Message 或 User Message 中需要包含 "JSON" 关键词（不区分大小写），否则会报错：'messages' must contain the word 'json' in some form, to use 'response_format' of type 'json_object'.

支持的模型
通义千问Max 系列：qwen3-max、qwen3-max-2025-09-23、qwen3-amx-preview、qwen-max、qwen-max-latest、qwen-max-2024-09-19 及之后的快照模型

通义千问Plus 系列（非思考模式）：qwen-plus、qwen-plus-latest、qwen-plus-2024-09-19及之后的快照模型

通义千问Flash 系列（非思考模式）：qwen-flash、qwen-flash-2025-07-28及之后的快照模型

通义千问Coder 系列：qwen3-coder-plus、qwen3-coder-plus-2025-07-22、qwen3-coder-flash、qwen3-coder-flash-2025-07-28

通义千问VL 系列：qwen-vl-max、qwen-vl-plus（不包括最新版与快照版模型）

通义千问Turbo 系列（非思考模式）：qwen-turbo、qwen-turbo-latest、qwen-turbo-2024-09-19及之后的快照模型

Qwen 开源系列

Qwen3（非思考模式）

Qwen3-Coder

Qwen2.5 系列的文本模型（不含math与coder模型）

说明
思考模式的模型暂不支持结构化输出功能。

模型的上下文、价格、快照版本等信息请参见模型列表与价格。

快速开始
以从个人简介中抽取信息的简单场景为例，介绍快速使用结构化输出的方法。

您需要已获取API Key并配置API Key到环境变量。如果通过OpenAI SDK或DashScope SDK进行调用，还需要安装SDK。

OpenAI兼容DashScope
PythonNode.jscurl
 
from openai import OpenAI
import os

client = OpenAI(
    # 如果没有配置环境变量，请用API Key将下行替换为：api_key="sk-xxx"
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 以下是北京地域base_url，如果使用新加坡地域的模型，需要将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen-flash",
    messages=[
        {
            "role": "system",
            "content": "请抽取用户的姓名与年龄信息，以JSON格式返回"
        },
        {
            "role": "user",
            "content": "大家好，我叫刘五，今年34岁，邮箱是liuwu@example.com，平时喜欢打篮球和旅游", 
        },
    ],
    response_format={"type": "json_object"}
)

json_string = completion.choices[0].message.content
print(json_string)
返回结果
 
{
  "姓名": "刘五",
  "年龄": 34
}

以上是官方手册，我这个文件是ango官方的这个模型的文件。你看看怎么改这个ango的文件才能实现结构化输出。使用中文与我交流