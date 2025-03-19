// 使用当前浏览器地址作为 BASE_URL
const BASE_URL = window.location.origin;

// 处理类型切换
document.addEventListener('DOMContentLoaded', function() {
    // 处理类型切换
    const videoProcessing = document.getElementById('videoProcessing');
    const imageProcessing = document.getElementById('imageProcessing');
    const videoSection = document.getElementById('videoProcessingSection');
    const imageSection = document.getElementById('imageProcessingSection');

    videoProcessing.addEventListener('change', function() {
        if (this.checked) {
            videoSection.style.display = 'block';
            imageSection.style.display = 'none';
        }
    });

    imageProcessing.addEventListener('change', function() {
        if (this.checked) {
            videoSection.style.display = 'none';
            imageSection.style.display = 'block';
        }
    });

    // 图片预览功能
    const imageFile = document.getElementById('imageFile');
    const imagePreview = document.getElementById('imagePreview');
    const imageThumbnail = document.getElementById('imageThumbnail');
    const imageSize = document.getElementById('imageSize');

    imageFile.addEventListener('change', function(e) {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            const reader = new FileReader();
            
            reader.onload = function(e) {
                imageThumbnail.src = e.target.result;
                imagePreview.style.display = 'block';
                
                // 显示文件大小
                const size = formatFileSize(file.size);
                imageSize.textContent = `(${size})`;
            };
            
            reader.readAsDataURL(file);
        }
    });

    // 图片背景类型切换
    const imgBgTypeColor = document.getElementById('imgBgTypeColor');
    const imgBgTypeImage = document.getElementById('imgBgTypeImage');
    const imgBgTypeTransparent = document.getElementById('imgBgTypeTransparent');
    const imgBgColorContainer = document.getElementById('imgBgColorContainer');
    const imgBgImageContainer = document.getElementById('imgBgImageContainer');

    imgBgTypeColor.addEventListener('change', function() {
        if (this.checked) {
            imgBgColorContainer.style.display = 'block';
            imgBgImageContainer.style.display = 'none';
        }
    });

    imgBgTypeImage.addEventListener('change', function() {
        if (this.checked) {
            imgBgColorContainer.style.display = 'none';
            imgBgImageContainer.style.display = 'block';
        }
    });

    imgBgTypeTransparent.addEventListener('change', function() {
        if (this.checked) {
            imgBgColorContainer.style.display = 'none';
            imgBgImageContainer.style.display = 'none';
        }
    });

    // 图片背景预览
    const imgBgImage = document.getElementById('imgBgImage');
    const imgBgImagePreview = document.getElementById('imgBgImagePreview');
    const imgBgImageThumbnail = document.getElementById('imgBgImageThumbnail');
    const imgBgImageSize = document.getElementById('imgBgImageSize');

    imgBgImage.addEventListener('change', function(e) {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            const reader = new FileReader();
            
            reader.onload = function(e) {
                imgBgImageThumbnail.src = e.target.result;
                imgBgImagePreview.style.display = 'block';
                
                // 显示文件大小
                const size = formatFileSize(file.size);
                imgBgImageSize.textContent = `(${size})`;
            };
            
            reader.readAsDataURL(file);
        }
    });

    // 质量滑块显示
    const imageQuality = document.getElementById('imageQuality');
    const qualityValue = document.getElementById('qualityValue');

    imageQuality.addEventListener('input', function() {
        qualityValue.textContent = `${this.value}%`;
    });

    // 图片处理表单提交
    const imageUploadForm = document.getElementById('imageUploadForm');
    
    imageUploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 图片处理逻辑
        submitImageTask();
    });

    // 页面加载完成后，隐藏下载链接
    document.getElementById('downloadLink').style.display = 'none';
});

