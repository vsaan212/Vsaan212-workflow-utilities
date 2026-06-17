/**
 * Lazy Image Loader — browse, drag-and-drop upload, open input folder,
 * aspect-ratio cover crop with live drag-to-position preview.
 */
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_CLASS = "LazyImageLoader";
const API = "/lazy_image_loader";
const PREVIEW_WIDTH = 240;

const RATIO_VALUES = {
    "9:16 (Phone)": 9 / 16,
    "16:9 (Landscape)": 16 / 9,
    "1:1 (Square)": 1,
    "4:5 (Instagram)": 4 / 5,
    "3:4 (Portrait)": 3 / 4,
    "4:3 (Classic)": 4 / 3,
    "2:3 (Photo)": 2 / 3,
    "21:9 (Ultrawide)": 21 / 9,
    "Original (no crop)": null,
};

function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
}

function widget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function setWidgetValue(node, name, value) {
    const w = widget(node, name);
    if (!w) return;
    w.value = value;
    if (typeof w.callback === "function") w.callback(value);
}

function hideWidgetRow(w) {
    if (!w) return;
    if (w.hidden !== undefined) w.hidden = true;
    try {
        const el = w.inputEl || w.domEl;
        let p = el?.parentElement;
        for (let i = 0; i < 6 && p; i++) {
            if (p.classList?.contains("comfy-widget") || p.classList?.contains("widget")) {
                p.style.display = "none";
                break;
            }
            p = p.parentElement;
        }
    } catch (_) {}
}

function computeCropBox(srcW, srcH, targetRatio, offsetX, offsetY, zoom = 1) {
    const z = Math.max(1, Number(zoom) || 1);
    const srcRatio = srcW / srcH;
    let cropW;
    let cropH;
    if (srcRatio > targetRatio) {
        cropH = srcH;
        cropW = Math.max(1, Math.round(srcH * targetRatio));
    } else {
        cropW = srcW;
        cropH = Math.max(1, Math.round(srcW / targetRatio));
    }
    cropW = Math.max(1, Math.round(cropW / z));
    cropH = Math.max(1, Math.round(cropH / z));
    const maxOx = Math.max(0, srcW - cropW) / 2;
    const maxOy = Math.max(0, srcH - cropH) / 2;
    const ox = clamp(offsetX, -1, 1);
    const oy = clamp(offsetY, -1, 1);
    let left = Math.round((srcW - cropW) / 2 + ox * maxOx);
    let top = Math.round((srcH - cropH) / 2 + oy * maxOy);
    left = clamp(left, 0, srcW - cropW);
    top = clamp(top, 0, srcH - cropH);
    return { left, top, cropW, cropH, maxOx, maxOy };
}

function previewFrameSize(targetRatio) {
    if (!targetRatio) return [PREVIEW_WIDTH, Math.round(PREVIEW_WIDTH * 4 / 3)];
    if (targetRatio < 1) {
        const h = 360;
        return [Math.round(h * targetRatio), h];
    }
    const w = PREVIEW_WIDTH;
    return [w, Math.round(w / targetRatio)];
}

async function fetchImageList() {
    const res = await api.fetchApi(`${API}/images`);
    if (!res.ok) return [];
    return res.json();
}

async function uploadImageFile(file) {
    const body = new FormData();
    body.append("image", file, file.name);
    body.append("overwrite", "true");
    const res = await api.fetchApi("/upload/image", { method: "POST", body });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    const data = await res.json();
    return data.name || data.filename || file.name;
}

function viewUrl(filename) {
    const subfolder = filename.includes("/") ? filename.slice(0, filename.lastIndexOf("/")) : "";
    const name = filename.includes("/") ? filename.slice(filename.lastIndexOf("/") + 1) : filename;
    const params = new URLSearchParams({
        filename: name,
        type: "input",
        subfolder,
        rand: String(Math.random()),
    });
    const route = `/view?${params}`;
    return typeof api.apiURL === "function" ? api.apiURL(route) : route;
}

