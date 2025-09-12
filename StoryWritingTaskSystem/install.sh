#!/bin/bash
# 糖果ClaudeCode 安装脚本
# 自动生成于: 2025-08-06T09:43:21.445Z
# 服务配置:
#   - 服务名称: 糖果ClaudeCode
#   - API密钥获取地址: https://newapi.pockgo.com
#   - Anthropic Base URL: https://claudecode.pockgo.com
#
# 此脚本支持 Linux、macOS 和 Termux 环境
# Termux 用户会自动获得优化的安装体验
#

# 设置中文字符支持
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

set -e

# 从环境变量获取服务配置
SERVICE_NAME="糖果ClaudeCode"
API_KEY_URL="https://newapi.pockgo.com"
ANTHROPIC_BASE_URL="https://claudecode.pockgo.com"

echo "🚀 Claude Code 安装脚本"
echo "=================================="
echo "📋 服务名称: $SERVICE_NAME"
echo "🌐 基础URL: $ANTHROPIC_BASE_URL"
echo "🔗 API地址: $API_KEY_URL"
echo ""

# 在Termux环境中安装Node.js的函数
install_nodejs_termux() {
    echo "🚀 正在Termux环境中安装Node.js..."
    
    # 检查并建议镜像选择（如果需要）
    echo "🌐 检查软件源镜像..."
    if command -v termux-change-repo >/dev/null 2>&1; then
        echo "💡 如果遇到下载缓慢或镜像问题，请运行: termux-change-repo"
    fi
    
    # 更新软件包列表
    echo "📦 更新软件包列表..."
    pkg update -y
    
    # 升级现有软件包以避免冲突
    echo "📦 升级现有软件包..."
    pkg upgrade -y
    
    # 直接从Termux软件包安装Node.js（npm包含在nodejs包中）
    echo "📦 从Termux软件包安装Node.js..."
    echo "ℹ️  注意: 在Termux中，npm包含在nodejs包中"
    pkg install -y nodejs
    
    # 验证安装
    if command -v node >/dev/null 2>&1; then
        echo -n "✅ Node.js安装完成！版本: "
        node -v
    else
        echo "❌ Node.js安装失败"
        exit 1
    fi
    
    if command -v npm >/dev/null 2>&1; then
        echo -n "✅ npm版本: "
        npm -v
    else
        echo "❌ 未找到npm。这可能表示安装有问题。"
        echo "🔧 尝试修复npm安装..."
        pkg install -y nodejs --reinstall
        
        if command -v npm >/dev/null 2>&1; then
            echo -n "✅ npm修复成功！版本: "
            npm -v
        else
            echo "❌ npm仍然不可用。请检查您的Termux安装。"
            exit 1
        fi
    fi
}

# 修复Termux中NVM问题的函数（如果存在）
fix_nvm_issues_termux() {
    if [ -d "$HOME/.nvm" ]; then
        echo "🔧 发现现有NVM安装。正在修复Termux兼容性问题..."
        
        # 临时取消设置PREFIX以进行NVM操作
        if [ -n "$PREFIX" ]; then
            echo "🔄 临时取消设置PREFIX以兼容NVM..."
            OLD_PREFIX="$PREFIX"
            unset PREFIX
        fi
        
        # 尝试加载NVM
        if [ -f "$HOME/.nvm/nvm.sh" ]; then
            echo "🔄 加载NVM环境..."
            \. "$HOME/.nvm/nvm.sh"
            
            # 检查Node.js是否通过NVM可用
            if command -v node >/dev/null 2>&1; then
                current_version=$(node -v | sed 's/v//')
                major_version=$(echo $current_version | cut -d. -f1)
                
                if [ "$major_version" -ge 18 ]; then
                    echo "✅ NVM Node.js正常工作: v$current_version"
                    # 恢复PREFIX
                    if [ -n "$OLD_PREFIX" ]; then
                        export PREFIX="$OLD_PREFIX"
                    fi
                    return 0
                fi
            fi
        fi
        
        # 恢复PREFIX
        if [ -n "$OLD_PREFIX" ]; then
            export PREFIX="$OLD_PREFIX"
        fi
        
        echo "⚠️  NVM安装有问题。改用Termux包管理器..."
    fi
    
    return 1
}

