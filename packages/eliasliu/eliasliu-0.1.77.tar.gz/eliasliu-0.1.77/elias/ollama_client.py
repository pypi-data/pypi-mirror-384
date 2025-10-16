import requests
import json
import sys
import os
import base64

class OllamaClient:
    """
    Ollama客户端，用于调用本地或远程的Ollama模型，并支持流式输出。
    """
    def __init__(self, base_url="http://localhost:11434", default_model="qwen3"):
        """
        初始化Ollama客户端
        
        Args:
            base_url (str): Ollama API的基础URL
            default_model (str): 默认使用的模型名称
        """
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.session = requests.Session()
    
    def generate(self, prompt, model=None, stream=True, images=None, files=None, **kwargs):
        """
        生成文本响应
        
        Args:
            prompt (str): 提示文本
            model (str, optional): 要使用的模型名称，如果为None则使用默认模型
            stream (bool, optional): 是否启用流式输出，默认为True
            images (list, optional): 图片文件路径列表
            files (list, optional): 其他文件路径列表
            **kwargs: 其他传递给Ollama API的参数
        
        Returns:
            str: 完整的响应文本
        """
        if model is None:
            model = self.default_model
        
        # 如果有图像，使用chat API而不是generate API
        if images:
            # 准备消息
            messages = [{"role": "user", "content": prompt}]
            
            # 对于带图像的请求，使用非流式响应以确保正确获取完整内容
            # 并提供有用的提示信息
            print(f"检测到图片，使用{model}模型进行图像分析...")
            print(f"提示：分析图片可能需要较多系统资源，这是正常的")
            
            return self.chat(
                messages=messages,
                model=model,
                stream=False,  # 禁用流式响应，确保完整获取响应内容
                images=images,
                **kwargs
            )
        
        url = f"{self.base_url}/api/generate"
        
        # 准备请求数据
        data = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **kwargs
        }
        
        # 发送请求
        response = self.session.post(url, json=data, stream=stream)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误: {e}")
            print(f"错误响应内容: {response.text}")
            raise
        
        full_response = ""
        
        # 处理流式响应
        if stream:
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        # 提取响应文本
                        if "response" in chunk:
                            print(chunk["response"], end="", flush=True)
                            full_response += chunk["response"]
                        # 检查是否完成
                        if chunk.get("done", False):
                            print()  # 输出换行
                            break
                    except json.JSONDecodeError:
                        continue
        else:
            # 非流式响应
            result = response.json()
            full_response = result.get("response", "")
            print(full_response)
        
        return full_response
    
    def list_models(self):
        """
        列出可用的模型
        
        Returns:
            list: 模型列表
        """
        url = f"{self.base_url}/api/tags"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])
    
    def chat(self, messages, model=None, stream=True, images=None, **kwargs):
        """
        使用聊天模式与模型交互
        
        Args:
            messages (list): 消息历史列表，每个消息包含role和content
            model (str, optional): 要使用的模型名称，如果为None则使用默认模型
            stream (bool, optional): 是否启用流式输出，默认为True
            images (list, optional): 图像文件路径列表
            **kwargs: 其他传递给Ollama API的参数
        
        Returns:
            str: 最新的响应文本
        """
        if model is None:
            model = self.default_model
        
        url = f"{self.base_url}/api/chat"
        
        # 准备请求数据
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        # 发送请求
        if images and len(images) > 0:
            # 首先检查图片文件是否存在
            if not os.path.exists(images[0]):
                raise FileNotFoundError(f"图片文件不存在: {images[0]}")
            
            print(f"正在使用{model}模型分析图片: {images[0]}")
            print(f"注意：Ollama处理图片可能需要较多资源，请确保系统有足够内存")
            
            try:
                # 读取图片并进行base64编码
                with open(images[0], 'rb') as f:
                    image_data = f.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # 为消息添加图片数据 - 使用Ollama API支持的方式
                messages_with_image = messages.copy()
                
                # 在最后一条消息中添加images字段（正确的Ollama API格式）
                if messages_with_image and "content" in messages_with_image[-1]:
                    # 确保最后一条消息是user角色
                    if messages_with_image[-1]["role"] == "user":
                        # 直接在原始消息中添加images字段
                        messages_with_image[-1]["images"] = [base64_image]
                    else:
                        # 如果最后一条消息不是user角色，则添加一条新的user消息
                        messages_with_image.append({
                            "role": "user",
                            "content": "请分析这张图片",
                            "images": [base64_image]
                        })
                else:
                    # 如果消息列表为空或最后一条消息没有content字段，则创建一条新消息
                    messages_with_image.append({
                        "role": "user",
                        "content": "请分析这张图片",
                        "images": [base64_image]
                    })
                
                # 更新数据
                data["messages"] = messages_with_image
                
                # 使用JSON格式发送请求
                response = self.session.post(url, json=data, stream=stream)
            except Exception as e:
                print(f"图片处理过程中出错: {str(e)}")
                print("提示：Ollama处理图片可能需要较多内存，请确保系统有足够资源")
                print("      也可能是模型不支持图片分析，请确认使用的是支持多模态的模型")
                raise
        else:
            # 没有图像时，使用JSON格式
            response = self.session.post(url, json=data, stream=stream)
        
        # 添加详细的错误处理
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP错误: {e}"
            if hasattr(response, 'text'):
                error_msg += f"\n错误响应内容: {response.text}"
                
                # 检查是否是资源限制错误
                if "resource limitations" in response.text:
                    error_msg += "\n\n提示：这可能是由于Ollama服务器资源不足导致的。\n"
                    error_msg += "      建议：\n"
                    error_msg += "      1. 关闭其他占用内存的程序\n"
                    error_msg += "      2. 尝试使用更小的模型\n"
                    error_msg += "      3. 增加系统内存\n"
                    error_msg += "      4. 检查Ollama服务器日志获取更多详细信息"
                
                # 检查是否是模型问题
                if "model runner" in response.text:
                    error_msg += "\n\n提示：这可能是由于模型运行器出现问题。\n"
                    error_msg += "      建议：\n"
                    error_msg += "      1. 尝试重新拉取模型: ollama pull model_name\n"
                    error_msg += "      2. 重启Ollama服务\n"
                    error_msg += "      3. 检查Ollama服务器日志"
        
            print(error_msg)
            raise
        
        full_response = ""
        
        # 处理流式响应
        if stream:
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        # 提取响应文本
                        if "message" in chunk and "content" in chunk["message"]:
                            print(chunk["message"]["content"], end="", flush=True)
                            full_response += chunk["message"]["content"]
                        # 检查是否完成
                        if chunk.get("done", False):
                            print()  # 输出换行
                            break
                    except json.JSONDecodeError:
                        continue
        else:
            # 非流式响应 - 添加更详细的调试信息
            try:
                result = response.json()
                print(f"完整响应: {result}")
                if "message" in result and "content" in result["message"]:
                    full_response = result["message"]["content"]
                    print(full_response)
                else:
                    print("响应中未找到message.content字段")
                    # 尝试直接获取响应文本
                    full_response = response.text
                    print(f"直接响应文本: {full_response}")
            except json.JSONDecodeError:
                print("解析JSON响应失败，尝试直接获取响应文本")
                full_response = response.text
                print(f"直接响应文本: {full_response}")
        
        return full_response