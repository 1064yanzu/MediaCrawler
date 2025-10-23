// MediaCrawler Control Panel

const API_BASE = '/api';

const state = {
  platforms: [],
  selectedPlatform: null,
  crawlerStatus: null,
  checkpoints: [],
  dataFiles: [],
  activeDataTab: 'json'
};

// Utility Functions
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

const formatDateTime = (timestamp) => {
  if (!timestamp) return '-';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

const showToast = (message, type = 'info') => {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('active'));
  setTimeout(() => {
    toast.classList.remove('active');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
};

const updateStatusText = () => {
  const indicator = document.getElementById('statusIndicator');
  const statusText = document.getElementById('statusText');
  const statusBadge = document.getElementById('crawlerStatusBadge');
  const startTime = document.getElementById('startTime');
  const notesCount = document.getElementById('notesCount');
  const commentsCount = document.getElementById('commentsCount');
  const progressBar = document.getElementById('progressBar');

  if (!state.crawlerStatus) return;

  const { running, progress, start_time, error } = state.crawlerStatus;
  indicator.textContent = running ? '运行中' : '未运行';
  indicator.classList.toggle('active', running);
  statusText.textContent = running ? '运行中' : '空闲';
  startTime.textContent = start_time ? formatDateTime(start_time) : '-';
  notesCount.textContent = progress?.notes_crawled ?? 0;
  commentsCount.textContent = progress?.comments_crawled ?? 0;

  const progressValue = progress?.total
    ? Math.min(100, Math.round((progress.current / progress.total) * 100))
    : 0;
  progressBar.style.width = `${progressValue}%`;

  statusBadge.classList.toggle('running', running);
  statusBadge.querySelector('span:last-child').textContent = running ? '运行中' : '准备就绪';

  if (error) {
    addLog(`错误: ${error}`, 'error');
  }
};

const addLog = (message, type = 'info') => {
  const logViewer = document.getElementById('logViewer');
  const entry = document.createElement('div');
  entry.className = `log-entry ${type === 'error' ? '--error' : type === 'success' ? '--success' : ''}`;
  entry.textContent = `${formatDateTime(Date.now())} - ${message}`;
  logViewer.appendChild(entry);
  logViewer.scrollTop = logViewer.scrollHeight;
};

const renderPlatforms = () => {
  const container = document.getElementById('platformOptions');
  container.innerHTML = '';

  state.platforms.forEach((platform) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'platform-btn';
    if (platform.id === state.selectedPlatform) button.classList.add('active');

    button.innerHTML = `
      <span class="icon">${platform.icon}</span>
      <span>${platform.name}</span>
    `;

    button.addEventListener('click', () => {
      state.selectedPlatform = platform.id;
      renderPlatforms();
    });

    container.appendChild(button);
  });
};

const renderCheckpoints = () => {
  const container = document.getElementById('checkpointList');
  const template = document.getElementById('checkpointTemplate');

  container.innerHTML = '';

  if (!state.checkpoints.length) {
    const empty = document.createElement('div');
    empty.className = 'checkpoint-empty';
    empty.textContent = '暂无检查点记录';
    container.appendChild(empty);
    return;
  }

  state.checkpoints.forEach((checkpoint) => {
    const clone = template.content.cloneNode(true);
    clone.querySelector('.checkpoint-id').textContent = checkpoint.id;
    clone.querySelector('.checkpoint-meta').textContent = `${checkpoint.platform} · ${formatDateTime(checkpoint.timestamp)}`;

    clone.querySelector('[data-action="resume"]').addEventListener('click', () => {
      resumeCrawler(checkpoint.id);
    });

    clone.querySelector('[data-action="download"]').addEventListener('click', () => {
      window.open(`/api/data/download/${checkpoint.file}`);
    });

    container.appendChild(clone);
  });
};

const renderDataTable = () => {
  const container = document.getElementById('dataTable');
  const template = document.getElementById('dataRowTemplate');

  const filteredFiles = state.dataFiles.filter((file) => file.type === state.activeDataTab);
  container.innerHTML = '';

  if (!filteredFiles.length) {
    const empty = document.createElement('div');
    empty.className = 'data-empty';
    empty.textContent = '暂无数据文件';
    container.appendChild(empty);
    return;
  }

  filteredFiles.forEach((file) => {
    const clone = template.content.cloneNode(true);
    clone.querySelector('.file-name').textContent = file.name;
    clone.querySelector('.file-size').textContent = formatBytes(file.size);
    clone.querySelector('.file-time').textContent = formatDateTime(file.modified);

    const actions = clone.querySelector('.file-actions');
    actions.querySelector('[data-action="preview"]').addEventListener('click', () => previewData(file.name));
    actions.querySelector('[data-action="download"]').addEventListener('click', () => window.open(`/api/data/download/${file.name}`));
    actions.querySelector('[data-action="delete"]').addEventListener('click', () => deleteData(file.name));

    container.appendChild(clone);
  });
};

// API Calls
const api = async (endpoint, options = {}) => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || '请求失败');
  }

  if (response.status === 204) return null;
  return response.json();
};

