# 设置环境变量以避免内存碎片
import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com/'

import torch
from transformers import AutoModelForImageSegmentation

# 设置计算精度
torch.set_float32_matmul_precision(['high', 'highest'][0])
print('设置精度高')

# 检查是否有可用的GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f'检查是否有可用的GPU: {device}')

# 加载模型
# local_path = "./data"
# birefnet = AutoModelForImageSegmentation.from_pretrained("ZhengPeng7/BiRefNet", trust_remote_code=True, cache_dir=local_path)
# birefnet.to(device)
# birefnet.eval()
# print('加载模型')


local_path = "./data"
birefnet = AutoModelForImageSegmentation.from_pretrained("ZhengPeng7/BiRefNet_HR", trust_remote_code=True, cache_dir=local_path)
birefnet.to(device)
birefnet.eval()
print('加载模型')

# local_path = "./data"
# birefnet = AutoModelForImageSegmentation.from_pretrained("briaai/RMBG-2.0", trust_remote_code=True, cache_dir=local_path)
# birefnet.to(device)
# birefnet.eval()
# print('加载模型')

# 动态调整批处理大小
def adjust_batch_size():
    if device == "cuda":
        total_memory = torch.cuda.get_device_properties(0).total_memory
        reserved_memory = torch.cuda.memory_reserved()
        available_memory = total_memory - reserved_memory
        # 根据实际测量值动态调整（测试测得每帧约150MB）
        batch_size_gpu = max(1, min(8, int(available_memory / (1024 ** 2 * 150))))
        return batch_size_gpu
    else:
        return 2  # CPU模式下保持较小的批处理大小