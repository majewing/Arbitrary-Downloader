let videoInfoData = null;
let selectedVideoFormat = null;
let selectedAudioFormat = null;

function showSection(id) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById('section-' + id).classList.add('active');
}

async function fetchInfo() {
    const url = document.getElementById('url-input').value.trim();
    const browser = document.getElementById('browser-select').value || null;
    const errorEl = document.getElementById('fetch-error');
    const btn = document.getElementById('fetch-btn');

    if (!url) {
        errorEl.textContent = '请输入视频链接';
        return;
    }
    errorEl.textContent = '';
    btn.disabled = true;
    btn.textContent = '正在获取...';

    try {
        const resp = await fetch('/api/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, browser })
        });
        const data = await resp.json();
        if (!resp.ok) {
            errorEl.textContent = data.error || '获取失败';
            btn.disabled = false;
            btn.textContent = '获取视频信息';
            return;
        }
        videoInfoData = data;
        renderFormatPage(data);
        showSection('format');
    } catch (e) {
        errorEl.textContent = '网络错误: ' + e.message;
    } finally {
        btn.disabled = false;
        btn.textContent = '获取视频信息';
    }
}

function renderFormatPage(data) {
    document.getElementById('video-title').textContent = data.title;
    document.getElementById('video-meta').textContent = data.uploader + '  |  时长: ' + data.duration;

    const vtBody = document.querySelector('#video-table tbody');
    vtBody.innerHTML = '';
    data.video_formats.forEach(f => {
        const tr = document.createElement('tr');
        tr.innerHTML =
            '<td><input type="radio" name="video-fmt" value="' + f.id + '"></td>' +
            '<td>' + f.id + '</td>' +
            '<td>' + f.resolution + '</td>' +
            '<td>' + f.ext + '</td>' +
            '<td>' + f.codec + '</td>' +
            '<td>' + f.fps + '</td>' +
            '<td>' + f.size + '</td>' +
            '<td>' + (f.has_audio ? '含音频' : '') + '</td>';
        tr.addEventListener('click', function () {
            vtBody.querySelectorAll('input').forEach(i => i.checked = false);
            tr.querySelector('input').checked = true;
            selectedVideoFormat = f.id;
        });
        vtBody.appendChild(tr);
    });

    const atBody = document.querySelector('#audio-table tbody');
    atBody.innerHTML = '';
    data.audio_formats.forEach(f => {
        const tr = document.createElement('tr');
        tr.innerHTML =
            '<td><input type="radio" name="audio-fmt" value="' + f.id + '"></td>' +
            '<td>' + f.id + '</td>' +
            '<td>' + f.ext + '</td>' +
            '<td>' + f.codec + '</td>' +
            '<td>' + f.abr + '</td>' +
            '<td>' + f.size + '</td>';
        tr.addEventListener('click', function () {
            atBody.querySelectorAll('input').forEach(i => i.checked = false);
            tr.querySelector('input').checked = true;
            selectedAudioFormat = f.id;
        });
        atBody.appendChild(tr);
    });

    loadConfig();
}

async function loadConfig() {
    try {
        const resp = await fetch('/api/config');
        const data = await resp.json();
        document.getElementById('download-dir').value = data.download_directory;
    } catch (e) { }
}

async function updateDir() {
    const dir = document.getElementById('download-dir').value.trim();
    const resp = await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ download_directory: dir })
    });
    const data = await resp.json();
    if (resp.ok) {
        document.getElementById('download-dir').value = data.download_directory;
    } else {
        alert(data.error || '更新失败');
    }
}

function goBack() {
    showSection('input');
    selectedVideoFormat = null;
    selectedAudioFormat = null;
}

async function startDownload() {
    const errorEl = document.getElementById('format-error');
    if (!selectedVideoFormat) {
        errorEl.textContent = '请选择视频流';
        return;
    }
    errorEl.textContent = '';

    const url = document.getElementById('url-input').value.trim();
    const browser = document.getElementById('browser-select').value || null;
    const downloadDir = document.getElementById('download-dir').value.trim();

    try {
        const resp = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url,
                video_format: selectedVideoFormat,
                audio_format: selectedAudioFormat || '',
                browser,
                download_directory: downloadDir
            })
        });
        const data = await resp.json();
        if (!resp.ok) {
            errorEl.textContent = data.error || '启动下载失败';
            return;
        }
        showSection('download');
        document.getElementById('dl-title').textContent = '正在下载: ' + (videoInfoData ? videoInfoData.title : '');
        connectWS(data.task_id);
    } catch (e) {
        errorEl.textContent = '网络错误: ' + e.message;
    }
}

function connectWS(taskId) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(protocol + '//' + location.host + '/ws/download/' + taskId);

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.status === 'downloading') {
            document.getElementById('dl-title').textContent = '正在下载...';
            document.getElementById('progress-fill').style.width = data.progress + '%';
            document.getElementById('progress-text').textContent = data.progress + '%';
            document.getElementById('info-size').textContent = data.total;
            document.getElementById('info-speed').textContent = data.speed;
            document.getElementById('info-downloaded').textContent = data.downloaded;
            document.getElementById('info-eta').textContent = data.eta;
        } else if (data.status === 'merging') {
            document.getElementById('dl-title').textContent = data.message;
            document.getElementById('progress-fill').style.width = '100%';
            document.getElementById('progress-text').textContent = '100%';
        } else if (data.status === 'complete') {
            onDownloadComplete(data.message);
        } else if (data.status === 'error') {
            onDownloadError(data.message);
        }
    };

    ws.onerror = function () {
        onDownloadError('WebSocket 连接失败');
    };
}

function onDownloadComplete(msg) {
    document.getElementById('dl-title').textContent = '下载完成！';
    document.getElementById('progress-fill').style.width = '100%';
    document.getElementById('progress-text').textContent = '100%';
    document.getElementById('dl-message').textContent = msg;
    document.getElementById('dl-message').className = 'dl-message success';
    document.getElementById('dl-actions').style.display = 'flex';
}

function onDownloadError(msg) {
    document.getElementById('dl-title').textContent = '下载失败';
    document.getElementById('dl-message').textContent = '错误: ' + msg;
    document.getElementById('dl-message').className = 'dl-message error';
    document.getElementById('dl-actions').style.display = 'flex';
}

function resetApp() {
    videoInfoData = null;
    selectedVideoFormat = null;
    selectedAudioFormat = null;
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('progress-text').textContent = '0%';
    document.getElementById('info-size').textContent = 'N/A';
    document.getElementById('info-speed').textContent = 'N/A';
    document.getElementById('info-downloaded').textContent = 'N/A';
    document.getElementById('info-eta').textContent = 'N/A';
    document.getElementById('dl-message').textContent = '';
    document.getElementById('dl-message').className = 'dl-message';
    document.getElementById('dl-actions').style.display = 'none';
    document.getElementById('url-input').value = '';
    showSection('input');
}

function openFolder() {
    const dir = document.getElementById('download-dir').value.trim();
    if (dir) {
        window.open('file://' + dir);
    }
}

document.getElementById('url-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') fetchInfo();
});
