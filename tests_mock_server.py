"""Nachbau der Netlify-Funktion für lokale Tests: statische Dateien + /api/state im Speicher."""
import json, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
STORE = {}; KEY_RE = re.compile(r"^[A-Za-z0-9-]{20,64}$")
class H(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, obj, status=200):
        b = json.dumps(obj).encode(); self.send_response(status); self.send_header("content-type","application/json"); self.send_header("content-length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.startswith("/api/state"):
            q = dict(p.split("=",1) for p in self.path.split("?",1)[1].split("&")) if "?" in self.path else {}
            if q.get("ping"): return self._json({"ok": True})
            k = q.get("key",""); 
            if not KEY_RE.match(k): return self._json({"error":"bad key"},400)
            if k not in STORE: return self._json({"error":"none"},404)
            return self._json(STORE[k])
        return super().do_GET()
    def do_PUT(self):
        q = dict(p.split("=",1) for p in self.path.split("?",1)[1].split("&")); k = q.get("key","")
        n = int(self.headers.get("content-length",0)); data = json.loads(self.rfile.read(n))
        import datetime; STORE[k] = {"updated": datetime.datetime.utcnow().isoformat()+"Z", "data": data}
        self._json({"updated": STORE[k]["updated"]})
    do_POST = do_PUT
ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
