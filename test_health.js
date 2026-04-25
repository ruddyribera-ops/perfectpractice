const https = require('https');
https.get('https://proactive-wisdom-production-cd0e.up.railway.app/api/health', res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => console.log(`Status: ${res.statusCode}, Body: ${d}`));
}).on('error', e => console.log('ERR:', e.message));