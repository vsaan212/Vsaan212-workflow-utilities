/**
 * Lazy Subject + Scene Automation — editable live buffers (queue uses live text),
 * save to disk, scenario 2 strength sliders override [LoraHighA]/[LoraLowA] in live text.
 */
import { app } from "../../scripts/app.js";

const LAZY_API = "/vsaan212/lazy-subject-scene";
const LIVE_WIDGETS = [
    "subject_live",
    "subject_2_live",
    "subject_3_live",
    "scenario_live",
    "scenario_2_live",
];
const USE_LIVE_WIDGETS = [
    "subject_use_live",
    "subject_2_use_live",
    "subject_3_use_live",
    "scenario_use_live",
    "scenario_2_use_live",
];
const SCENARIO2_SLIDER_WIDGETS = ["scenario_2_high_strength", "scenario_2_low_strength"];
const HIDDEN_WIDGETS = [...LIVE_WIDGETS, ...USE_LIVE_WIDGETS];
const NODE_MIN_WIDTH = 420;
const NODE_MIN_HEIGHT = 560;

let queueHooked = false;

function graphNodes(graph) {
    if (!graph) return [];
    if (Array.isArray(graph._nodes)) return graph._nodes;
    if (graph.nodes) return Object.values(graph.nodes);
    return [];
}

function formatStrengthValue(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return "1.0";
    return String(Math.round(n * 10000) / 10000)
        .replace(/(\.\d*?)0+$/, "$1")
        .replace(/\.$/, "");
}

function normTag(tag) {
    return String(tag || "")
        .toLowerCase()
        .replace(/[^a-z0-9]/g, "");
}

function readTagModelStrength(content, tag) {
    const tagKey = normTag(tag);
    for (const line of String(content || "").replace(/\r\n/g, "\n").split("\n")) {
        const stripped = line.trim();
        if (!stripped.startsWith("[")) continue;
        const groups = [...stripped.matchAll(/\[([^\]]*)\]/g)].map((m) => m[1]);
        if (!groups.length || normTag(groups[0]) !== tagKey) continue;
        if (groups.length > 1) {
            const n = parseFloat(groups[1]);
            return Number.isFinite(n) ? n : 1.0;
        }
        return 1.0;
    }
    return null;
}

function writeTagModelStrength(content, tag, modelStrength) {
    const tagKey = normTag(tag);
    const sm = formatStrengthValue(modelStrength);
    const lines = String(content || "").replace(/\r\n/g, "\n").split("\n");
    const out = [];
    let replaced = false;
    for (const line of lines) {
        const stripped = line.trim();
        if (!stripped.startsWith("[")) {
            out.push(line);
            continue;
        }
        const groups = [...stripped.matchAll(/\[([^\]]*)\]/g)].map((m) => m[1]);
        if (!groups.length || normTag(groups[0]) !== tagKey) {
            out.push(line);
            continue;
        }
        const clip = groups.length > 2 ? groups[2] : "1.0";
        out.push(`[${groups[0]}][${sm}][${clip}]`);
        replaced = true;
    }
    if (!replaced) {
        out.push(`[${tag}][${sm}][1.0]`, "bypass");
    }
    return out.join("\n");
}

function readScenario2Strengths(text) {
    return {
        high: readTagModelStrength(text, "LoraHighA") ?? 1.0,
        low: readTagModelStrength(text, "LoraLowA") ?? 1.0,
    };
}

/** Hide sync widgets without affecting node width (never use computeSize [0,0]). */
function hideLiveWidgets(node) {
    for (const name of HIDDEN_WIDGETS) {
        const w = node.widgets?.find((x) => x.name === name);
        if (!w) continue;
        if (w.hidden !== undefined) w.hidden = true;
    }
}

function setWidgetShown(node, name, shown) {
    const w = node.widgets?.find((x) => x.name === name);
    if (!w) return;
    w.hidden = !shown;
    if (shown) {
        delete w.computeSize;
    } else {
        w.computeSize = () => [0, -4];
    }
    const row = w.element?.closest?.(".comfy-widget") || w.element?.parentElement;
    if (row) row.style.display = shown ? "" : "none";
}