install_nodejs() {
    local platform=$(uname -s)
    
    # 检查是否在Termux环境中
    if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ] || [ "$PREFIX" = "/data/data/com.termux/files/usr" ]; then
        echo "✅ 检测到Termux环境"
        
        # 检查存储权限是否已设置
        if [ ! -d "$HOME/storage" ]; then
            echo "⚠️  存储访问权限未设置。您可能需要运行: termux-setup-storage"
        fi
        
        # 首先尝试修复NVM问题
        if ! fix_nvm_issues_termux; then
            echo "📦 通过Termux包管理器安装Node.js..."
            install_nodejs_termux
        fi
        return
    fi
    
    case "$platform" in
        Linux|Darwin)
            echo "🚀 在Unix/Linux/macOS上安装Node.js..."
            
            echo "📥 下载并安装nvm..."
            curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
            
            echo "🔄 加载nvm环境..."
            \. "$HOME/.nvm/nvm.sh"
            
            echo "📦 下载并安装Node.js v22..."
            nvm install 22
            
            echo -n "✅ Node.js安装完成！版本: "
            node -v # 应该输出 "v22.17.0"
            echo -n "✅ 当前nvm版本: "
            nvm current # 应该输出 "v22.17.0"
            echo -n "✅ npm版本: "
            npm -v # 应该输出 "10.9.2"
            ;;
        *)
            echo "不支持的平台: $platform"
            exit 1
            ;;
    esac
}

# 检查Node.js是否已安装且版本 >= 18
if command -v node >/dev/null 2>&1; then
    current_version=$(node -v | sed 's/v//')
    major_version=$(echo $current_version | cut -d. -f1)
    
    if [ "$major_version" -ge 18 ]; then
        echo "Node.js已安装: v$current_version"
    else
        echo "Node.js v$current_version已安装但版本 < 18。正在升级..."
        install_nodejs
    fi
else
    echo "未找到Node.js。正在安装..."
    install_nodejs
fi

# 检查Claude Code是否已安装
if command -v claude >/dev/null 2>&1; then
    echo "Claude Code已安装: $(claude --version)"
else
    echo "未找到Claude Code。正在安装..."
    
    # 检查是否在Termux环境中以进行特殊的npm处理
    if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ] || [ "$PREFIX" = "/data/data/com.termux/files/usr" ]; then
        echo "📦 在Termux环境中安装Claude Code..."
        
        # 确保npm正常工作
        if ! command -v npm >/dev/null 2>&1; then
            echo "❌ 未找到npm。请确保Node.js安装成功完成。"
            exit 1
        fi
        
        # 为Termux设置npm配置
        echo "🔧 为Termux配置npm..."
        npm config set prefix "$HOME/.npm-global"
        
        # 如果目录不存在则创建
        mkdir -p "$HOME/.npm-global/bin"
        mkdir -p "$HOME/bin"
        
        # 如果npm全局bin目录不在PATH中则添加
        if [[ ":$PATH:" != *":$HOME/.npm-global/bin:"* ]]; then
            export PATH="$HOME/.npm-global/bin:$PATH"
        fi
        
        if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
            export PATH="$HOME/bin:$PATH"
        fi
        
        # 安装Claude Code并处理错误
        echo "📦 安装@anthropic-ai/claude-code..."
        if npm install -g @anthropic-ai/claude-code; then
            echo "✅ 全局安装成功"
        else
            echo "⚠️  全局安装失败。尝试本地安装..."
            if npm install @anthropic-ai/claude-code; then
                echo "✅ 本地安装成功"
                # 为本地安装创建符号链接
                if [ -f "node_modules/.bin/claude" ]; then
                    ln -sf "$(pwd)/node_modules/.bin/claude" "$HOME/bin/claude"
                    echo "✅ 已为claude命令创建符号链接"
                fi
            else
                echo "❌ 全局和本地安装都失败了"
                echo "🔧 这可能是由于网络问题或包冲突导致的"
                echo "💡 您可以稍后手动安装: npm install -g @anthropic-ai/claude-code"
                exit 1
            fi
        fi
        
        # 验证安装
        if ! command -v claude >/dev/null 2>&1; then
            echo "⚠️  在PATH中未找到Claude命令。检查安装..."
            
            # 检查各种可能的位置
            if [ -f "$HOME/.npm-global/bin/claude" ]; then
                echo "✅ 在npm全局bin中找到claude"
                export PATH="$HOME/.npm-global/bin:$PATH"
            elif [ -f "$HOME/bin/claude" ]; then
                echo "✅ 在home bin中找到claude"
                export PATH="$HOME/bin:$PATH"
            elif [ -f "node_modules/.bin/claude" ]; then
                echo "✅ 在本地node_modules中找到claude"
                ln -sf "$(pwd)/node_modules/.bin/claude" "$HOME/bin/claude"
                export PATH="$HOME/bin:$PATH"
            else
                echo "❌ 安装后仍未找到Claude命令"
                echo "🔧 请检查您的npm安装并重试"
                exit 1
            fi
        fi
    else
        # 非Termux系统的标准安装
        npm install -g @anthropic-ai/claude-code
    fi
