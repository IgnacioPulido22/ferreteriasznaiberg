const REPO_OWNER = 'IgnacioPulido22';
const REPO_NAME  = 'ferreteriasznaiberg';
const FILE_PATH  = 'products.json';

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const token = (req.headers.authorization || '').replace('Bearer ', '');
  if (!token || token !== process.env.ADMIN_SECRET) {
    return res.status(401).json({ ok: false, error: 'No autorizado' });
  }

  const githubToken = process.env.GITHUB_TOKEN;
  if (!githubToken) {
    return res.status(500).json({ ok: false, error: 'GITHUB_TOKEN no configurado en Vercel' });
  }

  try {
    const products = req.body;
    if (!Array.isArray(products)) throw new Error('Datos inválidos');

    const ghHeaders = {
      'Authorization': `Bearer ${githubToken}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    };

    // Obtener SHA actual del archivo
    const metaRes = await fetch(
      `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}`,
      { headers: ghHeaders }
    );
    if (!metaRes.ok) {
      const err = await metaRes.text();
      throw new Error(`GitHub GET ${metaRes.status}: ${err}`);
    }
    const meta = await metaRes.json();
    const sha = meta.sha;

    // Codificar contenido en base64
    const content = Buffer.from(
      JSON.stringify(products, null, 4)
    ).toString('base64');

    // Actualizar archivo en GitHub
    const putRes = await fetch(
      `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}`,
      {
        method: 'PUT',
        headers: ghHeaders,
        body: JSON.stringify({
          message: `Admin: actualizar ${products.length} productos`,
          content,
          sha,
        }),
      }
    );

    if (!putRes.ok) {
      const err = await putRes.text();
      throw new Error(`GitHub PUT ${putRes.status}: ${err}`);
    }

    return res.status(200).json({ ok: true, count: products.length });
  } catch (e) {
    return res.status(500).json({ ok: false, error: e.message });
  }
};
