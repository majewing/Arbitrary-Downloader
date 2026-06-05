let videoInfoData = null;
let selectedVideoFormat = null;
let selectedAudioFormat = null;
let selectedBrowser = '';
let currentPage = 1;
const PAGE_SIZE = 20;

/* === Navigation === */

function switchPage(page) {
    document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
    document.getElementById('page-' + page).classList.add('active');
    document.querySelectorAll('.nav-link').forEach(function(n) { n.classList.remove('active'); });
    document.querySelector('.nav-link[data-page="' + page + '"]').classList.add('active');
    var main = document.querySelector('.main');
    if (page === 'history') {
        main.classList.add('main-wide');
        loadHistory(1);
    } else {
        main.classList.remove('main-wide');
    }
}

function showSection(id) {
    document.querySelectorAll('.section').forEach(function(s) { s.classList.remove('active'); });
    document.getElementById('section-' + id).classList.add('active');
}

/* === Pill Selector === */

function selectPill(el) {
    el.parentElement.querySelectorAll('.pill').forEach(function(p) { p.classList.remove('active'); });
    el.classList.add('active');
    selectedBrowser = el.dataset.browser || '';
}

/* === URL Input === */

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('url-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') fetchInfo();
    });
    document.getElementById('url-input').focus();
});

/* === Fetch Video Info === */

async function fetchInfo() {
    var url = document.getElementById('url-input').value.trim();
    var errorEl = document.getElementById('fetch-error');
    var btn = document.getElementById('fetch-btn');

    if (!url) {
        errorEl.textContent = '请输入视频链接';
        document.getElementById('url-input').focus();
        return;
    }
    errorEl.textContent = '';
    btn.disabled = true;
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;flex-shrink:0;animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>解析中...';

    try {
        var resp = await fetch('/api/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, browser: selectedBrowser || null })
        });
        var data = await resp.json();
        if (!resp.ok) {
            errorEl.textContent = data.error || '获取失败';
            resetFetchBtn();
            return;
        }
        videoInfoData = data;
        renderFormatPage(data);
        showSection('format');
    } catch (e) {
        errorEl.textContent = '网络错误: ' + e.message;
    } finally {
        resetFetchBtn();
    }
}

function resetFetchBtn() {
    var btn = document.getElementById('fetch-btn');
    btn.disabled = false;
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>解析视频';
}

/* === Format Page === */

function renderFormatPage(data) {
    document.getElementById('video-title').textContent = data.title;
    document.getElementById('video-meta').textContent = data.uploader + '  ·  ' + data.duration;

    var vtBody = document.querySelector('#video-table tbody');
    vtBody.innerHTML = '';
    var noVideo = document.getElementById('no-video');

    if (data.video_formats && data.video_formats.length > 0) {
        noVideo.style.display = 'none';
        document.querySelector('#video-table').style.display = '';
        data.video_formats.forEach(function(f) {
            var tr = document.createElement('tr');
            tr.dataset.formatId = f.id;
            var note = f.has_audio ? '<span class="badge">含音频</span>' : '';
            tr.innerHTML =
                '<td>' + esc(f.id) + '</td>' +
                '<td>' + esc(f.resolution) + '</td>' +
                '<td>' + esc(f.ext) + '</td>' +
                '<td>' + esc(f.codec) + '</td>' +
                '<td>' + esc(f.fps) + '</td>' +
                '<td>' + esc(f.size) + '</td>' +
                '<td>' + note + '</td>';
            tr.addEventListener('click', function() { selectRow('video-table', tr, f.id); });
            vtBody.appendChild(tr);
        });
    } else {
        document.querySelector('#video-table').style.display = 'none';
        noVideo.style.display = '';
    }

    var atBody = document.querySelector('#audio-table tbody');
    atBody.innerHTML = '';
    var noAudio = document.getElementById('no-audio');

    if (data.audio_formats && data.audio_formats.length > 0) {
        noAudio.style.display = 'none';
        document.querySelector('#audio-table').style.display = '';
        data.audio_formats.forEach(function(f) {
            var tr = document.createElement('tr');
            tr.dataset.formatId = f.id;
            tr.innerHTML =
                '<td>' + esc(f.id) + '</td>' +
                '<td>' + esc(f.ext) + '</td>' +
                '<td>' + esc(f.codec) + '</td>' +
                '<td>' + esc(f.abr) + '</td>' +
                '<td>' + esc(f.size) + '</td>';
            tr.addEventListener('click', function() { selectRow('audio-table', tr, f.id); });
            atBody.appendChild(tr);
        });
    } else {
        document.querySelector('#audio-table').style.display = 'none';
        noAudio.style.display = '';
    }

    loadConfig();
}

