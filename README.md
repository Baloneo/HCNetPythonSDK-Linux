# 海康威视Python封装

## Usage
将此代码复制或安装到你的项目即可

## Example
```
 
import random
from hikvision.hikvision import HIKVisionSDK

LIB_DIR = '/home/baloneo/PythonProject/HCNetPythonSDK-Linux/hklib'

sdk = HIKVisionSDK(lib_dir=LIB_DIR,
                   username='admin',
                   ip='192.168.1.124',
                   password='Admin12345')
try:
    sdk.init()
except Exception as e:
    print(e)
    print('Errcode ', sdk.err_code)
else:
    ok = sdk.take_picture('/tmp/jjjj.jpg', release_resources=False)
    print('ok1', ok)
    ok = sdk.take_picture('/tmp/jjjj3.jpg', release_resources=False)
    print('ok2', ok)
    value = sdk.get_zoom(release_resources=False)
    print('zoom value', value)
    ok = sdk.set_zoom(zoom=10, release_resources=True)
    print('zoom ok', ok)


print(sdk.get_infrared_value())
```

## Changelog
* 2019-12-20 开始封装
* 2019-12-20 修复使用logging模块会出现段错误的bug
* 2019-12-21 修复打印的错误

## Bugs
* 如果不在和`setup.py`同级目录执行`install`会失败
* 使用python的logging模块可能会出现bug
* libiconv.so.2 链接的时候可能会失败 删掉即可

