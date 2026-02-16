import { app } from "../../scripts/app.js";

const API_BASE = "/lazy_prompt_saver";

async function apiGet(endpoint) {
    const resp = await fetch(`${API_BASE}/${endpoint}`);
    return await resp.json();
}

async function apiPost(endpoint, body) {
    const resp = await fetch(`${API_BASE}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    return await resp.json();
}

app.registerExtension({
    name: "Vsaan212.LazyPromptSaver",

    async beforeRegisterNodeDef(nodeType, nodeData, appInstance) {
        if (nodeData.name !== "LazyPromptSaver") return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);

            const node = this;
            const promptNameWidget = node.widgets.find(w => w.name === "prompt_name");
            const promptTextWidget = node.widgets.find(w => w.name === "prompt_text");
            const savedPromptsWidget = node.widgets.find(w => w.name === "saved_prompts");

            const PLACEHOLDER = "-- None --";

            async function refreshDropdown(selectName) {
                const prompts = await apiGet("prompts");
                const names = Object.keys(prompts).sort();
                savedPromptsWidget.options.values = [PLACEHOLDER, ...names];
                if (selectName && names.includes(selectName)) {
                    savedPromptsWidget.value = selectName;
                } else {
                    savedPromptsWidget.value = PLACEHOLDER;
                }
                node.setDirtyCanvas(true, true);
            }

            // Save button
            node.addWidget("button", "Save", null, async () => {
                const name = promptNameWidget.value.trim();
                const text = promptTextWidget.value;
                if (!name) {
                    alert("Please enter a prompt name.");
                    return;
                }
                await apiPost("save", { name, text });
                await refreshDropdown(name);
            });

            // Clone button - client-side only, doesn't save until user hits Save
            node.addWidget("button", "Clone", null, async () => {
                const name = promptNameWidget.value.trim();
                if (!name) {
                    alert("Please enter a prompt name to clone.");
                    return;
                }
                const prompts = await apiGet("prompts");
                const existing = Object.keys(prompts);
                let newName = name + "_copy";
                while (existing.includes(newName)) {
                    newName += "_copy";
                }
                promptNameWidget.value = newName;
                savedPromptsWidget.value = PLACEHOLDER;
                node.setDirtyCanvas(true, true);
            });

            // Delete button
            node.addWidget("button", "Delete", null, async () => {
                const name = promptNameWidget.value.trim();
                if (!name) return;
                if (!confirm(`Delete prompt "${name}"?`)) return;
                await apiPost("delete", { name });
                promptNameWidget.value = "";
                promptTextWidget.value = "";
                await refreshDropdown();
            });

            // Refresh dropdown on node creation so it's always up-to-date
            refreshDropdown(savedPromptsWidget.value);

            // Dropdown selection callback
            savedPromptsWidget.callback = async (value) => {
                if (value === PLACEHOLDER) {
                    promptNameWidget.value = "";
                    promptTextWidget.value = "";
                    node.setDirtyCanvas(true, true);
                    return;
                }
                const prompts = await apiGet("prompts");
                if (prompts[value] !== undefined) {
                    promptNameWidget.value = value;
                    promptTextWidget.value = prompts[value];
                    node.setDirtyCanvas(true, true);
                }
            };
        };
    },
});
