module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const token = (req.headers.authorization || '').replace('Bearer ', '');
  if (token && token === process.env.ADMIN_SECRET) {
    return res.status(200).json({ ok: true });
  }
  return res.status(401).json({ ok: false, error: 'Contraseña incorrecta' });
};
