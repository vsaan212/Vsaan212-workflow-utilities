/**
 * Lazy Docs — split-pane Markdown viewer (index left, content right).
 * Subfolder via docs_subfolder widget + node.properties (right-click Properties).
 */
import { app } from "../../scripts/app.js";

const API = "/vsaan212/lazy-docs";
const NODE_MIN_WIDTH = 640;
const NODE_MIN_HEIGHT = 420;
const ROOT_LABEL = "(root)";

function ensureProps(node) {
    if (!node.properties) node.properties = {};
    if (node.properties.docs_subfolder === undefined) {
        node.properties.docs_subfolder = ROOT_LABEL;
    }
    if (node.properties.docs_selected === undefined) {
        node.properties.docs_selected = "";
    }
    if (node.properties.docs_raw === undefined) {
        node.properties.docs_raw = false;
    }
}

/** Widget / property value → API folder path ("" = Docs root). */
function folderToApi(value) {
    const s = String(value ?? "").trim();
    if (!s || s === ROOT_LABEL) return "";
    return s.replace(/\\/g, "/").replace(/^\/+|\/+$/g, "");
}

/** API / legacy empty → combo label. */
function folderToWidget(value) {
    const s = String(value ?? "").trim();
    if (!s || s === ROOT_LABEL) return ROOT_LABEL;
    return s.replace(/\\/g, "/").replace(/^\/+|\/+$/g, "");
}

function getSubfolderWidget(node) {
    return node.widgets?.find((x) => x.name === "docs_subfolder");
}

function getSubfolder(node) {
    ensureProps(node);
    const w = getSubfolderWidget(node);
    if (w?.value != null) return folderToApi(w.value);
    return folderToApi(node.properties.docs_subfolder);
}

function setSubfolder(node, value) {
    ensureProps(node);
    const label = folderToWidget(value);
    node.properties.docs_subfolder = label;
    const w = getSubfolderWidget(node);
    if (w) {
        if (Array.isArray(w.options?.values) && !w.options.values.includes(label)) {
            w.options.values = [ROOT_LABEL, ...w.options.values.filter((v) => v !== ROOT_LABEL), label];
        }
        w.value = label;
    }
}

async function refreshFolderChoices(node, preferValue) {
    const w = getSubfolderWidget(node);
    if (!w) return folderToWidget(preferValue);
    let folders = [];
    try {
        const data = await fetchJson(`${API}/folders`);
        folders = Array.isArray(data.folders) ? data.folders : [];
    } catch (_) {
        folders = [];
    }
    const values = [ROOT_LABEL, ...folders];
    const want = folderToWidget(
        preferValue != null ? preferValue : w.value || node.properties.docs_subfolder
    );
    w.options = w.options || {};
    w.options.values = values;
    w.value = values.includes(want) ? want : ROOT_LABEL;
    node.properties.docs_subfolder = w.value;
    node.setDirtyCanvas?.(true, true);
    return w.value;
}

function ensureNodeMinSize(node) {
    if (!node.size) node.size = [NODE_MIN_WIDTH, NODE_MIN_HEIGHT];
    if (node.size[0] < NODE_MIN_WIDTH) node.size[0] = NODE_MIN_WIDTH;
    if (node.size[1] < NODE_MIN_HEIGHT) node.size[1] = NODE_MIN_HEIGHT;
}

async function fetchJson(url) {
    const resp = await fetch(url);
    return await resp.json();
}