// 添加视频预览功能 - 使用video元素直接显示
document.getElementById('videoFile').addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
        // 获取视频预览元素
        const videoPreview = document.getElementById('videoPreview');
        const videoElement = document.getElementById('videoThumbnail');
        
        // 设置视频源
        videoElement.src = URL.createObjectURL(file);
        
        // 显示预览区域
        videoPreview.style.display = 'block';
        
        // 视频加载完成后暂停在第一帧并显示尺寸，然后自动开始上传处理
        videoElement.onloadeddata = function() {
            this.currentTime = 0;
            this.pause();
            // 显示视频尺寸
            document.getElementById('videoSize').textContent = `(${this.videoWidth}×${this.videoHeight})`;
            
            // 检查尺寸是否一致
            checkSizeConsistency();
        };
        
        // 添加错误处理
        videoElement.onerror = function() {
            console.error('视频加载失败', this.error);
            alert('视频预览加载失败: ' + (this.error ? this.error.message : '未知错误'));
        };
    }
});

// 显示选择的文件名和预览图片
document.getElementById('bgImage').addEventListener('change', function() {
    if (this.files.length > 0) {
        const file = this.files[0];
        
        // 显示图片预览
        const imgPreview = document.getElementById('bgImagePreview');
        const imgElement = document.getElementById('bgImageThumbnail');
        
        // 设置图片源
        imgElement.src = URL.createObjectURL(file);
        
        // 显示预览区域
        imgPreview.style.display = 'block';
        
        // 图片加载完成后显示尺寸
        imgElement.onload = function() {
            // 显示图片尺寸
            document.getElementById('bgImageSize').textContent = `(${this.naturalWidth}×${this.naturalHeight})`;
            URL.revokeObjectURL(this.src);
            
            // 检查尺寸是否一致
            checkSizeConsistency();
        };
        
        // 添加错误处理
        imgElement.onerror = function() {
            console.error('图片加载失败');
            alert('背景图片预览加载失败');
        };
    }
});

document.getElementById('bgVideo').addEventListener('change', function() {
    if (this.files.length > 0) {
        const file = this.files[0];
        
        // 显示视频预览
        const videoPreview = document.getElementById('bgVideoPreview');
        const videoElement = document.getElementById('bgVideoThumbnail');
        
        // 设置视频源
        videoElement.src = URL.createObjectURL(file);
        
        // 显示预览区域
        videoPreview.style.display = 'block';
        
        // 视频加载完成后暂停在第一帧并显示尺寸
        videoElement.onloadeddata = function() {
            this.currentTime = 0;
            this.pause();
            // 显示视频尺寸
            document.getElementById('bgVideoSize').textContent = `(${this.videoWidth}×${this.videoHeight})`;
            
            // 检查尺寸是否一致
            checkSizeConsistency();
        };
        
        // 添加错误处理
        videoElement.onerror = function() {
            console.error('视频加载失败', this.error);
            alert('背景视频预览加载失败: ' + (this.error ? this.error.message : '未知错误'));
        };
    }
});

// 添加背景类型切换逻辑
document.querySelectorAll('input[name="bgType"]').forEach(radio => {
    radio.addEventListener('change', function() {
        // 隐藏所有背景容器
        document.getElementById('bgColorContainer').style.display = 'none';
        document.getElementById('bgImageContainer').style.display = 'none';
        document.getElementById('bgVideoContainer').style.display = 'none';
        
        // 显示选中的背景容器
        if (this.value === 'color') {
            document.getElementById('bgColorContainer').style.display = 'block';
        } else if (this.value === 'image') {
            document.getElementById('bgImageContainer').style.display = 'block';
        } else if (this.value === 'video') {
            document.getElementById('bgVideoContainer').style.display = 'block';
        }
        
        // 检查尺寸是否一致
        checkSizeConsistency();
    });
});

