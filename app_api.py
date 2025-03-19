import asyncio
import uuid
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com/'
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import uvicorn


# 导入处理视频函数
from processor import tasks, tasks_lock, process_video, cleanup_resources, UPLOAD_DIR, to_share, backfilepath, process_image

# 设置端口号
port = 8081

# 创建FastAPI应用实例
app = FastAPI(
    title="背景视频处理 API",
    description="一个用于处理视频背景的 API 服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 设置静态文件目录
app.mount("/static", StaticFiles(directory="./static"), name="static")

# 设置模板目录
templates = Jinja2Templates(directory="./templates")

@app.get("/api/query_file/{file_type}/{file_md5}",
    summary="文件存在性查询接口",
    tags=["文件管理"])
async def query_file(file_type: str, file_md5: str):
    print(f'query file {file_type} {file_md5}')
    # 检查文件是否存在
    file_path = backfilepath(file_type, file_md5)
    if os.path.exists(file_path):
        return {"file_id": file_md5}
    else:
        return {"file_id": None}

@app.post("/api/upload-file",
    summary="统一文件上传接口",
    tags=["文件管理"])
async def upload_file(
    file: UploadFile = File(..., description="上传文件"),
    file_type: str = Form(..., description="文件类型（video/image/background_video）"),
    file_md5: str = Form(..., description="文件MD5校验值")
):
    file_path = backfilepath(file_type, file_md5)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"file_id": file_md5}

@app.post("/api/submit-task",
    summary="提交处理任务",
    tags=["任务管理"])
async def submit_task(
    background_tasks: BackgroundTasks,
    video_id: str = Form(..., description="通过/upload-video获取的视频ID"),
    background_color: Optional[str] = Form(None),
    background_image_id: Optional[str] = Form(None),
    background_video_id: Optional[str] = Form(None)
):
    task_id = str(uuid.uuid4())
    input_path = f"{UPLOAD_DIR}/source_{video_id}.mp4"
    if not os.path.exists(input_path):
        raise HTTPException(404, "video_id 视频文件不存在")

    if background_color is None and background_image_id is None and background_video_id is None:
        raise HTTPException(400, "至少需要提供一个背景参数")
    
    backimage_path = None
    if background_image_id is not None:
        backimage_path = f"{UPLOAD_DIR}/image_{background_image_id}.png"
    
    backvideo_path = None
    if background_video_id is not None:
        backvideo_path = f"{UPLOAD_DIR}/bgvideo_{background_video_id}.mp4"

    # 初始化任务信息
    tasks[task_id] = {
        "input_path": input_path,
        "background_color": background_color,
        "background_image": backimage_path,
        "background_video": backvideo_path,
        "status": "pending",
        "message": "开始处理",
        "progress": 0
    }
    # 启动后台任务
    background_tasks.add_task(process_video, task_id)
    return {"task_id": task_id, "message": "视频上传成功，开始处理"}

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """
    获取任务进度的接口
    :param task_id: 任务ID
    """
    async with tasks_lock:
    # 如果任务ID不存在，抛出HTTP异常
        if task_id not in tasks:
            raise HTTPException(status_code=404, detail="任务ID不存在")
        return tasks[task_id]

@app.get("/api/donwload_img/{task_id}")
async def download_img(task_id: str):
    output_img_path = f"{UPLOAD_DIR}/processed_{task_id}.png"
    if not os.path.exists(output_img_path):
        raise HTTPException(status_code=404, detail="处理后的图片不存在，可能任务尚未完成")
    return FileResponse(
        output_img_path,
        media_type="image/png",
        filename=f"processed_{task_id}.png",
        headers={
            "Accept-Ranges": "bytes",
            "cache-control": "public, max-age=536000",
        }
    )

@app.get("/api/download/{task_id}")
async def download_video(task_id: str):
    """
    下载处理后视频的接口
    :param task_id: 任务ID
    """
    # 生成处理后视频的路径
    output_video_path=f"{UPLOAD_DIR}/processed_{task_id}.mp4"
    # 如果处理后的视频不存在，抛出HTTP异常
    if not os.path.exists(output_video_path):
        raise HTTPException(status_code=404, detail="处理后的视频不存在，可能任务尚未完成")
    return FileResponse(
        output_video_path,
        media_type="video/mp4",
        filename=f"processed_{task_id}.mp4",
        headers={
            "Accept-Ranges": "bytes",
            "cache-control": "public, max-age=536000",
        }
    )

@app.post("/api/submit_image",
    summary="提交图片移除背景任务",
    tags=["任务管理"])
async def submit_image(
    background_tasks: BackgroundTasks,
    image_id:str = Form(..., description="通过上传接口返回的图片ID") ,
    background_color:Optional[str] = Form(None, description="背景色值#00FF00"),
    background_image_id:Optional[str] = Form(None, description="背景图")
):
    if image_id is None:
        raise HTTPException(status_code=400, detail="image_id is None")
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "image_id": image_id,
        "background_color":background_color,
        "background_image_id":background_image_id,
        "status": "pending",
        "message": "开始处理",
        "progress": 0
    }
    background_tasks.add_task(process_image, task_id)
    return {"task_id": task_id, "message": "图片上传成功，开始处理"}


@app.get("/")
async def root():
    # 处理根路径的请求,返回index.html
    return FileResponse("./templates/video.html")
    # return {"message": "Hello World"}

# 添加一个通用的静态文件处理路由
@app.get("/assets/{file_path:path}")
async def serve_assets(file_path: str):
    """
    提供静态资源文件的接口
    :param file_path: 资源文件路径
    """
    
    assets_dir = "/workspace/assets"
    file_location = f"{assets_dir}/{file_path}"
    
    if not os.path.exists(file_location):
        raise HTTPException(status_code=404, detail="资源文件不存在")
    
    # 根据文件扩展名设置正确的媒体类型
    media_types = {
        ".css": "text/css",
        ".js": "application/javascript",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
    }
    
    file_ext = os.path.splitext(file_path)[1].lower()
    media_type = media_types.get(file_ext, "application/octet-stream")
    
    return FileResponse(
        file_location,
        media_type=media_type,
        headers={
            "cache-control": "public, max-age=86400",  # 缓存一天
        }
    )

@app.get("/favicon.ico")
async def favicon():
    return {"message": "favicon"}

if __name__ == "__main__":
    try:
        to_share('0.0.0.0', port)
        uvicorn.run(app, host="0.0.0.0", port=port)
    finally:
        print("程序结束，清理资源")
        cleanup_resources()