function refmodCount(node) {
    const w = node.widgets?.find((x) => x.name === "multisubject_refmod");
    const n = parseInt(w?.value ?? 0, 10);
    if (!Number.isFinite(n)) return 0;
    return Math.max(0, Math.min(3, n));
}

function randomizeOn(node) {
    return !!node.widgets?.find((x) => x.name === "randomize_subject_in_directory")?.value;
}

function extraSubjectSlots(node) {
    const n = refmodCount(node);
    return n <= 1 ? 1 : n;
}

function setPaneGroupShown(el, shown) {
    if (!el) return;
    el.style.display = shown ? "flex" : "none";
}

function updateMultiSubjectUi(node) {
    const slots = extraSubjectSlots(node);
    const randomize = randomizeOn(node);
    setWidgetShown(node, "subject_2", slots >= 2 && !randomize);
    setWidgetShown(node, "subject_3", slots >= 3 && !randomize);
    setWidgetShown(node, "min_subjects", slots >= 2 && randomize);
    setPaneGroupShown(node.__lssSubject2Group, slots >= 2 && !randomize);
    setPaneGroupShown(node.__lssSubject3Group, slots >= 3 && !randomize);
    ensureNodeMinSize(node);
    node.setDirtyCanvas?.(true, true);
}

function relocateWidgetRows(node, names, container) {
    if (!container) return;
    for (const name of names) {
        const w = node.widgets?.find((x) => x.name === name);
        if (!w) continue;
        const row = w.element?.closest?.(".comfy-widget") || w.element?.parentElement;
        if (row) container.appendChild(row);
    }
}

function setScenario2SlidersEnabled(node, enabled) {
    for (const name of SCENARIO2_SLIDER_WIDGETS) {
        const w = node.widgets?.find((x) => x.name === name);
        if (!w) continue;
        if (w.disabled !== undefined) w.disabled = !enabled;
        const row = w.element?.closest?.(".comfy-widget");
        if (row) row.style.opacity = enabled ? "" : "0.45";
        if (row) row.style.pointerEvents = enabled ? "" : "none";
    }
}

function ensureNodeMinSize(node) {
    const w = Math.max(node.size?.[0] ?? 0, NODE_MIN_WIDTH);
    const h = Math.max(node.size?.[1] ?? 0, NODE_MIN_HEIGHT);
    if (node.size?.[0] !== w || node.size?.[1] !== h) {
        node.setSize?.([w, h]);
    }
}

function syncLiveToProperties(node) {
    node.properties = node.properties || {};
    node.properties.vsaan212_lssa = {
        subject_live: node.__lssSubjectTa?.value ?? "",
        subject_2_live: node.__lssSubject2Ta?.value ?? "",
        subject_3_live: node.__lssSubject3Ta?.value ?? "",
        scenario_live: node.__lssScenarioTa?.value ?? "",
        scenario_2_live: node.__lssScenario2Ta?.value ?? "",
        subject_use_live: !!node.widgets?.find((x) => x.name === "subject_use_live")?.value,
        subject_2_use_live: !!node.widgets?.find((x) => x.name === "subject_2_use_live")?.value,
        subject_3_use_live: !!node.widgets?.find((x) => x.name === "subject_3_use_live")?.value,
        scenario_use_live: !!node.widgets?.find((x) => x.name === "scenario_use_live")?.value,
        scenario_2_use_live: !!node.widgets?.find((x) => x.name === "scenario_2_use_live")?.value,
        scenario_2_high_strength:
            node.widgets?.find((x) => x.name === "scenario_2_high_strength")?.value ?? 1.0,
        scenario_2_low_strength:
            node.widgets?.find((x) => x.name === "scenario_2_low_strength")?.value ?? 1.0,
    };
}

function setWidgetValue(node, name, value) {
    const w = node.widgets?.find((x) => x.name === name);
    if (!w) return;
    w.value = value;
    if (typeof w.callback === "function") {
        w.callback(value, app.canvas, node, {}, w);
    }
}

function markPaneLive(node, which) {
    const flags = {
        subject: "subject_use_live",
        subject_2: "subject_2_use_live",
        subject_3: "subject_3_use_live",
        scenario: "scenario_use_live",
        scenario_2: "scenario_2_use_live",
    };
    const flag = flags[which] || "scenario_2_use_live";
    setWidgetValue(node, flag, true);
}

