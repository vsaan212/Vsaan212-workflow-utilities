/**
 * Lazy Subject + Scene Automation — live file previews, preset load/save, WebSocket preset list refresh.
 */
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const LAZY_API = "/vsaan212/lazy-subject-scene";
const WS_EVENT = "vsaan212.lazy_subject_scene.presets";

function graphNodes(graph) {
    if (!graph) return [];
    if (Array.isArray(graph._nodes)) return graph._nodes;
    if (graph.nodes) return Object.values(graph.nodes);
    return [];
}

let wsHooked = false;

function ensurePresetWsListener() {
    if (wsHooked) return;
    wsHooked = true;
    api.addEventListener(WS_EVENT, (event) => {
        const presets = event.detail?.presets || [];
        const values = ["(none)", ...presets];
        for (const node of graphNodes(app.graph)) {
            if (node.comfyClass !== "LazySubjectSceneAutomation") continue;
            const w = node.widgets?.find((x) => x.name === "preset_file");
            if (!w) continue;
            const cur = w.value;
            w.options.values = values;
            w.value = values.includes(cur) ? cur : "(none)";
            node.setDirtyCanvas(true, true);
        }
    });
}

async function fetchReadPair(node) {
    const subj = node.widgets?.find((w) => w.name === "subject");
    const scen = node.widgets?.find((w) => w.name === "scenario");
    const body = {
        subject: subj?.value ?? "none",
        scenario: scen?.value ?? "none",
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
        data = { subject_text: "", scenario_text: "", error: String(e) };
    }
    if (node.__lssSubjectTa) {
        const t = data.subject_text ?? "";
        const e = data.subject_error;
        node.__lssSubjectTa.value = e ? `${t}\n[${e}]` : t;
    }
    if (node.__lssScenarioTa) {
        const t = data.scenario_text ?? "";
        const e = data.scenario_error;
        node.__lssScenarioTa.value = e ? `${t}\n[${e}]` : t;
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

function buildLiveDom(node) {
    const wrap = document.createElement("div");
    wrap.className = "vsaan-lssa-live-wrap";
    wrap.style.cssText =
        "width:100%;display:flex;flex-direction:column;gap:6px;padding:4px 0;font-size:11px;";

    const mkLabel = (t) => {
        const el = document.createElement("div");
        el.textContent = t;
        el.style.cssText = "opacity:0.85;font-weight:600;";
        return el;
    };

    const mkTa = (readonly, minH) => {
        const ta = document.createElement("textarea");
        ta.readOnly = readonly;
        ta.spellcheck = false;
        ta.style.cssText = `width:100%;min-height:${minH}px;resize:vertical;font-family:monospace;font-size:11px;background:var(--comfy-input-bg);color:var(--comfy-input-color);border:1px solid var(--border-color);border-radius:4px;padding:4px;box-sizing:border-box;`;
        return ta;
    };

    wrap.appendChild(mkLabel("Subject file (live)"));
    const subjTa = mkTa(true, 96);
    wrap.appendChild(subjTa);

    wrap.appendChild(mkLabel("Scenario file (live)"));
    const scenTa = mkTa(true, 96);
    wrap.appendChild(scenTa);

    wrap.appendChild(
        mkLabel("scenario_template (stored in preset JSON; edit before Save preset)")
    );
    const tplTa = mkTa(false, 120);
    wrap.appendChild(tplTa);

    node.__lssSubjectTa = subjTa;
    node.__lssScenarioTa = scenTa;
    node.__lssTemplateTa = tplTa;

    return wrap;
}

app.registerExtension({
    name: "Vsaan212.LazySubjectSceneLive",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LazySubjectSceneAutomation") return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);
            const node = this;
            ensurePresetWsListener();

            const wrap = buildLiveDom(node);
            if (typeof node.addDOMWidget === "function") {
                node.addDOMWidget("lssa_live_previews", "live preview", wrap, {
                    getMinHeight: () => 340,
                    getMaxHeight: () => 920,
                });
            } else if (node.domElement) {
                node.domElement.appendChild(wrap);
            }

            const subj = node.widgets?.find((w) => w.name === "subject");
            const scen = node.widgets?.find((w) => w.name === "scenario");
            const presetW = node.widgets?.find((w) => w.name === "preset_file");

            chainWidgetCallback(subj, () => {
                fetchReadPair(node);
            });
            chainWidgetCallback(scen, () => {
                fetchReadPair(node);
            });

            chainWidgetCallback(presetW, async (v) => {
                if (!v || v === "(none)") return;
                let data;
                try {
                    const r = await fetch(`${LAZY_API}/load_preset`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ preset: v }),
                    });
                    data = await r.json();
                } catch (e) {
                    alert(String(e));
                    return;
                }
                if (data.error) {
                    alert(data.error);
                    return;
                }
                if (subj && data.subject != null) subj.value = data.subject;
                if (scen && data.scenario != null) scen.value = data.scenario;
                const pass = node.widgets?.find(
                    (w) => w.name === "pass_subject_to_main_prompt"
                );
                if (pass && typeof data.pass_subject_to_main_prompt === "boolean") {
                    pass.value = data.pass_subject_to_main_prompt;
                }
                if (node.__lssSubjectTa) node.__lssSubjectTa.value = data.subject_text ?? "";
                if (node.__lssScenarioTa) {
                    node.__lssScenarioTa.value = data.scenario_text ?? "";
                }
                if (node.__lssTemplateTa && data.scenario_template != null) {
                    node.__lssTemplateTa.value = data.scenario_template;
                }
                node.setDirtyCanvas(true, true);
            });

            node.addWidget("button", "Save preset", null, async () => {
                const name = window.prompt(
                    "Preset name (relative path without .json, e.g. mypack/studio):",
                    "default"
                );
                if (name == null || !String(name).trim()) return;
                const subjW = node.widgets?.find((w) => w.name === "subject");
                const scenW = node.widgets?.find((w) => w.name === "scenario");
                const passW = node.widgets?.find(
                    (w) => w.name === "pass_subject_to_main_prompt"
                );
                const key = String(name).trim().replace(/\\/g, "/").replace(/\.json$/i, "");
                const body = {
                    name: key,
                    subject: subjW?.value ?? "none",
                    scenario: scenW?.value ?? "none",
                    prepend_text: "",
                    post_text: "",
                    pass_subject_to_main_prompt: !!passW?.value,
                    scenario_template: node.__lssTemplateTa?.value ?? "",
                };
                let res;
                try {
                    const r = await fetch(`${LAZY_API}/save_preset`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                    });
                    res = await r.json();
                } catch (e) {
                    alert(String(e));
                    return;
                }
                if (res.error) {
                    alert(res.error);
                    return;
                }
                if (presetW) {
                    const cur = new Set(presetW.options.values || []);
                    cur.add("(none)");
                    cur.add(key);
                    presetW.options.values = Array.from(cur).sort((a, b) =>
                        String(a).localeCompare(String(b), undefined, {
                            sensitivity: "base",
                        })
                    );
                    presetW.value = key;
                }
                await fetchReadPair(node);
                node.setDirtyCanvas(true, true);
            });

            fetch(`${LAZY_API}/default_scenario_template`)
                .then((r) => r.json())
                .then((d) => {
                    const ta = node.__lssTemplateTa;
                    if (ta && !String(ta.value || "").trim()) {
                        ta.value = d.scenario_template || "";
                    }
                })
                .catch(() => {});

            setTimeout(() => fetchReadPair(node), 0);

            const h = Math.max(node.size?.[1] || 0, 420);
            const w = node.size?.[0] || 360;
            node.setSize?.([w, h]);
        };
    },
});
