const SB_URL  = 'https://ekxtowlurtuyiupkzwge.supabase.co';
const SB_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVreHRvd2x1cnR1eWl1cGt6d2dlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk1NjQxMDEsImV4cCI6MjA5NTE0MDEwMX0.cvh8lul1vwe6uXAqkCWRX1nK4n0KtNn1PWSL5Q23Ky8';

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const token = (req.headers.authorization || '').replace('Bearer ', '');
  if (!token || token !== process.env.ADMIN_SECRET) {
    return res.status(401).json({ ok: false, error: 'No autorizado' });
  }

  try {
    const products = req.body;
    if (!Array.isArray(products)) throw new Error('Datos inválidos');

    const sbUrl  = process.env.SUPABASE_URL  || SB_URL;
    const sbKey  = process.env.SUPABASE_SERVICE_KEY || SB_ANON;

    const r = await fetch(`${sbUrl}/rest/v1/catalog`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': sbKey,
        'Authorization': `Bearer ${sbKey}`,
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
      throw new Error(`Supabase ${r.status}: ${err}`);
    }

    return res.status(200).json({ ok: true, count: products.length });
  } catch (e) {
    return res.status(500).json({ ok: false, error: e.message });
  }
};
