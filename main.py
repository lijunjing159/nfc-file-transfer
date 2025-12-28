"""
NFC 触发的文件传输应用 - 主程序
支持通过 NFC 触发，在同一 WiFi 网络下传输图片和视频
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform
import threading
import json

from file_transfer import FileTransferServer, FileTransferClient
from nfc_handler import NFCHandler

class NFCFileTransferApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server = None
        self.client = None
        self.nfc_handler = None
        self.is_sender = False
        
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.status_label = Label(
            text='等待 NFC 触发...',
            size_hint=(1, 0.3),
            font_size='20sp'
        )
        
        self.info_label = Label(
            text='请将两台手机背靠背靠近',
            size_hint=(1, 0.2),
            font_size='16sp'
        )
        
        self.sender_btn = Button(
            text='设为发送方',
            size_hint=(1, 0.15),
            on_press=self.set_as_sender
        )
        
        self.receiver_btn = Button(
            text='设为接收方',
            size_hint=(1, 0.15),
            on_press=self.set_as_receiver
        )
        
        self.start_btn = Button(
            text='启动 NFC 监听',
            size_hint=(1, 0.2),
            on_press=self.start_nfc
        )
        
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.info_label)
        self.layout.add_widget(self.sender_btn)
        self.layout.add_widget(self.receiver_btn)
        self.layout.add_widget(self.start_btn)
        
        return self.layout
    
    def set_as_sender(self, instance):
        self.is_sender = True
        self.update_status('已设置为发送方')
        self.info_label.text = '将发送相册文件到对方手机'
        
    def set_as_receiver(self, instance):
        self.is_sender = False
        self.update_status('已设置为接收方')
        self.info_label.text = '将接收对方的相册文件'
        
    def start_nfc(self, instance):
        if platform == 'android':
            self.nfc_handler = NFCHandler(self.on_nfc_detected)
            self.nfc_handler.enable_nfc()
            self.update_status('NFC 已启动，等待触发...')
        else:
            self.update_status('此功能仅支持 Android 设备')
    
    def on_nfc_detected(self, peer_info):
        """NFC 检测到对方设备时的回调"""
        self.update_status('检测到 NFC 设备！')
        
        peer_ip = peer_info.get('ip')
        peer_port = peer_info.get('port', 8888)
        
        if self.is_sender:
            # 作为发送方，启动客户端传输文件
            threading.Thread(
                target=self.send_files,
                args=(peer_ip, peer_port),
                daemon=True
            ).start()
        else:
            # 作为接收方，启动服务器等待接收
            threading.Thread(
                target=self.receive_files,
                daemon=True
            ).start()
    
    def send_files(self, peer_ip, peer_port):
        """发送文件到对方"""
        Clock.schedule_once(lambda dt: self.update_status('正在连接...'), 0)
        
        self.client = FileTransferClient(peer_ip, peer_port)
        success = self.client.connect()
        
        if success:
            Clock.schedule_once(lambda dt: self.update_status('正在发送文件...'), 0)
            result = self.client.send_media_files()
            
            if result['success']:
                msg = f"发送完成！共 {result['total']} 个文件"
                Clock.schedule_once(lambda dt: self.update_status(msg), 0)
            else:
                Clock.schedule_once(
                    lambda dt: self.update_status(f"发送失败: {result['error']}"),
                    0
                )
        else:
            Clock.schedule_once(lambda dt: self.update_status('连接失败'), 0)
    
    def receive_files(self):
        """接收对方的文件"""
        Clock.schedule_once(lambda dt: self.update_status('等待接收文件...'), 0)
        
        self.server = FileTransferServer(port=8888)
        self.server.start()
        
        result = self.server.receive_files()
        
        if result['success']:
            msg = f"接收完成！共 {result['count']} 个文件"
            Clock.schedule_once(lambda dt: self.update_status(msg), 0)
        else:
            Clock.schedule_once(
                lambda dt: self.update_status(f"接收失败: {result['error']}"),
                0
            )
    
    def update_status(self, message):
        """更新状态显示"""
        self.status_label.text = message
    
    def on_pause(self):
        return True
    
    def on_resume(self):
        pass

if __name__ == '__main__':
    NFCFileTransferApp().run()
