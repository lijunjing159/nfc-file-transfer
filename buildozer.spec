[app]
title = NFC File Transfer
package.name = nfcfiletransfer
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

# Android 权限
android.permissions = INTERNET,NFC,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,ACCESS_WIFI_STATE

# Android API 级别
android.api = 31
android.minapi = 21
android.ndk = 25b

# 启用 Android Beam / NFC
android.add_features = android.hardware.nfc

[buildozer]
log_level = 2
warn_on_root = 1