// 修改submitTask函数，移除透明背景支持
async function submitTask() {
    // 禁用所有表单控件
    setFormDisabled(true, 'videoUploadForm');
    
    // 显示进度容器并重置进度条
    document.querySelector('.progress-container').style.display = 'block';
    updateUploadProgress(0);
    
    const formData = new FormData();
    
    // 获取视频文件并上传
    const videoFile = document.getElementById('videoFile').files[0];
    if (videoFile) {
        const videoId = await uploadFile(videoFile, 'video');
        if (videoId) {
            formData.append('video_id', videoId);
        } else {
            alert('视频上传失败');
            document.querySelector('.progress-container').style.display = 'none';
            setFormDisabled(false);
            return;
        }
    } else {
        alert('请选择视频文件');
        document.querySelector('.progress-container').style.display = 'none';
        setFormDisabled(false);
        return;
    }
    
    // 获取选中的背景类型
    const bgType = document.querySelector('input[name="bgType"]:checked').value;
    formData.append('background_type', bgType);
    
    if (bgType === 'color') {
        formData.append('background_color', document.getElementById('bgColor').value);
    } else if (bgType === 'image') {
        const bgImage = document.getElementById('bgImage').files[0];
        if (bgImage) {
            // 上传背景图片（如果尚未上传）
            const bgImageId = await uploadFile(bgImage, 'image');
            if (bgImageId) {
                formData.append('background_image_id', bgImageId);
            } else {
                alert('背景图片上传失败');
                document.querySelector('.progress-container').style.display = 'none';
                setFormDisabled(false);
                return;
            }
        } else {
            alert('请选择背景图片');
            document.querySelector('.progress-container').style.display = 'none';
            setFormDisabled(false);
            return;
        }
    } else if (bgType === 'video') {
        const bgVideo = document.getElementById('bgVideo').files[0];
        if (bgVideo) {
            // 上传背景视频（如果尚未上传）
            const bgVideoId = await uploadFile(bgVideo, 'background_video');
            if (bgVideoId) {
                formData.append('background_video_id', bgVideoId);
            } else {
                alert('背景视频上传失败');
                document.querySelector('.progress-container').style.display = 'none';
                setFormDisabled(false);
                return;
            }
        } else {
            alert('请选择背景视频');
            document.querySelector('.progress-container').style.display = 'none';
            setFormDisabled(false);
            return;
        }
    }

    try {
        const res = await fetch(`${BASE_URL}/api/submit-task`, {
            method: 'POST',
            body: formData
        });
        
        const result = await res.json();
        if (!result.task_id) throw new Error('任务提交失败');
        
        // 开始轮询任务进度
        pollTaskProgress(result.task_id);
    } catch (error) {
        alert(error.message);
        document.querySelector('.progress-container').style.display = 'none';
        setFormDisabled(false);
    }
}

// 计算MD5函数
async function calculateMD5(file) {
    return new Promise((resolve, reject) => {
        const blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice;
        const chunkSize = 2097152; // 2MB
        const chunks = Math.ceil(file.size / chunkSize);
        const spark = new SparkMD5.ArrayBuffer();
        const fileReader = new FileReader();
        let currentChunk = 0;

        fileReader.onload = function(e) {
            spark.append(e.target.result);
            currentChunk++;

            if (currentChunk < chunks) {
                loadNext();
            } else {
                resolve(spark.end());
            }
        };

        fileReader.onerror = function() {
            reject(new Error('MD5计算失败'));
        };

        function loadNext() {
            const start = currentChunk * chunkSize;
            const end = ((start + chunkSize) >= file.size) ? file.size : start + chunkSize;
            fileReader.readAsArrayBuffer(blobSlice.call(file, start, end));
        }

        loadNext();
    });
}

