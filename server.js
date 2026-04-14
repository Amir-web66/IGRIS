const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const PORT = 3737;
const DATA_FILE     = path.join(__dirname, 'data', 'brain_data.json');
const SKILLS_FILE   = path.join(__dirname, 'data', 'earned_skills.json');
const INSIGHTS_FILE = path.join(__dirname, 'data', 'insights.json');
const PUBLIC_DIR    = path.join(__dirname, 'public');

if (!fs.existsSync(DATA_FILE))    fs.writeFileSync(DATA_FILE,   '{}');
if (!fs.existsSync(SKILLS_FILE))  fs.writeFileSync(SKILLS_FILE, '[]');

function runAnalysis() {
  const cmd = process.platform === 'win32' ? 'python analyze.py' : 'python3 analyze.py';
  exec(cmd, { cwd: __dirname }, (err, stdout) => {
    if (err) {
      exec('python analyze.py', { cwd: __dirname }, (err2, out2) => {
        if (!err2) console.log(' ', out2.trim());
        else console.log('  [ML] Python not available — install Python to enable insights');
      });
    } else {
      if (stdout.trim()) console.log(' ', stdout.trim());
    }
  });
}

const MIME = {
  '.html': 'text/html', '.js': 'application/javascript',
  '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon'
};

function readBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => resolve(body));
  });
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  if (req.url === '/api/data' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(fs.readFileSync(DATA_FILE));
    return;
  }
  if (req.url === '/api/data' && req.method === 'POST') {
    const body = await readBody(req);
    fs.writeFileSync(DATA_FILE, body);
    // Re-run ML analysis whenever data is saved
    runAnalysis();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end('{"ok":true}');
    return;
  }
  if (req.url === '/api/skills' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(fs.readFileSync(SKILLS_FILE));
    return;
  }
  if (req.url === '/api/skills' && req.method === 'POST') {
    const body = await readBody(req);
    fs.writeFileSync(SKILLS_FILE, body);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end('{"ok":true}');
    return;
  }
  if (req.url === '/api/insights' && req.method === 'GET') {
    if (fs.existsSync(INSIGHTS_FILE)) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(fs.readFileSync(INSIGHTS_FILE));
    } else {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end('{"error":"not_ready"}');
    }
    return;
  }

  let filePath = req.url === '/' ? '/index.html' : req.url;
  filePath = path.join(PUBLIC_DIR, filePath);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain' });
    res.end(fs.readFileSync(filePath));
  } else {
    res.writeHead(404); res.end('Not found');
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log('\n  SkillForge running → http://localhost:' + PORT + '\n');
  runAnalysis();
  // Re-run analysis every hour
  setInterval(runAnalysis, 3600000);
  const open = process.platform === 'win32' ? 'start http://localhost:' + PORT :
               process.platform === 'darwin' ? 'open http://localhost:' + PORT :
               'xdg-open http://localhost:' + PORT;
  exec(open);
});
