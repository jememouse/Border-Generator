// static/script.js

// 等待整个 HTML 文档加载完成后再执行脚本
document.addEventListener('DOMContentLoaded', () => {
    // 获取需要操作的 DOM 元素
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
    const innerShapeSelect = document.getElementById('inner_shape_type'); // 内框形状选择器
    const cornerRadiusGroup = document.getElementById('corner-radius-group'); // 圆角半径的表单组
    const cornerRadiusInput = document.getElementById('inner_corner_radius_mm'); // 圆角半径输入框

    // --- 功能函数：切换圆角半径输入框的可见性和必需状态 ---
    function toggleCornerRadiusInput() {
        if (innerShapeSelect.value === 'rectangle') {
            // 如果选择矩形，显示圆角输入框并设为必填
            cornerRadiusGroup.style.display = 'block';
            cornerRadiusInput.required = true;
        } else {
            // 如果选择椭圆，隐藏圆角输入框并设为非必填
            cornerRadiusGroup.style.display = 'none';
            cornerRadiusInput.required = false;
            // 可选：隐藏时清空值
            // cornerRadiusInput.value = '';
        }
    }

    // 页面加载时立即执行一次，以设置正确的初始状态
    toggleCornerRadiusInput();
    // 监听内框形状下拉框的变化事件
    innerShapeSelect.addEventListener('change', toggleCornerRadiusInput);

    // --- 功能函数：重置状态显示 ---
    function resetStatusDisplays() {
        // 隐藏加载提示
        loadingIndicator1.style.display = 'none';
        loadingIndicator2.style.display = 'none';
        // 隐藏错误信息
        errorDisplay1.style.display = 'none';
        errorDisplay2.style.display = 'none';
        // 清空错误文本
        errorDisplay1.textContent = '';
        errorDisplay2.textContent = '';
        // 隐藏图片元素 (或者可以设置一个默认的占位图 src)
        imgElement1.style.display = 'none';
        imgElement1.src = ''; // 清除旧图片
        imgElement2.style.display = 'none';
        imgElement2.src = ''; // 清除旧图片
        // 显示结果容器（如果它们被隐藏了）
        resultContainer1.style.display = 'block';
        resultContainer2.style.display = 'block';
        // 启用提交按钮
        generateButton.disabled = false;
        generateButton.textContent = '生成图像'; // 恢复按钮文字
    }

    // --- 监听表单提交事件 ---
    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // 阻止表单的默认提交行为（页面跳转）

        console.log("表单提交事件触发");

        // 重置之前的状态和结果
        resetStatusDisplays();

        // 显示加载提示
        loadingIndicator1.style.display = 'block';
        loadingIndicator2.style.display = 'block';
        // 禁用提交按钮，防止重复提交
        generateButton.disabled = true;
        generateButton.textContent = '正在生成中...';

        // 从表单创建 FormData 对象，这会自动收集所有输入的值
        const formData = new FormData(form);
        console.log("FormData 已创建");

        // 定义请求参数
        const requestOptions = {
            method: 'POST',
            body: formData, // fetch API 可以直接发送 FormData
            // 注意：使用 FormData 时，浏览器会自动设置正确的 Content-Type (multipart/form-data)
            // 不需要手动设置 headers: { 'Content-Type': '...' }
        };

        // --- 并行发起两个请求 ---
        // 使用 Promise.allSettled 来等待两个请求都完成（无论成功或失败）
        const results = await Promise.allSettled([
            fetch('/generate_image_style1/', requestOptions),
            fetch('/generate_image_style2/', requestOptions)
        ]);

        console.log("两个 fetch 请求已完成 (settled)");

        // --- 处理样式1的请求结果 ---
        const result1 = results[0]; // 获取第一个 Promise 的结果
        if (result1.status === 'fulfilled') { // 请求成功完成
            const response = result1.value; // 获取 Response 对象
            console.log("样式1 fetch 成功，状态码:", response.status);
            if (response.ok) { // HTTP 状态码为 2xx
                try {
                    const blob = await response.blob(); // 将响应体解析为 Blob 对象 (二进制数据)
                    const objectURL = URL.createObjectURL(blob); // 为 Blob 创建一个临时的 URL
                    imgElement1.src = objectURL; // 设置 <img> 的 src 属性
                    imgElement1.style.display = 'block'; // 显示图片
                    console.log("样式1 图片已加载并显示");
                    // 可选：在图片加载完成后释放 Object URL
                    // imgElement1.onload = () => URL.revokeObjectURL(objectURL);
                } catch (error) {
                    console.error('处理样式1响应时出错:', error);
                    errorDisplay1.textContent = '无法处理返回的图像数据。';
                    errorDisplay1.style.display = 'block';
                }
            } else { // HTTP 状态码不是 2xx
                let errorDetail = `服务器错误 (状态码: ${response.status})`;
                try {
                    // 尝试解析服务器返回的 JSON 错误信息
                    const errorJson = await response.json();
                    errorDetail = errorJson.detail || errorDetail; // 使用 FastAPI 返回的 detail 字段
                } catch (e) {
                    console.warn("无法解析样式1的错误响应体为 JSON");
                }
                console.error('样式1请求失败:', errorDetail);
                errorDisplay1.textContent = `样式1生成失败: ${errorDetail}`;
                errorDisplay1.style.display = 'block';
            }
        } else { // 请求本身失败 (例如网络错误)
            console.error('样式1 fetch 请求失败:', result1.reason);
            errorDisplay1.textContent = `样式1请求失败: ${result1.reason}`;
            errorDisplay1.style.display = 'block';
        }
        // 隐藏样式1的加载提示
        loadingIndicator1.style.display = 'none';

        // --- 处理样式2的请求结果 (逻辑与样式1类似) ---
        const result2 = results[1]; // 获取第二个 Promise 的结果
        if (result2.status === 'fulfilled') {
            const response = result2.value;
            console.log("样式2 fetch 成功，状态码:", response.status);
            if (response.ok) {
                try {
                    const blob = await response.blob();
                    const objectURL = URL.createObjectURL(blob);
                    imgElement2.src = objectURL;
                    imgElement2.style.display = 'block';
                    console.log("样式2 图片已加载并显示");
                    // imgElement2.onload = () => URL.revokeObjectURL(objectURL);
                } catch (error) {
                    console.error('处理样式2响应时出错:', error);
                    errorDisplay2.textContent = '无法处理返回的图像数据。';
                    errorDisplay2.style.display = 'block';
                }
            } else {
                let errorDetail = `服务器错误 (状态码: ${response.status})`;
                try {
                    const errorJson = await response.json();
                    errorDetail = errorJson.detail || errorDetail;
                } catch (e) {
                     console.warn("无法解析样式2的错误响应体为 JSON");
                 }
                console.error('样式2请求失败:', errorDetail);
                errorDisplay2.textContent = `样式2生成失败: ${errorDetail}`;
                errorDisplay2.style.display = 'block';
            }
        } else {
            console.error('样式2 fetch 请求失败:', result2.reason);
            errorDisplay2.textContent = `样式2请求失败: ${result2.reason}`;
            errorDisplay2.style.display = 'block';
        }
        // 隐藏样式2的加载提示
        loadingIndicator2.style.display = 'none';

        // 所有请求处理完毕后，重新启用提交按钮
        generateButton.disabled = false;
        generateButton.textContent = '生成图像'; // 恢复按钮文字
        console.log("所有处理完成，按钮已恢复");
    });
});