// 轮询任务进度
let progressPollTimer = null;
async function pollTaskProgress(taskId) {
    try {
        // 修改为正确的API接口
        const res = await fetch(`${BASE_URL}/api/progress/${taskId}`);
        const result = await res.json();
        
        // 更新任务进度条
        const taskProgress = document.getElementById('taskProgress');
        taskProgress.style.width = `${result.progress}%`;
        taskProgress.textContent = `${Math.round(result.progress)}%`;
        
        if (result.status === 'completed') {
            // 任务完成，显示下载链接
            const downloadLink = document.getElementById('downloadLink');
            downloadLink.href = `${BASE_URL}/api/download/${taskId}`;
            // 根据当前处理类型选择下载链接
            if (document.getElementById('videoProcessing').checked) {
                downloadLink.href = `${BASE_URL}/api/download/${taskId}`;
                downloadLink.textContent = '下载处理后的视频';
            } else {
                downloadLink.href = `${BASE_URL}/api/donwload_img/${taskId}`;
                downloadLink.textContent = '下载处理后的图片';
            }
            downloadLink.style.display = 'inline-block';
            
            // 清除轮询定时器
            clearTimeout(progressPollTimer);
            
            // 启用表单控件
            if (document.getElementById('videoProcessing').checked) {
                setFormDisabled(false, 'videoUploadForm');
            } else {
                setFormDisabled(false, 'imageUploadForm');
            }
        } else if (result.status === 'failed') {
            // 任务失败
            alert(`处理失败: ${result.error || '未知错误'}`);
            
            // 清除轮询定时器
            clearTimeout(progressPollTimer);
            
            // 启用表单控件
            if (document.getElementById('videoProcessing').checked) {
                setFormDisabled(false, 'videoUploadForm');
            } else {
                setFormDisabled(false, 'imageUploadForm');
            }
        } else {
            // 继续轮询
            progressPollTimer = setTimeout(() => pollTaskProgress(taskId), 1000);
        }
    } catch (error) {
        console.error('轮询任务进度失败:', error);
        alert('获取任务进度失败');
        
        // 清除轮询定时器
        clearTimeout(progressPollTimer);
        
        // 启用表单控件
        if (document.getElementById('videoProcessing').checked) {
            setFormDisabled(false, 'videoUploadForm');
        } else {
            setFormDisabled(false, 'imageUploadForm');
        }
    }
}

// 设置表单禁用状态 - 增强版，支持指定表单ID
function setFormDisabled(disabled, formId = 'uploadForm') {
    const form = document.getElementById(formId);
    if (!form) return;
    
    if (disabled) {
        form.classList.add('form-disabled');
    } else {
        form.classList.remove('form-disabled');
    }
    
    // 禁用或启用所有表单元素
    const formElements = form.querySelectorAll('input, button, select, textarea');
    formElements.forEach(element => {
        element.disabled = disabled;
    });
}

// 图片处理任务提交函数
async function submitImageTask() {
    // 禁用所有表单控件
    setFormDisabled(true, 'imageUploadForm');
    
    // 显示进度容器并重置进度条
    document.querySelector('.progress-container').style.display = 'block';
    updateUploadProgress(0);
    
    const formData = new FormData();
    
    // 获取图片文件并上传
    const imageFile = document.getElementById('imageFile').files[0];
    if (imageFile) {
        const imageId = await uploadFile(imageFile, 'image');
        if (imageId) {
            formData.append('image_id', imageId);
        } else {
            alert('图片上传失败');
            document.querySelector('.progress-container').style.display = 'none';
            setFormDisabled(false, 'imageUploadForm');
            return;
        }
    } else {
        alert('请选择图片文件');
        document.querySelector('.progress-container').style.display = 'none';
        setFormDisabled(false, 'imageUploadForm');
        return;
    }
    
    // 获取选中的背景类型
    const bgType = document.querySelector('input[name="imgBgType"]:checked').value;
    formData.append('background_type', bgType);
    
    if (bgType === 'color') {
        formData.append('background_color', document.getElementById('imgBgColor').value);
    } else if (bgType === 'image') {
        const bgImage = document.getElementById('imgBgImage').files[0];
        if (bgImage) {
            // 上传背景图片（如果尚未上传）
            const bgImageId = await uploadFile(bgImage, 'image');
            if (bgImageId) {
                formData.append('background_image_id', bgImageId);
            } else {
                alert('背景图片上传失败');
                document.querySelector('.progress-container').style.display = 'none';
                setFormDisabled(false, 'imageUploadForm');
                return;
            }
        } else {
            alert('请选择背景图片');
            document.querySelector('.progress-container').style.display = 'none';
            setFormDisabled(false, 'imageUploadForm');
            return;
        }
    }
    // 透明背景不需要额外参数
    
    // 获取输出质量设置
    const imageQuality = document.getElementById('imageQuality').value;
    formData.append('quality', imageQuality);
    
    // 添加处理类型标识
    formData.append('process_type', 'image');

    try {
        // 修改为正确的API接口
        const res = await fetch(`${BASE_URL}/api/submit_image`, {
            method: 'POST',
            body: formData
        });
        
        const result = await res.json();
        if (!result.task_id) throw new Error('任务提交失败');
        
        // 开始轮询任务进度
        pollTaskProgress(result.task_id);
    } catch (error) {
        alert(error.message);
        document.querySelector('.progress-container').style.display = 'none';
        setFormDisabled(false, 'imageUploadForm');
    }
}