fi

# 配置Claude Code跳过引导并清除被拒绝的自定义API响应
echo "配置Claude Code跳过引导并清除被拒绝的自定义API响应..."
node -e '
const fs = require("fs");
const os = require("os");
const path = require("path");

const homeDir = os.homedir();
const filePath = path.join(homeDir, ".claude.json");

try {
    let content = {};
    if (fs.existsSync(filePath)) {
        content = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    }
    
    // 清除被拒绝的数组以允许重新批准自定义API
    if (content.customApiKeyResponses && content.customApiKeyResponses.rejected) {
        content.customApiKeyResponses.rejected = [];
    }
    
    // 设置引导为已完成
    content.hasCompletedOnboarding = true;
    
    fs.writeFileSync(filePath, JSON.stringify(content, null, 2), "utf-8");
    console.log("✅ Claude配置已更新");
} catch (error) {
    console.log("⚠️  无法更新Claude配置:", error.message);
}'

# 检查现有的ANTHROPIC_API_KEY
existing_api_key=""
if [ -n "$ANTHROPIC_API_KEY" ]; then
    existing_api_key="$ANTHROPIC_API_KEY"
elif [ -f "$HOME/.bashrc" ] && grep -q "export ANTHROPIC_API_KEY=" "$HOME/.bashrc"; then
    existing_api_key=$(grep "export ANTHROPIC_API_KEY=" "$HOME/.bashrc" | head -1 | cut -d'=' -f2 | tr -d '"')
elif [ -f "$HOME/.zshrc" ] && grep -q "export ANTHROPIC_API_KEY=" "$HOME/.zshrc"; then
    existing_api_key=$(grep "export ANTHROPIC_API_KEY=" "$HOME/.zshrc" | head -1 | cut -d'=' -f2 | tr -d '"')
elif [ -f "$HOME/.profile" ] && grep -q "export ANTHROPIC_API_KEY=" "$HOME/.profile"; then
    existing_api_key=$(grep "export ANTHROPIC_API_KEY=" "$HOME/.profile" | head -1 | cut -d'=' -f2 | tr -d '"')
fi

# 处理API密钥输入
api_key=""
if [ -n "$existing_api_key" ]; then
    echo "🔍 发现现有的ANTHROPIC_API_KEY: ${existing_api_key:0:8}...${existing_api_key: -4}"
    echo ""
    echo "您是否要重新输入API密钥？(y/N):"
    
    # 修复管道执行（curl | bash）- 从/dev/tty重定向
    if [ -t 0 ]; then
        # 标准执行 - stdin可用
        read -r choice
    else
        # 管道执行 - 从终端重定向
        read -r choice < /dev/tty
    fi
    
    case "$choice" in
        [Yy]|[Yy][Ee][Ss])
            echo "🔑 请输入您的$SERVICE_NAME API密钥:"
            echo "   您可以从以下地址获取API密钥: $API_KEY_URL"
            echo "   注意: 为了安全，输入是隐藏的。请直接粘贴您的API密钥。"
            echo ""
            
            # 修复管道执行（curl | bash）- 从/dev/tty重定向
            if [ -t 0 ]; then
                # 标准执行 - stdin可用
                read -s api_key
            else
                # 管道执行 - 从终端重定向
                read -s api_key < /dev/tty
            fi
            echo ""
            
            if [ -z "$api_key" ]; then
                echo "⚠️  API密钥不能为空。使用现有密钥。"
                api_key="$existing_api_key"
            fi
            ;;
        *)
            echo "✅ 使用现有API密钥。"
            api_key="$existing_api_key"
            ;;
    esac
else
    echo "🔑 请输入您的$SERVICE_NAME API密钥:"
    echo "   您可以从以下地址获取API密钥: $API_KEY_URL"
    echo "   注意: 为了安全，输入是隐藏的。请直接粘贴您的API密钥。"
    echo ""
    
    # 修复管道执行（curl | bash）- 从/dev/tty重定向
    if [ -t 0 ]; then
        # 标准执行 - stdin可用
        read -s api_key
    else
        # 管道执行 - 从终端重定向
        read -s api_key < /dev/tty
    fi
    echo ""
    
    if [ -z "$api_key" ]; then
        echo "⚠️  API密钥不能为空。请重新运行脚本。"
        exit 1
    fi
