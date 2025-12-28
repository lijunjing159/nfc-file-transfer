"""
文件传输模块
通过 Socket 在 WiFi 网络中传输文件
"""
import socket
import os
import json
import struct
from pathlib import Path
from kivy.utils import platform

if platform == 'android':
    from android.storage import primary_external_storage_path
    from android.permissions import request_permissions, Permission
    
    # 请求必要的权限
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.INTERNET,
        Permission.ACCESS_WIFI_STATE,
        Permission.NFC
    ])

class FileTransferServer:
    """文件接收服务器"""
    
    def __init__(self, port=8888):
        self.port = port
        self.socket = None
        self.save_path = self.get_save_path()
        
    def get_save_path(self):
        """获取保存路径（相册目录）"""
        if platform == 'android':
            base_path = primary_external_storage_path()
            save_path = os.path.join(base_path, 'DCIM', 'ReceivedFiles')
        else:
            save_path = os.path.join(os.path.expanduser('~'), 'Pictures', 'ReceivedFiles')
        
        os.makedirs(save_path, exist_ok=True)
        return save_path
    
    def start(self):
        """启动服务器"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.listen(1)
        print(f"服务器启动，监听端口 {self.port}")
    
    def receive_files(self):
        """接收文件"""
        try:
            conn, addr = self.socket.accept()
            print(f"连接来自: {addr}")
            
            file_count = 0
            
            while True:
                # 接收文件元数据长度
                meta_len_data = self.recv_exact(conn, 4)
                if not meta_len_data:
                    break
                
                meta_len = struct.unpack('!I', meta_len_data)[0]
                
                # 接收文件元数据
                meta_data = self.recv_exact(conn, meta_len)
                metadata = json.loads(meta_data.decode('utf-8'))
                
                if metadata.get('type') == 'END':
                    break
                
                filename = metadata['filename']
                filesize = metadata['size']
                
                print(f"接收文件: {filename} ({filesize} 字节)")
                
                # 接收文件内容
                filepath = os.path.join(self.save_path, filename)
                with open(filepath, 'wb') as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        chunk = self.recv_exact(conn, chunk_size)
                        if not chunk:
                            raise Exception("连接中断")
                        f.write(chunk)
                        remaining -= len(chunk)
                
                file_count += 1
                print(f"文件保存到: {filepath}")
            
            conn.close()
            self.socket.close()
            
            return {'success': True, 'count': file_count}
            
        except Exception as e:
            print(f"接收错误: {e}")
            return {'success': False, 'error': str(e)}
    
    def recv_exact(self, conn, size):
        """精确接收指定字节数"""
        data = b''
        while len(data) < size:
            chunk = conn.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data


class FileTransferClient:
    """文件发送客户端"""
    
    def __init__(self, host, port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.media_path = self.get_media_path()
    
    def get_media_path(self):
        """获取相册路径"""
        if platform == 'android':
            base_path = primary_external_storage_path()
            return os.path.join(base_path, 'DCIM', 'Camera')
        else:
            return os.path.join(os.path.expanduser('~'), 'Pictures')
    
    def connect(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"已连接到 {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def send_media_files(self):
        """发送相册中的图片和视频"""
        try:
            if not os.path.exists(self.media_path):
                return {'success': False, 'error': '相册路径不存在'}
            
            # 获取所有图片和视频文件
            media_files = []
            extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mov', '.avi', '.mkv'}
            
            for root, dirs, files in os.walk(self.media_path):
                for file in files:
                    if Path(file).suffix.lower() in extensions:
                        media_files.append(os.path.join(root, file))
            
            if not media_files:
                return {'success': False, 'error': '没有找到媒体文件'}
            
            print(f"找到 {len(media_files)} 个媒体文件")
            
            # 发送每个文件
            for filepath in media_files:
                self.send_file(filepath)
            
            # 发送结束标记
            self.send_end_marker()
            
            self.socket.close()
            
            return {'success': True, 'total': len(media_files)}
            
        except Exception as e:
            print(f"发送错误: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_file(self, filepath):
        """发送单个文件"""
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        
        # 准备元数据
        metadata = {
            'filename': filename,
            'size': filesize,
            'type': 'FILE'
        }
        
        meta_data = json.dumps(metadata).encode('utf-8')
        meta_len = struct.pack('!I', len(meta_data))
        
        # 发送元数据
        self.socket.sendall(meta_len)
        self.socket.sendall(meta_data)
        
        # 发送文件内容
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                self.socket.sendall(chunk)
        
        print(f"已发送: {filename}")
    
    def send_end_marker(self):
        """发送结束标记"""
        metadata = {'type': 'END'}
        meta_data = json.dumps(metadata).encode('utf-8')
        meta_len = struct.pack('!I', len(meta_data))
        
        self.socket.sendall(meta_len)
        self.socket.sendall(meta_data)
