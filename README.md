# fridge-picks

Personal project by an appliance associate: a phone tool for helping customers choose a refrigerator that fits their kitchen, plus a take-home planner customers open from a QR code.

- **Customer planner:** https://odthakang-kai.github.io/fridge-picks/
- **Floor app (add to home screen, works offline):** https://odthakang-kai.github.io/fridge-picks/app/
- **Build:** `python3 tools/build.py` (see `CLAUDE.md` for how everything fits together)

Prices and specs come from public homedepot.com product pages and are refreshed weekly. Fit checks are a guide based on the measurements entered; confirm with each model's installation guide before buying. Not affiliated with or endorsed by The Home Depot.

Includes [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) by Kazuhiko Arase (MIT license).
Includes [zxing-wasm](https://github.com/Sec-ant/zxing-wasm) by Ze-Zheng Wu (MIT license), built from [ZXing-C++](https://github.com/zxing-cpp/zxing-cpp) (Apache 2.0).
