"""
NFC 处理模块
使用 pyjnius 访问 Android NFC API
"""
from kivy.utils import platform
import json

if platform == 'android':
    from jnius import autoclass, cast
    from android.runnable import run_on_ui_thread
    
    # Android 类
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    NfcAdapter = autoclass('android.nfc.NfcAdapter')
    PendingIntent = autoclass('android.app.PendingIntent')
    Intent = autoclass('android.content.Intent')
    NdefMessage = autoclass('android.nfc.NdefMessage')
    NdefRecord = autoclass('android.nfc.NdefRecord')
    WifiManager = autoclass('android.net.wifi.WifiManager')
    Context = autoclass('android.content.Context')

class NFCHandler:
    def __init__(self, callback):
        self.callback = callback
        self.nfc_adapter = None
        self.activity = None
        
        if platform == 'android':
            self.activity = PythonActivity.mActivity
            self.nfc_adapter = NfcAdapter.getDefaultAdapter(self.activity)
    
    @run_on_ui_thread
    def enable_nfc(self):
        """启用 NFC 前台调度"""
        if not self.nfc_adapter:
            print("设备不支持 NFC")
            return False
        
        if not self.nfc_adapter.isEnabled():
            print("请在设置中启用 NFC")
            return False
        
        # 创建 PendingIntent
        intent = Intent(self.activity, self.activity.getClass())
        intent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        
        pending_intent = PendingIntent.getActivity(
            self.activity, 0, intent, PendingIntent.FLAG_MUTABLE
        )
        
        # 启用前台调度
        self.nfc_adapter.enableForegroundDispatch(
            self.activity,
            pending_intent,
            None,
            None
        )
        
        # 设置 NDEF 消息（包含本机 IP 和端口）
        self.set_ndef_message()
        
        return True
    
    def set_ndef_message(self):
        """设置要通过 NFC 发送的消息（本机 IP 地址）"""
        local_ip = self.get_local_ip()
        
        # 创建包含 IP 和端口的 JSON 数据
        data = json.dumps({
            'ip': local_ip,
            'port': 8888,
            'type': 'file_transfer'
        })
        
        # 创建 NDEF 记录
        ndef_record = NdefRecord.createMime(
            'application/vnd.nfc.filetransfer',
            data.encode('utf-8')
        )
        
        ndef_message = NdefMessage([ndef_record])
        
        # 设置为默认的 NDEF 消息
        self.nfc_adapter.setNdefPushMessage(ndef_message, self.activity)
    
    def get_local_ip(self):
        """获取本机在 WiFi 网络中的 IP 地址"""
        if platform != 'android':
            return '127.0.0.1'
        
        wifi_manager = self.activity.getSystemService(Context.WIFI_SERVICE)
        wifi_info = wifi_manager.getConnectionInfo()
        ip_int = wifi_info.getIpAddress()
        
        # 将整数 IP 转换为字符串格式
        ip = "{}.{}.{}.{}".format(
            ip_int & 0xff,
            (ip_int >> 8) & 0xff,
            (ip_int >> 16) & 0xff,
            (ip_int >> 24) & 0xff
        )
        
        return ip
    
    def on_new_intent(self, intent):
        """处理新的 NFC Intent"""
        action = intent.getAction()
        
        if action == NfcAdapter.ACTION_NDEF_DISCOVERED:
            # 解析 NDEF 消息
            raw_msgs = intent.getParcelableArrayExtra(NfcAdapter.EXTRA_NDEF_MESSAGES)
            
            if raw_msgs:
                ndef_message = cast('android.nfc.NdefMessage', raw_msgs[0])
                records = ndef_message.getRecords()
                
                if records:
                    payload = records[0].getPayload()
                    data_str = bytes(payload).decode('utf-8')
                    
                    try:
                        peer_info = json.loads(data_str)
                        self.callback(peer_info)
                    except json.JSONDecodeError:
                        print("无法解析 NFC 数据")
    
    @run_on_ui_thread
    def disable_nfc(self):
        """禁用 NFC 前台调度"""
        if self.nfc_adapter:
            self.nfc_adapter.disableForegroundDispatch(self.activity)
