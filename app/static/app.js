/** Select a view without changing the persisted task list. */
export function selectTodos(todos, filter, query, sort) {
  const needle = query.trim().toLocaleLowerCase();
  return todos.filter(todo =>
    (filter === 'all' || todo.done === (filter === 'completed')) &&
    todo.title.toLocaleLowerCase().includes(needle)
  ).sort((a, b) => sort === 'title'
    ? a.title.localeCompare(b.title, 'zh-Hant') || a.id - b.id
    : sort === 'oldest' ? a.id - b.id : b.id - a.id);
}

/** Derive progress from the full list, including an empty database. */
export function summarize(todos) {
  const completed = todos.filter(todo => todo.done).length;
  return { total: todos.length, active: todos.length - completed, completed,
    percentage: todos.length ? Math.round(completed / todos.length * 100) : 0 };
}

/** SQLite stores the application's UTC timestamps without a timezone suffix. */
export function taskDate(value) {
  return new Date(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
}

/** Check every API response; never retry a write automatically. */
export async function request(path, method = 'GET', payload) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    let response;
    try {
      response = await fetch(path, {
        method, signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
        ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
      });
    } catch {
      throw new Error('連線中斷或逾時，請檢查伺服器。若剛才有儲存或刪除，請先重新整理確認結果再試。');
    }
    if (!response.ok) {
      if (response.status === 422) throw new Error('請輸入 1–200 字的標題，不可只有空白。');
      if (response.status === 404) throw new Error('這筆待辦已不存在，請重新整理清單。');
      throw new Error(`操作失敗（${response.status}），請稍後重新整理確認結果。`);
    }
    if (response.status === 204) return null;
    try {
      return await response.json();
    } catch {
      throw new Error('無法讀取伺服器回應，請重新整理確認結果。');
    }
  } finally {
    clearTimeout(timeout);
  }
}

