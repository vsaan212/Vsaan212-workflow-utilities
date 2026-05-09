import { app } from "../../scripts/app.js";

function parseLines(text) {
    if (!text) return [];
    return text
        .split(/\r?\n/)
        .map((s) => s.trim())
        .filter(Boolean);
}

/** @param {string} s */
function parseSelectedIndices(s) {
    const set = new Set();
    if (!s) return set;
    for (const part of String(s).split(",")) {
        const n = parseInt(part.trim(), 10);
        if (!Number.isNaN(n)) set.add(n);
    }
    return set;
}

/** @param {Set<number>} set */
function serializeIndices(set) {
    return [...set].sort((a, b) => a - b).join(",");
}

/** Drop indices outside [0, len) */
function clampSelectionToLines(set, len) {
    const next = new Set();
    for (const i of set) {
        if (i >= 0 && i < len) next.add(i);
    }
    return next;
}

app.registerExtension({
    name: "Vsaan212.PromptGarnish",

    async beforeRegisterNodeDef(nodeType, nodeData, appInstance) {
        if (nodeData.name !== "Vsaan_PromptGarnish") return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);

            const node = this;
            const phraseListWidget = node.widgets.find((w) => w.name === "phrase_list");
            const selectedIndicesWidget = node.widgets.find((w) => w.name === "selected_indices");

            if (!phraseListWidget || !selectedIndicesWidget) return;

            const boxWrap = document.createElement("div");
            boxWrap.className = "vsaan-prompt-garnish-checkboxes";
            boxWrap.style.cssText =
                "margin:4px 0 2px 0;padding:4px 6px;border:1px solid rgba(255,255,255,0.12);border-radius:6px;max-height:220px;overflow:auto;font-size:12px;";

            function getLines() {
                return parseLines(phraseListWidget.value);
            }

            function getSelection() {
                const lines = getLines();
                let set = parseSelectedIndices(selectedIndicesWidget.value);
                set = clampSelectionToLines(set, lines.length);
                return set;
            }

            function setSelection(set) {
                const lines = getLines();
                const clamped = clampSelectionToLines(set, lines.length);
                selectedIndicesWidget.value = serializeIndices(clamped);
            }

            function syncSelectionToLines() {
                const lines = getLines();
                let set = parseSelectedIndices(selectedIndicesWidget.value);
                set = clampSelectionToLines(set, lines.length);
                selectedIndicesWidget.value = serializeIndices(set);
            }

            function renderCheckboxes() {
                boxWrap.innerHTML = "";
                const lines = getLines();
                syncSelectionToLines();
                const selected = getSelection();

                if (lines.length === 0) {
                    const empty = document.createElement("div");
                    empty.textContent = "(no lines - use Add line)";
                    empty.style.opacity = "0.7";
                    boxWrap.appendChild(empty);
                    node.setDirtyCanvas(true, true);
                    return;
                }

                lines.forEach((line, i) => {
                    const row = document.createElement("div");
                    row.style.cssText =
                        "display:flex;align-items:flex-start;gap:6px;margin:3px 0;cursor:pointer;";

                    const cb = document.createElement("input");
                    cb.type = "checkbox";
                    cb.checked = selected.has(i);
                    cb.style.marginTop = "2px";
                    cb.id = `vsaan_pg_${node.id}_${i}`;

                    const label = document.createElement("label");
                    label.setAttribute("for", cb.id);
                    const display = line.length > 96 ? line.slice(0, 93) + "…" : line;
                    label.textContent = display;
                    label.title = line;
                    label.style.cssText =
                        "flex:1;word-break:break-word;cursor:pointer;line-height:1.35;";

                    cb.onchange = () => {
                        const sel = getSelection();
                        if (cb.checked) sel.add(i);
                        else sel.delete(i);
                        setSelection(sel);
                        renderCheckboxes();
                        node.setDirtyCanvas(true, true);
                    };

                    row.appendChild(cb);
                    row.appendChild(label);
                    boxWrap.appendChild(row);
                });

                node.setDirtyCanvas(true, true);
            }

            node.addDOMWidget("garnish_pick", "pick", boxWrap, {
                getMinHeight: () => 72,
                getMaxHeight: () => 240,
            });

            node.addWidget("button", "Add line", null, () => {
                const cur = phraseListWidget.value || "";
                const add = window.prompt("New phrase line (empty cancels):", "");
                if (add === null) return;
                const next = cur.replace(/\s*$/, "") + (cur.trim() ? "\n" : "") + add;
                phraseListWidget.value = next;
                const lines = parseLines(next);
                const sel = getSelection();
                sel.add(lines.length - 1);
                setSelection(sel);
                renderCheckboxes();
                node.setDirtyCanvas(true, true);
            });

            node.addWidget("button", "Delete checked lines", null, () => {
                const lines = getLines();
                if (lines.length === 0) return;
                const sel = getSelection();
                if (sel.size === 0) return;
                const toRemove = [...sel].sort((a, b) => b - a);
                for (const idx of toRemove) {
                    lines.splice(idx, 1);
                }
                phraseListWidget.value = lines.join("\n");
                selectedIndicesWidget.value = "";
                renderCheckboxes();
                node.setDirtyCanvas(true, true);
            });

            const origPhraseCb = phraseListWidget.callback;
            phraseListWidget.callback = function (v) {
                if (origPhraseCb) origPhraseCb.apply(this, arguments);
                syncSelectionToLines();
                renderCheckboxes();
            };

            const origSelCb = selectedIndicesWidget.callback;
            selectedIndicesWidget.callback = function (v) {
                if (origSelCb) origSelCb.apply(this, arguments);
                renderCheckboxes();
            };

            if (selectedIndicesWidget.hidden !== undefined) {
                selectedIndicesWidget.hidden = true;
            }
            try {
                const el = selectedIndicesWidget.domEl || selectedIndicesWidget.inputEl;
                let p = el;
                for (let i = 0; i < 6 && p; i++) {
                    if (p.classList?.contains?.("lg-widget") || p.classList?.contains?.("widget")) {
                        p.style.display = "none";
                        break;
                    }
                    p = p.parentElement;
                }
            } catch (_) {}

            renderCheckboxes();
        };
    },
});
