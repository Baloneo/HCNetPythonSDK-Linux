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
