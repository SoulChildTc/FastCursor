import sys
from flask import Flask, jsonify, request, render_template
from account_manager import AccountManager, AccountStatus
from logger import logging
from scheduler import AccountScheduler
import threading
from config import Config
from change_account import change_cursor_account
import os
import json
import shutil
from datetime import datetime
import time
import tempfile
from exchange_token import get_new_token

app = Flask(__name__)
account_manager = AccountManager()

config = Config()

# 创建并启动调度器
scheduler = AccountScheduler(enable_register=config.enable_register)
scheduler_thread = threading.Thread(target=scheduler.run, daemon=True)
scheduler_thread.start()

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/account', methods=['GET'])
def get_account():
    """获取一个可用的账号
    
    Returns:
        JSON响应:
        - 成功: {'code': 200, 'data': account_info, 'message': '获取账号成功'}
        - 失败: {'code': 404, 'message': '暂无可用账号'}
    """
    try:
        account = account_manager.get_available_account()
        if account:
            account["token"] = get_new_token(account['token'])
            return jsonify({
                'code': 200,
                'data': account,
                'message': '获取账号成功'
            })
        else:
            return jsonify({
                'code': 404,
                'message': '暂无可用账号'
            }), 404
    except Exception as e:
        logging.error(f"获取账号时发生错误: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取账号统计信息
    
    Returns:
        JSON响应:
        - 成功: {'code': 200, 'data': stats, 'message': '获取统计信息成功'}
        - 失败: {'code': 500, 'message': '服务器内部错误'}
    """
    try:
        stats = account_manager.get_accounts_stats()
        return jsonify({
            'code': 200,
            'data': stats,
            'message': '获取统计信息成功'
        })
    except Exception as e:
        logging.error(f"获取统计信息时发生错误: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """获取所有账号列表
    
    Returns:
        JSON响应:
        - 成功: {'code': 200, 'data': accounts_list, 'message': '获取账号列表成功'}
        - 失败: {'code': 500, 'message': '服务器内部错误'}
    """
    try:
        accounts = account_manager.get_all_accounts()
        return jsonify({
            'code': 200,
            'data': accounts,
            'message': '获取账号列表成功'
        })
    except Exception as e:
        logging.error(f"获取账号列表时发生错误: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@app.route('/api/scheduler/next', methods=['GET'])
def get_next_run():
    """获取下一次账号注册的时间信息
    
    Returns:
        JSON响应:
        - 成功: {'code': 200, 'data': next_run_info, 'message': '获取下一次注册时间成功'}
        - 失败: {'code': 500, 'message': '服务器内部错误'}
    """
    try:
        next_run_info = scheduler.get_next_run_info()
        return jsonify({
            'code': 200,
            'data': next_run_info,
            'message': '获取下一次注册时间成功'
        })
    except Exception as e:
        logging.error(f"获取下一次注册时间时发生错误: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@app.route('/api/scheduler/trigger', methods=['POST'])
def trigger_registration():
    """立即触发一次账号注册
    
    Returns:
        JSON响应:
        - 成功: {'code': 200, 'message': '已触发账号注册任务'}
        - 失败: {'code': 500, 'message': '服务器内部错误'}
    """
    try:
        # 创建一个新线程来执行注册任务，避免阻塞API响应
        threading.Thread(target=scheduler.register_account, daemon=True).start()
        return jsonify({
            'code': 200,
            'message': '已触发账号注册任务'
        })
    except Exception as e:
        logging.error(f"触发账号注册任务时发生错误: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '服务器内部错误'
        }), 500

@app.route('/api/accounts/batch-mark-invalid', methods=['POST'])
def batch_mark_invalid():
    """批量标记账号为无效状态"""
    try:
        data = request.get_json()
        suffix = data.get('suffix')
        if not suffix or not suffix.startswith('@'):
            return jsonify({
                'code': 400,
                'message': '请提供正确的邮箱后缀'
            }), 400
            
        success = account_manager.batch_mark_invalid_by_suffix(suffix)
        return jsonify({
            'code': 200,
            'message': '批量标记完成'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@app.route('/api/account/mark-status', methods=['POST'])
def mark_account_status():
    """标记账号状态"""
    try:
        data = request.get_json()
        email = data.get('email')
        status = data.get('status')

        if status == 'available':
            status = AccountStatus.AVAILABLE
        elif status == 'allocated':
            status = AccountStatus.ALLOCATED
        elif status == 'invalid':
            status = AccountStatus.INVALID
        else:
            return jsonify({
                'code': 400,
                'message': '请提供正确的状态'
            }), 400

        account_manager.mark_account_status(email, status, True)
        return jsonify({
            'code': 200,
            'message': '账号状态标记成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500



@app.route('/api/account/switch', methods=['POST'])
def account_switch():
    """更换账号
    
    请求体参数:
        account_id: 要切换到的账号ID
    
    Returns:
        JSON响应:
        - 成功: {'code': 200, 'message': '账号更换成功'}
        - 失败: {'code': 500, 'message': '服务器错误信息'}
    """
    try:
        data = request.get_json()
        if not data or 'account_id' not in data:
            change_cursor_account()
        else:
            account_id = data['account_id']
            change_cursor_account(account_id)
            
        return jsonify({
            'code': 200,
            'message': '账号更换成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500

@app.route('/api/logs/stream')
def stream_logs():
    """提供实时日志流
    
    Returns:
        Response: 包含实时日志的 Server-Sent Events 流
    """
    def generate():
        if sys.platform == "win32":
            log_pipe_path = os.path.join(tempfile.gettempdir(), "cursor_register.pipe")
        else:
            log_pipe_path = '/tmp/cursor_register.pipe'
            
        # 打开管道进行读取
        with open(log_pipe_path, 'r') as pipe:
            while True:
                line = pipe.readline().strip()
                if line:
                    # 格式化为SSE消息
                    yield f"data: {json.dumps({'log': line})}\n\n"
                time.sleep(0.1)  # 避免过度消耗CPU
                
    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # 禁用Nginx缓冲
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=False)