fi

# 检测当前shell并确定rc文件
current_shell=$(basename "$SHELL")
case "$current_shell" in
    bash)
        rc_file="$HOME/.bashrc"
        ;;
    zsh)
        rc_file="$HOME/.zshrc"
        ;;
    fish)
        rc_file="$HOME/.config/fish/config.fish"
        ;;
    *)
        rc_file="$HOME/.profile"
        ;;
esac

# 将环境变量添加到rc文件
echo ""
echo "📝 将环境变量添加到$rc_file..."

# 检查变量是否已存在并删除它们以避免重复
if [ -f "$rc_file" ] && grep -q "ANTHROPIC_BASE_URL\|ANTHROPIC_API_KEY" "$rc_file"; then
    echo "🔄 更新$rc_file中的现有环境变量..."
    # 删除现有的Claude Code环境变量
    # 检测操作系统以使用正确的sed语法
    # termux也需要空字符串参数  sed -i ''
    if [[ "$OSTYPE" == "darwin"* ]] ; then
        echo "macOS"
        # macOS需要空字符串参数
        sed -i '' '/# Claude Code environment variables/d' "$rc_file"
        sed -i '' '/export ANTHROPIC_BASE_URL=/d' "$rc_file"
        sed -i '' '/export ANTHROPIC_API_KEY=/d' "$rc_file"
        sed -i '' '/export PATH.*npm-global/d' "$rc_file"
        # 删除可能留下的空行
        sed -i '' '/^$/N;/^\n$/d' "$rc_file"
    elif [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ] || [ "$PREFIX" = "/data/data/com.termux/files/usr" ]; then
        echo "termux"
        # termux需要空字符串参数
        sed -i '' '/# Claude Code environment variables/d' "$rc_file"
        sed -i '' '/export ANTHROPIC_BASE_URL=/d' "$rc_file"
        sed -i '' '/export ANTHROPIC_API_KEY=/d' "$rc_file"
        sed -i '' '/export PATH.*npm-global/d' "$rc_file"
        # 删除可能留下的空行
        sed -i '' '/^$/N;/^\n$/d' "$rc_file"
    else
        echo "Linux/Windows Git Bash"
        # Linux/Windows Git Bash不需要空字符串参数
        sed -i '/# Claude Code environment variables/d' "$rc_file"
        sed -i '/export ANTHROPIC_BASE_URL=/d' "$rc_file"
        sed -i '/export ANTHROPIC_API_KEY=/d' "$rc_file"
        sed -i '/export PATH.*npm-global/d' "$rc_file"
        # 删除可能留下的空行
        sed -i '/^$/N;/^\n$/d' "$rc_file"
    fi
else
    echo "📝 向$rc_file添加新的环境变量..."
fi

# 添加新条目
echo "" >> "$rc_file"
echo "# Claude Code环境变量" >> "$rc_file"
echo "export ANTHROPIC_BASE_URL=\"$ANTHROPIC_BASE_URL\"" >> "$rc_file"
echo "export ANTHROPIC_API_KEY=\"$api_key\"" >> "$rc_file"

# 如果需要，为Termux添加PATH
if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ] || [ "$PREFIX" = "/data/data/com.termux/files/usr" ]; then
    echo "export PATH=\"\$HOME/.npm-global/bin:\$HOME/bin:\$PATH\"" >> "$rc_file"
fi

echo "✅ $rc_file中的环境变量已更新"

# 如果目录不存在则创建
mkdir -p "$HOME/.claude"

SETTING_PATH="$HOME/.claude/settings.json"
if [ -f "$SETTING_PATH" ]; then
    echo "📝 settings.json已存在。正在更新URL和API配置..."
    
    # 使用Node.js读取现有配置并只更新特定字段
    node -e '
    const fs = require("fs");
    const settingPath = process.argv[1];
    const apiKey = process.argv[2];
    const baseUrl = process.argv[3];
    
    try {
        let settings = {};
        if (fs.existsSync(settingPath)) {
            const content = fs.readFileSync(settingPath, "utf-8");
            settings = JSON.parse(content);
        }
        
        // 确保env对象存在
        if (!settings.env) {
            settings.env = {};
        }
        
        // 只更新API相关字段
        settings.env.ANTHROPIC_API_KEY = apiKey;
        settings.env.ANTHROPIC_BASE_URL = baseUrl;
        settings.apiKeyHelper = "\""+apiKey+"\"";
        
        // 如果permissions不存在，创建默认值
        if (!settings.permissions) {
            settings.permissions = {
                "allow": [],
                "deny": []
            };
        }
        
        fs.writeFileSync(settingPath, JSON.stringify(settings, null, 2), "utf-8");
        console.log("✅ Claude设置文件已更新（保留现有配置）");
    } catch (error) {
        console.log("❌ 更新设置文件失败:", error.message);
        console.log("🔄 将创建新的设置文件...");
        
        // 如果读取失败，创建新的配置文件
        const newSettings = {
            "env": {
                "ANTHROPIC_API_KEY": apiKey,
                "ANTHROPIC_BASE_URL": baseUrl
            },
            "permissions": {
                "allow": [],
                "deny": []
            },
            "apiKeyHelper": "\""+apiKey+"\""
        };
        
        fs.writeFileSync(settingPath, JSON.stringify(newSettings, null, 2), "utf-8");
        console.log("✅ 新的Claude设置文件已创建");
    }
    ' "$SETTING_PATH" "$api_key" "$ANTHROPIC_BASE_URL"
