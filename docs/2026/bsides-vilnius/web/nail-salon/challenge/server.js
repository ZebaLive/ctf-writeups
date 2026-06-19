const express = require('express');
const path = require('path');
const csstree = require('css-tree');

const app = express();
const PORT = 1337;

app.use(express.json({ limit: '250kb' }));

app.get('/', (_req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.post('/api/submit', async (req, res) => {
  const { customCSS } = req.body;

  const MAX_CSS_BYTES = 200 * 1024;

  if (!customCSS) return res.status(400).json({ message: 'CSS code cannot be empty!' });
  if (Buffer.byteLength(customCSS, 'utf8') > MAX_CSS_BYTES) {
    return res.status(400).json({ message: 'CSS must be under 200 KB' });
  }
  try {
    csstree.parse(customCSS, { onParseError: (err) => { throw err; } });
  } catch (err) {
    return res.status(400).json({ message: `Invalid CSS: ${err.message}` });
  }

  // Submission gets sent to admin, they will review it shortly

  return res.json({ message: 'Submission received! Admin bot is reviewing it now.' });
});


app.get('/access', (req, res) => {
    const { token } = req.query;

    if (token !== ADMIN_TOKEN) {
        return res.status(403).json({ message: 'Forbidden' });
    }

    res.set('Content-Type', 'text/plain');
    return res.send(
        `DEBUG USER ACCESS\nACCESS-KEY: ${process.env.ACCESS_KEY_ID}\nSECRET-KEY: ${process.env.SECRET_KEY}\nREGION: us-east-1`
    );
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Listening on port ${PORT}`);
});