/** Escape HTML text nodes. */
function esc(s) {
    return String(s ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// Private-use sentinels so nested **`code`** bold/code does not collide with content.
const SLOT_L = "\uE000";
const SLOT_R = "\uE001";

/** Expand parked HTML slots, including nested placeholders (e.g. **`code`**). */
function expandSlots(s, slots) {
    let out = String(s ?? "");
    for (let guard = 0; guard < 64 && out.includes(SLOT_L); guard++) {
        out = out.replace(
            new RegExp(`${SLOT_L}(\\d+)${SLOT_R}`, "g"),
            (_, n) => slots[Number(n)] ?? ""
        );
    }
    // Strip any unbroken sentinels rather than leaking glyphs
    return out.replace(new RegExp(`${SLOT_L}\\d+${SLOT_R}`, "g"), "");
}

/** Inline MD → HTML (bold, italic, code, links). */
function inlineMd(text) {
    let s = esc(text);
    const slots = [];
    const park = (html) => {
        const i = slots.length;
        // Expand any nested slots before parking so parents hold final HTML
        slots.push(expandSlots(html, slots));
        return `${SLOT_L}${i}${SLOT_R}`;
    };

    // Code first — supports **`TextGenerate (CLIP)`** (bold wrapping a code span)
    s = s.replace(/`([^`]+)`/g, (_, code) => park(`<code>${code}</code>`));
    s = s.replace(
        /\[([^\]]+)\]\((https?:[^)\s]+)\)/g,
        (_, label, href) => park(`<a href="${href}">${label}</a>`)
    );
    // Autolink bare URLs (after explicit [text](url) links)
    s = s.replace(
        /(https?:\/\/[^\s<]+[^.\s<),;:!?"'\]])/g,
        (url) => park(`<a href="${url}">${url}</a>`)
    );
    s = s.replace(/\*\*([^*]+)\*\*/g, (_, t) => park(`<strong>${t}</strong>`));
    s = s.replace(/__([^_]+)__/g, (_, t) => park(`<strong>${t}</strong>`));
    s = s.replace(/\*([^*]+)\*/g, (_, t) => park(`<em>${t}</em>`));
    // Avoid turning snake_case into italics: require word boundaries-ish
    s = s.replace(/(^|[\s(])_([^_\s][^_]*)_(?=[\s).,!?:;]|$)/g, (_, pre, t) =>
        `${pre}${park(`<em>${t}</em>`)}`
    );
    return expandSlots(s, slots);
}

function isTableSep(line) {
    return /^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$/.test(line) && /-/.test(line);
}

function splitTableRow(line) {
    let s = line.trim();
    if (s.startsWith("|")) s = s.slice(1);
    if (s.endsWith("|")) s = s.slice(0, -1);
    return s.split("|").map((c) => c.trim());
}

/**
 * Client-side Markdown → HTML (GFM-ish), same idea as Comfy Markdown Note
 * (frontend render). Does not depend on the Python `markdown` package.
 */
function renderMarkdownToHtml(md) {
    const src = String(md || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    if (!src.trim()) return "";

    const lines = src.split("\n");
    const out = [];
    let i = 0;
    let inUl = false;
    let inOl = false;
    let para = [];

    const closeLists = () => {
        if (inUl) {
            out.push("</ul>");
            inUl = false;
        }
        if (inOl) {
            out.push("</ol>");
            inOl = false;
        }
    };
    const flushPara = () => {
        if (!para.length) return;
        out.push(`<p>${inlineMd(para.join(" "))}</p>`);
        para = [];
    };

    while (i < lines.length) {
        const line = lines[i];

        // fenced code
        const fence = line.match(/^```(\w*)\s*$/);
        if (fence) {
            flushPara();
            closeLists();
            const buf = [];
            i += 1;
            while (i < lines.length && !/^```\s*$/.test(lines[i])) {
                buf.push(lines[i]);
                i += 1;
            }
            out.push(`<pre><code>${esc(buf.join("\n"))}</code></pre>`);
            i += 1;
            continue;
        }

        // table: header + separator + rows
        if (
            line.includes("|") &&
            i + 1 < lines.length &&
            isTableSep(lines[i + 1])
        ) {
            flushPara();
            closeLists();
            const headers = splitTableRow(line);
            i += 2;
            const rows = [];
            while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
                rows.push(splitTableRow(lines[i]));
                i += 1;
            }
            let html = "<table><thead><tr>";
            for (const h of headers) html += `<th>${inlineMd(h)}</th>`;
            html += "</tr></thead><tbody>";
            for (const row of rows) {
                html += "<tr>";
                for (let c = 0; c < headers.length; c++) {
                    html += `<td>${inlineMd(row[c] ?? "")}</td>`;
                }
                html += "</tr>";
            }
            html += "</tbody></table>";
            out.push(html);
            continue;
        }

        // blank
        if (!line.trim()) {
            flushPara();
            closeLists();
            i += 1;
            continue;
        }

        // hr
        if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line)) {
            flushPara();
            closeLists();
            out.push("<hr>");
            i += 1;
            continue;
        }

        // headings
        const hm = line.match(/^(#{1,6})\s+(.*)$/);
        if (hm) {
            flushPara();
            closeLists();
            const level = hm[1].length;
            out.push(`<h${level}>${inlineMd(hm[2].trim())}</h${level}>`);
            i += 1;
            continue;
        }

        // unordered list
        const ul = line.match(/^\s*[-*+]\s+(.*)$/);
        if (ul) {
            flushPara();
            if (inOl) {
                out.push("</ol>");
                inOl = false;
            }
            if (!inUl) {
                out.push("<ul>");
                inUl = true;
            }
            out.push(`<li>${inlineMd(ul[1])}</li>`);
            i += 1;
            continue;
        }

        // ordered list
        const ol = line.match(/^\s*\d+\.\s+(.*)$/);
        if (ol) {
            flushPara();
            if (inUl) {
                out.push("</ul>");
                inUl = false;
            }
            if (!inOl) {
                out.push("<ol>");
                inOl = true;
            }
            out.push(`<li>${inlineMd(ol[1])}</li>`);
            i += 1;
            continue;
        }

        // blockquote
        const bq = line.match(/^\s*>\s?(.*)$/);
        if (bq) {
            flushPara();
            closeLists();
            const buf = [bq[1]];
            i += 1;
            while (i < lines.length) {
                const m = lines[i].match(/^\s*>\s?(.*)$/);
                if (!m) break;
                buf.push(m[1]);
                i += 1;
            }
            out.push(`<blockquote>${inlineMd(buf.join(" "))}</blockquote>`);
            continue;
        }

        para.push(line.trim());
        i += 1;
    }

    flushPara();
    closeLists();
    return out.join("\n");
}

function styleRenderedArticle(article) {
    article.querySelectorAll("h1,h2,h3,h4,h5,h6").forEach((h) => {
        h.style.margin = "0.7em 0 0.35em";
        h.style.lineHeight = "1.25";
    });
    article.querySelectorAll("p").forEach((p) => {
        p.style.margin = "0.45em 0";
    });
    article.querySelectorAll("a").forEach((a) => {
        a.style.color = "#8cf";
        a.setAttribute("target", "_blank");
        a.setAttribute("rel", "noopener noreferrer");
    });
    article.querySelectorAll("table").forEach((t) => {
        t.style.borderCollapse = "collapse";
        t.style.width = "100%";
        t.style.margin = "0.5em 0";
    });
    article.querySelectorAll("th,td").forEach((c) => {
        c.style.border = "1px solid #444";
        c.style.padding = "4px 8px";
        c.style.textAlign = "left";
    });
    article.querySelectorAll("th").forEach((c) => {
        c.style.background = "#1c1c1c";
    });
    article.querySelectorAll("code").forEach((c) => {
        if (c.parentElement?.tagName === "PRE") return;
        c.style.background = "#222";
        c.style.padding = "1px 4px";
        c.style.borderRadius = "3px";
        c.style.fontFamily = "ui-monospace, Consolas, monospace";
    });
    article.querySelectorAll("pre").forEach((p) => {
        p.style.background = "#1a1a1a";
        p.style.padding = "8px";
        p.style.overflow = "auto";
        p.style.borderRadius = "4px";
    });
    article.querySelectorAll("ul,ol").forEach((l) => {
        l.style.margin = "0.4em 0 0.4em 1.2em";
        l.style.paddingLeft = "0.6em";
    });
    article.querySelectorAll("blockquote").forEach((b) => {
        b.style.margin = "0.5em 0";
        b.style.padding = "0.2em 0.8em";
        b.style.borderLeft = "3px solid #555";
        b.style.opacity = "0.9";
    });
    article.querySelectorAll("hr").forEach((hr) => {
        hr.style.border = "none";
        hr.style.borderTop = "1px solid #444";
        hr.style.margin = "1em 0";
    });
}

function buildViewerDom(node) {
    ensureProps(node);

    const root = document.createElement("div");
    root.className = "vsaan212-lazy-docs";
    root.style.cssText =
        "display:flex;flex-direction:column;gap:6px;width:100%;height:100%;" +
        "min-height:320px;box-sizing:border-box;font:12px/1.4 sans-serif;color:#ddd;";

    const toolbar = document.createElement("div");
    toolbar.style.cssText =
        "display:flex;align-items:center;gap:8px;flex-wrap:wrap;flex:0 0 auto;";

    const folderLabel = document.createElement("span");
    folderLabel.style.cssText = "opacity:0.75;white-space:nowrap;";
    folderLabel.textContent = "Doc set:";

    const folderSelect = document.createElement("select");
    folderSelect.title = "Doc set under Docs/. (root) = files in Docs/ root only.";
    folderSelect.style.cssText =
        "flex:1;min-width:140px;max-width:260px;padding:3px 6px;" +
        "background:#1e1e1e;border:1px solid #444;color:#eee;border-radius:3px;";

    const refreshBtn = document.createElement("button");
    refreshBtn.textContent = "Refresh";
    refreshBtn.style.cssText =
        "padding:3px 10px;cursor:pointer;background:#333;border:1px solid #555;" +
        "color:#eee;border-radius:3px;";

    const rawLabel = document.createElement("label");
    rawLabel.style.cssText = "display:flex;align-items:center;gap:4px;cursor:pointer;user-select:none;";
    const rawToggle = document.createElement("input");
    rawToggle.type = "checkbox";
    rawToggle.checked = !!node.properties.docs_raw;
    rawLabel.appendChild(rawToggle);
    rawLabel.appendChild(document.createTextNode("Raw"));

    const status = document.createElement("span");
    status.style.cssText = "opacity:0.7;flex:1;min-width:80px;overflow:hidden;text-overflow:ellipsis;";

    toolbar.appendChild(folderLabel);
    toolbar.appendChild(folderSelect);
    toolbar.appendChild(refreshBtn);
    toolbar.appendChild(rawLabel);
    toolbar.appendChild(status);

    const panes = document.createElement("div");
    panes.style.cssText =
        "display:flex;gap:8px;flex:1 1 auto;min-height:280px;overflow:hidden;" +
        "border:1px solid #333;border-radius:4px;background:#141414;";

    const indexPane = document.createElement("nav");
    indexPane.style.cssText =
        "flex:0 0 28%;max-width:280px;min-width:140px;overflow:auto;" +
        "border-right:1px solid #333;padding:6px 0;";

    const contentPane = document.createElement("div");
    contentPane.style.cssText =
        "flex:1 1 auto;overflow:auto;padding:10px 12px;min-width:0;";

    panes.appendChild(indexPane);
    panes.appendChild(contentPane);
    root.appendChild(toolbar);
    root.appendChild(panes);

    let entries = [];
    let currentPath = String(node.properties.docs_selected || "");
    let currentPayload = null;

    function renderContent() {
        contentPane.innerHTML = "";
        if (!currentPayload) {
            const empty = document.createElement("div");
            empty.style.opacity = "0.6";
            empty.textContent = entries.length
                ? "Select a document from the index."
                : "No Markdown files in this folder.";
            contentPane.appendChild(empty);
            return;
        }
        if (currentPayload.error) {
            const err = document.createElement("div");
            err.style.color = "#f88";
            err.textContent = currentPayload.error;
            contentPane.appendChild(err);
            return;
        }
        if (rawToggle.checked) {
            const pre = document.createElement("pre");
            pre.style.cssText =
                "margin:0;white-space:pre-wrap;word-break:break-word;font:12px/1.45 monospace;";
            pre.textContent = currentPayload.raw || "";
            contentPane.appendChild(pre);
        } else {
            // Render on the client from Markdown source (same approach as
            // utilities → Markdown Note). Do not rely on server HTML — Comfy's
            // venv often lacks the Python `markdown` package.
            const article = document.createElement("article");
            article.className = "vsaan212-lazy-docs-html";
            article.style.cssText = "line-height:1.5;color:#ddd;";
            article.innerHTML = renderMarkdownToHtml(currentPayload.raw || "");
            styleRenderedArticle(article);
            contentPane.appendChild(article);
        }
    }

    function highlightIndex() {
        indexPane.querySelectorAll("a[data-path]").forEach((a) => {
            const active = a.getAttribute("data-path") === currentPath;
            a.style.background = active ? "#2a3a4a" : "transparent";
            a.style.fontWeight = active ? "600" : "400";
        });
    }

    function renderIndex() {
        indexPane.innerHTML = "";
        if (!entries.length) {
            const empty = document.createElement("div");
            empty.style.cssText = "padding:8px 10px;opacity:0.6;";
            empty.textContent = "No .md files";
            indexPane.appendChild(empty);
            return;
        }
        for (const entry of entries) {
            const a = document.createElement("a");
            a.href = "#";
            a.setAttribute("data-path", entry.path);
            a.textContent = entry.title;
            a.title = entry.path;
            a.style.cssText =
                "display:block;padding:6px 10px;color:#cde;text-decoration:none;" +
                "border-left:3px solid transparent;cursor:pointer;";
            a.onmouseenter = () => {
                if (a.getAttribute("data-path") !== currentPath) a.style.background = "#1c1c1c";
            };
            a.onmouseleave = () => highlightIndex();
            a.onclick = (ev) => {
                ev.preventDefault();
                loadContent(entry.path);
            };
            indexPane.appendChild(a);
        }
        highlightIndex();
    }

    async function loadContent(path) {
        if (!path) {
            currentPath = "";
            currentPayload = null;
            node.properties.docs_selected = "";
            renderContent();
            highlightIndex();
            return;
        }
        status.textContent = "Loading…";
        try {
            const data = await fetchJson(
                `${API}/content?path=${encodeURIComponent(path)}`
            );
            currentPayload = data;
            currentPath = data.error ? "" : path;
            node.properties.docs_selected = currentPath;
            status.textContent = data.error ? data.error : data.title || path;
            renderContent();
            highlightIndex();
            node.setDirtyCanvas?.(true, true);
        } catch (e) {
            status.textContent = "Failed to load";
            currentPayload = { error: String(e) };
            renderContent();
        }
    }

    function syncFolderSelectFromWidget() {
        const w = getSubfolderWidget(node);
        const values = Array.isArray(w?.options?.values)
            ? w.options.values
            : [ROOT_LABEL];
        const current = folderToWidget(w?.value ?? node.properties.docs_subfolder);
        folderSelect.innerHTML = "";
        for (const v of values) {
            const opt = document.createElement("option");
            opt.value = v;
            opt.textContent = v;
            folderSelect.appendChild(opt);
        }
        folderSelect.value = values.includes(current) ? current : ROOT_LABEL;
    }

    async function loadIndex(preferPath) {
        const folder = getSubfolder(node);
        syncFolderSelectFromWidget();
        status.textContent = "Refreshing…";
        try {
            const data = await fetchJson(
                `${API}/index?folder=${encodeURIComponent(folder)}`
            );
            if (data.error) {
                status.textContent = data.error;
                entries = [];
                currentPayload = { error: data.error };
                renderIndex();
                renderContent();
                return;
            }
            entries = data.entries || [];
            status.textContent = folder
                ? `Docs/${folder} · ${entries.length} file(s)`
                : `Docs/ · ${entries.length} file(s)`;
            renderIndex();

            const want =
                preferPath ||
                node.properties.docs_selected ||
                (entries[0] && entries[0].path) ||
                "";
            const exists = entries.some((e) => e.path === want);
            if (exists) {
                await loadContent(want);
            } else if (entries[0]) {
                await loadContent(entries[0].path);
            } else {
                await loadContent("");
            }
        } catch (e) {
            status.textContent = "Index failed";
            entries = [];
            currentPayload = { error: String(e) };
            renderIndex();
            renderContent();
        }
    }

    folderSelect.onchange = () => {
        setSubfolder(node, folderSelect.value);
        node.properties.docs_selected = "";
        loadIndex("");
        node.setDirtyCanvas?.(true, true);
    };

    refreshBtn.onclick = async () => {
        await refreshFolderChoices(node, folderSelect.value);
        syncFolderSelectFromWidget();
        await loadIndex(currentPath);
    };

    rawToggle.onchange = () => {
        node.properties.docs_raw = !!rawToggle.checked;
        renderContent();
        node.setDirtyCanvas?.(true, true);
    };

    node.__lazyDocsReload = async () => {
        await refreshFolderChoices(node, getSubfolderWidget(node)?.value);
        syncFolderSelectFromWidget();
        await loadIndex(node.properties.docs_selected || currentPath);
    };

    setTimeout(async () => {
        await refreshFolderChoices(node, getSubfolderWidget(node)?.value);
        syncFolderSelectFromWidget();
        await loadIndex(node.properties.docs_selected || "");
    }, 0);

    return root;
}

app.registerExtension({
    name: "Vsaan212.LazyDocs",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LazyDocs") return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);
            const node = this;
            ensureProps(node);

            const subW = getSubfolderWidget(node);
            if (subW) {
                // Migrate legacy empty-string / free-text saves to combo labels.
                subW.value = folderToWidget(
                    node.properties.docs_subfolder || subW.value || ROOT_LABEL
                );
                node.properties.docs_subfolder = folderToWidget(subW.value);
                const prev = subW.callback;
                subW.callback = function (v) {
                    if (prev) prev.apply(this, arguments);
                    node.properties.docs_subfolder = folderToWidget(v);
                    node.properties.docs_selected = "";
                    if (node.__lazyDocsReload) node.__lazyDocsReload();
                };
            }

            const wrap = buildViewerDom(node);
            const domOpts = {
                getMinHeight: () => 320,
                getMaxHeight: () => 1200,
                getMinWidth: () => NODE_MIN_WIDTH,
            };
            if (typeof node.addDOMWidget === "function") {
                node.addDOMWidget("lazy_docs_viewer", "docs", wrap, domOpts);
            } else if (node.domElement) {
                node.domElement.appendChild(wrap);
            }

            ensureNodeMinSize(node);
            requestAnimationFrame(() => ensureNodeMinSize(node));
        };

        const origOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            if (origOnConfigure) origOnConfigure.apply(this, arguments);
            ensureProps(this);
            const w = getSubfolderWidget(this);
            if (w) {
                w.value = folderToWidget(
                    this.properties.docs_subfolder || w.value || ROOT_LABEL
                );
                this.properties.docs_subfolder = folderToWidget(w.value);
            }
            if (this.__lazyDocsReload) {
                setTimeout(() => this.__lazyDocsReload(), 0);
            }
        };

        const origGetExtra = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (_, options) {
            if (origGetExtra) origGetExtra.apply(this, arguments);
            const node = this;
            options.push({
                content: "Refresh Lazy Docs sets",
                callback: async () => {
                    await refreshFolderChoices(node, getSubfolderWidget(node)?.value);
                    if (node.__lazyDocsReload) await node.__lazyDocsReload();
                    node.setDirtyCanvas?.(true, true);
                },
            });
        };
    },
});