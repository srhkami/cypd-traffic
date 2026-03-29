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
        '<td><a href="#" class="case-link">' + esc(c.number) + '</a></td>' +
        '<td>' + esc(c.car) + '</td>' +
        '<td>' + esc(c.status) + '</td>' +
        '<td>' + c.input_code + '</td>' +
        '<td>' + esc(c.fine || '') + '</td>' +
        '<td>' + esc(c.reject_answer || '') + '</td>';

      // 點擊案號開啟詳情視窗
      tr.querySelector('.case-link').onclick = (e) => {
        e.preventDefault();
        openCaseDetail(c);
      };

      tbody.appendChild(tr);
    });
  }
}

function esc(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}


// ─────────────────── 法條快取 ───────────────────

let _articleCache = null; // { input_key: text }

async function getArticleCache() {
  if (_articleCache) return _articleCache;
  try {
    const res = await api('GET', '/api/articles');
    if (res.success && res.data) {
      _articleCache = {};
      res.data.forEach(a => { _articleCache[a.input_key] = a.text; });
    }
  } catch { /* 忽略 */ }
  return _articleCache || {};
}

/** 設定頁異動法條時清除快取，迫使下次重新取得 */
function invalidateArticleCache() {
  _articleCache = null;
}


// ─────────────────── 案件詳情彈出視窗 ───────────────────

async function openCaseDetail(c) {
  const modal = document.getElementById('case-modal');
  const title = document.getElementById('modal-title');
  const body = document.getElementById('modal-body');

  title.textContent = '案件詳情 - ' + c.number;

  // 預先載入法條快取
  const articles = await getArticleCache();

  // 基本資訊區塊
  const time = c.year_roc + '/' + c.month + '/' + c.day + ' ' + c.hour + ':' + c.minute;
  let html = '<div class="detail-section">';
  html += '<h4>基本資訊</h4>';
  html += '<table class="detail-table">';
  html += '<tr><th>案號</th><td>' + esc(c.number) + '</td></tr>';
  html += '<tr><th>車號</th><td>' + esc(c.car) + '</td></tr>';
  html += '<tr><th>案件網址</th><td><a href="' + esc(c.detail_url) + '" target="_blank" rel="noopener noreferrer" class="case-link">' + esc(c.detail_url) + '</a></td></tr>';
  html += '<tr><th>違規地點</th><td>' + esc(c.place) + '</td></tr>';
  html += '<tr><th>違規內容</th><td class="detail-wrap">' + esc(c.content) + '</td></tr>';
  html += '<tr><th>承辦人</th><td>' + esc(c.undertaker) + '</td></tr>';
  html += '<tr><th>檢舉人</th><td>' + esc(c.sender) + '</td></tr>';
  html += '<tr><th>違規時間</th><td>' + esc(time) + '</td></tr>';
  html += '<tr><th>狀態</th><td>' + esc(c.status) + '</td></tr>';
  html += '</table>';
  html += '</div>';

  // 回填資訊區塊（可編輯）
  const inputCode = c.input_code || 0;
  const articleText = articles[inputCode];
  const hasArticle = articleText !== undefined;

  html += '<div class="detail-section">';
  html += '<h4>回填資訊</h4>';
  html += '<div class="reply-form">';

  html += '<div class="reply-row">';
  html += '<label>簡碼</label>';
  html += '<input type="number" id="modal-input-code" class="reply-input" value="' + inputCode + '">';
  html += '<div id="modal-article-hint" class="article-hint ' + (hasArticle ? 'hint-ok' : (inputCode ? 'hint-warn' : '')) + '">';
  if (hasArticle) {
    html += esc(articleText);
  } else if (inputCode) {
    html += '簡碼不存在於法條對照表中';
  }
  html += '</div>';
  html += '</div>';

  html += '<div class="reply-row">';
  html += '<label>舉發單號</label>';
  html += '<input type="text" id="modal-fine" class="reply-input" value="' + esc(c.fine || '') + '">';
  html += '</div>';

  html += '<div class="reply-row">';
  html += '<label>不舉發理由</label>';
  html += '<input type="text" id="modal-reject-answer" class="reply-input reply-input-wide" value="' + esc(c.reject_answer || '') + '">';
  html += '</div>';

  html += '<div class="reply-actions">';
  html += '<button class="btn btn-save" id="modal-save-reply"' + (inputCode && !hasArticle ? ' disabled' : '') + '>儲存回填</button>';
  html += '</div>';

  html += '</div>';
  html += '</div>';

  // 附件檔案區塊
  html += '<div class="detail-section">';
  html += '<h4>附件檔案</h4>';
  html += '<div id="modal-files" class="file-list"><div class="info-text">載入中…</div></div>';
  html += '</div>';

  body.innerHTML = html;
  modal.classList.remove('hidden');

  // ── 簡碼即時校驗 ──
  const codeInput = document.getElementById('modal-input-code');
  const hintEl = document.getElementById('modal-article-hint');
  const saveBtn = document.getElementById('modal-save-reply');

  codeInput.addEventListener('input', () => {
    const val = parseInt(codeInput.value);
    if (!val && val !== 0) {
      // 空白或非數字：清除提示，允許儲存（簡碼 0 代表未設定）
      hintEl.textContent = '';
      hintEl.className = 'article-hint';
      saveBtn.disabled = false;
      return;
    }
    if (val === 0) {
      hintEl.textContent = '';
      hintEl.className = 'article-hint';
      saveBtn.disabled = false;
      return;
    }
    const text = articles[val];
    if (text !== undefined) {
      hintEl.textContent = text;
      hintEl.className = 'article-hint hint-ok';
      saveBtn.disabled = false;
    } else {
      hintEl.textContent = '簡碼不存在於法條對照表中';
      hintEl.className = 'article-hint hint-warn';
      saveBtn.disabled = true;
    }
  });

  // ── 儲存回填 ──
  saveBtn.onclick = async () => {
    const code = parseInt(codeInput.value) || 0;
    // 雙重防呆：非 0 時必須存在於法條
    if (code !== 0 && articles[code] === undefined) {
      toast('簡碼不存在於法條對照表，無法儲存');
      return;
    }
    const fine = document.getElementById('modal-fine').value || null;
    const rejectAnswer = document.getElementById('modal-reject-answer').value || null;

    saveBtn.disabled = true;
    saveBtn.textContent = '儲存中…';

    const r = await api('PATCH', '/api/cases/' + c.number + '/reply-fields', {
      input_code: code,
      fine: fine,
      reject_answer: rejectAnswer,
    });
    toast(r.message);

    if (r.success) {
      // 同步更新彈窗內的案件資料（供下次操作使用）
      c.input_code = code;
      c.fine = fine;
      c.reject_answer = rejectAnswer;
      // 同步更新列表
      loadCases();
    }

    saveBtn.disabled = false;
    saveBtn.textContent = '儲存回填';
  };

  // 載入檔案列表
  loadCaseFiles(c.number, c.files_json);
}