function buildUi(node) {
    const imageW = widget(node, "image");
    const aspectW = widget(node, "aspect_ratio");
    const autoCropW = widget(node, "auto_crop");
    const offsetXW = widget(node, "offset_x");
    const offsetYW = widget(node, "offset_y");
    const zoomW = widget(node, "zoom");
    if (!imageW || !aspectW || !autoCropW) return;

    hideWidgetRow(offsetXW);
    hideWidgetRow(offsetYW);
    hideWidgetRow(zoomW);

    const root = document.createElement("div");
    root.className = "vsaan-lazy-image-loader";
    root.style.cssText =
        "display:flex;flex-direction:column;gap:6px;margin:4px 0;font-size:12px;";

    const toolbar = document.createElement("div");
    toolbar.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;";

    const btnStyle =
        "flex:1;min-width:72px;padding:5px 8px;border-radius:6px;border:1px solid rgba(255,255,255,0.18);background:rgba(255,255,255,0.06);color:inherit;cursor:pointer;";

    const browseBtn = document.createElement("button");
    browseBtn.type = "button";
    browseBtn.textContent = "Browse…";
    browseBtn.style.cssText = btnStyle;

    const folderBtn = document.createElement("button");
    folderBtn.type = "button";
    folderBtn.textContent = "Open input folder";
    folderBtn.style.cssText = btnStyle;

    const resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.textContent = "Center crop";
    resetBtn.style.cssText = btnStyle;

    toolbar.append(browseBtn, folderBtn, resetBtn);

    const hint = document.createElement("div");
    hint.style.cssText = "opacity:0.72;line-height:1.35;";
    hint.textContent = "Drag the preview to pan. Zoom in to trim dead space, then pan to frame.";

    const controls = document.createElement("div");
    controls.style.cssText = "display:flex;flex-direction:column;gap:4px;";

    const zoomRow = document.createElement("div");
    zoomRow.style.cssText = "display:flex;align-items:center;gap:8px;";
    const zoomLabel = document.createElement("span");
    zoomLabel.textContent = "Zoom";
    zoomLabel.style.minWidth = "36px";
    const zoomRange = document.createElement("input");
    zoomRange.type = "range";
    zoomRange.min = "1";
    zoomRange.max = "4";
    zoomRange.step = "0.05";
    zoomRange.value = String(zoomW?.value ?? 1);
    zoomRange.style.flex = "1";
    const zoomValue = document.createElement("span");
    zoomValue.style.minWidth = "40px";
    zoomValue.style.textAlign = "right";
    zoomRow.append(zoomLabel, zoomRange, zoomValue);

    const panReadout = document.createElement("div");
    panReadout.style.cssText = "opacity:0.75;font-size:11px;font-variant-numeric:tabular-nums;";
    controls.append(zoomRow, panReadout);

    const frame = document.createElement("div");
    frame.style.cssText =
        "position:relative;margin:0 auto;border:1px solid rgba(255,255,255,0.22);border-radius:8px;overflow:hidden;background:#111;touch-action:none;";

    const canvas = document.createElement("canvas");
    canvas.style.cssText = "display:block;width:100%;height:100%;cursor:grab;";
    frame.appendChild(canvas);

    const dropOverlay = document.createElement("div");
    dropOverlay.style.cssText =
        "display:none;position:absolute;inset:0;align-items:center;justify-content:center;background:rgba(80,140,255,0.22);border:2px dashed rgba(140,190,255,0.85);font-weight:600;pointer-events:none;";
    dropOverlay.textContent = "Drop image";
    frame.appendChild(dropOverlay);

    const status = document.createElement("div");
    status.style.cssText = "opacity:0.8;min-height:16px;";

    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";
    fileInput.style.display = "none";
    root.append(toolbar, hint, frame, controls, status, fileInput);

    function currentZoom() {
        return Math.max(1, Number(zoomW?.value) || 1);
    }

    function syncPanReadout() {
        const ox = Number(offsetXW?.value) || 0;
        const oy = Number(offsetYW?.value) || 0;
        const z = currentZoom();
        panReadout.textContent = `Pan X ${ox.toFixed(2)} · Y ${oy.toFixed(2)} · Zoom ${z.toFixed(2)}×`;
        zoomValue.textContent = `${z.toFixed(2)}×`;
        if (Math.abs(Number(zoomRange.value) - z) > 0.001) {
            zoomRange.value = String(z);
        }
    }

    const state = {
        img: null,
        imgName: "",
        dragging: false,
        lastX: 0,
        lastY: 0,
    };

    function targetRatio() {
        if (!autoCropW.value) return null;
        return RATIO_VALUES[aspectW.value] ?? 9 / 16;
    }

    function canPan() {
        return !!state.img && autoCropW.value && targetRatio() !== null;
    }

    function resizeFrame() {
        const ratio = targetRatio();
        const [fw, fh] = previewFrameSize(ratio);
        frame.style.width = `${fw}px`;
        frame.style.height = `${fh}px`;
        canvas.width = fw;
        canvas.height = fh;
    }

    function drawPreview() {
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#111";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        if (!state.img) {
            ctx.fillStyle = "rgba(255,255,255,0.45)";
            ctx.font = "13px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("No image selected", canvas.width / 2, canvas.height / 2);
            return;
        }

        const ratio = targetRatio();
        if (!ratio) {
            const scale = Math.min(canvas.width / state.img.width, canvas.height / state.img.height);
            const dw = state.img.width * scale;
            const dh = state.img.height * scale;
            const dx = (canvas.width - dw) / 2;
            const dy = (canvas.height - dh) / 2;
            ctx.drawImage(state.img, dx, dy, dw, dh);
            return;
        }

        const ox = Number(offsetXW?.value) || 0;
        const oy = Number(offsetYW?.value) || 0;
        const box = computeCropBox(
            state.img.width,
            state.img.height,
            ratio,
            ox,
            oy,
            currentZoom(),
        );
        ctx.drawImage(
            state.img,
            box.left,
            box.top,
            box.cropW,
            box.cropH,
            0,
            0,
            canvas.width,
            canvas.height,
        );
        syncPanReadout();
    }

    async function refreshImageList(selectName) {
        const names = await fetchImageList();
        if (imageW.options) imageW.options.values = names;
        if (selectName && names.includes(selectName)) {
            setWidgetValue(node, "image", selectName);
        }
    }

    async function loadPreview(filename) {
        state.imgName = filename || "";
        state.img = null;
        resizeFrame();
        if (!filename) {
            drawPreview();
            status.textContent = "";
            return;
        }
        status.textContent = "Loading preview…";
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => {
            state.img = img;
            status.textContent = `${filename} — ${img.width}×${img.height}`;
            drawPreview();
            node.setDirtyCanvas?.(true, true);
        };
        img.onerror = () => {
            status.textContent = `Could not preview: ${filename}`;
            drawPreview();
        };
        img.src = viewUrl(filename);
    }

    async function handleFile(file) {
        if (!file || !file.type?.startsWith("image/")) return;
        status.textContent = "Uploading…";
        try {
            const name = await uploadImageFile(file);
            await refreshImageList(name);
            setWidgetValue(node, "offset_x", 0);
            setWidgetValue(node, "offset_y", 0);
            setWidgetValue(node, "zoom", 1);
            await loadPreview(name);
        } catch (err) {
            status.textContent = String(err?.message || err);
        }
    }

    browseBtn.onclick = () => fileInput.click();
    fileInput.onchange = () => {
        const file = fileInput.files?.[0];
        fileInput.value = "";
        if (file) handleFile(file);
    };

    folderBtn.onclick = async () => {
        try {
            const res = await api.fetchApi(`${API}/open-input`, { method: "POST" });
            const data = await res.json();
            if (data.path) status.textContent = `Opened: ${data.path}`;
        } catch (err) {
            status.textContent = String(err?.message || err);
        }
    };

    resetBtn.onclick = () => {
        setWidgetValue(node, "offset_x", 0);
        setWidgetValue(node, "offset_y", 0);
        setWidgetValue(node, "zoom", 1);
        drawPreview();
        node.setDirtyCanvas?.(true, true);
    };

    zoomRange.addEventListener("input", () => {
        setWidgetValue(node, "zoom", Number(zoomRange.value));
        drawPreview();
        node.setDirtyCanvas?.(true, true);
    });

    canvas.addEventListener("pointerdown", (e) => {
        if (!canPan()) return;
        state.dragging = true;
        state.lastX = e.clientX;
        state.lastY = e.clientY;
        canvas.style.cursor = "grabbing";
        canvas.setPointerCapture(e.pointerId);
        e.preventDefault();
    });

    canvas.addEventListener("pointermove", (e) => {
        if (!state.dragging || !canPan()) return;
        const dx = e.clientX - state.lastX;
        const dy = e.clientY - state.lastY;
        state.lastX = e.clientX;
        state.lastY = e.clientY;

        const ratio = targetRatio();
        const ox = Number(offsetXW.value) || 0;
        const oy = Number(offsetYW.value) || 0;
        const box = computeCropBox(
            state.img.width,
            state.img.height,
            ratio,
            ox,
            oy,
            currentZoom(),
        );

        let nextX = ox;
        let nextY = oy;
        if (box.maxOx > 0) nextX -= dx / box.maxOx;
        if (box.maxOy > 0) nextY -= dy / box.maxOy;
        setWidgetValue(node, "offset_x", clamp(nextX, -1, 1));
        setWidgetValue(node, "offset_y", clamp(nextY, -1, 1));
        drawPreview();
        e.preventDefault();
    });

    const endDrag = (e) => {
        if (!state.dragging) return;
        state.dragging = false;
        canvas.style.cursor = "grab";
        try {
            canvas.releasePointerCapture(e.pointerId);
        } catch (_) {}
        node.setDirtyCanvas?.(true, true);
    };
    canvas.addEventListener("pointerup", endDrag);
    canvas.addEventListener("pointercancel", endDrag);

    for (const zone of [frame, root]) {
        zone.addEventListener("dragover", (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropOverlay.style.display = "flex";
        });
        zone.addEventListener("dragleave", (e) => {
            if (!zone.contains(e.relatedTarget)) dropOverlay.style.display = "none";
        });
        zone.addEventListener("drop", (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropOverlay.style.display = "none";
            const file = e.dataTransfer?.files?.[0];
            if (file) handleFile(file);
        });
    }

    const onImageChange = () => {
        setWidgetValue(node, "offset_x", 0);
        setWidgetValue(node, "offset_y", 0);
        setWidgetValue(node, "zoom", 1);
        loadPreview(imageW.value);
    };

    const origImageCb = imageW.callback;
    imageW.callback = function (...args) {
        if (origImageCb) origImageCb.apply(this, args);
        onImageChange();
    };

    const origAspectCb = aspectW.callback;
    aspectW.callback = function (...args) {
        if (origAspectCb) origAspectCb.apply(this, args);
        resizeFrame();
        drawPreview();
        node.setDirtyCanvas?.(true, true);
    };

    const origAutoCb = autoCropW.callback;
    autoCropW.callback = function (...args) {
        if (origAutoCb) origAutoCb.apply(this, args);
        resizeFrame();
        drawPreview();
        node.setDirtyCanvas?.(true, true);
    };

    resizeFrame();
    loadPreview(imageW.value);

    return root;
}

app.registerExtension({
    name: "Vsaan212.LazyImageLoader",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_CLASS) return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = origOnNodeCreated?.apply(this, arguments);
            const node = this;
            const uiRoot = buildUi(node);
            node.addDOMWidget("lazy_image_preview", "preview", uiRoot, {
                getMinHeight: () => 460,
                getMaxHeight: () => 560,
            });
            node.setSize?.([Math.max(node.size?.[0] ?? 0, 300), Math.max(node.size?.[1] ?? 0, 560)]);
            return r;
        };
    },
});