function selectRow(tableId, tr, formatId) {
    var tbody = tr.parentElement;
    tbody.querySelectorAll('tr').forEach(function(r) { r.classList.remove('selected'); });
    tr.classList.add('selected');
    if (tableId === 'video-table') {
        selectedVideoFormat = formatId;
    } else {
        selectedAudioFormat = formatId;
    }
}

/* === Config === */

async function loadConfig() {
    try {
        var resp = await fetch('/api/config');
        var data = await resp.json();
        document.getElementById('download-dir').value = data.download_directory;
    } catch (e) { }
}

async function updateDir() {
    var dir = document.getElementById('download-dir').value.trim();
    var resp = await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ download_directory: dir })
    });
    var data = await resp.json();
    if (resp.ok) {
        document.getElementById('download-dir').value = data.download_directory;
    } else {
        alert(data.error || '更新失败');
    }
}

/* === Download === */

function goBack() {
    showSection('input');
    selectedVideoFormat = null;
    selectedAudioFormat = null;
}

async function startDownload() {
    var errorEl = document.getElementById('format-error');
    if (!selectedVideoFormat) {
        errorEl.textContent = '请选择视频流';
        return;
    }
    errorEl.textContent = '';

    var url = document.getElementById('url-input').value.trim();
    var downloadDir = document.getElementById('download-dir').value.trim();

    try {
        var resp = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                video_format: selectedVideoFormat,
                audio_format: selectedAudioFormat || '',
                browser: selectedBrowser || null,
                download_directory: downloadDir,
                title: videoInfoData ? videoInfoData.title : '',
                uploader: videoInfoData ? videoInfoData.uploader : '',
                thumbnail: videoInfoData ? videoInfoData.thumbnail : '',
                duration: videoInfoData ? videoInfoData.duration : ''
            })
        });
        var data = await resp.json();
        if (!resp.ok) {
            errorEl.textContent = data.error || '启动下载失败';
            return;
        }
        showSection('download');
        document.getElementById('dl-title').textContent = '正在下载: ' + (videoInfoData ? videoInfoData.title : '');
        document.getElementById('dl-actions').style.display = 'none';
        document.getElementById('dl-message').textContent = '';
        document.getElementById('dl-message').className = 'dl-message';
        connectWS(data.task_id);
    } catch (e) {
        errorEl.textContent = '网络错误: ' + e.message;
    }
}

function connectWS(taskId) {
    var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    var ws = new WebSocket(protocol + '//' + location.host + '/ws/download/' + taskId);

    ws.onmessage = function(event) {
        var data = JSON.parse(event.data);
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
            document.getElementById('progress-fill').classList.add('complete');
            document.getElementById('progress-text').textContent = '100%';
        } else if (data.status === 'complete') {
            onDownloadComplete(data.message);
        } else if (data.status === 'error') {
            onDownloadError(data.message);
        }
    };

    ws.onerror = function() {
        onDownloadError('连接失败');
    };
}

function onDownloadComplete(msg) {
    document.getElementById('dl-title').textContent = '下载完成';
    document.getElementById('progress-fill').style.width = '100%';
    document.getElementById('progress-fill').classList.add('complete');
    document.getElementById('progress-text').textContent = '100%';
    document.getElementById('dl-message').textContent = msg;
    document.getElementById('dl-message').className = 'dl-message success';
    document.getElementById('dl-actions').style.display = 'flex';
}

function onDownloadError(msg) {
    document.getElementById('dl-title').textContent = '下载失败';
    document.getElementById('dl-message').textContent = msg;
    document.getElementById('dl-message').className = 'dl-message error';
    document.getElementById('dl-actions').style.display = 'flex';
}

