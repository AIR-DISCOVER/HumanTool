#!/bin/sh
# 这个脚本会在Nginx启动前自动运行，修复API路径

# 动态查找主JS文件的路径
JS_FILE=$(find /usr/share/nginx/html/static/js -name 'main.*.js')

if [ -f "$JS_FILE" ]; then
  echo "✅ Found JS file to patch: $JS_FILE"
  echo "🚀 Patching hardcoded 'localhost:8000' to be a relative path..."
  # 将 http://localhost:8000 替换为空字符串，使其变为相对路径
  sed -i 's|http://localhost:8000||g' "$JS_FILE"
  echo "🎉 Patching complete."
else
  echo "⚠️ WARNING: main.*.js file not found. API calls might fail."
fi

# 脚本执行完毕后，Nginx会继续正常启动