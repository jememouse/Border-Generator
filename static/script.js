// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    // ... (获取 DOM 元素的部分不变) ...
    const form = document.getElementById('image-form');
    const generateButton = document.getElementById('generate-button');
    const resultContainer1 = document.getElementById('result-style1');
    const resultContainer2 = document.getElementById('result-style2');
    const imgElement1 = document.getElementById('img-style1');
    const imgElement2 = document.getElementById('img-style2');
    const loadingIndicator1 = document.getElementById('loading-style1');
    const loadingIndicator2 = document.getElementById('loading-style2');
    const errorDisplay1 = document.getElementById('error-style1');
    const errorDisplay2 = document.getElementById('error-style2');
    const downloadLink1 = document.getElementById('download-style1');
    const downloadLink2 = document.getElementById('download-style2');
    const innerShapeSelect = document.getElementById('inner_shape_type');
    const cornerRadiusGroup = document.getElementById('corner-radius-group');
    const cornerRadiusInput = document.getElementById('inner_corner_radius_mm');

    let previousObjectURL1 = null;
    let previousObjectURL2 = null;

    function toggleCornerRadiusInput() {
        // ... (不变) ...
         if (innerShapeSelect.value === 'rectangle') {
            cornerRadiusGroup.style.display = 'block';
            cornerRadiusInput.required = true;
        } else {
            cornerRadiusGroup.style.display = 'none';
            cornerRadiusInput.required = false;
        }
    }
    toggleCornerRadiusInput();
    innerShapeSelect.addEventListener('change', toggleCornerRadiusInput);

    function resetStatusDisplays() {
        // ... (不变) ...
        loadingIndicator1.style.display = 'none';
        loadingIndicator2.style.display = 'none';
        errorDisplay1.style.display = 'none';
        errorDisplay2.style.display = 'none';
        errorDisplay1.textContent = '';
        errorDisplay2.textContent = '';
        imgElement1.style.display = 'none';
        imgElement1.src = '';
        imgElement2.style.display = 'none';
        imgElement2.src = '';
        downloadLink1.style.display = 'none';
        downloadLink1.href = '#';
        downloadLink2.style.display = 'none';
        downloadLink2.href = '#';

        if (previousObjectURL1) {
            URL.revokeObjectURL(previousObjectURL1);
            console.log("已释放之前的 Object URL 1:", previousObjectURL1);
            previousObjectURL1 = null;
        }
        if (previousObjectURL2) {
            URL.revokeObjectURL(previousObjectURL2);
            console.log("已释放之前的 Object URL 2:", previousObjectURL2);
            previousObjectURL2 = null;
        }
        resultContainer1.style.display = 'block';
        resultContainer2.style.display = 'block';
        generateButton.disabled = false;
        generateButton.textContent = '生成图像';
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        console.log("表单提交事件触发 - 开始");
        resetStatusDisplays();

        loadingIndicator1.style.display = 'block';
        loadingIndicator2.style.display = 'block';
        generateButton.disabled = true;
        generateButton.textContent = '正在生成中...';

        const formData = new FormData(form);
        const requestOptions = { method: 'POST', body: formData };

        console.log("开始并行发送 fetch 请求...");
        const results = await Promise.allSettled([
            fetch('/generate_image_style1/', requestOptions),
            fetch('/generate_image_style2/', requestOptions)
        ]);
        console.log("两个 fetch 请求已完成 (settled)。结果:", results);

        // --- 处理样式1的请求结果 ---
        console.log("--- 开始处理样式 1 ---");
        const result1 = results[0];
        if (result1.status === 'fulfilled') { // 请求成功完成
            const response = result1.value;
            console.log("样式1 fetch 响应状态:", response.status, response.ok);
            if (response.ok) { // HTTP 状态 OK
                try {
                    console.log("样式1: 尝试获取 Blob...");
                    const blob = await response.blob();
                    console.log("样式1 Blob 获取成功:", blob);
                    if (blob.size === 0) { // 检查返回的 Blob 是否为空
                         console.error("样式1: 服务器返回了空的图像数据!");
                         throw new Error("服务器返回了空的图像数据");
                    }
                    const objectURL = URL.createObjectURL(blob);
                    console.log("样式1 Object URL 创建:", objectURL);
                    previousObjectURL1 = objectURL; // 保存新 URL

                    // 确认 DOM 元素存在
                    if (!imgElement1 || !downloadLink1) {
                        console.error("样式1: 无法找到 img 或 download 元素!");
                        throw new Error("页面元素丢失");
                    }

                    imgElement1.src = objectURL;
                    imgElement1.style.display = 'block';
                    downloadLink1.href = objectURL;
                    downloadLink1.style.display = 'inline-block';
                    console.log("样式1 图像和下载链接已更新");
                } catch (error) {
                    console.error('处理样式1响应时出错:', error);
                    errorDisplay1.textContent = `处理图像数据时出错: ${error.message}`;
                    errorDisplay1.style.display = 'block';
                    downloadLink1.style.display = 'none'; // 确保出错时隐藏下载
                }
            } else { // HTTP 状态不 OK
                let errorMessage = `服务器错误 (状态码: ${response.status})`;
                try {
                    const errorJson = await response.json();
                    errorMessage = errorJson.detail || errorMessage;
                } catch (e) { console.warn("无法解析样式1的错误响应体为 JSON"); }
                console.error('样式1请求失败:', errorMessage);
                errorDisplay1.textContent = `样式1生成失败: ${errorMessage}`;
                errorDisplay1.style.display = 'block';
                downloadLink1.style.display = 'none';
            }
        } else { // 请求本身失败
            console.error('样式1 fetch 请求失败:', result1.reason);
            errorDisplay1.textContent = `样式1网络请求失败: ${result1.reason}`;
            errorDisplay1.style.display = 'block';
            downloadLink1.style.display = 'none';
        }
        loadingIndicator1.style.display = 'none';
        console.log("--- 样式 1 处理结束 ---");


        // --- 处理样式2的请求结果 ---
        console.log("--- 开始处理样式 2 ---");
        const result2 = results[1];
        if (result2.status === 'fulfilled') { // 请求成功完成
            const response = result2.value;
            console.log("样式2 fetch 响应状态:", response.status, response.ok);
             if (response.ok) { // HTTP 状态 OK
                try {
                    console.log("样式2: 尝试获取 Blob...");
                    const blob = await response.blob();
                    console.log("样式2 Blob 获取成功:", blob);
                     if (blob.size === 0) {
                         console.error("样式2: 服务器返回了空的图像数据!");
                         throw new Error("服务器返回了空的图像数据");
                    }
                    const objectURL = URL.createObjectURL(blob);
                    console.log("样式2 Object URL 创建:", objectURL);
                    previousObjectURL2 = objectURL; // 保存新 URL

                    // 确认 DOM 元素存在
                    if (!imgElement2 || !downloadLink2) {
                        console.error("样式2: 无法找到 img 或 download 元素!");
                        throw new Error("页面元素丢失");
                    }

                    imgElement2.src = objectURL;
                    imgElement2.style.display = 'block';
                    downloadLink2.href = objectURL;
                    downloadLink2.style.display = 'inline-block';
                    console.log("样式2 图像和下载链接已更新");
                } catch (error) {
                    console.error('处理样式2响应时出错:', error);
                    errorDisplay2.textContent = `处理图像数据时出错: ${error.message}`;
                    errorDisplay2.style.display = 'block';
                    downloadLink2.style.display = 'none'; // 确保出错时隐藏下载
                }
            } else { // HTTP 状态不 OK
                let errorMessage = `服务器错误 (状态码: ${response.status})`;
                try {
                    const errorJson = await response.json();
                    errorMessage = errorJson.detail || errorMessage;
                } catch (e) { console.warn("无法解析样式2的错误响应体为 JSON"); }
                console.error('样式2请求失败:', errorMessage);
                errorDisplay2.textContent = `样式2生成失败: ${errorMessage}`;
                errorDisplay2.style.display = 'block';
                downloadLink2.style.display = 'none';
            }
        } else { // 请求本身失败
            console.error('样式2 fetch 请求失败:', result2.reason);
            errorDisplay2.textContent = `样式2网络请求失败: ${result2.reason}`;
            errorDisplay2.style.display = 'block';
            downloadLink2.style.display = 'none';
        }
        loadingIndicator2.style.display = 'none';
        console.log("--- 样式 2 处理结束 ---");


        // 所有处理完成后，重新启用提交按钮
        generateButton.disabled = false;
        generateButton.textContent = '生成图像';
        console.log("所有处理完成，按钮已恢复");
    });
});