async function loadCaseFiles(caseNumber, filesJson) {
  const container = document.getElementById('modal-files');

  // 解析原始附件連結
  let fileUrls = [];
  try {
    fileUrls = JSON.parse(filesJson || '[]');
  } catch { fileUrls = []; }

  if (fileUrls.length === 0) {
    container.innerHTML = '<div class="info-text">此案件沒有附件</div>';
    return;
  }

  try {
    // 從 API 取得已下載的檔案清單（僅以案號為路徑）
    const res = await api('GET', '/api/files/' + encodeURIComponent(caseNumber));

    let html = '';

    // 重新下載按鈕（不論是否已下載都顯示）
    html += '<div class="file-actions">';
    if (res.success && res.data && res.data.exists && res.data.files.length > 0) {
      html += '<button class="btn btn-small" id="btn-open-folder">開啟資料夾</button>';
    }
    html += '<button class="btn btn-small" id="btn-redownload">重新下載</button>';
    html += '</div>';

    if (res.success && res.data && res.data.exists && res.data.files.length > 0) {
      // 已下載：顯示可開啟的檔案列表
      res.data.files.forEach(f => {
        const sizeKB = (f.size / 1024).toFixed(1);
        html += '<div class="file-item">';
        html += '<span class="file-name">' + esc(f.name) + '</span>';
        html += '<span class="file-size">' + sizeKB + ' KB</span>';
        html += '<button class="btn btn-small btn-open-file" data-name="' + esc(f.name) + '">開啟</button>';
        html += '</div>';
      });
    } else {
      // 尚未下載：顯示原始連結檔名
      html += '<div class="info-text">檔案尚未下載</div>';
      fileUrls.forEach(url => {
        const fileName = url.split('/').pop() || url;
        html += '<div class="file-item file-item-pending">';
        html += '<span class="file-name">' + esc(fileName) + '</span>';
        html += '<span class="file-status">未下載</span>';
        html += '</div>';
      });
    }

    container.innerHTML = html;

    // 綁定開啟資料夾按鈕
    const folderBtn = container.querySelector('#btn-open-folder');
    if (folderBtn) {
      folderBtn.onclick = async () => {
        const r = await api('POST', '/api/files/open-folder', { case_number: caseNumber });
        toast(r.message);
      };
    }

    // 綁定重新下載按鈕
    const redownloadBtn = container.querySelector('#btn-redownload');
    if (redownloadBtn) {
      redownloadBtn.onclick = async () => {
        redownloadBtn.disabled = true;
        redownloadBtn.textContent = '下載中…';
        try {
          const r = await api('POST', '/api/tasks/download/' + encodeURIComponent(caseNumber));
          toast(r.message);
          if (r.success) {
            // 等待下載完成後重新載入檔案列表
            const taskId = r.data && r.data.task_id;
            if (taskId) {
              await waitForTask(taskId);
            }
            toast('下載完成，已重新載入檔案列表');
            loadCaseFiles(caseNumber, filesJson);
          } else {
            redownloadBtn.disabled = false;
            redownloadBtn.textContent = '重新下載';
          }
        } catch (e) {
          toast('下載請求失敗：' + e);
          redownloadBtn.disabled = false;
          redownloadBtn.textContent = '重新下載';
        }
      };
    }

    // 綁定每個檔案的開啟按鈕
    container.querySelectorAll('.btn-open-file').forEach(btn => {
      btn.onclick = async () => {
        const fileName = btn.dataset.name;
        const r = await api('POST', '/api/files/open', { case_number: caseNumber, file_name: fileName });
        toast(r.message);
      };
    });
  } catch (e) {
    container.innerHTML = '<div class="info-text">載入檔案清單失敗</div>';
  }
}

