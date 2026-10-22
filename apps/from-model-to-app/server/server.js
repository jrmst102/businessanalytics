/* Node.js web server for "Business Analytics in Action: From Model to App".
 *
 * Serves the static three-tab dashboard and forwards /api/* requests to the
 * Python engine API (engine_api.py), which owns every model result. This
 * server contains no analytics logic.
 *
 *   PORT        port to listen on            (default 8080)
 *   HOST        address to bind              (default 0.0.0.0)
 *   ENGINE_URL  Python engine API base URL   (default http://127.0.0.1:8000)
 */
const path = require('path');
const express = require('express');
const compression = require('compression');

const PORT = parseInt(process.env.PORT || '8080', 10);
const HOST = process.env.HOST || '0.0.0.0';
const ENGINE_URL = (process.env.ENGINE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

const app = express();
app.use(compression());

// Health endpoint for the hosting platform: healthy only if the engine is up.
app.get('/healthz', async (_req, res) => {
  try {
    const engine = await fetch(`${ENGINE_URL}/api/health`);
    res.status(engine.ok ? 200 : 503).send(engine.ok ? 'ok' : 'engine unhealthy');
  } catch {
    res.status(503).send('engine unreachable');
  }
});

// Forward API calls to the Python engine unchanged.
app.use('/api', express.raw({ type: '*/*', limit: '1mb' }), async (req, res) => {
  try {
    const headers = { 'content-type': req.headers['content-type'] || 'application/json' };
    if (req.headers['x-session-id']) headers['x-session-id'] = req.headers['x-session-id'];
    const upstream = await fetch(`${ENGINE_URL}/api${req.url}`, {
      method: req.method,
      headers,
      body: ['GET', 'HEAD'].includes(req.method) ? undefined : req.body,
    });
    res.status(upstream.status);
    res.type(upstream.headers.get('content-type') || 'application/json');
    res.send(Buffer.from(await upstream.arrayBuffer()));
  } catch (error) {
    res.status(502).json({ error: `The engine API is not reachable (${error.message}). ` +
      'If running locally, start the app with: python launch.py' });
  }
});

// Chart.js served from the installed package so the app works offline.
// (chart.js v4's exports map blocks require.resolve on dist/, so use the path.)
const CHART_JS = path.join(__dirname, 'node_modules', 'chart.js', 'dist', 'chart.umd.js');
app.get('/vendor/chart.js', (_req, res) => {
  res.sendFile(CHART_JS);
});

app.use(express.static(path.join(__dirname, 'static')));

app.listen(PORT, HOST, () => {
  console.log(`Dashboard listening on http://${HOST}:${PORT} (engine: ${ENGINE_URL})`);
});