// 格式化文件大小的辅助函数
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 检查图片尺寸一致性
function checkImageSizeConsistency() {
    // 获取当前选择的背景类型
    const bgType = document.querySelector('input[name="imgBgType"]:checked').value;
    
    // 如果是纯色背景，不需要检查尺寸
    if (bgType === 'color') {
        return;
    }
    
    // 获取主图片元素
    const mainImage = document.getElementById('imageThumbnail');
    if (!mainImage.naturalWidth) {
        return; // 主图片尚未加载
    }
    
    // 获取背景图片元素
    const bgImage = document.getElementById('imgBgImageThumbnail');
    if (!bgImage.naturalWidth) {
        return; // 背景图片尚未加载
    }
    
    // 获取或创建警告元素
    let warningElement = document.getElementById('imgBgImageSizeWarning');
    if (!warningElement) {
        warningElement = document.createElement('div');
        warningElement.id = 'imgBgImageSizeWarning';
        warningElement.className = 'size-warning';
        document.getElementById('imgBgImagePreview').appendChild(warningElement);
    }
    
    // 检查尺寸是否一致
    if (bgImage.naturalWidth !== mainImage.naturalWidth || bgImage.naturalHeight !== mainImage.naturalHeight) {
        warningElement.textContent = `警告：背景尺寸(${bgImage.naturalWidth}×${bgImage.naturalHeight})与图片尺寸(${mainImage.naturalWidth}×${mainImage.naturalHeight})不一致，可能导致画面变形或裁剪`;
        warningElement.style.display = 'block';
    } else {
        warningElement.style.display = 'none';
    }
}

// 为图片背景类型切换添加事件监听
document.addEventListener('DOMContentLoaded', function() {
    // 已有的代码...
    
    // 添加图片背景类型切换事件监听
    document.querySelectorAll('input[name="imgBgType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            // 隐藏所有背景容器
            document.getElementById('imgBgColorContainer').style.display = 'none';
            document.getElementById('imgBgImageContainer').style.display = 'none';
            
            // 显示选中的背景容器
            if (this.value === 'color') {
                document.getElementById('imgBgColorContainer').style.display = 'block';
            } else if (this.value === 'image') {
                document.getElementById('imgBgImageContainer').style.display = 'block';
            }
            // 透明背景不需要显示任何容器
            
            // 检查尺寸是否一致
            checkImageSizeConsistency();
        });
    });
    
    // 当背景图片加载完成后，检查尺寸一致性
    document.getElementById('imgBgImageThumbnail').addEventListener('load', function() {
        checkImageSizeConsistency();
    });
    
    // 当主图片加载完成后，检查尺寸一致性
    document.getElementById('imageThumbnail').addEventListener('load', function() {
        checkImageSizeConsistency();
    });
});

// 添加表单提交事件监听
document.getElementById('videoUploadForm').addEventListener('submit', function(e) {
    e.preventDefault();
    submitTask();
});

// 页面加载完成后，隐藏下载链接
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('downloadLink').style.display = 'none';
});

