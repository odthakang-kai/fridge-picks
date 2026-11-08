#!/usr/bin/env python3
"""Save harvested catalog rows from the browser straight to a file.

homedepot.com's security policy blocks fetch() to other hosts, but a tab may still navigate to localhost.
So: start this, then in the harvest tab (after HV.phase === "done") run

    location.href = "http://127.0.0.1:8766/#" + encodeURIComponent(HV.rows.join("\\n"))

The rows ride in the URL fragment (never sent over the network), this page posts them back to this
script, and it writes OUT_FILE and exits. Then: python tools/apply_refresh.py OUT_FILE YYYY-MM-DD index.html

Read HV.reportText() BEFORE navigating: the harvest's state is lost once the tab leaves homedepot.com.

usage: python tools/receive_rows.py OUT_FILE [PORT]
"""
import http.server, sys, threading

out = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8766

PAGE = (b"<!doctype html><meta charset=utf-8><title>Rows</title><p id=s>No rows in the link.</p><script>"
        b"(async()=>{const h=location.hash.slice(1);if(!h)return;"
        b"const r=await fetch('/',{method:'POST',body:decodeURIComponent(h)});"
        b"document.getElementById('s').textContent=await r.text();history.replaceState(null,'','/')})()</script>")


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("content-length", 0)))
        rows = [l for l in body.decode("utf-8").split("\n") if l.strip()]
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(rows) + "\n")
        msg = f"Saved {len(rows)} rows to {out}. You can close this tab."
        self.send_response(200)
        self.send_header("content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(msg.encode())
        print(msg, flush=True)
        threading.Thread(target=self.server.shutdown).start()


print(f"Waiting for rows on http://127.0.0.1:{port}/ ...", flush=True)
http.server.HTTPServer(("127.0.0.1", port), Handler).serve_forever()
