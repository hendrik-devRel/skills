#!/usr/bin/env node
// Local review server. Runs a website's dev server and serves it through a
// loopback proxy that adds a commenting layer. Comments are saved to comments.json.
//
//   node server.mjs [--dir article-review]
//     --dir <path>        workspace: holds comments.json, review.config.json and site/ (default: ./article-review)
//     --site-dir <path>   folder to run the dev server in (default: <dir>/site, plus "app" from the config)
//     --cmd "<command>"   dev command; {port} is replaced (default: the app's own "dev" script)
//     --target <url>      use an already-running site instead of starting one
//     --port 4710         port to open in the browser (or PORT)
//     --site-port 3411    internal port for the dev server
//     --open <path>       page to open first (default: /)
//     --file <path>       where comments are stored (default: <dir>/comments.json)
//
// review.config.json in the workspace may set: app, cmd, open, port, sitePort, target.
import http from 'node:http';
import net from 'node:net';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { readFile, writeFile, rename, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const flag = name => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : undefined;
};
const workspace = path.resolve(flag('dir') ?? 'article-review');
const readJson = file => {
  try {
    return JSON.parse(readFileSync(file, 'utf8'));
  } catch {
    return {};
  }
};
const config = readJson(path.join(workspace, 'review.config.json'));
const port = Number(flag('port') ?? process.env.PORT ?? config.port ?? 4710);
const sitePort = Number(flag('site-port') ?? config.sitePort ?? 3411);
const siteDir = path.resolve(flag('site-dir') ?? path.join(workspace, 'site', config.app ?? ''));
const explicitTarget = flag('target') ?? config.target;
const target = new URL(explicitTarget ?? `http://127.0.0.1:${sitePort}`);
const file = path.resolve(flag('file') ?? path.join(workspace, 'comments.json'));
const startPath = flag('open') ?? config.open ?? '/';
const overlayTag = '<script src="/__review/overlay.js" defer></script>';

// ---- website dev server -----------------------------------------------------
// The package manager is whatever the site pins in a "packageManager" field, run through corepack.
function packageManager(from) {
  for (let dir = from, i = 0; i < 6; i++, dir = path.dirname(dir)) {
    const pinned = readJson(path.join(dir, 'package.json')).packageManager;
    if (pinned) return `corepack ${pinned.split('+')[0]}`;
    if (dir === path.dirname(dir)) break;
  }
  return 'npx';
}
function devCommand() {
  const custom = flag('cmd') ?? config.cmd;
  if (custom) return custom.replaceAll('{port}', String(sitePort));
  const dev = readJson(path.join(siteDir, 'package.json')).scripts?.dev;
  if (!dev) throw new Error(`No "dev" script in ${siteDir}/package.json. Pass --cmd "<command using {port}>" or --target <url>.`);
  const pm = packageManager(siteDir);
  // Next.js takes the host and port as flags; other tools read PORT from the environment.
  return /^next dev\b/.test(dev)
    ? `${pm} ${pm === 'npx' ? '' : 'exec '}${dev} -H 127.0.0.1 -p ${sitePort}`
    : `${pm === 'npx' ? 'npm' : pm} run dev`;
}
const reachable = async () => {
  try {
    await fetch(target, { method: 'HEAD', signal: AbortSignal.timeout(1500) });
    return true;
  } catch {
    return false;
  }
};
let child;
if (!explicitTarget && !(await reachable())) {
  if (!existsSync(siteDir)) {
    console.error(`[review] ${siteDir} does not exist. Run setup.sh first, or pass --site-dir or --target.`);
    process.exit(1);
  }
  const command = devCommand();
  console.log(`[review] starting the site: ${command}`);
  child = spawn(command, {
    cwd: siteDir,
    shell: true,
    stdio: ['ignore', 'inherit', 'inherit'],
    detached: true,
    env: { ...process.env, PORT: String(sitePort), HOST: '127.0.0.1', COREPACK_ENABLE_DOWNLOAD_PROMPT: '0' },
  });
  child.on('exit', code => {
    console.error(`[review] the website dev server stopped (code ${code}).`);
    child = null;
  });
}
const stop = () => {
  if (child?.pid) {
    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch {}
  }
};
process.on('exit', stop);
for (const signal of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(signal, () => process.exit(0));
await mkdir(path.dirname(file), { recursive: true });

// ---- comment store ----------------------------------------------------------
const empty = () => ({ version: 1, comments: [] });
async function load() {
  try {
    const data = JSON.parse(await readFile(file, 'utf8'));
    return Array.isArray(data.comments) ? data : empty();
  } catch (error) {
    if (error.code === 'ENOENT') return empty();
    throw error;
  }
}
let queue = Promise.resolve();
// Read-modify-write runs one at a time, so edits made to the file by hand or by Claude are kept.
const mutate = fn =>
  (queue = queue.catch(() => {}).then(async () => {
    const data = await load();
    const result = await fn(data);
    await writeFile(`${file}.tmp`, `${JSON.stringify(data, null, 2)}\n`);
    await rename(`${file}.tmp`, file);
    return result;
  }));
const text = (value, max) => (typeof value === 'string' ? value.slice(0, max) : '');
const body = req =>
  new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', chunk => {
      size += chunk.length;
      if (size > 200_000) reject(new Error('too large'));
      else chunks.push(chunk);
    });
    req.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'));
      } catch (error) {
        reject(error);
      }
    });
    req.on('error', reject);
  });
const json = (res, status, value) => {
  const out = JSON.stringify(value);
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(out);
};

