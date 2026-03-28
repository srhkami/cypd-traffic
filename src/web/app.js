// ─────────────────── API 工具函式 ───────────────────

async function api(method, path, body) {
  const opts = {method, headers: {'Content-Type': 'application/json'}};
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  return res.json();
}

function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 3000);
}


// ─────────────────── 導覽列切換 ───────────────────

document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.panel).classList.add('active');
  });
});


// ─────────────────── 認證狀態 ───────────────────

async function checkAuth() {
  const el = document.getElementById('auth-status');
  try {
    const res = await api('GET', '/api/auth/status');
    if (res.data && res.data.authenticated) {
      el.textContent = '已認證';
      el.className = 'auth-badge ok';
    } else {
      el.textContent = '未認證';
      el.className = 'auth-badge fail';
    }
  } catch {
    el.textContent = '連線失敗';
    el.className = 'auth-badge fail';
  }
}


// ─────────────────── 案件列表 ───────────────────

async function loadCases() {
  const filter = document.getElementById('case-filter').value;
  const qs = filter ? '?status=' + encodeURIComponent(filter) : '';
  const res = await api('GET', '/api/cases' + qs);
  const tbody = document.getElementById('case-tbody');
  tbody.innerHTML = '';

  if (res.success && res.data) {
    document.getElementById('case-count').textContent = '共 ' + res.data.length + ' 筆案件';
    res.data.forEach(c => {
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + esc(c.number) + '</td>' +
        '<td>' + esc(c.car) + '</td>' +
        '<td>' + esc(c.place) + '</td>' +
        '<td>' + esc(c.content) + '</td>' +
        '<td>' + esc(c.undertaker) + '</td>' +
        '<td>' + esc(c.status) + '</td>' +
        '<td>' + c.input_code + '</td>';
      tbody.appendChild(tr);
    });
  }
}

function esc(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}


// ─────────────────── 背景任務 ───────────────────

async function loadTasks() {
  const res = await api('GET', '/api/tasks');
  const wrap = document.getElementById('task-list');
  wrap.innerHTML = '';

  if (res.success && res.data) {
    if (res.data.length === 0) {
      wrap.innerHTML = '<div class="info-text">目前沒有任務</div>';
      return;
    }
    res.data.slice().reverse().forEach(t => {
      const statusCls = t.status === '執行中' ? 'running' : t.status === '已完成' ? 'completed' : t.status === '失敗' ? 'failed' : '';
      const card = document.createElement('div');
      card.className = 'task-card';
      card.innerHTML =
        '<div class="task-header">' +
          '<span class="task-type">' + esc(t.task_type) + '</span>' +
          '<span class="task-status ' + statusCls + '">' + esc(t.status) + '</span>' +
        '</div>' +
        '<div>' + esc(t.message) + ' (' + t.current + '/' + t.total + ')</div>' +
        '<div class="progress-bar"><div class="fill" style="width:' + t.progress + '%"></div></div>';

      if (t.status === '執行中' || t.status === '待處理') {
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn';
        cancelBtn.style.marginTop = '8px';
        cancelBtn.textContent = '取消';
        cancelBtn.onclick = async () => {
          await api('DELETE', '/api/tasks/' + t.task_id);
          toast('已取消任務');
          loadTasks();
        };
        card.appendChild(cancelBtn);
      }

      wrap.appendChild(card);
    });
  }
}


// ─────────────────── 操作按鈕 ───────────────────

// 爬取
document.getElementById('btn-scrape').onclick = async () => {
  const res = await api('POST', '/api/tasks/scrape', {handle_mode: false});
  toast(res.message);
  if (res.success) autoRefreshTasks();
};

// 分派+爬取
document.getElementById('btn-scrape-assign').onclick = async () => {
  const sel = document.getElementById('undertaker-select');
  if (sel.style.display === 'none') {
    const utRes = await api('GET', '/api/undertakers');
    if (utRes.success && utRes.data) {
      sel.innerHTML = utRes.data.map(u =>
        '<option value="' + u.station_id + '">' + u.unit + ' - ' + u.name + '</option>'
      ).join('');
      sel.style.display = '';
    }
    return;
  }
  const uid = parseInt(sel.value);
  const res = await api('POST', '/api/tasks/scrape', {handle_mode: true, undertaker_id: uid});
  toast(res.message);
  sel.style.display = 'none';
  if (res.success) autoRefreshTasks();
};

