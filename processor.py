import os
import gc
import asyncio
import numpy as np
import torch
from torchvision import transforms
import ffmpeg
import shutil
import subprocess
import json
from PIL import Image
from model_service import device, birefnet, adjust_batch_size

# 初始化总帧数
total_frames = 0

# 用于存储任务，任务ID为键，进度为值
tasks = {}

# 创建一个锁对象
tasks_lock = asyncio.Lock()

# 设置上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
print('设置上传目录')

# 设置临时目录用于存储帧
TEMP_DIR = "temp_frames"
os.makedirs(TEMP_DIR, exist_ok=True)
print('设置临时目录')


target_size = (1024, 1024)
# target_size = (2048, 2048)
transform_image = transforms.Compose([
    transforms.Resize(target_size),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
print('设置图像处理')

def to_share(server_name='0.0.0.0', server_port=8080): 
    try:           
        from gradio import networking           
        import secrets       
    except ImportError as e:           
        missing_package = str(e).split("No module named ")[-1].replace("'", "")           
        print(f"创建分享链接时出错，缺少必要的包：{missing_package}. 请安装它后再试。使用命令：pip install {missing_package}")           
        return          
    share_token = secrets.token_urlsafe(32)  
    print(f'share_token: {share_token}')     
    try:           
        share_url = networking.setup_tunnel(server_name, server_port, share_token, None, None)           
        print("分享的链接为：", share_url)       
    except Exception as e:           
        print(f"创建分享链接时出错：{e}")         
        return

# 定义一个函数，根据文件类型和MD5值返回文件路径
def backfilepath(filetype, filemd5):
    switcher = {
        "video": f"{UPLOAD_DIR}/source_{filemd5}.mp4",
        "image": f"{UPLOAD_DIR}/image_{filemd5}.png",
        "background_video": f"{UPLOAD_DIR}/bgvideo_{filemd5}.mp4"
    }
    return switcher.get(filetype, None)

# 获取视频信息
def get_video_info(video_path):
    print(f"获取视频信息: {video_path}")
    
    # 使用subprocess调用ffprobe来获取视频信息
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        probe = json.loads(result.stdout)
        
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        if video_stream is None:
            raise Exception("无法找到视频流")
        
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        
        # 获取帧率
        fps_parts = video_stream.get('r_frame_rate', '30/1').split('/')
        fps = int(fps_parts[0]) / int(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])
        
        # 获取总帧数
        total_frames = int(video_stream.get('nb_frames', 0))
        if total_frames == 0:
            # 如果无法直接获取帧数，则根据时长和帧率计算
            duration = float(video_stream.get('duration', 0))
            total_frames = int(duration * fps)
        
        return width, height, fps, total_frames
    
    except Exception as e:
        print(f"获取视频信息时出错: {e}")
        raise

# 提取视频帧到临时目录
def extract_frames(video_path, output_dir, task_id):
    print(f"提取视频帧: {video_path} 到 {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 使用subprocess直接调用ffmpeg命令
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            f"{output_dir}/frame_%06d.png"
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"成功提取视频帧到 {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取视频帧时出错: {e}")
        return False
    except Exception as e:
        print(f"提取视频帧时出错: {str(e)}")
        return False

# 提取背景视频帧
def extract_bg_frames(video_path, output_dir, width, height, task_id):
    print(f"提取背景视频帧: {video_path} 到 {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'scale={width}:{height}',
            f"{output_dir}/bg_frame_%06d.png"
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"成功提取背景视频帧到 {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"提取背景视频帧时出错: {e}")
        return False
    except Exception as e:
        print(f"提取背景视频帧时出错: {str(e)}")
        return False

# 创建纯色背景帧
def create_color_bg(color, width, height, output_path):
    # 创建纯色图像
    color_rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    img = Image.new('RGB', (width, height), color_rgb)
    img.save(output_path)
    return output_path

# 调整背景图像大小
def resize_bg_image(image_path, width, height, output_path):
    try:
        cmd = [
            'ffmpeg',
            '-i', image_path,
            '-vf', f'scale={width}:{height}',
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"调整背景图像大小时出错: {e}")
        return None
    except Exception as e:
        print(f"调整背景图像大小时出错: {str(e)}")
        return None


async def process_batch(frame_paths, bg_paths, bg_img, output_dir, task_id):
    """优化后的批次处理函数"""
    try:        
        # 批量预处理函数
        def preprocess_frame(frame_path):
            try:
                with Image.open(frame_path) as img:
                        image = Image.open(frame_path)
                        return transform_image(image).unsqueeze(0).to(device).half()
            except Exception as e:
                print(f"预处理失败 {frame_path}: {e}")
                return None

        # 批量加载和预处理
        batch_tensors = []
        valid_indices = []
        
        for i, path in enumerate(frame_paths):
            tensor = preprocess_frame(path)
            if tensor is not None:
                batch_tensors.append(tensor)
                valid_indices.append(i)
                
        if not batch_tensors:
            print("警告: 空批次")
            return

        # 内存优化配置
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        masks = []
        # 模型推理
        with torch.inference_mode(), torch.autocast(device_type=device):
            try:
                for i, tensor in enumerate(batch_tensors):
                    outputs = birefnet(tensor)[-1].sigmoid().cpu()
                    mask = outputs[0].squeeze()
                    masks.append(mask)
            except Exception as e:
                print(f"推理错误: {e}")
                return

        # 及时释放内存
        del outputs, batch_tensors
        if device == "cuda":
            torch.cuda.empty_cache()

        # 背景预处理
        bg_cache = {}
        def get_background(bg_path):
            if bg_path not in bg_cache:
                bg = Image.open(bg_path).convert("RGB")
                bg_cache[bg_path] = bg
            return bg_cache[bg_path]

        # 并行处理优化
        for idx, (i, mask) in enumerate(zip(valid_indices, masks)):
            if idx >= len(masks):
                break
                
            frame_path = frame_paths[i]
            bg_path = bg_img if bg_img else bg_paths[i]
            
            try:
                # 加载数据
                with Image.open(frame_path) as frame:
                    bg = get_background(bg_path).resize(frame.size, Image.LANCZOS)
                    
                    # 生成掩膜
                    mask_pil = Image.fromarray((mask.squeeze().numpy() * 255).astype(np.uint8))
                    mask_pil = mask_pil.resize(frame.size, Image.LANCZOS)
                    
                    # 优化合成计算
                    composite = Image.composite(
                        frame.convert("RGBA"),
                        bg.convert("RGBA"),
                        mask_pil
                    ).convert("RGB")
                    
                    # 保存结果
                    output_path = os.path.join(output_dir, os.path.basename(frame_path))
                    composite.save(output_path, quality=95, subsampling=0)

                # 进度更新
                path_str = os.path.basename(output_path).split('_')[-1]
                frame_num = int(os.path.splitext(path_str)[0])
                await update_progress(task_id, frame_num)
                
            except Exception as e:
                print(f"合成失败 {frame_path}: {e}")
                continue

        # 清理缓存
        del masks, bg_cache, valid_indices
        gc.collect()

    except Exception as e:
        print(f"批次处理异常: {e}")


# 将处理后的帧合成为视频
def frames_to_video(frames_dir, output_path, fps):
    try:
        print(f"将帧合成为视频: {frames_dir} -> {output_path}")
        
        # 首先检查输入目录中是否有帧
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("frame_") and f.endswith(".png")])
        if not frame_files:
            raise Exception("没有找到要处理的帧文件")
        print(f"找到 {len(frame_files)} 个帧文件")
        
        # 检查第一帧是否存在并可以打开
        first_frame = os.path.join(frames_dir, frame_files[0])
        if not os.path.exists(first_frame):
            raise Exception(f"找不到第一帧: {first_frame}")
        
        # 首先检查可用的编码器
        try:
            # 尝试获取可用的编码器列表
            encoders_cmd = ['ffmpeg', '-encoders']
            encoders_process = subprocess.Popen(
                encoders_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            encoders_stdout, _ = encoders_process.communicate()
            
            # 检查是否有常用的视频编码器
            encoders = encoders_stdout.lower()
            if 'libx264' in encoders:
                video_codec = 'libx264'
            elif 'h264' in encoders:
                video_codec = 'h264'
            elif 'mpeg4' in encoders:
                video_codec = 'mpeg4'
            elif 'mjpeg' in encoders:
                video_codec = 'mjpeg'
            else:
                # 如果没有找到常用编码器，使用默认编码器
                video_codec = 'mpeg4'
                
            print(f"使用视频编码器: {video_codec}")
            
        except Exception as e:
            print(f"检查编码器时出错: {e}")
            # 默认使用 mpeg4 编码器
            video_codec = 'mpeg4'
            
        cmd = [
            'ffmpeg',
            '-framerate', str(fps),
            '-i', f"{frames_dir}/frame_%06d.png",
            '-c:v', video_codec,
            '-pix_fmt', 'yuv420p',
            '-y',
            output_path
        ]
        
        # 使用subprocess.Popen获取详细的错误输出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print("FFmpeg 错误输出:")
            print(stderr)
            
            # 如果第一次尝试失败，尝试使用更基本的编码器和设置
            print("尝试使用备用编码设置...")
            backup_cmd = [
                'ffmpeg',
                '-framerate', str(fps),
                '-i', f"{frames_dir}/frame_%06d.png",
                '-vcodec', 'mjpeg',  # 尝试使用 mjpeg 编码器
                '-q:v', '3',         # 质量设置
                '-y',
                output_path
            ]
            
            backup_process = subprocess.Popen(
                backup_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            backup_stdout, backup_stderr = backup_process.communicate()
            
            if backup_process.returncode != 0:
                print("备用 FFmpeg 错误输出:")
                print(backup_stderr)
                raise Exception(f"FFmpeg 命令失败，返回码: {backup_process.returncode}\n错误信息: {backup_stderr}")
            
        print(f"成功将帧合成为视频: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"将帧合成为视频时出错: {e}")
        if hasattr(e, 'stderr'):
            print(f"FFmpeg 错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"将帧合成为视频时出错: {str(e)}")
        return False

# 处理帧批次的异步函数
async def process_frames_batch(rank, frames_dir, bg_dir, bg_img, output_dir, task_id, start_idx, end_idx):
    print(f"[{rank}] 处理帧批次: {start_idx}-{end_idx}")
    
    # 获取指定范围内的帧
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("frame_")])
    bg_files = sorted([f for f in os.listdir(bg_dir) if f.startswith("bg_")])
    
    # 确保索引在有效范围内
    start_idx = max(0, start_idx)
    end_idx = min(len(frame_files), end_idx)
    
    # 动态调整批处理大小
    batch_size = adjust_batch_size()
    # batch_size = 1
    print(f"[{rank}] 批处理大小: {batch_size}")
    
    # 按批次处理帧
    for i in range(start_idx, end_idx, batch_size):
        batch_end = min(i + batch_size, end_idx)
        frame_paths = [os.path.join(frames_dir, frame_files[j]) for j in range(i, batch_end)]
        bg_paths = []
        if bg_img is None: # 没有背景图像，就使用背景视频
            bg_paths = [os.path.join(bg_dir, bg_files[j]) for j in range(i, batch_end)]
        # bg_paths = [os.path.join(bg_dir, bg_files[j]) for j in range(i, batch_end)]
        
        await process_batch(frame_paths, bg_paths, bg_img, output_dir, task_id)
        # 每处理一批后让出控制权，让其他任务有机会执行
        await asyncio.sleep(0.001) 
        # 每处理8批进行一次垃圾回收
        if (i - start_idx) % (8 * batch_size) == 0:
            gc.collect()
            if device == "cuda":
                torch.cuda.empty_cache()
            # 出让CPU资源
            # await asyncio.sleep(0)
    
    print(f"[{rank}] 处理批次完成: {start_idx}-{end_idx}")
    return True

# 更新进度的函数
async def update_progress(task_id, frame_index):
    """
    更新任务进度
    :param task_id: 任务ID
    :param frame_index: 当前处理的帧索引
    """
    # print(f"更新进度: {frame_index}/{total_frames}")

    async with tasks_lock:
        # 计算进度百分比
        print(f"更新进度: {frame_index}/{total_frames}")
        progress = min(99, int((frame_index + 1) / total_frames * 100))
        tasks[task_id].update({"progress": progress, "message": f"处理中 {progress}%"})



# 处理视频函数
async def process_video(task_id):
    try:
        input_video_path = tasks[task_id]["input_path"] 
        output_video_path = f"{UPLOAD_DIR}/processed_{task_id}.mp4"
        
        # 创建任务特定的临时目录
        task_temp_dir = os.path.join(TEMP_DIR, task_id)
        frames_dir = os.path.join(task_temp_dir, "frames")
        bg_dir = os.path.join(task_temp_dir, "backgrounds")
        output_dir = os.path.join(task_temp_dir, "output")
        
        # 创建必要的目录
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(bg_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取视频信息
        width, height, fps, frame_count = get_video_info(input_video_path)
        global total_frames
        total_frames = frame_count
        
        print(f"视频信息: 宽={width}, 高={height}, 帧率={fps}, 总帧数={total_frames}")
        
        # 提取视频帧
        if not extract_frames(input_video_path, frames_dir, task_id):
            raise Exception("提取视频帧失败")
        
        # 准备背景
        background_color = tasks[task_id]["background_color"]
        background_image_path = tasks[task_id]["background_image"]
        background_video_path = tasks[task_id]["background_video"]

        bg_img = None
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("frame_")])

        if background_color:
            # 创建纯色背景
            color_bg_path = os.path.join(bg_dir, "color_bg.png")
            create_color_bg(background_color, width, height, color_bg_path)
            bg_img = color_bg_path

        elif background_image_path:
            # 调整背景图像大小
            bg_resized_path = os.path.join(bg_dir, "bg_resized.png")
            if not resize_bg_image(background_image_path, width, height, bg_resized_path):
                raise Exception("调整背景图像大小失败")
            bg_img = bg_resized_path

        elif background_video_path:
            # 提取背景视频帧
            if not extract_bg_frames(background_video_path, bg_dir, width, height, task_id):
                raise Exception("提取背景视频帧失败")
            
            # 确保背景帧数量与原视频帧数量匹配
            bg_files = sorted([f for f in os.listdir(bg_dir) if f.startswith("bg_")])
            
            
            # 如果背景帧数量不足，循环使用
            if len(bg_files) < len(frame_files):
                for i in range(len(bg_files), len(frame_files)):
                    src_idx = i % len(bg_files)
                    os.symlink(
                        os.path.join(bg_dir, bg_files[src_idx]),
                        os.path.join(bg_dir, f"bg_{i+1:06d}.png")
                    )
        
        # 计算每个任务处理的帧范围
        # num_tasks = min(os.cpu_count()-2, 8)  # 限制最大任务数
        num_tasks = 1
        frames_per_task = len(frame_files) // num_tasks
        print(f"使用 {num_tasks} 个异步任务处理视频，每个任务处理 {frames_per_task} 帧")
        
        # 创建并启动处理任务
        process_tasks = []
        for i in range(num_tasks):
            start_idx = i * frames_per_task
            end_idx = (i + 1) * frames_per_task if i < num_tasks - 1 else len(frame_files)
            task = asyncio.create_task(
                process_frames_batch(i, frames_dir, bg_dir, bg_img, output_dir, task_id, start_idx, end_idx)
            )
            process_tasks.append(task)
        
        # 等待所有处理任务完成
        await asyncio.gather(*process_tasks)
        
        # 将处理后的帧合成为视频
        if not frames_to_video(output_dir, output_video_path, fps):
            raise Exception("将帧合成为视频失败")
        
        print(f"任务 {task_id} 完成")
        # 更新任务状态
        tasks[task_id].update({
            "status": "completed", 
            "message": "处理完成", 
            "progress": 100
        })
        
    except Exception as e:
        print(f"处理视频时出错: {e}")
        tasks[task_id].update({
            "status": "failed", 
            "message": f"处理失败: {str(e)}", 
            "progress": 0
        })
    finally:
        try:
            cleanup_resources()
        except Exception as e:
            print(f"清理临时文件时出错: {e}")

async def process_image(task_id):
    try:
        background_color = tasks[task_id]["background_color"]
        background_image_id = tasks[task_id]["background_image_id"]

        image_id = tasks[task_id]["image_id"]
        image_path = f"{UPLOAD_DIR}/image_{image_id}.png"
        output_path = f"{UPLOAD_DIR}/processed_{task_id}.png"

        with Image.open(image_path) as image:
            width, height = image.size
            
            # 确保使用正确的数据类型
            input_image = transform_image(image).unsqueeze(0).to(device)
            
            # 使用与模型相同的精度模式
            with torch.inference_mode(), torch.autocast(device_type=device):
                preds = birefnet(input_image)[-1].sigmoid().cpu()

            mask = preds[0].squeeze()
            pred_pil = Image.fromarray((mask.numpy() * 255).astype(np.uint8))
            pred_pil = pred_pil.resize(image.size, Image.LANCZOS)

            # 创建背景图
            backimage = None
            if background_color:
                color_rgb = tuple(int(background_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                backimage = Image.new('RGB', image.size, color_rgb)
            elif background_image_id:
                background_image_path = backfilepath("image", background_image_id)
                if not os.path.exists(background_image_path):
                    raise Exception("背景图像不存在")
                with Image.open(background_image_path) as bg:
                    backimage = bg.resize(image.size, Image.LANCZOS)

            # 合成图像
            if backimage:
                composite = Image.composite(
                    image.convert("RGBA"),
                    backimage.convert("RGBA"),
                    pred_pil
                )#.convert("RGB")
            else:
                # 如果没有背景，只返回透明的图像
                composite = Image.composite(
                    image.convert("RGBA"),
                    Image.new('RGBA', image.size, (0, 0, 0, 0)),
                    pred_pil
                )#.convert("RGB")
                
            # 保存结果
            composite.save(output_path, quality=95, subsampling=0)

        print(f"任务 {task_id} 完成")
        tasks[task_id].update({
            "status": "completed",
            "message": "处理完成",
            "progress": 100
        })
    except Exception as e:
        print(f"处理图片时出错: {e}")
        tasks[task_id].update({
            "status": "failed",
            "message": f"处理失败: {str(e)}",
            "progress": 0
        })
        
# 清理资源的函数
def cleanup_resources():
    gc.collect()
    # 清理GPU内存
    if device == "cuda":
        torch.cuda.empty_cache()
    # 清理临时目录
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

        