function resetApp() {
    videoInfoData = null;
    selectedVideoFormat = null;
    selectedAudioFormat = null;
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('progress-fill').classList.remove('complete');
    document.getElementById('progress-text').textContent = '0%';
    document.getElementById('info-size').textContent = '—';
    document.getElementById('info-speed').textContent = '—';
    document.getElementById('info-downloaded').textContent = '—';
    document.getElementById('info-eta').textContent = '—';
    document.getElementById('dl-message').textContent = '';
    document.getElementById('dl-message').className = 'dl-message';
    document.getElementById('dl-actions').style.display = 'none';
    document.getElementById('url-input').value = '';
    document.getElementById('url-input').focus();
    showSection('input');
}

function openFolder() {
    var dir = document.getElementById('download-dir').value.trim();
    if (dir) {
        window.open('file://' + dir);
    }
}

/* === History === */

async function loadHistory(page) {
    if (page < 1) page = 1;
    currentPage = page;
    try {
        var resp = await fetch('/api/history?page=' + page + '&size=' + PAGE_SIZE);
        var data = await resp.json();
        renderHistory(data);
    } catch (e) {
        document.getElementById('history-list').innerHTML = '<div class="empty-state">加载失败</div>';
    }
}

function renderHistory(data) {
    var list = document.getElementById('history-list');
    var pagination = document.getElementById('history-pagination');

    if (!data.items || data.items.length === 0) {
        list.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><div>暂无下载记录</div></div>';
        pagination.style.display = 'none';
        return;
    }

    var html = '';
    data.items.forEach(function(item) {
        var dotClass = item.status === 'success' ? 'success' : 'failed';
        var statusText = item.status === 'success' ? '成功' : '失败';
        var time = relativeTime(item.created_at);
        var fmt = '';
        if (item.video_format) fmt = item.video_format;
        if (item.audio_format) fmt += '+' + item.audio_format;

        html += '<div class="history-item">' +
            '<div class="history-dot ' + dotClass + '"></div>' +
            '<div class="history-content">' +
                '<div class="history-item-title">' + esc(item.title || item.url) + '</div>' +
                '<div class="history-item-meta">' +
                    '<span>' + time + '</span>' +
                    (fmt ? '<span class="badge">' + esc(fmt) + '</span>' : '') +
                    '<span>' + statusText + '</span>' +
                '</div>' +
            '</div>' +
            '<div class="history-actions">' +
                '<button class="btn-icon" title="重新下载" onclick="redownload(\'' + escAttr(item.url) + '\')">' +
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>' +
                '</button>' +
                '<button class="btn-icon" title="删除" onclick="deleteHistoryItem(' + item.id + ')">' +
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>' +
                '</button>' +
            '</div>' +
        '</div>';
    });
    list.innerHTML = html;

    var totalPages = Math.ceil(data.total / PAGE_SIZE);
    if (totalPages > 1) {
        pagination.style.display = 'flex';
        document.getElementById('history-prev').disabled = (currentPage <= 1);
        document.getElementById('history-next').disabled = (currentPage >= totalPages);
        document.getElementById('history-page-info').textContent = currentPage + ' / ' + totalPages;
    } else {
        pagination.style.display = 'none';
    }
}

function redownload(url) {
    switchPage('download');
    showSection('input');
    document.getElementById('url-input').value = url;
    document.getElementById('url-input').focus();
}

async function deleteHistoryItem(id) {
    if (!confirm('确定删除这条记录？')) return;
    await fetch('/api/history/' + id, { method: 'DELETE' });
    loadHistory(currentPage);
}

async function clearAllHistory() {
    if (!confirm('确定清空所有下载记录？')) return;
    await fetch('/api/history', { method: 'DELETE' });
    loadHistory(1);
}

/* === Utilities === */

function relativeTime(isoStr) {
    if (!isoStr) return '';
    var now = Date.now();
    var then = new Date(isoStr).getTime();
    if (isNaN(then)) return isoStr;
    var diff = Math.floor((now - then) / 1000);
    if (diff < 60) return '刚刚';
    if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前';
    if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前';
    if (diff < 604800) return Math.floor(diff / 86400) + ' 天前';
    return isoStr.replace('T', ' ').substring(0, 16);
}

function esc(text) {
    if (!text) return '';
    var d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

function escAttr(text) {
    if (!text) return '';
    return text.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}