async function api(req, res, url) {
  const id = url.pathname.split('/')[4];
  if (req.method === 'GET') {
    const { comments } = await load();
    const only = url.searchParams.get('path');
    return json(res, 200, { file, comments: only ? comments.filter(c => c.path === only) : comments });
  }
  // A JSON content type forces a preflight for cross-site requests, which this server never answers.
  if (!String(req.headers['content-type'] || '').includes('application/json')) return json(res, 415, { error: 'json only' });
  if (req.method === 'POST') {
    const input = await body(req);
    if (!text(input.comment, 1).trim()) return json(res, 400, { error: 'empty comment' });
    const now = new Date().toISOString();
    const comment = {
      id: randomUUID().slice(0, 8),
      status: 'open',
      path: text(input.path, 500),
      title: text(input.title, 300),
      section: text(input.section, 300),
      kind: input.kind === 'block' ? 'block' : 'text',
      quote: text(input.quote, 2000),
      prefix: text(input.prefix, 80),
      suffix: text(input.suffix, 80),
      pos: Number.isFinite(input.pos) ? input.pos : 0,
      comment: text(input.comment, 10000),
      reply: '',
      createdAt: now,
      updatedAt: now,
    };
    await mutate(data => data.comments.push(comment));
    return json(res, 201, comment);
  }
  if (req.method === 'PATCH' && id) {
    const input = await body(req);
    const updated = await mutate(data => {
      const comment = data.comments.find(c => c.id === id);
      if (!comment) return null;
      if (typeof input.comment === 'string' && input.comment.trim()) comment.comment = text(input.comment, 10000);
      if (input.status === 'open' || input.status === 'done') comment.status = input.status;
      comment.updatedAt = new Date().toISOString();
      return comment;
    });
    return updated ? json(res, 200, updated) : json(res, 404, { error: 'not found' });
  }
  if (req.method === 'DELETE' && id) {
    await mutate(data => {
      data.comments = data.comments.filter(c => c.id !== id);
    });
    return json(res, 200, { ok: true });
  }
  return json(res, 405, { error: 'method not allowed' });
}

// ---- proxy ------------------------------------------------------------------
const waiting = `<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="2"><title>Starting…</title>
<body style="font:16px system-ui;background:#16141a;color:#eee8e3;display:grid;place-items:center;height:100vh;margin:0">
<p>Starting the local site. This page reloads by itself…</p></body>`;
const localHost = host => /^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/.test(String(host || ''));

function proxy(req, res) {
  const headers = { ...req.headers, host: target.host, 'accept-encoding': 'identity' };
  if (headers.origin) headers.origin = target.origin;
  const upstream = http.request(
    { hostname: target.hostname, port: target.port, path: req.url, method: req.method, headers },
    reply => {
      const out = { ...reply.headers };
      delete out['content-security-policy'];
      delete out['content-security-policy-report-only'];
      if (out.location) out.location = String(out.location).replace(target.origin, `http://${req.headers.host}`);
      if (req.method !== 'GET' || !String(out['content-type'] || '').includes('text/html')) {
        res.writeHead(reply.statusCode, out);
        return reply.pipe(res);
      }
      const chunks = [];
      reply.on('data', chunk => chunks.push(chunk));
      reply.on('end', () => {
        let html = Buffer.concat(chunks).toString('utf8');
        const at = html.lastIndexOf('</body>');
        html = at > -1 ? html.slice(0, at) + overlayTag + html.slice(at) : html + overlayTag;
        delete out['content-length'];
        delete out['transfer-encoding'];
        res.writeHead(reply.statusCode, { ...out, 'content-length': Buffer.byteLength(html) });
        res.end(html);
      });
    }
  );
  upstream.on('error', () => {
    if (res.headersSent) return res.destroy();
    res.writeHead(503, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
    res.end(waiting);
  });
  req.pipe(upstream);
}

const server = http.createServer(async (req, res) => {
  try {
    if (!localHost(req.headers.host)) {
      res.writeHead(403);
      return res.end('local only');
    }
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname === '/__review/overlay.js') {
      res.writeHead(200, { 'content-type': 'text/javascript; charset=utf-8', 'cache-control': 'no-store' });
      return res.end(await readFile(path.join(here, 'overlay.js')));
    }
    if (url.pathname.startsWith('/__review/api/comments')) return await api(req, res, url);
    // A fresh visit to the root lands on the configured start page; links inside the site still reach its home page.
    if (url.pathname === '/__review' || (url.pathname === '/' && startPath !== '/' && !req.headers.referer)) {
      res.writeHead(302, { location: startPath });
      return res.end();
    }
    proxy(req, res);
  } catch (error) {
    if (!res.headersSent) json(res, 500, { error: String(error.message || error) });
    else res.destroy();
  }
});
// Hot reload uses a WebSocket, tunnelled as-is.
server.on('upgrade', (req, socket, head) => {
  if (!localHost(req.headers.host)) return socket.destroy();
  const upstream = net.connect(Number(target.port), target.hostname, () => {
    const headers = { ...req.headers, host: target.host };
    if (headers.origin) headers.origin = target.origin;
    const lines = Object.entries(headers).map(([key, value]) => `${key}: ${value}`);
    upstream.write(`${req.method} ${req.url} HTTP/1.1\r\n${lines.join('\r\n')}\r\n\r\n`);
    if (head.length) upstream.write(head);
    socket.pipe(upstream).pipe(socket);
  });
  upstream.on('error', () => socket.destroy());
  socket.on('error', () => upstream.destroy());
});
server.listen(port, '127.0.0.1', () => {
  console.log(`[review] open http://localhost:${port}${startPath}`);
  console.log(`[review] comments are saved to ${file}`);
  console.log(`[review] site: ${child ? `${siteDir} (starting on port ${sitePort})` : target.origin}`);
});
