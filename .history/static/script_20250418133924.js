// static/script.js

// 等待整个 HTML 文档加载完成后再执行脚本
document.addEventListener('DOMContentLoaded', () => {
    // 获取需要操作的 DOM 元素 (添加下载按钮)
    const form = document.getElementById('image-form');
    const generateButton = document.getElementById('generate-button'); // 获取按钮
    const resultContainer1 = document.getElementById('result-style1'); // 结果容器1
    const resultContainer2 = document.getElementById('result-style2'); // 结果容器2
    const imgElement1 = document.getElementById('img-style1');        // 图片元素1
    const imgElement2 = document.getElementById('img-style2');        // 图片元素2
    const loadingIndicator1 = document.getElementById('loading-style1'); // 加载提示1
    const loadingIndicator2 = document.getElementById('loading-style2'); // 加载提示2
    const errorDisplay1 = document.getElementById('error-style1');       // 错误显示1
    const errorDisplay2 = document.getElementById('error-style2');       // 错误显示2
    const downloadLink1 = document.getElementById('download-style1'); // 获取下载链接1
    const downloadLink2 = document.getElementById('download-style2'); // 获取下载链接2
    const innerShapeSelect = document.getElementById('inner_shape_type'); // 内框形状选择器
    const cornerRadiusGroup = document.getElementById('corner-radius-group'); // 圆角半径的表单组
    const cornerRadiusInput = document.getElementById('inner_corner_radius_mm'); // 圆角半径输入框

    // 用于存储上一次生成的 Object URL，以便稍后释放
    let previousObjectURL1 = null;
    let previousObjectURL2 = null;

    // --- 功能函数：切换圆角半径输入框的可见性和必需状态 ---
    function toggleCornerRadiusInput() {
        if (innerShapeSelect.value === 'rectangle') {
            cornerRadiusGroup.style.display = 'block';
            cornerRadiusInput.required = true;
        } else {
            cornerRadiusGroup.style.display = 'none';
            cornerRadiusInput.required = false;
        }
    }

    // 页面加载时立即执行一次
    toggleCornerRadiusInput();
    // 监听内框形状下拉框的变化事件
    innerShapeSelect.addEventListener('change', toggleCornerRadiusInput);


    // --- 功能函数：重置状态显示 (包括下载按钮) ---
    function resetStatusDisplays() {
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
        // 隐藏并重置下载链接
        downloadLink1.style.display = 'none';
        downloadLink1.href = '#'; // 重置 href
        downloadLink2.style.display = 'none';
        downloadLink2.href = '#'; // 重置 href

        // 尝试释放上一次生成的 Object URL (如果存在)
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

        // 显示结果容器，以便显示加载或错误信息
        resultContainer1.style.display = 'block';
        resultContainer2.style.display = 'block';

        generateButton.disabled = false;
        generateButton.textContent = '生成图像';
    }

    // --- 监听表单提交事件 ---
    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // 阻止表单的默认提交行为
        console.log("表单提交事件触发");
        resetStatusDisplays(); // 先重置状态

        // 显示加载提示
        loadingIndicator1.style.display = 'block';
        loadingIndicator2.style.display = 'block';
        // 禁用提交按钮，防止重复提交
        generateButton.disabled = true;
        generateButton.textContent = '正在生成中...';

        // 从表单创建 FormData 对象
        const formData = new FormData(form);
        console.log("FormData 已创建");
        const requestOptions = { method: 'POST', body: formData };

        // --- 并行发起两个请求 ---
        console.log("开始并行发送 fetch 请求...");
        const results = await Promise.allSettled([
            fetch('/generate_image_style1/', requestOptions),
            fetch('/generate_image_style2/', requestOptions)
        ]);
        console.log("两个 fetch 请求已完成 (settled)");

        // --- 处理样式1的请求结果 ---
        const result1 = results[0]; // 获取第一个 Promise 的结果
        if (result1.status === 'fulfilled' && result1.value.ok) { // 请求成功完成且 HTTP 状态 OK
            const response = result1.value; // 获取 Response 对象
            console.log("样式1 fetch 成功，状态码:", response.status);
            try {
                const blob = await response.blob(); // 将响应体解析为 Blob 对象
                const objectURL = URL.createObjectURL(blob); // 为 Blob 创建一个临时的 URL
                console.log("样式1 Object URL 创建:", objectURL);
                // 保存新的 URL 以便下次释放
                previousObjectURL1 = objectURL;

                imgElement1.src = objectURL; // 设置图片预览
                imgElement1.style.display = 'block'; // 显示图片

                downloadLink1.href = objectURL; // 设置下载链接的 href
                // downloadLink1.download = "自定义文件名1.png"; // 可选：动态设置下载文件名
                downloadLink1.style.display = 'inline-block'; // 显示下载按钮

                console.log("样式1 图片已加载并显示，下载链接已设置");
            } catch (error) {
                console.error('处理样式1响应时出错:', error);
                errorDisplay1.textContent = '无法处理返回的图像数据。';
                errorDisplay1.style.display = 'block';
            }
        } else { // 请求失败或 HTTP 状态不 OK
            let errorMessage = '样式1请求失败';
            if (result1.status === 'fulfilled') { // 请求完成但状态码不对
                const response = result1.value;
                errorMessage = `服务器错误 (状态码: ${response.status})`;
                try { // 尝试从 FastAPI 获取详细错误信息
                    const errorJson = await response.json();
                    errorMessage = errorJson.detail || errorMessage;
                } catch (e) { console.warn("无法解析样式1的错误响应体为 JSON"); }
            } else { // 请求本身失败 (例如网络错误)
                errorMessage = `网络请求错误: ${result1.reason}`;
            }
            console.error('样式1处理失败:', errorMessage);
            errorDisplay1.textContent = `样式1生成失败: ${errorMessage}`;
            errorDisplay1.style.display = 'block';
            downloadLink1.style.display = 'none'; // 确保失败时不显示下载按钮
        }
        loadingIndicator1.style.display = 'none'; // 隐藏加载提示

        // --- 处理样式2的请求结果 (逻辑与样式1类似) ---
        const result2 = results[1]; // 获取第二个 Promise 的结果
        if (result2.status === 'fulfilled' && result2.value.ok) {
            const response = result2.value;
            console.log("样式2 fetch 成功，状态码:", response.status);
            try {
                const blob = await response.blob();
                const objectURL = URL.createObjectURL(blob);
                console.log("样式2 Object URL 创建:", objectURL);
                previousObjectURL2 = objectURL; // 保存新的 URL

                imgElement2.src = objectURL; // 设置图片预览
                imgElement2.style.display = 'block'; // 显示图片

                downloadLink2.href = objectURL; // 设置下载链接的 href
                // downloadLink2.download = "自定义文件名2.png";
                downloadLink2.style.display = 'inline-block'; // 显示下载按钮

                console.log("样式2 图片已加载并显示，下载链接已设置");
            } catch (error) {
                console.error('处理样式2响应时出错:', error);
                errorDisplay2.textContent = '无法处理返回的图像数据。';
                errorDisplay2.style.display = 'block';
            }
        } else {
             let errorMessage = '样式2请求失败';
            if (result2.status === 'fulfilled') {
                const response = result2.value;
                errorMessage = `服务器错误 (状态码: ${response.status})`;
                try {
                    const errorJson = await response.json();
                    errorMessage = errorJson.detail || errorMessage;
                } catch (e) { console.warn("无法解析样式2的错误响应体为 JSON"); }
            } else {
                errorMessage = `网络请求错误: ${result2.reason}`;
            }
            console.error('样式2处理失败:', errorMessage);
            errorDisplay2.textContent = `样式2生成失败: ${errorMessage}`;
            errorDisplay2.style.display = 'block';
            downloadLink2.style.display = 'none'; // 确保失败时不显示下载按钮
        }
        loadingIndicator2.style.display = 'none'; // 隐藏加载提示

        // 所有请求处理完毕后，重新启用提交按钮
        generateButton.disabled = false;
        generateButton.textContent = '生成图像';
        console.log("所有处理完成，按钮已恢复");
    });
});