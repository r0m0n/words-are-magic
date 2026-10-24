// Lernstand-Abgleich: ein JSON-Dokument je Lernschlüssel in Netlify Blobs.
//   GET  /api/state?key=<schlüssel>   → { updated, data } oder 404
//   PUT  /api/state?key=<schlüssel>   (Body: JSON) → { updated }
//   GET  /api/state?ping=1            → { ok: true }  (Verfügbarkeitstest der App)
// Der Schlüssel ist das einzige Geheimnis: 20–64 Zeichen [A-Za-z0-9-]. Kein Konto, keine Namen.
import { getStore } from "@netlify/blobs";

const KEY_RE = /^[A-Za-z0-9-]{20,64}$/;
const MAX_BYTES = 2_000_000;
const headers = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const json = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers });

export default async (req) => {
  const url = new URL(req.url);
  if (url.searchParams.get("ping")) return json({ ok: true });
  const key = url.searchParams.get("key") || "";
  if (!KEY_RE.test(key)) return json({ error: "Ungültiger Lernschlüssel" }, 400);
  const store = getStore("lernstand");

  if (req.method === "GET") {
    const doc = await store.get(key, { type: "json" });
    if (!doc) return json({ error: "Kein Stand unter diesem Schlüssel" }, 404);
    return json(doc);
  }
  if (req.method === "PUT" || req.method === "POST") {
    const text = await req.text();
    if (text.length > MAX_BYTES) return json({ error: "Zu groß" }, 413);
    let data;
    try { data = JSON.parse(text); } catch { return json({ error: "Kein JSON" }, 400); }
    if (!data || typeof data !== "object" || !data.state) return json({ error: "Kein Lernstand" }, 400);
    const doc = { updated: new Date().toISOString(), data };
    await store.setJSON(key, doc);
    return json({ updated: doc.updated });
  }
  if (req.method === "DELETE") { await store.delete(key); return json({ ok: true }); }
  return json({ error: "Methode nicht erlaubt" }, 405);
};

export const config = { path: "/.netlify/functions/state" };
