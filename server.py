"""Forkful local server.

Serves the app and relays Open Food Facts text searches. Open Food Facts blocks
search calls made straight from a browser, and asks apps to send an identifying
User-Agent, so the page calls /off/... here and this server forwards them.
USDA FoodData Central allows browser calls, so the page talks to it directly.

Run:  python server.py        then open http://localhost:8765
"""
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = Path(__file__).resolve().parent
USER_AGENT = "Forkful/0.3 (personal nutrition app; https://github.com/PythDom/food)"
FIELDS = ("code,product_name,product_name_fr,product_name_en,generic_name,brands,nutriments,"
          "serving_size,serving_quantity,image_small_url,nutriscore_grade")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".webmanifest": "application/manifest+json", ".js": "text/javascript", ".json": "application/json"}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/off/"):
            return self.relay_off(parsed)
        return super().do_GET()

    def relay_off(self, parsed):
        qs = urllib.parse.parse_qs(parsed.query)
        lang = "fr" if qs.get("lang", ["en"])[0] == "fr" else "en"
        try:
            m = re.fullmatch(r"/off/product/(\d{8,14})", parsed.path)
            if m:
                data = fetch_json(f"https://world.openfoodfacts.org/api/v2/product/{m.group(1)}.json"
                                  f"?fields={FIELDS}&lc={lang}")
                products = [data["product"]] if data.get("status") == 1 else []
            elif parsed.path == "/off/search":
                q = qs.get("q", [""])[0].strip()
                params = urllib.parse.urlencode({"q": q, "page_size": 25, "langs": lang, "fields": FIELDS})
                data = fetch_json(f"https://search.openfoodfacts.org/search?{params}")
                products = data.get("hits", [])
            else:
                return self.send_json(404, {"error": "not found"})
            self.send_json(200, {"products": products})
        except urllib.error.HTTPError as e:
            self.send_json(502, {"error": f"Open Food Facts returned HTTP {e.code}"})
        except Exception as e:  # network down, timeout, bad JSON
            self.send_json(502, {"error": str(e)})

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(ROOT)))
    print(f"Forkful running at http://localhost:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