function clearLiveFlags(node) {
    for (const name of USE_LIVE_WIDGETS) {
        setWidgetValue(node, name, false);
    }
}

function syncLiveToWidgets(node) {
    if (node.__lssSubjectTa) {
        setWidgetValue(node, "subject_live", node.__lssSubjectTa.value ?? "");
    }
    if (node.__lssSubject2Ta) {
        setWidgetValue(node, "subject_2_live", node.__lssSubject2Ta.value ?? "");
    }
    if (node.__lssSubject3Ta) {
        setWidgetValue(node, "subject_3_live", node.__lssSubject3Ta.value ?? "");
    }
    if (node.__lssScenarioTa) {
        setWidgetValue(node, "scenario_live", node.__lssScenarioTa.value ?? "");
    }
    if (node.__lssScenario2Ta) {
        setWidgetValue(node, "scenario_2_live", node.__lssScenario2Ta.value ?? "");
    }
    syncLiveToProperties(node);
    node.setDirtyCanvas?.(true, true);
}

function syncAllLazyLiveNodesForQueue() {
    for (const node of graphNodes(app.graph)) {
        if (node.comfyClass !== "LazySubjectSceneAutomation") continue;
        applyScenario2StrengthFromSliders(node, false);
        if (String(node.__lssSubjectTa?.value ?? "").trim()) {
            markPaneLive(node, "subject");
        }
        if (String(node.__lssSubject2Ta?.value ?? "").trim()) {
            markPaneLive(node, "subject_2");
        }
        if (String(node.__lssSubject3Ta?.value ?? "").trim()) {
            markPaneLive(node, "subject_3");
        }
        if (String(node.__lssScenarioTa?.value ?? "").trim()) {
            markPaneLive(node, "scenario");
        }
        if (String(node.__lssScenario2Ta?.value ?? "").trim()) {
            markPaneLive(node, "scenario_2");
        }
        syncLiveToWidgets(node);
    }
}

function ensureQueueHook() {
    if (queueHooked) return;
    queueHooked = true;
    const orig = app.queuePrompt;
    if (typeof orig === "function") {
        app.queuePrompt = function (...args) {
            syncAllLazyLiveNodesForQueue();
            return orig.apply(this, args);
        };
    }
}

function updateScenario2SlidersFromText(node) {
    const ta = node.__lssScenario2Ta;
    if (!ta) return;
    const { high, low } = readScenario2Strengths(ta.value);
    node.__lssUpdatingSliders = true;
    setWidgetValue(node, "scenario_2_high_strength", high);
    setWidgetValue(node, "scenario_2_low_strength", low);
    node.__lssUpdatingSliders = false;
}

function applyScenario2StrengthFromSliders(node, markLive = true) {
    if (node.__lssUpdatingSliders) return;
    const scen2 = node.widgets?.find((w) => w.name === "scenario_2");
    if (!scen2?.value || scen2.value === "none") return;

    const highW = node.widgets?.find((w) => w.name === "scenario_2_high_strength");
    const lowW = node.widgets?.find((w) => w.name === "scenario_2_low_strength");
    const ta = node.__lssScenario2Ta;
    if (!ta) return;

    let text = ta.value ?? "";
    text = writeTagModelStrength(text, "LoraHighA", highW?.value ?? 1.0);
    text = writeTagModelStrength(text, "LoraLowA", lowW?.value ?? 1.0);
    ta.value = text;
    if (markLive) {
        markPaneLive(node, "scenario_2");
        syncLiveToWidgets(node);
    }
}

function setupScenario2Sliders(node) {
    for (const name of SCENARIO2_SLIDER_WIDGETS) {
        const w = node.widgets?.find((x) => x.name === name);
        if (!w) continue;
        const orig = w.callback;
        w.callback = function (v) {
            if (orig) orig.apply(this, arguments);
            if (!node.__lssUpdatingSliders) {
                applyScenario2StrengthFromSliders(node);
            }
        };
    }
}

