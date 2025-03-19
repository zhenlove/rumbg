# 创建虚拟环境
```bash
conda create --name rbgm python=3.11
```
# 激活环境
```bash
conda activate rbgm
```
# 安装需要的库
```bash
pip install -r requirements.txt
```
# 安装ffmpeg
```bash
apt install ffmpeg
# 安装完重启电脑
```

# 删除虚拟环境
```bash
conda remove --name rbgm --all
```

# 退出虚拟环境
```bash
conda deactivate
```

# gradio安装
```bash
# 下载
wget -O frpc_linux_amd64_v0.3 https://cdn-media.hf-mirror.com/frpc-gradio-0.3/frpc_linux_amd64
# 移动文件到指定路径
mv frpc_linux_amd64_v0.3 /root/miniforge3/envs/rbgm/lib/python3.11/site-packages/gradio
# 设置文件执行权限
chmod +x ..../frpc_linux_amd64_v0.3
```
