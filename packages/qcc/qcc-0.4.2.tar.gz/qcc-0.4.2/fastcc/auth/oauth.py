"""OAuth认证模块"""

import json
import secrets
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import requests
from typing import Optional, Dict, Any
from pathlib import Path


class OAuthHandler(BaseHTTPRequestHandler):
    """OAuth回调处理器"""
    
    def do_GET(self):
        """处理OAuth回调"""
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        if 'code' in query_params:
            self.server.oauth_code = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            success_html = """
            <html>
            <head><title>认证成功</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: green;">[!] 认证成功！</h1>
                <p>您已成功授权FastCC访问您的GitHub账户。</p>
                <p>现在可以关闭此页面，返回终端继续操作。</p>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode('utf-8'))
        else:
            error = query_params.get('error', ['未知错误'])[0]
            self.server.oauth_error = error
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            error_html = f"""
            <html>
            <head><title>认证失败</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">[X] 认证失败</h1>
                <p>错误信息: {error}</p>
                <p>请关闭此页面，返回终端重试。</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """禁用日志输出"""
        pass


class GitHubOAuth:
    """GitHub OAuth认证"""
    
    # GitHub OAuth应用信息
    CLIENT_ID = "Iv1.b507a08c87ecfe98"  # GitHub CLI的客户端ID（临时使用）
    CLIENT_SECRET = None  # 公开应用不需要客户端密钥
    REDIRECT_URI = "http://localhost:8080/callback"
    SCOPE = "gist"
    
    # 使用GitHub Device Flow，更适合CLI应用
    DEVICE_CODE_URL = "https://github.com/login/device/code"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    AUTH_URL = "https://github.com/login/oauth/authorize"
    
    def __init__(self):
        self.state = None
        self.access_token = None
    
    def start_auth_flow(self) -> bool:
        """开始OAuth认证流程 - 使用Device Flow"""
        try:
            print("🔐 开始GitHub设备认证流程...")
            
            # 第一步：获取设备码和用户码
            device_response = self._get_device_code()
            if not device_response:
                return False
            
            device_code = device_response['device_code']
            user_code = device_response['user_code']
            verification_uri = device_response['verification_uri']
            expires_in = device_response.get('expires_in', 900)
            interval = device_response.get('interval', 5)
            
            print(f"\n[L] 请按以下步骤完成认证：")
            print(f"1. 打开浏览器访问: {verification_uri}")
            print(f"2. 输入设备码: {user_code}")
            print(f"3. 完成GitHub授权")
            print(f"\n⏰ 该码在 {expires_in//60} 分钟内有效")
            print(f"[...] 等待授权...")
            
            # 自动打开浏览器
            webbrowser.open(verification_uri)
            
            # 第二步：轮询获取访问令牌
            return self._poll_for_token(device_code, interval, expires_in)
            
        except Exception as e:
            print(f"[X] 启动认证流程失败: {e}")
            return False
    
    def _get_device_code(self) -> Optional[Dict[str, Any]]:
        """获取设备码"""
        try:
            data = {
                'client_id': self.CLIENT_ID,
                'scope': self.SCOPE
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'FastCC/1.0'
            }
            
            response = requests.post(
                self.DEVICE_CODE_URL,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"[X] 获取设备码失败: {e}")
            return None
    
    def _poll_for_token(self, device_code: str, interval: int, expires_in: int) -> bool:
        """轮询获取访问令牌"""
        import time
        
        try:
            start_time = time.time()
            
            while time.time() - start_time < expires_in:
                response = self._check_token(device_code)
                
                if response and 'access_token' in response:
                    self.access_token = response['access_token']
                    print("[OK] 认证成功！")
                    return True
                elif response and response.get('error') == 'authorization_pending':
                    # 继续等待
                    print("[...] 等待用户授权...", end='\r')
                    time.sleep(interval)
                elif response and response.get('error') == 'slow_down':
                    # 减慢轮询速度
                    interval += 5
                    time.sleep(interval)
                elif response and response.get('error'):
                    error = response.get('error_description', response['error'])
                    print(f"[X] 认证失败: {error}")
                    return False
                else:
                    time.sleep(interval)
            
            print("[X] 认证超时，请重试")
            return False
            
        except KeyboardInterrupt:
            print("\n[X] 用户取消认证")
            return False
        except Exception as e:
            print(f"[X] 轮询令牌失败: {e}")
            return False
    
    def _check_token(self, device_code: str) -> Optional[Dict[str, Any]]:
        """检查令牌状态"""
        try:
            data = {
                'client_id': self.CLIENT_ID,
                'device_code': device_code,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'FastCC/1.0'
            }
            
            response = requests.post(
                self.TOKEN_URL,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return response.json() if response.content else None
                
        except Exception:
            return None
    
    def _wait_for_callback(self) -> bool:
        """等待OAuth回调"""
        try:
            # 创建HTTP服务器
            server = HTTPServer(('localhost', 8080), OAuthHandler)
            server.oauth_code = None
            server.oauth_error = None
            
            print("[...] 等待GitHub授权回调...")
            print("请在浏览器中完成授权操作")
            
            # 在单独线程中运行服务器
            server_thread = Thread(target=server.handle_request)
            server_thread.daemon = True
            server_thread.start()
            
            # 等待回调
            server_thread.join(timeout=300)  # 5分钟超时
            
            if server.oauth_code:
                # 使用授权码获取访问令牌
                return self._exchange_code_for_token(server.oauth_code)
            elif server.oauth_error:
                print(f"[X] 授权失败: {server.oauth_error}")
                return False
            else:
                print("[X] 授权超时，请重试")
                return False
                
        except Exception as e:
            print(f"[X] 等待授权回调失败: {e}")
            return False
    
    def _exchange_code_for_token(self, code: str) -> bool:
        """使用授权码交换访问令牌"""
        try:
            token_data = {
                'client_id': self.CLIENT_ID,
                'code': code,
                'redirect_uri': self.REDIRECT_URI
            }
            
            # 如果有客户端密钥，添加它
            if self.CLIENT_SECRET:
                token_data['client_secret'] = self.CLIENT_SECRET
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'FastCC/1.0'
            }
            
            response = requests.post(
                self.TOKEN_URL,
                data=token_data,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                print("[OK] 成功获取访问令牌")
                return True
            else:
                error = result.get('error_description', '未知错误')
                print(f"[X] 获取访问令牌失败: {error}")
                return False
                
        except Exception as e:
            print(f"[X] 交换访问令牌失败: {e}")
            return False
    
    def save_token(self) -> bool:
        """保存访问令牌到本地"""
        if not self.access_token:
            return False
        
        try:
            config_dir = Path.home() / ".fastcc"
            config_dir.mkdir(exist_ok=True)
            
            token_file = config_dir / "github_token.json"
            data = {
                'access_token': self.access_token,
                'scope': self.SCOPE
            }
            
            with open(token_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # 设置文件权限
            token_file.chmod(0o600)
            return True
            
        except Exception as e:
            print(f"[X] 保存令牌失败: {e}")
            return False
    
    @staticmethod
    def load_token() -> Optional[str]:
        """从本地加载访问令牌"""
        try:
            token_file = Path.home() / ".fastcc" / "github_token.json"
            if not token_file.exists():
                return None
            
            with open(token_file, 'r') as f:
                data = json.load(f)
                return data.get('access_token')
                
        except Exception:
            return None
    
    @staticmethod
    def remove_token() -> bool:
        """删除本地访问令牌"""
        try:
            token_file = Path.home() / ".fastcc" / "github_token.json"
            if token_file.exists():
                token_file.unlink()
            return True
        except:
            return False


def authenticate_github() -> Optional[str]:
    """GitHub认证主函数"""
    # 首先尝试加载现有令牌
    token = GitHubOAuth.load_token()
    if token:
        # 验证令牌是否有效
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={'Authorization': f'token {token}'}
            )
            if response.status_code == 200:
                user_info = response.json()
                print(f"[OK] 已使用缓存令牌登录为: {user_info.get('login', '未知用户')}")
                return token
        except:
            pass
    
    # 开始新的认证流程
    oauth = GitHubOAuth()
    if oauth.start_auth_flow() and oauth.save_token():
        return oauth.access_token
    
    return None