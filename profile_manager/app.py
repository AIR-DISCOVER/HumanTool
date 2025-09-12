from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import json
from datetime import datetime, date
import uuid
import os

app = Flask(__name__)
CORS(app)

# 数据库配置 - 支持环境变量
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'mysql'),          # 改为 'mysql'
    'port': int(os.environ.get('DB_PORT', '3306')),      # 改为 '3306'
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '123456'),
    'database': os.environ.get('DB_NAME', 'tata'),
    'charset': 'utf8mb4'
}

print(f"=== 数据库配置 ===")
print(f"DB_HOST: {DB_CONFIG['host']}")
print(f"DB_PORT: {DB_CONFIG['port']}")
print(f"DB_USER: {DB_CONFIG['user']}")
print(f"DB_NAME: {DB_CONFIG['database']}")
print(f"=================")

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def safe_json_loads(json_str):
    """安全地解析JSON字符串"""
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working!', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, name, display_name, user_type, experiment_group,
                   overall_profile, last_updated, `accessible`, created_at, updated_at
            FROM users
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        
        # 安全处理日期字段
        for user in users:
            # 处理日期字段
            if user['last_updated']:
                user['last_updated'] = user['last_updated'].isoformat() if hasattr(user['last_updated'], 'isoformat') else str(user['last_updated'])
            if user['created_at']:
                user['created_at'] = user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
            if user['updated_at']:
                user['updated_at'] = user['updated_at'].isoformat() if hasattr(user['updated_at'], 'isoformat') else str(user['updated_at'])
        
        return jsonify(users), 200
    except Exception as e:
        print(f"Error in get_users: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM users WHERE id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # 安全处理JSON字段
        user['preferences'] = safe_json_loads(user['preferences']) or {}
        
        # 处理日期字段
        if user['last_updated']:
            user['last_updated'] = user['last_updated'].isoformat() if hasattr(user['last_updated'], 'isoformat') else str(user['last_updated'])
        if user['created_at']:
            user['created_at'] = user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
        if user['updated_at']:
            user['updated_at'] = user['updated_at'].isoformat() if hasattr(user['updated_at'], 'isoformat') else str(user['updated_at'])
        
        return jsonify(user), 200
    except Exception as e:
        print(f"Error in get_user: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 生成用户ID
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        
        # 构建overall_profile - 将所有信息都放在这里
        profile_parts = []
        
        # Capabilities部分
        capabilities = data.get('capabilities', {})
        if capabilities.get('cognitive_judgment'):
            profile_parts.append(f"认知判断与创造力：{capabilities['cognitive_judgment']}")
        if capabilities.get('specialized_skill'):
            profile_parts.append(f"专业技能与能力：{capabilities['specialized_skill']}")
        if capabilities.get('external_interaction'):
            profile_parts.append(f"外部世界交互：{capabilities['external_interaction']}")
        
        # Information部分
        information = data.get('information', {})
        if information.get('domain_expertise'):
            profile_parts.append(f"领域专业知识：{information['domain_expertise']}")
        if information.get('private_domain'):
            profile_parts.append(f"私有领域信息：{information['private_domain']}")
        if information.get('preference_constraints'):
            profile_parts.append(f"偏好约束：{information['preference_constraints']}")
        
        # Authority部分
        authority = data.get('authority', {})
        if authority.get('responsibility_scope'):
            profile_parts.append(f"责任范围定义：{authority['responsibility_scope']}")
        if authority.get('authorizable_content'):
            profile_parts.append(f"用户可授权内容：{authority['authorizable_content']}")
        
        overall_profile = "；".join(profile_parts)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 只更新需要的字段，不包括 information_capabilities 和 reasoning_capabilities
        cursor.execute("""
            INSERT INTO users (
                id, name, display_name, user_type, experiment_group,
                overall_profile, last_updated, `accessible`, preferences, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            )
        """, (
            user_id,
            data.get('name', ''),
            data.get('display_name', ''),
            data.get('user_type', 'general'),
            data.get('experiment_group', 'A'),
            overall_profile,
            datetime.now().date(),
            data.get('accessible', True),
            json.dumps(data.get('preferences', {}), ensure_ascii=False)
        ))
        
        conn.commit()
        
        return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
    except Exception as e:
        print(f"Error in create_user: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 构建overall_profile - 将所有信息都放在这里
        profile_parts = []
        
        capabilities = data.get('capabilities', {})
        if capabilities.get('cognitive_judgment'):
            profile_parts.append(f"认知判断与创造力：{capabilities['cognitive_judgment']}")
        if capabilities.get('specialized_skill'):
            profile_parts.append(f"专业技能与能力：{capabilities['specialized_skill']}")
        if capabilities.get('external_interaction'):
            profile_parts.append(f"外部世界交互：{capabilities['external_interaction']}")
        
        information = data.get('information', {})
        if information.get('domain_expertise'):
            profile_parts.append(f"领域专业知识：{information['domain_expertise']}")
        if information.get('private_domain'):
            profile_parts.append(f"私有领域信息：{information['private_domain']}")
        if information.get('preference_constraints'):
            profile_parts.append(f"偏好约束：{information['preference_constraints']}")
        
        authority = data.get('authority', {})
        if authority.get('responsibility_scope'):
            profile_parts.append(f"责任范围定义：{authority['responsibility_scope']}")
        if authority.get('authorizable_content'):
            profile_parts.append(f"用户可授权内容：{authority['authorizable_content']}")
        
        overall_profile = "；".join(profile_parts)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 只更新需要的字段，不包括 information_capabilities 和 reasoning_capabilities
        cursor.execute("""
            UPDATE users SET
                name = %s,
                display_name = %s,
                user_type = %s,
                experiment_group = %s,
                overall_profile = %s,
                last_updated = %s,
                `accessible` = %s,
                preferences = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (
            data.get('name', ''),
            data.get('display_name', ''),
            data.get('user_type', 'general'),
            data.get('experiment_group', 'A'),
            overall_profile,
            datetime.now().date(),
            data.get('accessible', True),
            json.dumps(data.get('preferences', {}), ensure_ascii=False),
            user_id
        ))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        print(f"Error in update_user: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        print(f"Error in delete_user: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)