/** Connect the accessible page controls to the persistent API. */
function initialize() {
  const $ = selector => document.querySelector(selector);
  const state = {
    todos: [], filter: 'all', loaded: false, busy: false, selected: null, focusedControl: null,
  };
  const dateFormat = new Intl.DateTimeFormat('zh-TW', { month: 'short', day: 'numeric' });
  const today = new Date();
  $('#today').dateTime = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  $('#today').textContent = new Intl.DateTimeFormat('zh-TW', {
    year: 'numeric', month: 'long', day: 'numeric', weekday: 'long',
  }).format(today);

  function message(text, target = '#error') {
    $(target).textContent = text;
    $(target).hidden = !text;
  }

  function setBusy(busy) {
    // Disabling the active control can move browser focus to the body.
    if (busy) state.focusedControl = document.activeElement;
    state.busy = busy;
    document.querySelectorAll('button, input, select').forEach(control => {
      control.disabled = busy;
    });
    // Do not allow writes against a list that has never loaded successfully.
    $('#add-button').disabled = busy || !state.loaded;
    $('#title').disabled = busy || !state.loaded;
    $('#list').setAttribute('aria-busy', String(busy));
    if (!busy) {
      const previous = state.focusedControl;
      const target = previous?.id ? document.getElementById(previous.id) || $('#title') : previous;
      if (target?.isConnected && !target.disabled) target.focus({ preventScroll: true });
      state.focusedControl = null;
    }
  }

  function render() {
    const focusedId = document.activeElement?.id;
    const summary = summarize(state.todos);
    for (const key of ['total', 'active', 'completed']) {
      $(`#${key}`).textContent = state.loaded ? summary[key] : '—';
    }
    $('#percentage').textContent = state.loaded ? `${summary.percentage}%` : '—';
    $('#progress').value = summary.percentage;
    $('#count-all').textContent = summary.total;
    $('#count-active').textContent = summary.active;
    $('#count-completed').textContent = summary.completed;
    document.querySelectorAll('[data-filter]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.filter === state.filter));
    });
    const visible = selectTodos(state.todos, state.filter, $('#search').value, $('#sort').value);
    $('#result-count').textContent = state.loaded ? `顯示 ${visible.length} 筆，共 ${summary.total} 筆` : '等待載入';
    $('#list').replaceChildren(...visible.map(createRow));
    $('#empty').hidden = !state.loaded || visible.length > 0;
    const isNew = state.todos.length === 0 && !$('#search').value.trim() && state.filter === 'all';
    $('#empty-title').textContent = isNew ? '從一件小事開始' : '這裡暫時沒有待辦';
    $('#empty-description').textContent = isNew
      ? '新增第一筆待辦，為今天留下一個清楚的起點。'
      : '試試其他狀態，或調整搜尋文字。';
    if (focusedId && !document.querySelector('dialog[open]')) {
      (document.getElementById(focusedId) || $('#title')).focus();
    }
  }

  function createRow(todo) {
    const row = document.createElement('li');
    row.className = `task${todo.done ? ' done' : ''}`;
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `complete-${todo.id}`;
    checkbox.checked = todo.done;
    checkbox.disabled = state.busy;
    checkbox.setAttribute('aria-label', `${todo.done ? '標為未完成' : '標為完成'}：${todo.title}`);
    checkbox.addEventListener('change', () => toggle(todo, checkbox));
    const copy = document.createElement('div');
    copy.className = 'task-copy';
    const title = document.createElement('label');
    title.className = 'task-title';
    title.htmlFor = checkbox.id;
    // User content is always text, never interpreted as HTML.
    title.textContent = todo.title;
    const date = document.createElement('time');
    date.className = 'task-date';
    const created = taskDate(todo.created_at);
    if (!Number.isNaN(created.getTime())) {
      date.dateTime = created.toISOString();
      date.textContent = `${dateFormat.format(created)} 新增`;
      date.title = created.toLocaleString('zh-TW');
    }
    copy.append(title, date);
    const actions = document.createElement('div');
    actions.className = 'task-actions';
    for (const [action, label] of [['edit', '編輯'], ['delete', '刪除']]) {
      const button = document.createElement('button');
      button.type = 'button';
      button.id = `${action}-${todo.id}`;
      button.className = action;
      button.textContent = label;
      button.disabled = state.busy;
      button.setAttribute('aria-label', `${label}：${todo.title}`);
      button.addEventListener('click', () => openDialog(action, todo));
      actions.append(button);
    }
    row.append(checkbox, copy, actions);
    return row;
  }

  async function load() {
    if (state.busy) return;
    setBusy(true);
    message('');
    $('#status').textContent = '正在載入待辦…';
    try {
      state.todos = await request('/todos');
      state.loaded = true;
      render();
      $('#status').textContent = '清單已更新。';
      $('#saved-state').textContent = '已與伺服器同步';
    } catch (error) {
      message(error.message);
      $('#status').textContent = state.loaded ? '保留上次載入的清單。' : '載入失敗，請按「重新整理」重試。';
      $('#saved-state').textContent = '尚未同步';
    } finally {
      setBusy(false);
    }
  }

  async function mutate(operation, success, target = '#error') {
    if (state.busy || !state.loaded) return false;
    message('');
    message('', target);
    setBusy(true);
    $('#status').textContent = '正在儲存…';
    try {
      await operation();
      $('#status').textContent = success;
      $('#saved-state').textContent = '變更已儲存';
      return true;
    } catch (error) {
      message(error.message, target);
      $('#status').textContent = '操作未確認，請查看錯誤訊息。';
      $('#saved-state').textContent = '請確認操作結果';
      return false;
    } finally {
      setBusy(false);
    }
  }

  function replaceTask(saved) {
    state.todos = state.todos.map(todo => todo.id === saved.id ? saved : todo);
  }

  async function toggle(todo, checkbox) {
    const updated = await mutate(async () => {
      replaceTask(await request(`/todos/${todo.id}`, 'PATCH', { done: checkbox.checked }));
    }, checkbox.checked ? '又完成了一件事！' : '已恢復為未完成。');
    if (updated) render();
    else checkbox.checked = todo.done;
  }

  function openDialog(action, todo) {
    if (state.busy) return;
    state.selected = todo.id;
    message('', `#${action}-error`);
    if (action === 'edit') $('#edit-title').value = todo.title;
    else $('#delete-title').textContent = todo.title;
    $(`#${action}-dialog`).showModal();
    if (action === 'edit') {
      $('#edit-title').focus();
      $('#edit-title').select();
    }
  }

  $('#add-form').addEventListener('submit', async event => {
    event.preventDefault();
    const title = $('#title').value.trim();
    if (!title) { message('請先輸入待辦標題，不可只有空白。'); return; }
    const added = await mutate(async () => {
      state.todos.push(await request('/todos', 'POST', { title }));
    }, '待辦已新增。');
    if (added) {
      $('#title').value = '';
      $('#search').value = '';
      state.filter = 'all';
      $('#sort').value = 'newest';
      render();
    }
    $('#title').focus();
  });

  $('#edit-form').addEventListener('submit', async event => {
    event.preventDefault();
    const title = $('#edit-title').value.trim();
    if (!title) { message('請先輸入待辦標題，不可只有空白。', '#edit-error'); return; }
    const edited = await mutate(async () => {
      replaceTask(await request(`/todos/${state.selected}`, 'PATCH', { title }));
    }, '待辦已更新。', '#edit-error');
    if (edited) { $('#edit-dialog').close(); render(); }
  });

  $('#delete-form').addEventListener('submit', async event => {
    event.preventDefault();
    const deleted = await mutate(async () => {
      await request(`/todos/${state.selected}`, 'DELETE');
      state.todos = state.todos.filter(todo => todo.id !== state.selected);
    }, '待辦已刪除。', '#delete-error');
    if (deleted) { $('#delete-dialog').close(); render(); $('#title').focus(); }
  });

  for (const action of ['edit', 'delete']) {
    $(`#${action}-cancel`).addEventListener('click', () => $(`#${action}-dialog`).close());
    $(`#${action}-dialog`).addEventListener('cancel', event => {
      if (state.busy) event.preventDefault();
    });
  }
  document.querySelectorAll('[data-filter]').forEach(button => {
    button.addEventListener('click', () => { state.filter = button.dataset.filter; render(); });
  });
  $('#search').addEventListener('input', render);
  $('#sort').addEventListener('change', render);
  $('#refresh').addEventListener('click', load);
  request('/health').then(health => {
    $('#version').textContent = `版本 ${health.version}`;
  }).catch(() => {
    $('#version').textContent = '版本暫時無法取得';
  });
  load();
}

if (typeof document !== 'undefined') initialize();