async function waitForTask(taskId) {
  // 等待背景任務完成（最長等待 120 秒）
  for (let i = 0; i < 120; i++) {
    await new Promise(r => setTimeout(r, 1000));
    try {
      const res = await api('GET', '/api/tasks');
      if (res.success && res.data) {
        const task = res.data.find(t => t.task_id === taskId);
        if (!task || task.status === '已完成' || task.status === '失敗' || task.status === '已取消') {
          return;
        }
      }
    } catch { return; }
  }
}

// 關閉 Modal
document.getElementById('modal-close').onclick = () => {
  document.getElementById('case-modal').classList.add('hidden');
};
document.getElementById('case-modal').onclick = (e) => {
  if (e.target === e.currentTarget) {
    e.currentTarget.classList.add('hidden');
  }
};


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

      // 執行中或待處理：顯示取消按鈕
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

      // 任務結果明細（已完成/失敗/已取消且有結果時顯示）
      if (t.results && t.results.length > 0 && t.status !== '執行中' && t.status !== '待處理') {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'btn btn-small task-results-toggle';
        toggleBtn.textContent = '展開結果（' + t.results.length + ' 筆）';
        toggleBtn.style.marginTop = '8px';

        const resultsDiv = document.createElement('div');
        resultsDiv.className = 'task-results hidden';

        let tbl = '<table class="task-results-table"><thead><tr><th>案號</th><th>動作</th><th>結果</th><th>原因</th></tr></thead><tbody>';
        t.results.forEach(r => {
          const cls = r.success ? 'result-ok' : 'result-fail';
          tbl += '<tr class="' + cls + '">' +
            '<td>' + esc(r.number || '') + '</td>' +
            '<td>' + esc(r.action || '') + '</td>' +
            '<td>' + (r.success ? '成功' : '失敗') + '</td>' +
            '<td>' + esc(r.reason || '') + '</td>' +
          '</tr>';
        });
        tbl += '</tbody></table>';
        resultsDiv.innerHTML = tbl;

        toggleBtn.onclick = () => {
          const isHidden = resultsDiv.classList.contains('hidden');
          resultsDiv.classList.toggle('hidden');
          toggleBtn.textContent = isHidden
            ? '收合結果（' + t.results.length + ' 筆）'
            : '展開結果（' + t.results.length + ' 筆）';
        };

        card.appendChild(toggleBtn);
        card.appendChild(resultsDiv);
      }

      wrap.appendChild(card);
    });

    // 問題 5 修復：若所有任務都已結束，停止自動輪詢
    if (taskInterval && res.data.every(t => t.status !== '執行中' && t.status !== '待處理')) {
      clearInterval(taskInterval);
      taskInterval = null;
      loadCases();
    }
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
          if (key === 'check') {
            const hint = document.createElement('span');
            hint.textContent = '（僅適用於 CLI 模式）';
            hint.style.cssText = 'font-size:12px;color:#636e72;margin-left:8px;';
            row.appendChild(hint);
          }
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
    if (res.success) {
      invalidateArticleCache();
      loadArticles();
    }
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
  if (res.success) {
    invalidateArticleCache();
    loadArticles();
  }
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

async function loadVersion() {
  try {
    const res = await api('GET', '/api/version');
    if (res.success && res.data && res.data.version) {
      document.getElementById('app-version').textContent = 'v' + res.data.version;
    }
  } catch { /* 版本取得失敗不影響功能 */ }
}

checkAuth();
loadCases();
loadSettings();
loadVersion();
