# AutodlGPU-
定时监控是否有空闲GPU。若有则autodl小程序向绑定微信发送信息
#
1.在py文件中配置账号，密码，token(autodl-我的-设置-开发者token。token用于发送微信信息)
#
2，配置时间，单位为秒，每次间隔时间到则查看空闲GPU
#
3.安装所有依赖 pip install requests hashlib logging time