// 添加尺寸一致性检查函数
function checkSizeConsistency() {
    // 获取当前选择的背景类型
    const bgType = document.querySelector('input[name="bgType"]:checked').value;
    
    // 如果是纯色背景或透明背景，不需要检查尺寸
    if (bgType === 'color' || bgType === 'transparent') {
        return;
    }
    
    // 获取主视频元素
    const mainVideo = document.getElementById('videoThumbnail');
    if (!mainVideo.videoWidth) {
        return; // 主视频尚未加载
    }
    
    let bgWidth = 0;
    let bgHeight = 0;
    let warningElement = null;
    
    // 根据背景类型获取尺寸
    if (bgType === 'image') {
        const bgImage = document.getElementById('bgImageThumbnail');
        if (!bgImage.naturalWidth) {
            return; // 背景图片尚未加载
        }
        
        bgWidth = bgImage.naturalWidth;
        bgHeight = bgImage.naturalHeight;
        
        // 获取或创建警告元素
        warningElement = document.getElementById('bgImageSizeWarning');
        if (!warningElement) {
            warningElement = document.createElement('div');
            warningElement.id = 'bgImageSizeWarning';
            warningElement.className = 'size-warning';
            document.getElementById('bgImagePreview').appendChild(warningElement);
        }
    } else if (bgType === 'video') {
        const bgVideo = document.getElementById('bgVideoThumbnail');
        if (!bgVideo.videoWidth) {
            return; // 背景视频尚未加载
        }
        
        bgWidth = bgVideo.videoWidth;
        bgHeight = bgVideo.videoHeight;
        
        // 获取或创建警告元素
        warningElement = document.getElementById('bgVideoSizeWarning');
        if (!warningElement) {
            warningElement = document.createElement('div');
            warningElement.id = 'bgVideoSizeWarning';
            warningElement.className = 'size-warning';
            document.getElementById('bgVideoPreview').appendChild(warningElement);
        }
    }
    
    // 检查尺寸是否一致
    if (bgWidth !== mainVideo.videoWidth || bgHeight !== mainVideo.videoHeight) {
        warningElement.textContent = `警告：背景尺寸(${bgWidth}×${bgHeight})与视频尺寸(${mainVideo.videoWidth}×${mainVideo.videoHeight})不一致，可能导致画面变形或裁剪`;
        warningElement.style.display = 'block';
    } else {
        warningElement.style.display = 'none';
    }
}

// 通用文件上传函数
async function uploadFile(file, fileType) {
    try {
        // 计算MD5
        const md5 = await calculateMD5(file);
        
        // 检查文件是否存在
        const checkRes = await fetch(`${BASE_URL}/api/query_file/${fileType}/${md5}`);
        if (checkRes.ok) {
            const result = await checkRes.json();
            if (result.file_id) {
                console.log(`${fileType} 文件已存在，文件ID:`, result.file_id);
                // 文件已存在时，将上传进度条设置为100%
                updateUploadProgress(100);
                return result.file_id;
            }
        }

        // 上传文件
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', fileType);
        formData.append('file_md5', md5);

        // 使用XMLHttpRequest替代fetch以获取上传进度
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // 监听上传进度
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    updateUploadProgress(percentComplete);
                }
            });
            
            // 监听请求完成
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        console.log(`${fileType} 上传成功，文件ID:`, response.file_id);
                        resolve(response.file_id);
                    } catch (e) {
                        reject(new Error(`解析响应失败: ${e.message}`));
                    }
                } else {
                    reject(new Error(`${fileType} 上传失败: 状态码 ${xhr.status}`));
                }
            });
            
            // 监听错误
            xhr.addEventListener('error', () => {
                reject(new Error(`${fileType} 上传网络错误`));
            });
            
            // 监听中止
            xhr.addEventListener('abort', () => {
                reject(new Error(`${fileType} 上传被中止`));
            });
            
            // 发送请求
            xhr.open('POST', `${BASE_URL}/api/upload-file`);
            xhr.send(formData);
        });
    } catch (error) {
        console.error(`${fileType} 上传失败:`, error);
        return null;
    }
}

// 添加更新上传进度的函数
function updateUploadProgress(percent) {
    const progressBar = document.getElementById('uploadProgress');
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
        progressBar.textContent = `${Math.round(percent)}%`;
    }
}
