// 异步提交 → 轮询 → 完成后自动下载, 无需用户额外点击
document.addEventListener("DOMContentLoaded", function() {
    var form = document.getElementById("form-requirement");
    if (!form) return;

    form.addEventListener("submit", function(e) {
        e.preventDefault();
        var btn = form.querySelector("button[type='submit']");
        btn.disabled = true;
        btn.textContent = "AI 生成中, 请稍候...";

        var fd = new FormData(form);

        fetch(form.dataset.submitUrl, {
            method: "POST", body: fd,
            headers: {"X-Requested-With": "XMLHttpRequest"},
            credentials: "same-origin"
        }).then(function(r) { return r.json(); })
        .then(function(payload) {
            var data = payload.data || payload;
            var jobId = data.job_id;
            if (!jobId) throw new Error("no job_id");

            var statusUrl = form.dataset.statusUrlTemplate.replace("__JOB_ID__", jobId);
            return poll(statusUrl);
        }).then(function(final) {
            btn.textContent = "下载中...";
            var downloadUrl = form.dataset.downloadUrlTemplate.replace("__JOB_ID__", final.design_job_id || final.job_id);
            // 自动下载
            var a = document.createElement("a");
            a.href = downloadUrl; a.download = ""; a.style.display = "none";
            document.body.appendChild(a); a.click(); a.remove();
            btn.textContent = "已完成, 可再次提交";
            btn.disabled = false;
        }).catch(function(err) {
            btn.textContent = "生成测试用例";
            btn.disabled = false;
            alert("失败: " + (err.message || "未知错误"));
        });
    });

    function poll(statusUrl) {
        return new Promise(function(resolve, reject) {
            function check() {
                fetch(statusUrl, {
                    headers: {"X-Requested-With": "XMLHttpRequest"},
                    credentials: "same-origin"
                }).then(function(r) { return r.json(); })
                .then(function(payload) {
                    var data = payload.data || payload;
                    if (data.is_finished) {
                        if (data.is_success) resolve(data);
                        else reject(new Error(data.error_message || "AI 生成失败"));
                    } else {
                        setTimeout(check, 2000);
                    }
                }).catch(reject);
            }
            check();
        });
    }
});