else
    echo "📝 创建新的settings.json文件..."
    
    cat > "$SETTING_PATH" << EOF
{
  "env": {
    "ANTHROPIC_API_KEY": "$api_key",
    "ANTHROPIC_BASE_URL": "$ANTHROPIC_BASE_URL"
  },
  "permissions": {
    "allow": [],
    "deny": []
  },
  "apiKeyHelper": "$api_key"
}
EOF
    echo "✅ Claude设置文件已创建"
fi

# 立即应用更改，加载rc文件
echo "🔄 尝试加载$rc_file..."
if [ -f "$rc_file" ]; then
    echo "📁 RC文件存在: $rc_file"
    echo "🔍 检查RC文件内容是否有潜在问题..."
    
    # 检查rc文件是否有明显问题
    if grep -q "read\|input\|prompt" "$rc_file" 2>/dev/null; then
        echo "⚠️  RC文件可能包含交互式命令，跳过加载"
    else
        echo "🔄 加载RC文件..."
        if timeout 10 source "$rc_file" 2>/dev/null; then
            echo "✅ RC文件加载成功"
        else
            echo "⚠️  RC文件加载超时或失败，继续执行"
        fi
    fi
else
    echo "❌ 未找到RC文件: $rc_file"
fi
echo "🔄 继续完成安装..."

echo ""
echo "🎉 安装成功完成！"
echo ""

# 检查是否在Termux中以提供特定说明
if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ] || [ "$PREFIX" = "/data/data/com.termux/files/usr" ]; then
    echo "📋 Termux特定的后续步骤:"
    echo "   1. 重启您的Termux会话或运行: source $rc_file"
    echo "   2. 使用以下命令测试Claude Code: claude --version"
    echo "   3. 如果找不到'claude'命令，请尝试: hash -r"
    echo "   4. 开始使用Claude Code:"
    echo "      ANTHROPIC_BASE_URL=\"$ANTHROPIC_BASE_URL\" ANTHROPIC_API_KEY=\"$api_key\" claude"
    echo ""
    echo "🔧 Termux故障排除:"
    echo "   - 如果遇到权限错误，请尝试: termux-setup-storage"
    echo "   - 对于NVM问题，此脚本使用Termux的原生Node.js包"
    echo "   - 如果PATH问题持续存在，请手动添加到您的shell配置:"
    echo "     export PATH=\"\$HOME/.npm-global/bin:\$HOME/bin:\$PATH\""
else
    echo "🔄 如果启动baseurl和apikey没有生效，请重启您的终端或运行:"
    echo "   source $rc_file"
    echo ""
    echo "🚀 如果启动baseurl和apikey没有生效，您也可以开始使用Claude Code:"
    echo "   ANTHROPIC_BASE_URL=\"$ANTHROPIC_BASE_URL\" ANTHROPIC_API_KEY=\"$api_key\" claude"
fi

echo ""
echo "✅ $SERVICE_NAME配置已应用！"
echo "🌐 使用基础URL: $ANTHROPIC_BASE_URL"
echo "🔗 API密钥URL: $API_KEY_URL"
# 颜文字警告
echo "⚠️  注意第一次启动claude后，选择使用自定义api，如果选错了，请重新运行该脚本"
echo "⚠️  注意第一次启动claude后，选择使用自定义api，如果选错了，请重新运行该脚本"
echo "⚠️  注意第一次启动claude后，选择使用自定义api，如果选错了，请重新运行该脚本"
# 倒计时3秒
for i in {3..1}; do
    echo -n "$i "
    sleep 1
done
echo "直接输入claude启动即可..."