const fetchPlatforms = async () => {
  try {
    const data = await api('/platforms');
    state.platforms = data.platforms;
    state.selectedPlatform = state.selectedPlatform || data.platforms[0]?.id;
    renderPlatforms();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

const fetchStatus = async () => {
  try {
    state.crawlerStatus = await api('/crawler/status');
    updateStatusText();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

const fetchCheckpoints = async () => {
  try {
    const data = await api('/checkpoints');
    state.checkpoints = data.checkpoints;
    renderCheckpoints();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

const fetchDataFiles = async () => {
  try {
    const data = await api('/data/files');
    state.dataFiles = data.files;
    renderDataTable();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

const startCrawler = async (config) => {
  try {
    await api('/crawler/start', {
      method: 'POST',
      body: JSON.stringify(config)
    });
    showToast('爬虫任务已启动', 'success');
    addLog(`任务启动: ${config.platform} / ${config.crawler_type}`);
    await fetchStatus();
  } catch (err) {
    showToast(err.message, 'error');
    addLog(`任务启动失败: ${err.message}`, 'error');
  }
};

const stopCrawler = async () => {
  try {
    const data = await api('/crawler/stop', { method: 'POST' });
    showToast('爬虫任务已停止', 'info');
    addLog('任务已停止');
    if (data.checkpoint) {
      addLog(`已创建检查点: ${data.checkpoint}`, 'success');
    }
    await Promise.all([fetchStatus(), fetchCheckpoints()]);
  } catch (err) {
    showToast(err.message, 'error');
    addLog(`停止任务失败: ${err.message}`, 'error');
  }
};

const resumeCrawler = async (checkpointId) => {
  try {
    await api('/crawler/resume', {
      method: 'POST',
      body: JSON.stringify({ checkpoint_id: checkpointId })
    });
    showToast(`已从检查点恢复: ${checkpointId}`, 'success');
    addLog(`从检查点恢复: ${checkpointId}`);
    await fetchStatus();
  } catch (err) {
    showToast(err.message, 'error');
    addLog(`恢复失败: ${err.message}`, 'error');
  }
};

const previewData = async (filename) => {
  try {
    const data = await api(`/data/preview/${encodeURIComponent(filename)}`);
    const modal = document.getElementById('previewModal');
    const content = document.getElementById('modalContent');

    content.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    modal.classList.add('active');
  } catch (err) {
    showToast(err.message, 'error');
  }
};

const deleteData = async (filename) => {
  if (!confirm(`确定要删除 ${filename} 吗？`)) return;

  try {
    await api(`/data/delete/${encodeURIComponent(filename)}`, { method: 'DELETE' });
    showToast('文件已删除', 'info');
    addLog(`删除数据文件: ${filename}`);
    await fetchDataFiles();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Event Handlers
const initEventListeners = () => {
  const form = document.getElementById('crawlerForm');
  const refreshStatusBtn = document.getElementById('refreshStatusBtn');
  const stopCrawlerBtn = document.getElementById('stopCrawlerBtn');
  const tabs = document.querySelectorAll('.tab');
  const modal = document.getElementById('previewModal');
  const modalMask = document.getElementById('modalMask');
  const modalCloseBtn = document.getElementById('modalCloseBtn');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const config = Object.fromEntries(formData.entries());

    const booleanFields = ['enable_comments', 'enable_sub_comments', 'enable_resume', 'headless'];
    booleanFields.forEach((field) => (config[field] = formData.get(field) === 'on'));

    config.platform = state.selectedPlatform;
    config.max_notes = Number(config.max_notes);
    config.max_comments = Number(config.max_comments);

    if (!config.platform) {
      showToast('请选择平台', 'warning');
      return;
    }

    await startCrawler(config);
  });

  refreshStatusBtn.addEventListener('click', () => {
    fetchStatus();
    fetchCheckpoints();
    fetchDataFiles();
    showToast('状态已刷新');
  });

  stopCrawlerBtn.addEventListener('click', stopCrawler);

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      state.activeDataTab = tab.dataset.type;
      renderDataTable();
    });
  });

  const closeModal = () => modal.classList.remove('active');
  modalCloseBtn.addEventListener('click', closeModal);
  modalMask.addEventListener('click', closeModal);

  // Auto refresh status every 10 seconds
  setInterval(fetchStatus, 10000);
};

// Initialize Application
const init = async () => {
  await Promise.all([fetchPlatforms(), fetchStatus(), fetchCheckpoints(), fetchDataFiles()]);
  initEventListeners();
  addLog('欢迎使用 MediaCrawler 控制面板');
};

window.addEventListener('DOMContentLoaded', init);
