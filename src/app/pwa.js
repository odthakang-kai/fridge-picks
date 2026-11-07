/* Home-screen app extras. Inlined only into app/index.html by tools/build.py. */
(function () {
  // barcode decoder fallback (iPhone and other browsers without BarcodeDetector)
  // (the decoder script is deferred, so set it up once the page has parsed; never fetch from a CDN)
  const prepZX = () => {
    if (window.ZXingWASM && ZXingWASM.prepareZXingModule) {
      try {
        ZXingWASM.prepareZXingModule({overrides: {locateFile: (path, prefix) => path.endsWith(".wasm") ? new URL("vendor/" + path, location.href).href : prefix + path}});
      } catch (e) {}
    }
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", prepZX); else prepZX();

  // offline cache
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
    navigator.serviceWorker.register("sw.js").then(() => navigator.serviceWorker.ready).then(() => {
      try {
        if (!localStorage.getItem("fc_offline_ok")) {
          localStorage.setItem("fc_offline_ok", "1");
          toast("Saved for offline use");
        }
      } catch (e) {}
    }).catch(() => {});
  }

  // install hint
  const standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  if (standalone) return;
  let dismissed = false;
  try { dismissed = localStorage.getItem("fc_install_hint") === "off"; } catch (e) {}
  if (dismissed) return;
  const bar = document.createElement("div");
  bar.className = "installbar";
  bar.innerHTML = '<span id="installTxt"></span><button class="btn y" id="installGo" hidden>Install</button><button class="rm" id="installX">Not now</button>';
  const st = document.createElement("style");
  st.textContent = ".installbar{position:fixed;left:8px;right:8px;bottom:calc(70px + env(safe-area-inset-bottom,0px));z-index:30;background:#333333;color:#FFFFFF;border-radius:6px;padding:10px 12px;display:flex;gap:10px;align-items:center;font-size:14px;box-shadow:0 4px 16px rgba(0,0,0,.25)}.installbar span{flex:1}.installbar .rm{color:#FFFFFF}.installbar .btn{padding:8px 12px}";
  document.head.appendChild(st);
  const ios = /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const show = txt => { bar.querySelector("#installTxt").textContent = txt; document.body.appendChild(bar); };
  const hide = () => { bar.remove(); try { localStorage.setItem("fc_install_hint", "off"); } catch (e) {} };
  bar.querySelector("#installX").onclick = hide;
  if (ios) {
    show("Add to your home screen: tap Share, then Add to Home Screen. It works offline after that.");
  } else {
    window.addEventListener("beforeinstallprompt", e => {
      e.preventDefault();
      show("Install Floor Copilot on this phone. It opens like an app and works offline.");
      const go = bar.querySelector("#installGo");
      go.hidden = false;
      go.onclick = async () => { e.prompt(); try { await e.userChoice; } catch (x) {} hide(); };
    });
  }
})();
