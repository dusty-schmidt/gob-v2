// Branding loader for nano webui
(function () {
  const TOML_URL = "/public/branding.toml";
  const DEFAULT_BRAND = "GOB";
  const DEFAULT_EXPANSIONS = [
    "General Operations Bot",
    "Global Orchestration Bridge",
    "Generalized Orchestration Brain",
    "Guided Operations Backend",
    "Graph-Oriented Brain",
    "General Operator Bot"
  ];

  function pickRandom(arr) {
    if (!arr || !arr.length) return DEFAULT_BRAND;
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function parseTomlExpansions(tomlText) {
    try {
      const match = tomlText.match(/(^|\n)\s*expansions\s*=\s*\[(.*?)]/s);
      if (!match) return DEFAULT_EXPANSIONS;
      const inner = match[2];
      const re = /"((?:\\"|[^"])*)"/g;
      const result = [];
      let m;
      while ((m = re.exec(inner)) !== null) {
        result.push(m[1].replace(/\\"/g, '"'));
      }
      return result.length ? result : DEFAULT_EXPANSIONS;
    } catch (_) {
      return DEFAULT_EXPANSIONS;
    }
  }

  function replaceTextNodes(node, target, replacement) {
    const skip = ["SCRIPT", "STYLE", "TEXTAREA"]; 
    if (skip.includes(node.nodeName)) return;
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.nodeValue && node.nodeValue.includes(target)) {
        node.nodeValue = node.nodeValue.split(target).join(replacement);
      }
    } else {
      for (let i = 0; i < node.childNodes.length; i++) {
        replaceTextNodes(node.childNodes[i], target, replacement);
      }
    }
  }

  async function initBranding() {
    let expansions = DEFAULT_EXPANSIONS;
    try {
      const resp = await fetch(TOML_URL, { credentials: "same-origin" });
      if (resp.ok) {
        const text = await resp.text();
        expansions = parseTomlExpansions(text);
      }
    } catch (_) {}

    const brand = pickRandom(expansions);
    try { document.title = brand; } catch (_) {}
    const applyBrand = () => replaceTextNodes(document.body, DEFAULT_BRAND, brand);
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", applyBrand);
    } else {
      applyBrand();
    }
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        for (const n of m.addedNodes) {
          if (n.nodeType === 1) replaceTextNodes(n, DEFAULT_BRAND, brand);
        }
      }
    });
    try { observer.observe(document.documentElement || document.body, { childList: true, subtree: true }); } catch (_) {}
  }

  try { initBranding(); } catch (_) {}
})();

