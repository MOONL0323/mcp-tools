本地大模型API用户使用手册（持续更新中）
1.概述
为紧跟业界明星LLM，确保内部人员能够最快时间体验到业界最新模型的表现，快速响应和适应最新的研究成果和行业趋势，确保我们始终处于行业的前沿，增强市场竞争力。
2.本地部署模型

目前推出了API调用体验的方式
key:sk-1Lo9AiW9a5Sh63tO78927e8eAe0844F6A070DfEb79Ec48B9
本地模型信息
模型名	原始模型名	上下文长度	function_call	是否可直接使用	备注
qwq-32b	QwQ-32B	64K		是	自动负载以下qwq实例
qwq-32b-128k	QwQ-32B	128K	支持	是	实例数少
qwen72b-int8	Qwen2.5-72B-Instruct-GPTQ-Int8	16K		是	即将下架，推荐后续使用qwen3-32b非think模式
qwen72b-awq	Qwen2.5-72B-Instruct-AWQ	16K	支持	是	即将下架，推荐后续使用qwen3-32b非think模式
qwen32b-awq(试用)	Qwen2.5-32B-Instruct-AWQ	32K	支持	是	即将下架，推荐后续使用qwen3-32b非think模式
qwen25-vl-7b	Qwen2.5-VL-32B-Instruct	32K		是	

key:sk-KskGcDMEQWGncNHr6bE2Ee61F22b40F8A1C09c8b150968Ff
模型名	原始模型名	上下文长度	function_call	think	think开关	是否可直接使用	备注
qwen3-32b	Qwen3-32B	32K	支持	支持	支持	think字段在reasoning_content	自动负载以下qwq实例
qwen3-30b-a3b	Qwen3-30B-A3B	32K	支持
	支持	支持
	即将下架，推荐后续使用qwen3-32b	



3.调用接口示例
对话调用示例
Url	https://oneapi.sangfor.com/v1/chat/completions
header	Authorization: sk-1Lo9AiW9a5Sh63tO78927e8eAe0844F6A070DfEb79Ec48B9
header	Content-Type: application/json
body	{
    "messages": [
        {
            "role": "user",
            "content": "你好"
        }
    ],
    "model":"qwen32b-awq(试用)"
}

function call 调用示例
Url	https://oneapi.sangfor.com/v1/chat/completions
header	Authorization: sk-1Lo9AiW9a5Sh63tO78927e8eAe0844F6A070DfEb79Ec48B9
header	Content-Type: application/json
body	{
    "messages": [
        {
            "role": "user",
            "content": "What is the weather like in Paris today?"
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA"
                        },
                        "unit": {
                            "type": "string",
                            "enum": [
                                "celsius",
                                "fahrenheit"
                            ]
                        }
                    },
                    "required": [
                        "location"
                    ]
                }
            }
        }
    ],
    "model": "qwen72b-awq"
}
返回参考	{
    "id": "1b36bf9444664ae680f7340bff904792",
    "object": "chat.completion",
    "created": 1743068982,
    "model": "qwen72b-awq",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": null,
                "reasoning_content": null,
                "tool_calls": [
                    {
                        "id": "0",
                        "type": "function",
                        "function": {
                            "name": "get_current_weather",
                            "arguments": "{\"location\": \"Paris\", \"unit\": \"celsius\"}"
                        }
                    }
                ]
            },
            "logprobs": null,
            "finish_reason": "tool_calls",
            "matched_stop": null
        }
    ],
    "usage": {
        "prompt_tokens": 207,
        "total_tokens": 235,
        "completion_tokens": 28,
        "prompt_tokens_details": null
    }
}


4.Python调用示例
1.非流式输出

2.流式输出

3.流式输出转非流式（每次token生成比较长的时候建议用这种方式）

3.使用OpenAI包


4.使用OpenAI包-Qwen3关闭think


5.Embedding
新增 Qwen3-Embedding-8B 

6.Rerank

7.多模型图片请求正文

8.Qwen3
key:sk-KskGcDMEQWGncNHr6bE2Ee61F22b40F8A1C09c8b150968Ff
模型名	原始模型名	上下文长度	function_call	think	think开关	是否可直接使用	备注
qwen3-32b	Qwen3-32B	32K	暂不支持	支持	支持	think字段在reasoning_content	自动负载以下qwq实例
qwen3-30b-a3b	Qwen3-30B-A3B	32K	暂不支持
	支持	支持
		

关闭think返回，返回速度会变快，效果暂未测试


返回示例


非think模式下，function_call请求示例

返回示例


9.注意事项
为保障模型接口响应速度，如需要跑大量请求，请提前联系，在资源相对空闲的时候进行。
