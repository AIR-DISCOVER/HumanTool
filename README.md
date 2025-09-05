# TATA-创意写作评估系统

## 项目简介

TATA-创意写作评估系统是一个基于Django开发的创意写作评估平台，使用AI技术对用户提交的创意写作文本进行专业评估。系统支持六个核心评估维度，提供详细的分数和专业解释。

## 主要功能

### 📝 评估功能
- **六维度评估**: 角色深度与共情、主题表达与思想论证、叙事技巧与视觉叙事、情节逻辑与因果关系、故事结构与转折点、冲突深度与对抗性
- **智能分析**: 基于AI的专业文学评估
- **详细反馈**: 每个维度提供1-7分评分和详细解释
- **用户分组**: 支持写作A-1、A-2、B-1、B-2四个组别

### 🎯 用户界面
- **简洁表单**: 用户友好的文本提交界面
- **实时评估**: 提交后自动调用AI进行评估
- **结果展示**: 清晰的评估结果展示页面
- **数据下载**: 支持评估结果下载

### 🔧 管理功能
- **Django Admin**: 完整的后台管理系统
- **数据管理**: 评估结果的查看、搜索、过滤
- **用户管理**: 超级用户权限控制
- **日志记录**: 详细的系统运行日志

## 技术架构

- **后端框架**: Django 4.x
- **数据库**: SQLite3
- **AI接口**: OpenAI API (支持自定义API Base)
- **前端**: Bootstrap 5 + 自定义CSS
- **部署**: systemd服务 + 开机自启动

## 快速部署

### 1. 环境准备

**系统要求:**
- Ubuntu 18.04+ / CentOS 7+ / Debian 9+
- Python 3.8+
- 网络连接（用于AI API调用）

**安装依赖:**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install python3 python3-pip python3-venv -y

# 安装系统依赖
sudo apt install git curl wget -y
```

### 2. 项目部署

**克隆项目:**
```bash
cd /home/your_username/projects
git clone <your-repo-url>
cd bench/Django
```

**安装Python依赖:**
```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install django langchain-openai python-dotenv
```

**配置环境变量:**
```bash
# 创建.env文件
cat > .env << EOF
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=your_api_base_url_here
OPENAI_MODEL=gpt-4o
EOF
```

**数据库初始化:**
```bash
# 执行数据库迁移
python manage.py migrate

# 创建超级用户
python create_superuser.py
```

### 3. 服务安装

**一键安装系统服务:**
```bash
# 安装并启动服务
sudo ./manage_service.sh install
```

**手动安装（可选）:**
```bash
# 设置权限
chmod +x start_service.py start_production.py

# 安装服务
sudo bash install_service.sh
```

### 4. 访问应用

**服务启动后，可通过以下地址访问:**
- **主应用**: `http://your_server_ip:8003/`
- **管理后台**: `http://your_server_ip:8003/admin/`
- **管理界面**: `http://your_server_ip:8003/management/`

**默认管理员账户:**
- 用户名: `admin`
- 密码: `admin123`

## 服务管理

### 基本命令

```bash
# 查看服务状态
sudo systemctl status django-evaluation

# 启动服务
sudo systemctl start django-evaluation

# 停止服务
sudo systemctl stop django-evaluation

# 重启服务
sudo systemctl restart django-evaluation

# 查看服务日志
sudo journalctl -u django-evaluation -f

# 查看最近日志
sudo journalctl -u django-evaluation -n 50
```

### 使用管理脚本

```bash
# 查看所有可用命令
./manage_service.sh

# 查看服务状态
./manage_service.sh status

# 查看实时日志
./manage_service.sh logs

# 重启服务
sudo ./manage_service.sh restart

# 停止服务
sudo ./manage_service.sh stop

# 卸载服务
sudo ./manage_service.sh uninstall
```

### 开机自启动

```bash
# 启用开机自启动
sudo systemctl enable django-evaluation

# 禁用开机自启动
sudo systemctl disable django-evaluation

# 检查自启动状态
sudo systemctl is-enabled django-evaluation
```

## 配置说明

### 端口配置
- 默认端口: `8003`
- 修改端口: 编辑 `start_service.py` 文件中的端口号

### 防火墙配置
```bash
# Ubuntu/Debian
sudo ufw allow 8003
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8003/tcp
sudo firewall-cmd --reload
```

### API配置
在 `.env` 文件中配置AI API相关参数:
```bash
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

## 故障排除

### 常见问题

**1. 服务启动失败**
```bash
# 查看详细错误
sudo journalctl -u django-evaluation -n 20

# 检查端口占用
sudo netstat -tulpn | grep :8003

# 手动测试启动
cd /path/to/project
python start_service.py
```

**2. API调用失败**
- 检查 `.env` 文件中的API配置
- 确认网络连接正常
- 查看日志中的具体错误信息

**3. 权限问题**
```bash
# 修改文件所有者
sudo chown -R your_username:your_username /path/to/project

# 检查服务文件权限
ls -la /etc/systemd/system/django-evaluation.service
```

**4. 数据库问题**
```bash
# 重新执行迁移
python manage.py migrate

# 检查数据库文件权限
ls -la db.sqlite3
```

### 调试模式

**启用详细日志:**
在 `settings.py` 中设置 `DEBUG = True`（仅用于调试）

**手动运行服务:**
```bash
# 开发模式运行
python manage.py runserver 0.0.0.0:8003

# 查看详细输出
python start_service.py
```

## 数据备份

### 定期备份
```bash
# 备份数据库
cp db.sqlite3 backup/db_$(date +%Y%m%d_%H%M%S).sqlite3

# 备份评估结果
tar -czf backup/evaluation_results_$(date +%Y%m%d).tar.gz evaluation_results/

# 备份配置文件
cp .env backup/env_backup_$(date +%Y%m%d).txt
```

### 恢复数据
```bash
# 停止服务
sudo systemctl stop django-evaluation

# 恢复数据库
cp backup/db_backup.sqlite3 db.sqlite3

# 重启服务
sudo systemctl start django-evaluation
```

## 更新维护

### 更新代码
```bash
# 停止服务
sudo systemctl stop django-evaluation

# 更新代码
git pull origin main

# 执行迁移（如有需要）
python manage.py migrate

# 重启服务
sudo systemctl start django-evaluation
```

### 监控建议
- 定期检查服务状态
- 监控磁盘空间使用
- 定期备份重要数据
- 查看系统日志

## 技术支持

### 日志位置
- 系统日志: `sudo journalctl -u django-evaluation`
- Django日志: 查看应用配置的日志文件

### 性能监控
```bash
# 查看进程资源使用
top -p $(pgrep -f django-evaluation)

# 查看端口连接
sudo ss -tulpn | grep :8003
```

---

**版本**: v1.0  
**更新时间**: 2025-08-19  
**维护者**: TATA团队