function setPane(ta, statusEl, text, error, canSaveKey) {
    const node = ta.__lssNode;
    ta.value = text ?? "";
    if (error) {
        statusEl.textContent = String(error);
        statusEl.style.display = "block";
        node[canSaveKey] = false;
    } else {
        statusEl.textContent = "";
        statusEl.style.display = "none";
        node[canSaveKey] = true;
    }
}

async function fetchReadPair(node) {
    const subj = node.widgets?.find((w) => w.name === "subject");
    const subj2 = node.widgets?.find((w) => w.name === "subject_2");
    const subj3 = node.widgets?.find((w) => w.name === "subject_3");
    const scen = node.widgets?.find((w) => w.name === "scenario");
    const scen2 = node.widgets?.find((w) => w.name === "scenario_2");
    const body = {
        subject: subj?.value ?? "none",
        subject_2: subj2?.value ?? "none",
        subject_3: subj3?.value ?? "none",
        scenario: scen?.value ?? "none",
        scenario_2: scen2?.value ?? "none",
    };
    let data;
    try {
        const r = await fetch(`${LAZY_API}/read_pair`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        data = await r.json();
    } catch (e) {
        data = {
            subject_text: "",
            subject_2_text: "",
            subject_3_text: "",
            scenario_text: "",
            scenario_2_text: "",
            subject_error: String(e),
        };
    }

    const subjActive = body.subject && body.subject !== "none";
    const subj2Active = body.subject_2 && body.subject_2 !== "none";
    const subj3Active = body.subject_3 && body.subject_3 !== "none";
    const scenActive = body.scenario && body.scenario !== "none";
    const scen2Active = body.scenario_2 && body.scenario_2 !== "none";

    if (node.__lssSubjectTa) {
        setPane(
            node.__lssSubjectTa,
            node.__lssSubjectStatus,
            subjActive ? data.subject_text ?? "" : "",
            subjActive ? data.subject_error : null,
            "__lssCanSaveSubject"
        );
        if (!subjActive) node.__lssCanSaveSubject = false;
    }
    if (node.__lssSubject2Ta) {
        setPane(
            node.__lssSubject2Ta,
            node.__lssSubject2Status,
            subj2Active ? data.subject_2_text ?? "" : "",
            subj2Active ? data.subject_2_error : null,
            "__lssCanSaveSubject2"
        );
        if (!subj2Active) node.__lssCanSaveSubject2 = false;
    }
    if (node.__lssSubject3Ta) {
        setPane(
            node.__lssSubject3Ta,
            node.__lssSubject3Status,
            subj3Active ? data.subject_3_text ?? "" : "",
            subj3Active ? data.subject_3_error : null,
            "__lssCanSaveSubject3"
        );
        if (!subj3Active) node.__lssCanSaveSubject3 = false;
    }
    if (node.__lssScenarioTa) {
        setPane(
            node.__lssScenarioTa,
            node.__lssScenarioStatus,
            scenActive ? data.scenario_text ?? "" : "",
            scenActive ? data.scenario_error : null,
            "__lssCanSaveScenario"
        );
        if (!scenActive) node.__lssCanSaveScenario = false;
    }
    if (node.__lssScenario2Ta) {
        setPane(
            node.__lssScenario2Ta,
            node.__lssScenario2Status,
            scen2Active ? data.scenario_2_text ?? "" : "",
            scen2Active ? data.scenario_2_error : null,
            "__lssCanSaveScenario2"
        );
        if (!scen2Active) node.__lssCanSaveScenario2 = false;
    }

    setScenario2SlidersEnabled(node, scen2Active);
    if (scen2Active) {
        updateScenario2SlidersFromText(node);
    }

    clearLiveFlags(node);
    syncLiveToWidgets(node);
    updateMultiSubjectUi(node);
}

async function saveLiveFiles(node) {
    applyScenario2StrengthFromSliders(node);
    syncLiveToWidgets(node);

    const subj = node.widgets?.find((w) => w.name === "subject");
    const subj2 = node.widgets?.find((w) => w.name === "subject_2");
    const subj3 = node.widgets?.find((w) => w.name === "subject_3");
    const scen = node.widgets?.find((w) => w.name === "scenario");
    const scen2 = node.widgets?.find((w) => w.name === "scenario_2");

    const body = {
        subject: subj?.value ?? "none",
        subject_2: subj2?.value ?? "none",
        subject_3: subj3?.value ?? "none",
        scenario: scen?.value ?? "none",
        scenario_2: scen2?.value ?? "none",
    };

    if (node.__lssCanSaveSubject && String(node.__lssSubjectTa?.value ?? "").trim()) {
        body.subject_text = node.__lssSubjectTa.value;
    }
    if (node.__lssCanSaveSubject2 && String(node.__lssSubject2Ta?.value ?? "").trim()) {
        body.subject_2_text = node.__lssSubject2Ta.value;
    }
    if (node.__lssCanSaveSubject3 && String(node.__lssSubject3Ta?.value ?? "").trim()) {
        body.subject_3_text = node.__lssSubject3Ta.value;
    }
    if (node.__lssCanSaveScenario && String(node.__lssScenarioTa?.value ?? "").trim()) {
        body.scenario_text = node.__lssScenarioTa.value;
    }
    if (node.__lssCanSaveScenario2 && String(node.__lssScenario2Ta?.value ?? "").trim()) {
        body.scenario_2_text = node.__lssScenario2Ta.value;
    }

    if (
        !body.subject_text &&
        !body.subject_2_text &&
        !body.subject_3_text &&
        !body.scenario_text &&
        !body.scenario_2_text
    ) {
        alert("Nothing to save (empty panes or no file selected).");
        return;
    }

    let res;
    try {
        const r = await fetch(`${LAZY_API}/save_live_files`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        res = await r.json();
    } catch (e) {
        alert(String(e));
        return;
    }
    if (res.error && !res.saved?.length) {
        alert(res.error);
        return;
    }
    const names = (res.saved || []).map((p) => p.split(/[/\\]/).pop()).join(", ");
    if (res.errors?.length) {
        alert(`Saved: ${names || "(none)"}\n\nWarnings:\n${res.errors.join("\n")}`);
    } else {
        alert(names ? `Saved: ${names}` : "Saved.");
    }
}

function chainWidgetCallback(widget, fn) {
    if (!widget) return;
    const orig = widget.callback;
    widget.callback = function (v) {
        if (orig) orig.apply(this, arguments);
        fn.call(this, v);
    };
}

function restoreFromStored(node) {
    const subj = node.widgets?.find((w) => w.name === "subject");
    const subj2 = node.widgets?.find((w) => w.name === "subject_2");
    const subj3 = node.widgets?.find((w) => w.name === "subject_3");
    const scen = node.widgets?.find((w) => w.name === "scenario");
    const scen2 = node.widgets?.find((w) => w.name === "scenario_2");
    const subjLiveW = node.widgets?.find((w) => w.name === "subject_live");
    const subj2LiveW = node.widgets?.find((w) => w.name === "subject_2_live");
    const subj3LiveW = node.widgets?.find((w) => w.name === "subject_3_live");
    const scenLiveW = node.widgets?.find((w) => w.name === "scenario_live");
    const scen2LiveW = node.widgets?.find((w) => w.name === "scenario_2_live");
    const stored = node.properties?.vsaan212_lssa;

    const subjText = subjLiveW?.value ?? stored?.subject_live ?? "";
    const subj2Text = subj2LiveW?.value ?? stored?.subject_2_live ?? "";
    const subj3Text = subj3LiveW?.value ?? stored?.subject_3_live ?? "";
    const scenText = scenLiveW?.value ?? stored?.scenario_live ?? "";
    const scen2Text = scen2LiveW?.value ?? stored?.scenario_2_live ?? "";
    const hasBuffered =
        String(subjText).length > 0 ||
        String(subj2Text).length > 0 ||
        String(subj3Text).length > 0 ||
        String(scenText).length > 0 ||
        String(scen2Text).length > 0;

    if (!hasBuffered) return false;

    node.__lssSubjectTa.value = subjText;
    if (node.__lssSubject2Ta) node.__lssSubject2Ta.value = subj2Text;
    if (node.__lssSubject3Ta) node.__lssSubject3Ta.value = subj3Text;
    node.__lssScenarioTa.value = scenText;
    node.__lssScenario2Ta.value = scen2Text;
    node.__lssCanSaveSubject = subj?.value && subj.value !== "none";
    node.__lssCanSaveSubject2 = subj2?.value && subj2.value !== "none";
    node.__lssCanSaveSubject3 = subj3?.value && subj3.value !== "none";
    node.__lssCanSaveScenario = scen?.value && scen.value !== "none";
    node.__lssCanSaveScenario2 = scen2?.value && scen2.value !== "none";

    const scen2Active = scen2?.value && scen2.value !== "none";
    setScenario2SlidersEnabled(node, scen2Active);
    if (scen2Active) {
        if (stored?.scenario_2_high_strength != null) {
            node.__lssUpdatingSliders = true;
            setWidgetValue(node, "scenario_2_high_strength", stored.scenario_2_high_strength);
            setWidgetValue(node, "scenario_2_low_strength", stored.scenario_2_low_strength ?? 1.0);
            node.__lssUpdatingSliders = false;
            applyScenario2StrengthFromSliders(node);
        } else {
            updateScenario2SlidersFromText(node);
        }
    }

    syncLiveToWidgets(node);
    updateMultiSubjectUi(node);
    return true;
}

function buildLiveDom(node) {
    const wrap = document.createElement("div");
    wrap.className = "vsaan-lssa-live-wrap";
    wrap.style.cssText = [
        "width:100%",
        "min-width:380px",
        "max-width:100%",
        "display:flex",
        "flex-direction:column",
        "gap:6px",
        "padding:4px 0",
        "font-size:11px",
        "box-sizing:border-box",
    ].join(";");

    const mkLabel = (t) => {
        const el = document.createElement("div");
        el.textContent = t;
        el.style.cssText = "opacity:0.85;font-weight:600;white-space:normal;";
        return el;
    };

    const mkStatus = () => {
        const el = document.createElement("div");
        el.style.cssText =
            "display:none;font-size:10px;color:var(--error-text,#e88);margin-top:-4px;";
        return el;
    };

    const mkTa = (minH, which) => {
        const ta = document.createElement("textarea");
        ta.readOnly = false;
        ta.spellcheck = false;
        ta.__lssNode = node;
        ta.__lssWhich = which;
        ta.style.cssText = [
            "width:100%",
            "min-width:0",
            `min-height:${minH}px`,
            "resize:vertical",
            "font-family:monospace",
            "font-size:11px",
            "background:var(--comfy-input-bg)",
            "color:var(--comfy-input-color)",
            "border:1px solid var(--border-color)",
            "border-radius:4px",
            "padding:4px",
            "box-sizing:border-box",
        ].join(";");
        ta.addEventListener("input", () => {
            markPaneLive(node, which);
            if (which === "scenario_2" && !node.__lssUpdatingSliders) {
                updateScenario2SlidersFromText(node);
            }
            syncLiveToWidgets(node);
        });
        return ta;
    };

    const mkGroup = () => {
        const el = document.createElement("div");
        el.style.cssText = "display:none;flex-direction:column;gap:6px;width:100%;";
        return el;
    };

    wrap.appendChild(mkLabel("Subject file (live — used on queue)"));
    const subjTa = mkTa(96, "subject");
    const subjStatus = mkStatus();
    wrap.appendChild(subjTa);
    wrap.appendChild(subjStatus);

    const subj2Group = mkGroup();
    subj2Group.appendChild(mkLabel("Subject 2 file (live — used on queue)"));
    const subj2Ta = mkTa(80, "subject_2");
    const subj2Status = mkStatus();
    subj2Group.appendChild(subj2Ta);
    subj2Group.appendChild(subj2Status);
    wrap.appendChild(subj2Group);

    const subj3Group = mkGroup();
    subj3Group.appendChild(mkLabel("Subject 3 file (live — used on queue)"));
    const subj3Ta = mkTa(80, "subject_3");
    const subj3Status = mkStatus();
    subj3Group.appendChild(subj3Ta);
    subj3Group.appendChild(subj3Status);
    wrap.appendChild(subj3Group);

    wrap.appendChild(mkLabel("Scenario file (live — used on queue)"));
    const scenTa = mkTa(96, "scenario");
    const scenStatus = mkStatus();
    wrap.appendChild(scenTa);
    wrap.appendChild(scenStatus);

    const sliderHost = document.createElement("div");
    sliderHost.className = "vsaan-lssa-scenario2-sliders";
    sliderHost.style.cssText = "display:flex;flex-direction:column;gap:2px;width:100%;";
    wrap.appendChild(sliderHost);

    wrap.appendChild(mkLabel("Scenario 2 file (live — used on queue)"));
    const scen2Ta = mkTa(96, "scenario_2");
    const scen2Status = mkStatus();
    wrap.appendChild(scen2Ta);
    wrap.appendChild(scen2Status);

    node.__lssSubjectTa = subjTa;
    node.__lssSubject2Ta = subj2Ta;
    node.__lssSubject3Ta = subj3Ta;
    node.__lssScenarioTa = scenTa;
    node.__lssScenario2Ta = scen2Ta;
    node.__lssSubjectStatus = subjStatus;
    node.__lssSubject2Status = subj2Status;
    node.__lssSubject3Status = subj3Status;
    node.__lssScenarioStatus = scenStatus;
    node.__lssScenario2Status = scen2Status;
    node.__lssSubject2Group = subj2Group;
    node.__lssSubject3Group = subj3Group;
    node.__lssScenario2SliderHost = sliderHost;

    return wrap;
}

app.registerExtension({
    name: "Vsaan212.LazySubjectSceneLive",

    async beforeQueuePrompt() {
        syncAllLazyLiveNodesForQueue();
    },

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LazySubjectSceneAutomation") return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function () {
            if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);
            const node = this;
            ensureQueueHook();
            hideLiveWidgets(node);

            const wrap = buildLiveDom(node);
            const domOpts = {
                getMinHeight: () => 380,
                getMaxHeight: () => 1200,
                getMinWidth: () => NODE_MIN_WIDTH,
            };
            if (typeof node.addDOMWidget === "function") {
                node.addDOMWidget("lssa_live_previews", "live preview", wrap, domOpts);
            } else if (node.domElement) {
                node.domElement.appendChild(wrap);
            }

            const placeSliders = () =>
                relocateWidgetRows(
                    node,
                    SCENARIO2_SLIDER_WIDGETS,
                    node.__lssScenario2SliderHost
                );
            placeSliders();
            requestAnimationFrame(placeSliders);
            setupScenario2Sliders(node);
            hideLiveWidgets(node);

            const subj = node.widgets?.find((w) => w.name === "subject");
            const subj2 = node.widgets?.find((w) => w.name === "subject_2");
            const subj3 = node.widgets?.find((w) => w.name === "subject_3");
            const scen = node.widgets?.find((w) => w.name === "scenario");
            const scen2 = node.widgets?.find((w) => w.name === "scenario_2");
            const refmodW = node.widgets?.find((w) => w.name === "multisubject_refmod");
            const randomizeW = node.widgets?.find((w) => w.name === "randomize_subject_in_directory");

            chainWidgetCallback(subj, () => fetchReadPair(node));
            chainWidgetCallback(subj2, () => fetchReadPair(node));
            chainWidgetCallback(subj3, () => fetchReadPair(node));
            chainWidgetCallback(scen, () => fetchReadPair(node));
            chainWidgetCallback(scen2, () => fetchReadPair(node));
            chainWidgetCallback(refmodW, () => updateMultiSubjectUi(node));
            chainWidgetCallback(randomizeW, () => updateMultiSubjectUi(node));

            node.addWidget("button", "Save edits", null, () => saveLiveFiles(node));

            if (!restoreFromStored(node)) {
                setTimeout(() => fetchReadPair(node), 0);
            } else {
                const scen2Active = scen2?.value && scen2.value !== "none";
                setScenario2SlidersEnabled(node, scen2Active);
            }

            updateMultiSubjectUi(node);
            ensureNodeMinSize(node);
            requestAnimationFrame(() => {
                updateMultiSubjectUi(node);
                ensureNodeMinSize(node);
            });
        };
    },
});
