import requests
import json
from urllib.parse import urlencode, parse_qs, urlparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from token_manager import TokenManager

class InoreaderClient:
    def __init__(self, client_id, client_secret, redirect_uri="https://aerthos.vercel.app/api/oauth/callback"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.base_url = "https://www.inoreader.com"
        self.token_manager = TokenManager()
        
        # 尝试加载保存的令牌
        self._load_saved_tokens()
    
    def _load_saved_tokens(self):
        """加载保存的令牌"""
        token_data = self.token_manager.load_tokens()
        if token_data:
            if token_data.get('expired'):
                # 令牌过期，需要刷新
                self.refresh_token = token_data['refresh_token']
                try:
                    self.refresh_access_token()
                except:
                    print("⚠️ 令牌刷新失败，需要重新认证")
            else:
                # 令牌有效
                self.access_token = token_data['access_token']
                self.refresh_token = token_data['refresh_token']
    
    def is_authenticated(self):
        """检查是否已认证"""
        return self.access_token is not None
        
    def get_auth_url(self, scope="read write", state="csrf_protection_123"):
        """生成OAuth认证URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'state': state
        }
        return f"{self.base_url}/oauth2/auth?{urlencode(params)}"
    
    def exchange_code_for_token(self, auth_code):
        """用授权码换取访问令牌"""
        token_url = f"{self.base_url}/oauth2/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'scope': ''
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'InoreaderClient/1.0'
        }
        
        response = requests.post(token_url, data=data, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            # 保存令牌到文件
            expires_in = token_data.get('expires_in', 3600)
            self.token_manager.save_tokens(self.access_token, self.refresh_token, expires_in)
            
            return token_data
        else:
            raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")
    
    def refresh_access_token(self):
        """刷新访问令牌"""
        if not self.refresh_token:
            raise Exception("No refresh token available")
            
        token_url = f"{self.base_url}/oauth2/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'InoreaderClient/1.0'
        }
        
        response = requests.post(token_url, data=data, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            # 保存刷新后的令牌
            expires_in = token_data.get('expires_in', 3600)
            self.token_manager.save_tokens(self.access_token, self.refresh_token, expires_in)
            
            return token_data
        else:
            raise Exception(f"Token refresh failed: {response.status_code} - {response.text}")
    
    def _make_authenticated_request(self, endpoint, method='GET', params=None, data=None):
        """发送认证请求"""
        if not self.access_token:
            raise Exception("No access token available. Please authenticate first.")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/reader/api/0{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code == 401:
            try:
                self.refresh_access_token()
                headers['Authorization'] = f'Bearer {self.access_token}'
                if method == 'GET':
                    response = requests.get(url, headers=headers, params=params)
                else:
                    response = requests.post(url, headers=headers, data=data)
            except:
                raise Exception("Authentication failed. Please re-authenticate.")
        
        return response
    
    def get_subscription_list(self):
        """获取所有订阅的feeds"""
        response = self._make_authenticated_request('/subscription/list')
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get subscription list: {response.status_code} - {response.text}")
    
    def get_user_info(self):
        """获取用户信息"""
        response = self._make_authenticated_request('/user-info')
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user info: {response.status_code} - {response.text}")
    
    def get_unread_articles(self, stream_id="user/-/state/com.google/reading-list", 
                           max_articles=None, include_read=False):
        """
        获取未读文章
        
        参数:
        - stream_id: 流ID，默认获取所有订阅的文章
        - max_articles: 最大文章数，None表示获取所有
        - include_read: 是否包含已读文章，默认False（只获取未读）
        
        常用stream_id:
        - "user/-/state/com.google/reading-list": 所有订阅文章
        - "feed/http://example.com/feed": 特定feed的文章
        - "user/-/label/文件夹名": 特定文件夹的文章
        """
        all_articles = []
        continuation = None
        
        while True:
            # 构建请求参数
            params = {
                'n': 100,  # 每次最多获取100篇
                'output': 'json'
            }
            
            # 如果不包含已读文章，添加排除参数
            if not include_read:
                params['xt'] = 'user/-/state/com.google/read'
            
            # 添加continuation参数用于分页
            if continuation:
                params['c'] = continuation
            
            # 对stream_id进行URL编码
            from urllib.parse import quote
            encoded_stream_id = quote(stream_id, safe='')
            
            # 发送请求
            endpoint = f'/stream/contents/{encoded_stream_id}'
            response = self._make_authenticated_request(endpoint, params=params)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get articles: {response.status_code} - {response.text}")
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
                
            all_articles.extend(items)
            
            # 检查是否达到最大文章数
            if max_articles and len(all_articles) >= max_articles:
                all_articles = all_articles[:max_articles]
                break
            
            # 检查是否有更多文章
            continuation = data.get('continuation')
            if not continuation:
                break
                
            print(f"已获取 {len(all_articles)} 篇文章，继续获取...")
        
        return {
            'total': len(all_articles),
            'articles': all_articles
        }
    
    def get_unread_count(self):
        """获取未读文章数量"""
        response = self._make_authenticated_request('/unread-count')
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get unread count: {response.status_code} - {response.text}")
    
    def mark_article_as_read(self, article_id):
        """标记文章为已读"""
        data = {
            'i': article_id,
            'a': 'user/-/state/com.google/read'
        }
        
        response = self._make_authenticated_request('/edit-tag', method='POST', data=data)
        
        if response.status_code == 200:
            return True
        else:
            raise Exception(f"Failed to mark article as read: {response.status_code} - {response.text}")
    
    def mark_articles_as_read(self, article_ids):
        """批量标记文章为已读"""
        if not article_ids:
            return True
            
        # 构建批量请求数据
        data = {
            'a': 'user/-/state/com.google/read'
        }
        
        # 添加多个文章ID
        for i, article_id in enumerate(article_ids):
            data[f'i'] = article_id if i == 0 else data['i'] + '&i=' + article_id
        
        response = self._make_authenticated_request('/edit-tag', method='POST', data=data)
        
        if response.status_code == 200:
            return True
        else:
            raise Exception(f"Failed to mark articles as read: {response.status_code} - {response.text}")

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            query_params = parse_qs(urlparse(self.path).query)
            auth_code = query_params.get('code', [None])[0]
            
            if auth_code:
                self.server.auth_code = auth_code
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>')
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Authorization failed!</h1></body></html>')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def authenticate_with_browser(client):
    """使用浏览器进行OAuth认证"""
    auth_url = client.get_auth_url()
    print(f"Opening browser for authentication...")
    print(f"If browser doesn't open automatically, visit: {auth_url}")
    
    server = HTTPServer(('localhost', 8080), CallbackHandler)
    server.auth_code = None
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    webbrowser.open(auth_url)
    
    print("Waiting for authorization...")
    timeout = 60
    start_time = time.time()
    
    while not server.auth_code and (time.time() - start_time) < timeout:
        time.sleep(1)
    
    server.shutdown()
    
    if server.auth_code:
        print("Authorization code received!")
        token_data = client.exchange_code_for_token(server.auth_code)
        print("Access token obtained successfully!")
        return token_data
    else:
        raise Exception("Authorization timeout or failed")