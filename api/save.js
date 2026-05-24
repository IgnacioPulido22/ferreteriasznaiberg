module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  // Verificar contraseña
  const token = (req.headers.authorization || '').replace('Bearer ', '');
  if (!token || token !== process.env.ADMIN_SECRET) {
    return res.status(401).json({ ok: false, error: 'No autorizado' });
  }

  try {
    const products = req.body;
    if (!Array.isArray(products)) throw new Error('Datos inválidos');

    const r = await fetch(`${process.env.SUPABASE_URL}/rest/v1/catalog`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': process.env.SUPABASE_SERVICE_KEY,
        'Authorization': `Bearer ${process.env.SUPABASE_SERVICE_KEY}`,
        'Prefer': 'resolution=merge-duplicates',
      },
      body: JSON.stringify({
        id: 1,
        products,
        updated_at: new Date().toISOString(),
      }),
    });

    if (!r.ok) {
      const err = await r.text();
      throw new Error(err);
    }

    return res.status(200).json({ ok: true, count: products.length });
  } catch (e) {
    return res.status(500).json({ ok: false, error: e.message });
  }
};