// 回覆
document.getElementById('btn-reply-station').onclick = async () => {
  const res = await api('POST', '/api/tasks/reply', {station_mode: true, re_assign: false});
  toast(res.message);
  if (res.success) autoRefreshTasks();
};
document.getElementById('btn-reply-precinct').onclick = async () => {
  const res = await api('POST', '/api/tasks/reply', {station_mode: false, re_assign: true});
  toast(res.message);
  if (res.success) autoRefreshTasks();
};
document.getElementById('btn-reply-precinct-no').onclick = async () => {
  const res = await api('POST', '/api/tasks/reply', {station_mode: false, re_assign: false});
  toast(res.message);
  if (res.success) autoRefreshTasks();
};

// 下載
document.getElementById('btn-download').onclick = async () => {
  const res = await api('POST', '/api/tasks/download');
  toast(res.message);
  if (res.success) autoRefreshTasks();
};

// 匯出
document.getElementById('btn-export').onclick = async () => {
  const filter = document.getElementById('export-filter').value || null;
  const res = await api('POST', '/api/excel/export', {status_filter: filter});
  toast(res.message);
  if (res.success && res.data && res.data.filename) {
    window.open('/api/excel/download/' + encodeURIComponent(res.data.filename));
  }
};

// 匯入
document.getElementById('btn-import').onclick = () => {
  document.getElementById('import-file').click();
};
document.getElementById('import-file').onchange = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/excel/import', {method: 'POST', body: form});
  const data = await res.json();
  toast(data.message);
  e.target.value = '';
};

// 認證
document.getElementById('btn-login').onclick = async () => {
  // 透過 pywebview js_api 開啟認證視窗
  if (window.pywebview && window.pywebview.api) {
    toast('正在開啟內網認證視窗…');
    try {
      const result = await window.pywebview.api.login();
      if (result && result.success) {
        toast('認證成功');
      } else {
        toast(result ? result.message : '認證失敗');
      }
    } catch (e) {
      toast('認證過程發生錯誤：' + e);
    }
    checkAuth();
  } else {
    toast('pywebview API 尚未就緒，請稍候再試');
  }
};
document.getElementById('btn-logout').onclick = async () => {
  await api('POST', '/api/auth/logout');
  checkAuth();
  toast('已登出');
};


// ─────────────────── 設定頁面 ───────────────────

const OPTION_LABELS = {
  check: '安全模式',
  car: '顯示車號',
  article: '顯示法條',
  text_y: '舉發回覆文字',
  text_n: '不舉發回覆文字',
  download_limit: '重下載次數',
};

async function loadSettings() {
  await Promise.all([
    loadOptions(),
    loadUndertakers(),
    loadArticles(),
    loadMigration(),
  ]);
}

async function loadOptions() {
  try {
    const optRes = await api('GET', '/api/options');
    const optForm = document.getElementById('options-form');
    optForm.innerHTML = '';
    if (optRes.success && optRes.data) {
      const opts = optRes.data;
      for (const [key, label] of Object.entries(OPTION_LABELS)) {
        const row = document.createElement('div');
        row.className = 'settings-row';
        const lbl = document.createElement('label');
        lbl.textContent = label;
        row.appendChild(lbl);

        if (key === 'check' || key === 'car' || key === 'article') {
          const sel = document.createElement('select');
          sel.innerHTML = '<option value="開啟">開啟</option><option value="關閉">關閉</option>';
          sel.value = opts[key] ? '開啟' : '關閉';
          sel.onchange = () => api('PUT', '/api/options', {key, value: sel.value}).then(r => toast(r.message));
          row.appendChild(sel);
        } else {
          const inp = document.createElement('input');
          inp.type = 'text';
          inp.value = opts[key] || '';
          inp.onblur = () => api('PUT', '/api/options', {key, value: inp.value}).then(r => toast(r.message));
          row.appendChild(inp);
        }
        optForm.appendChild(row);
      }
    }
  } catch (e) {
    document.getElementById('options-form').innerHTML = '<div class="info-text">載入選項失敗</div>';
  }
}

