import os
import time
import requests
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

class ImageGeneratorTool:
    """图片生成工具 - 使用OpenAI API生成图片"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        # 🎯 关键修复：使用绝对路径，确保路径正确
        self.output_dir = os.path.abspath("static/generated_images")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 配置OpenAI
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_base = os.getenv('OPENAI_API_BASE')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # 创建OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base if self.api_base else None
        )
    
    def execute(self, task_description: str, image_style: str = "realistic", 
                image_size: str = "1792x1024", **kwargs) -> str:  # 🎯 改为横屏尺寸
        """
        生成图片
        
        Args:
            task_description: 图片描述
            image_style: 图片风格 (realistic, artistic, cartoon, sci-fi)
            image_size: 图片尺寸 (1792x1024横屏, 1024x1792竖屏, 1024x1024正方形)
        """
        if self.verbose:
            print(f"[ImageGeneratorTool LOG] 开始生成图片: {task_description}")
        
        try:
            # 🎯 调用OpenAI图片生成API
            image_url = self._generate_with_openai(task_description, image_style, image_size)
            
            if image_url:
                return f"""✅ **图片生成完成**

**描述**: {task_description}
**风格**: {image_style}
**尺寸**: {image_size}

![生成的图片]({image_url})

🎨 图片已生成并保存"""
            else:
                return f"❌ 图片生成失败: API调用失败"
                
        except Exception as e:
            if self.verbose:
                print(f"[ImageGeneratorTool ERROR] {e}")
            return f"❌ 图片生成时发生错误: {str(e)}"
    
    def _generate_with_openai(self, description: str, style: str, size: str) -> Optional[str]:
        """使用OpenAI API生成图片"""
        try:
            # 🎯 构建增强的提示词
            enhanced_prompt = self._enhance_prompt(description, style)
            
            if self.verbose:
                print(f"[ImageGeneratorTool] 调用OpenAI API，提示词: {enhanced_prompt}")
            
            # 🎯 调用OpenAI图片生成API (新版本API)
            response = self.client.images.generate(
                model="dall-e-3",  # 使用DALL-E 3模型
                prompt=enhanced_prompt,
                n=1,
                size=size,
                response_format="url"
            )
            
            if response and response.data:
                image_url = response.data[0].url
                
                if self.verbose:
                    print(f"[ImageGeneratorTool] 图片生成成功: {image_url}")
                
                # 🎯 下载并保存图片到本地
                local_path = self._download_and_save_image(image_url, description)
                return local_path
            
            return None
            
        except Exception as e:
            if self.verbose:
                print(f"[ImageGeneratorTool] OpenAI API调用失败: {e}")
            return None
    
    def _enhance_prompt(self, description: str, style: str) -> str:
        """增强提示词以获得更好的生成效果"""
        style_modifiers = {
            "realistic": "photorealistic, high quality, detailed",
            "artistic": "creative, Asia"
        }
        
        modifier = style_modifiers.get(style, "high quality")
        return f"{description}, {modifier}, 4k resolution"
    
    def _download_and_save_image(self, image_url: str, description: str) -> str:
        """下载图片并保存到本地"""
        try:
            # 下载图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 🎯 生成安全的文件名
            timestamp = int(time.time())
            
            # 移除非ASCII字符，只保留英文、数字和基本符号
            import re
            safe_desc = re.sub(r'[^\w\s-]', '', description)  # 移除特殊字符
            safe_desc = re.sub(r'[^\x00-\x7F]', '', safe_desc)  # 移除非ASCII字符
            safe_desc = "".join(c for c in safe_desc[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_desc = safe_desc.replace(' ', '_')
            
            # 如果处理后为空，使用默认名称
            if not safe_desc:
                safe_desc = "image"
            
            filename = f"ai_generated_{timestamp}_{safe_desc}.png"
            # 🎯 关键修复：使用正确的路径分隔符
            filepath = os.path.join(self.output_dir, filename)
            
            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            if self.verbose:
                print(f"[ImageGeneratorTool] 图片保存成功: {filepath}")
                # 🎯 调试信息：检查文件是否真的存在
                print(f"[ImageGeneratorTool] 文件是否存在: {os.path.exists(filepath)}")
                print(f"[ImageGeneratorTool] 文件大小: {os.path.getsize(filepath)} bytes")
            
            # 🎯 关键修复：返回正确的URL路径（使用正斜杠）
            return f"/static/generated_images/{filename}"
        
        except Exception as e:
            if self.verbose:
                print(f"[ImageGeneratorTool] 图片下载失败: {e}")
            return None