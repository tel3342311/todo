import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

// Load the browser module without introducing a Node package or a DOM dependency.
const source = await readFile(new URL('../app/static/app.js', import.meta.url), 'utf8');
const { selectTodos, summarize, request, taskDate, todoPayload } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
);
const todos = [
  { id: 1, title: 'Buy milk', done: false },
  { id: 2, title: '買茶', done: true },
  { id: 3, title: 'Buy bread', done: true },
];

test('search and completion filter combine without mutating source order', () => {
  assert.deepEqual(selectTodos(todos, 'completed', ' BUY ', 'newest').map(t => t.id), [3]);
  assert.deepEqual(selectTodos(todos, 'active', '', 'newest').map(t => t.id), [1]);
  assert.deepEqual(selectTodos(todos, 'all', '茶', 'newest').map(t => t.id), [2]);
  assert.deepEqual(todos.map(t => t.id), [1, 2, 3]);
});

test('sorts newest, oldest, and alphabetical titles', () => {
  assert.deepEqual(selectTodos(todos, 'all', '', 'newest').map(t => t.id), [3, 2, 1]);
  assert.deepEqual(selectTodos(todos, 'all', '', 'oldest').map(t => t.id), [1, 2, 3]);
  assert.deepEqual(selectTodos([todos[0], todos[2]], 'all', '', 'title').map(t => t.id), [3, 1]);
});

test('no matches and empty list produce an empty result', () => {
  assert.deepEqual(selectTodos(todos, 'all', 'missing', 'newest'), []);
  assert.deepEqual(selectTodos([], 'all', '', 'newest'), []);
});

test('progress handles empty lists and rounds completion percentage', () => {
  assert.deepEqual(summarize([]), { total: 0, active: 0, completed: 0, percentage: 0 });
  assert.deepEqual(summarize(todos), { total: 3, active: 1, completed: 2, percentage: 67 });
});

test('SQLite naive timestamps are interpreted as UTC', () => {
  assert.equal(taskDate('2026-09-24T06:00:00').toISOString(), '2026-09-24T06:00:00.000Z');
  assert.equal(taskDate('2026-09-24T14:00:00+08:00').toISOString(), '2026-09-24T06:00:00.000Z');
});

test('request returns a saved task and sends the intended JSON', async t => {
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    assert.equal(path, '/todos');
    assert.equal(options.method, 'POST');
    assert.deepEqual(JSON.parse(options.body), { title: 'Buy milk' });
    return new Response(JSON.stringify(todos[0]), { status: 201 });
  });
  assert.deepEqual(await request('/todos', 'POST', { title: 'Buy milk' }), todos[0]);
});

test('204 delete succeeds without trying to parse an empty response', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response(null, { status: 204 }));
  assert.equal(await request('/todos/1', 'DELETE'), null);
});

test('HTTP errors reject instead of being treated as saved tasks', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('Internal Server Error', { status: 500 }));
  await assert.rejects(request('/todos'), /500/);
});

test('validation and missing-task errors explain how to recover', async t => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => new Response('{}', { status: 422 }));
  await assert.rejects(request('/todos', 'POST', { title: ' ' }), /200/);
  fetchMock.mock.mockImplementation(async () => new Response('{}', { status: 404 }));
  await assert.rejects(request('/todos/1'), /重新整理/);
});

test('network failure rejects with a connection message', async t => {
  t.mock.method(globalThis, 'fetch', async () => { throw new TypeError('Failed to fetch'); });
  await assert.rejects(request('/todos'), /連線/);
});

test('date form payload preserves the calendar date and clears blank dates explicitly', () => {
  assert.deepEqual(todoPayload('  Plan  ', '2026-10-01'), {
    title: 'Plan', finish_date: '2026-10-01',
  });
  assert.deepEqual(todoPayload('Plan', ''), { title: 'Plan', finish_date: null });
});

test('saving and clearing a target date sends the expected API payload', async t => {
  const saved = { id: 8, title: 'Plan', done: false, finish_date: '2026-10-01' };
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    assert.equal(path, '/todos/8');
    assert.equal(options.method, 'PATCH');
    const body = JSON.parse(options.body);
    return new Response(JSON.stringify({ ...saved, ...body }), { status: 200 });
  });
  assert.equal((await request('/todos/8', 'PATCH', todoPayload('Plan', '2026-10-01'))).finish_date,
    '2026-10-01');
  assert.equal((await request('/todos/8', 'PATCH', todoPayload('Plan', ''))).finish_date, null);
});

test('invalid finish dates receive a date-specific validation error', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({
    detail: [{ loc: ['body', 'finish_date'], msg: 'Invalid date' }],
  }), { status: 422 }));
  await assert.rejects(request('/todos', 'POST', { title: 'Plan', finish_date: 'bad' }), /日期/);
});