async function loadUndertakers() {
  try {
    const utRes = await api('GET', '/api/undertakers');
    const utList = document.getElementById('undertaker-list');
    if (utRes.success && utRes.data) {
      let html = '<table><thead><tr><th>代號</th><th>單位</th><th>姓名</th><th>代碼</th><th>操作</th></tr></thead><tbody>';
      utRes.data.forEach(u => {
        html += renderUndertakerRow(u.station_id, u.unit, u.name, u.code);
      });
      html += '</tbody></table>';
      html += '<button class="btn btn-small" id="btn-add-undertaker">新增承辦人</button>';
      utList.innerHTML = html;

      // 綁定新增按鈕
      document.getElementById('btn-add-undertaker').onclick = () => {
        const tbody = utList.querySelector('tbody');
        const tr = document.createElement('tr');
        tr.className = 'new-row';
        tr.innerHTML =
          '<td><input type="number" class="inline-input" data-field="station_id" placeholder="代號"></td>' +
          '<td><input type="text" class="inline-input" data-field="unit" placeholder="單位"></td>' +
          '<td><input type="text" class="inline-input" data-field="name" placeholder="姓名"></td>' +
          '<td><input type="number" class="inline-input" data-field="code" placeholder="代碼"></td>' +
          '<td class="action-cell">' +
            '<button class="btn btn-small btn-save" title="儲存">儲存</button>' +
            '<button class="btn btn-small btn-danger" title="取消">取消</button>' +
          '</td>';
        tbody.appendChild(tr);

        tr.querySelector('.btn-save').onclick = () => saveUndertakerRow(tr, true);
        tr.querySelector('.btn-danger').onclick = () => tr.remove();
      };

      // 綁定每一行的按鈕
      utList.querySelectorAll('tbody tr:not(.new-row)').forEach(bindUndertakerRowEvents);
    }
  } catch (e) {
    document.getElementById('undertaker-list').innerHTML = '<div class="info-text">載入承辦人失敗</div>';
  }
}

function renderUndertakerRow(stationId, unit, name, code) {
  return '<tr data-id="' + stationId + '">' +
    '<td><input type="number" class="inline-input" data-field="station_id" value="' + stationId + '" readonly></td>' +
    '<td><input type="text" class="inline-input" data-field="unit" value="' + esc(unit) + '"></td>' +
    '<td><input type="text" class="inline-input" data-field="name" value="' + esc(name) + '"></td>' +
    '<td><input type="number" class="inline-input" data-field="code" value="' + code + '"></td>' +
    '<td class="action-cell">' +
      '<button class="btn btn-small btn-save" title="儲存">儲存</button>' +
      '<button class="btn btn-small btn-danger" title="刪除">刪除</button>' +
    '</td>' +
  '</tr>';
}

function bindUndertakerRowEvents(tr) {
  tr.querySelector('.btn-save').onclick = () => saveUndertakerRow(tr, false);
  tr.querySelector('.btn-danger').onclick = async () => {
    const id = tr.dataset.id;
    if (!confirm('確定要刪除代號 ' + id + ' 的承辦人？')) return;
    const res = await api('DELETE', '/api/undertakers/' + id);
    toast(res.message);
    if (res.success) loadUndertakers();
  };
}

async function saveUndertakerRow(tr, isNew) {
  const inputs = tr.querySelectorAll('.inline-input');
  const data = {};
  inputs.forEach(inp => { data[inp.dataset.field] = inp.value; });

  if (!data.station_id || !data.unit || !data.name || !data.code) {
    toast('所有欄位皆為必填');
    return;
  }

  const body = {
    station_id: parseInt(data.station_id),
    unit: data.unit,
    name: data.name,
    code: parseInt(data.code),
  };

  const res = await api('POST', '/api/undertakers', body);
  toast(res.message);
  if (res.success) loadUndertakers();
}

async function loadArticles() {
  try {
    const artRes = await api('GET', '/api/articles');
    const artList = document.getElementById('article-list');
    if (artRes.success && artRes.data) {
      let html = '<table><thead><tr><th>簡碼</th><th>代碼</th><th>法條</th><th>操作</th></tr></thead><tbody>';
      artRes.data.forEach(a => {
        html += renderArticleRow(a.input_key, a.code, a.text);
      });
      html += '</tbody></table>';
      html += '<button class="btn btn-small" id="btn-add-article">新增法條</button>';
      artList.innerHTML = html;

      // 綁定新增按鈕
      document.getElementById('btn-add-article').onclick = () => {
        const tbody = artList.querySelector('tbody');
        const tr = document.createElement('tr');
        tr.className = 'new-row';
        tr.innerHTML =
          '<td><input type="number" class="inline-input" data-field="input_key" placeholder="簡碼"></td>' +
          '<td><input type="number" class="inline-input" data-field="code" placeholder="代碼"></td>' +
          '<td><input type="text" class="inline-input inline-input-wide" data-field="text" placeholder="法條內容"></td>' +
          '<td class="action-cell">' +
            '<button class="btn btn-small btn-save" title="儲存">儲存</button>' +
            '<button class="btn btn-small btn-danger" title="取消">取消</button>' +
          '</td>';
        tbody.appendChild(tr);

        tr.querySelector('.btn-save').onclick = () => saveArticleRow(tr, true);
        tr.querySelector('.btn-danger').onclick = () => tr.remove();
      };

      // 綁定每一行的按鈕
      artList.querySelectorAll('tbody tr:not(.new-row)').forEach(bindArticleRowEvents);
    }
  } catch (e) {
    document.getElementById('article-list').innerHTML = '<div class="info-text">載入法條失敗</div>';
  }
}

