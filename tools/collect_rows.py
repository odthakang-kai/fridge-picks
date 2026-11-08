"""Pull catalog rows out of saved browser-tool outputs.
usage: python3 collect_rows.py OUT_FILE SAVED_OUTPUT_FILE [SAVED_OUTPUT_FILE ...]
Each saved file is the JSON the harness wrote when a javascript_tool result was too large;
the text inside holds rows between ROWS_START and ROWS_END."""
import json, sys
out, files = sys.argv[1], sys.argv[2:]
rows = []
for f in files:
    raw = open(f, encoding="utf-8").read()
    try:
        data = json.loads(raw)
        text = data[0]["text"] if isinstance(data, list) else data.get("text", raw)
    except Exception:
        text = raw
    text = text.split("\n\n(captured")[0]
    if text.startswith('"'):
        text = json.loads(text)
    body = text.split("ROWS_START\n", 1)[1].split("\nROWS_END", 1)[0]
    rows += [l for l in body.split("\n") if l.strip()]
open(out, "w", encoding="utf-8", newline="\n").write("\n".join(rows))
print(f"{len(rows)} rows from {len(files)} file(s)")
