/**
 * Lazy Multi Frame Select — grid of VAE Decode frames, pick up to 6, continue.
 */
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_CLASS = "LazyMultiFrameSelect";
const EVENT_NAME = "vsaan212-multi-frame-select";
const API = "/vsaan212/multi-frame-select";
const MAX_SELECT = 6;
const NODE_MIN_WIDTH = 420;
const NODE_MIN_HEIGHT = 460;
const STYLE_ID = "vsaan212-lazy-mfs-style";

const liveNodes = new Set();

function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
.lazy-mfs { display:flex; flex-direction:column; gap:6px; height:100%; min-height:280px;
    font: 12px/1.35 sans-serif; color:#ddd; user-select:none; }
.lazy-mfs-status { padding:6px 8px; border-radius:6px; background:rgba(255,255,255,0.06);
    border:1px solid rgba(255,255,255,0.08); }
.lazy-mfs-status.waiting { background:rgba(180,120,20,0.22); border-color:rgba(230,170,50,0.45); color:#f3d48a; }
.lazy-mfs-status.done { background:rgba(40,120,60,0.18); border-color:rgba(80,180,100,0.4); color:#b6e0c0; }
.lazy-mfs-bar { display:flex; gap:6px; flex-wrap:wrap; }
.lazy-mfs-bar button { pointer-events:auto; cursor:pointer; padding:5px 10px; border-radius:6px;
    border:1px solid rgba(255,255,255,0.16); background:#2a2a2a; color:#eee; font-weight:600; }
.lazy-mfs-bar button.primary { background:#3d6d3d; border-color:#6aad6a; }
.lazy-mfs-bar button:disabled { opacity:0.45; cursor:default; }
.lazy-mfs-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(76px, 1fr));
    gap:6px; overflow:auto; flex:1; min-height:180px; padding:2px; pointer-events:auto; }
.lazy-mfs-cell { position:relative; aspect-ratio:1; border-radius:6px; overflow:hidden;
    border:2px solid transparent; background:#111; cursor:pointer; }
.lazy-mfs-cell img { width:100%; height:100%; object-fit:cover; display:block; pointer-events:none; }
.lazy-mfs-cell .idx { position:absolute; left:4px; bottom:4px; font-size:10px; padding:1px 4px;
    border-radius:4px; background:rgba(0,0,0,0.65); }
.lazy-mfs-cell.selected { border-color:#e0b84a; box-shadow:0 0 0 1px rgba(224,184,74,0.5) inset; }
.lazy-mfs-cell .slot { position:absolute; right:4px; top:4px; min-width:16px; height:16px;
    padding:0 4px; border-radius:999px; background:#e0b84a; color:#221; font-size:10px;
    font-weight:700; display:flex; align-items:center; justify-content:center; }
.lazy-mfs-cell.disabled { cursor:default; opacity:0.55; }
`;
    document.head.appendChild(style);
}

function viewUrl(img) {
    const p = new URLSearchParams();
    p.set("filename", img.filename);
    p.set("type", img.type || "temp");
    p.set("subfolder", img.subfolder || "");
    const route = `/view?${p.toString()}`;
    return typeof api.apiURL === "function" ? api.apiURL(route) : route;
}

function unwrapDetail(event) {
    let d = event?.detail;
    if (Array.isArray(d)) d = d[0];
    return d || null;
}

function findNode(nodeId) {
    const id = String(nodeId);
    if (app.graph?.getNodeById) {
        const n = app.graph.getNodeById(nodeId) || app.graph.getNodeById(Number(nodeId));
        if (n) return n;
    }
    for (const node of liveNodes) {
        if (String(node.id) === id) return node;
    }
    const nodes = app.graph?._nodes || [];
    const match = nodes.find((n) => String(n.id) === id);
    if (match) return match;
    const ours = [...liveNodes];
    if (ours.length === 1) return ours[0];
    return null;
}

function hideNativePreview(node) {
    if (!node) return;
    node.imgs = undefined;
}

function ensureNodeMinSize(node) {
    if (!node.size) node.size = [NODE_MIN_WIDTH, NODE_MIN_HEIGHT];
    if (node.size[0] < NODE_MIN_WIDTH) node.size[0] = NODE_MIN_WIDTH;
    if (node.size[1] < NODE_MIN_HEIGHT) node.size[1] = NODE_MIN_HEIGHT;
}

function buildUi(node) {
    ensureStyle();

    const root = document.createElement("div");
    root.className = "lazy-mfs";

    const status = document.createElement("div");
    status.className = "lazy-mfs-status";
    status.textContent = "Idle — queue the workflow to pick frames from VAE Decode.";

    const bar = document.createElement("div");
    bar.className = "lazy-mfs-bar";

    const continueBtn = document.createElement("button");
    continueBtn.className = "primary";
    continueBtn.textContent = "Continue";
    continueBtn.disabled = true;

    const clearBtn = document.createElement("button");
    clearBtn.textContent = "Clear";
    clearBtn.disabled = true;

    const cancelBtn = document.createElement("button");
    cancelBtn.textContent = "Cancel";
    cancelBtn.disabled = true;

    bar.append(continueBtn, clearBtn, cancelBtn);

    const grid = document.createElement("div");
    grid.className = "lazy-mfs-grid";

    root.append(status, bar, grid);

    const state = {
        waiting: false,
        promptId: "",
        nodeId: "",
        images: [],
        selected: [],
        maxSelect: MAX_SELECT,
    };

    function setStatus(text, mode) {
        status.textContent = text;
        status.classList.remove("waiting", "done");
        if (mode) status.classList.add(mode);
    }

    function canEdit() {
        return state.waiting;
    }

    function render() {
        grid.innerHTML = "";
        const n = state.images.length;
        if (!n) {
            const empty = document.createElement("div");
            empty.style.opacity = "0.7";
            empty.style.padding = "8px";
            empty.textContent = "No frames yet.";
            grid.appendChild(empty);
            return;
        }
        state.images.forEach((img, i) => {
            const cell = document.createElement("div");
            cell.className = "lazy-mfs-cell";
            if (!canEdit()) cell.classList.add("disabled");
            const slot = state.selected.indexOf(i);
            if (slot >= 0) {
                cell.classList.add("selected");
                const badge = document.createElement("span");
                badge.className = "slot";
                badge.textContent = String(slot + 1);
                cell.appendChild(badge);
            }
            const picture = document.createElement("img");
            picture.alt = `Frame ${i + 1}`;
            picture.src = viewUrl(img);
            const idx = document.createElement("span");
            idx.className = "idx";
            idx.textContent = String(i + 1);
            cell.append(picture, idx);
            cell.addEventListener("pointerdown", (e) => e.stopPropagation());
            cell.addEventListener("mousedown", (e) => e.stopPropagation());
            cell.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (!canEdit()) return;
                toggle(i);
            });
            grid.appendChild(cell);
        });
    }

    function toggle(i) {
        const pos = state.selected.indexOf(i);
        if (pos >= 0) {
            state.selected.splice(pos, 1);
        } else if (state.selected.length < state.maxSelect) {
            state.selected.push(i);
        }
        updateChrome();
        render();
        node.setDirtyCanvas?.(true, true);
    }

    function updateChrome() {
        const waiting = state.waiting;
        continueBtn.disabled = !waiting;
        clearBtn.disabled = !waiting || state.selected.length === 0;
        cancelBtn.disabled = !waiting;
        const n = state.images.length;
        const picked = state.selected.length;
        if (waiting) {
            setStatus(
                `Waiting — click up to ${state.maxSelect} frames (${picked}/${state.maxSelect} selected, ${n} total). Click again to deselect.`,
                "waiting"
            );
        }
    }

    async function post(body) {
        const res = await api.fetchApi(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        return res.json();
    }

    function stopNodeDrag(el) {
        el.addEventListener("pointerdown", (e) => e.stopPropagation());
        el.addEventListener("mousedown", (e) => e.stopPropagation());
    }
    stopNodeDrag(root);
    stopNodeDrag(bar);

    continueBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!state.waiting) return;
        continueBtn.disabled = true;
        cancelBtn.disabled = true;
        clearBtn.disabled = true;
        setStatus("Continuing with selected frames…", "waiting");
        try {
            await post({
                action: "continue",
                node_id: state.nodeId || String(node.id),
                prompt_id: state.promptId,
                indices: state.selected.slice(),
            });
        } catch (err) {
            setStatus(`Continue failed: ${err}`, "waiting");
            updateChrome();
            return;
        }
        state.waiting = false;
        setStatus(
            `Selected ${state.selected.length} frame(s)` +
                (state.selected.length
                    ? ` → outputs ${state.selected.map((i) => i + 1).join(", ")}`
                    : " (all slots empty)"),
            "done"
        );
        updateChrome();
        render();
    });

    clearBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!state.waiting) return;
        state.selected = [];
        updateChrome();
        render();
    });

    cancelBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!state.waiting) return;
        cancelBtn.disabled = true;
        continueBtn.disabled = true;
        setStatus("Cancelling…", "waiting");
        try {
            await post({
                action: "cancel",
                node_id: state.nodeId || String(node.id),
                prompt_id: state.promptId,
            });
        } catch (_) {}
        if (typeof api.interrupt === "function") {
            try {
                api.interrupt();
            } catch (_) {}
        }
        state.waiting = false;
        setStatus("Cancelled.", "done");
        updateChrome();
        render();
    });

    node._lazyMfsShow = function (data) {
        state.waiting = true;
        state.promptId = String(data.prompt_id || "");
        state.nodeId = String(data.node_id || node.id);
        state.images = Array.isArray(data.images) ? data.images : [];
        state.selected = [];
        state.maxSelect = Number(data.max_select) || MAX_SELECT;
        updateChrome();
        render();
        hideNativePreview(node);
        node.setDirtyCanvas?.(true, true);
    };

    updateChrome();
    render();
    return root;
}

app.registerExtension({
    name: "Vsaan212.LazyMultiFrameSelect",

    async setup() {
        api.addEventListener(EVENT_NAME, (event) => {
            const data = unwrapDetail(event);
            if (!data?.node_id) return;
            const node = findNode(data.node_id);
            if (node && typeof node._lazyMfsShow === "function") {
                node._lazyMfsShow(data);
            }
        });
    },

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_CLASS) return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = origOnNodeCreated?.apply(this, arguments);
            const node = this;
            liveNodes.add(node);
            const wrap = buildUi(node);
            const domOpts = {
                getMinHeight: () => 280,
                getMaxHeight: () => 1100,
                getMinWidth: () => NODE_MIN_WIDTH,
            };
            if (typeof node.addDOMWidget === "function") {
                node.addDOMWidget("lazy_mfs_grid", "frames", wrap, domOpts);
            } else if (node.domElement) {
                node.domElement.appendChild(wrap);
            }
            ensureNodeMinSize(node);
            requestAnimationFrame(() => ensureNodeMinSize(node));
            return r;
        };

        const origOnRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            liveNodes.delete(this);
            return origOnRemoved?.apply(this, arguments);
        };

        const origOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const r = origOnExecuted?.apply(this, arguments);
            hideNativePreview(this);
            return r;
        };

        const origOnDrawBackground = nodeType.prototype.onDrawBackground;
        nodeType.prototype.onDrawBackground = function (ctx) {
            const r = origOnDrawBackground?.apply(this, arguments);
            hideNativePreview(this);
            return r;
        };
    },
});