function renderArticleRow(inputKey, code, text) {
  return '<tr data-id="' + inputKey + '">' +
    '<td><input type="number" class="inline-input" data-field="input_key" value="' + inputKey + '" readonly></td>' +
    '<td><input type="number" class="inline-input" data-field="code" value="' + code + '"></td>' +
    '<td><input type="text" class="inline-input inline-input-wide" data-field="text" value="' + esc(text) + '"></td>' +
    '<td class="action-cell">' +
      '<button class="btn btn-small btn-save" title="儲存">儲存</button>' +
      '<button class="btn btn-small btn-danger" title="刪除">刪除</button>' +
    '</td>' +
  '</tr>';
}

function bindArticleRowEvents(tr) {
  tr.querySelector('.btn-save').onclick = () => saveArticleRow(tr, false);
  tr.querySelector('.btn-danger').onclick = async () => {
    const id = tr.dataset.id;
    if (!confirm('確定要刪除簡碼 ' + id + ' 的法條？')) return;
    const res = await api('DELETE', '/api/articles/' + id);
    toast(res.message);
    if (res.success) loadArticles();
  };
}

async function saveArticleRow(tr, isNew) {
  const inputs = tr.querySelectorAll('.inline-input');
  const data = {};
  inputs.forEach(inp => { data[inp.dataset.field] = inp.value; });

  if (!data.input_key || !data.code || !data.text) {
    toast('所有欄位皆為必填');
    return;
  }

  const body = {
    input_key: parseInt(data.input_key),
    code: parseInt(data.code),
    text: data.text,
  };

  const res = await api('POST', '/api/articles', body);
  toast(res.message);
  if (res.success) loadArticles();
}

async function loadMigration() {
  const section = document.getElementById('migration-section');
  try {
    const res = await api('GET', '/api/excel/migrate/status');
    if (!res.success || !res.data) {
      section.innerHTML = '<div class="info-text">無法取得遷移狀態</div>';
      return;
    }

    const d = res.data;
    if (!d.available) {
      section.innerHTML = '<div class="info-text">未偵測到舊版 Excel 檔案（data/database.xlsx 或 data/setting.xlsx）</div>';
      return;
    }

    let html = '<div class="migration-info">';
    html += '<p>偵測到舊版 Excel 檔案，可將資料遷移至資料庫：</p><ul>';
    if (d.has_database) html += '<li>database.xlsx（案件、法條）</li>';
    if (d.has_setting) html += '<li>setting.xlsx（承辦人、選項）</li>';
    html += '</ul>';
    if (d.cases_count > 0) {
      html += '<p class="migration-warn">目前資料庫已有 ' + d.cases_count + ' 筆案件，遷移將略過重複資料（INSERT OR IGNORE）。</p>';
    }
    html += '<button class="btn btn-primary" id="btn-run-migrate">執行遷移</button>';
    html += '</div>';
    section.innerHTML = html;

    document.getElementById('btn-run-migrate').onclick = async () => {
      if (!confirm('確定要從舊版 Excel 遷移資料至資料庫？')) return;
      const btn = document.getElementById('btn-run-migrate');
      btn.disabled = true;
      btn.textContent = '遷移中…';
      const migRes = await api('POST', '/api/excel/migrate');
      toast(migRes.message);
      if (migRes.success) {
        await loadSettings();
        loadCases();
      } else {
        btn.disabled = false;
        btn.textContent = '執行遷移';
      }
    };
  } catch (e) {
    section.innerHTML = '<div class="info-text">載入遷移狀態失敗</div>';
  }
}


// ─────────────────── 自動重新整理任務 ───────────────────

let taskInterval = null;

function autoRefreshTasks() {
  // 切換到任務面板
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-panel="tasks"]').classList.add('active');
  document.getElementById('panel-tasks').classList.add('active');

  loadTasks();
  if (taskInterval) clearInterval(taskInterval);
  taskInterval = setInterval(loadTasks, 2000);
}


// ─────────────────── 事件綁定 ───────────────────

document.getElementById('btn-refresh-cases').onclick = loadCases;
document.getElementById('btn-refresh-tasks').onclick = loadTasks;
document.getElementById('case-filter').onchange = loadCases;


// ─────────────────── 初始化 ───────────────────

checkAuth();
loadCases();
loadSettings();
