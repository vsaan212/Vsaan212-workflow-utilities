import { app } from "../../scripts/app.js";

const SELECTORS = {
    "ComfyUI_subjectselector": {
        endpoint: "/vsaan212/subjects",
        widgetName: "subject",
    },
    "ComfyUI_ScenarioSelector": {
        endpoint: "/vsaan212/scenarios",
        widgetName: "scenario",
    },
};

app.registerExtension({
    name: "Vsaan212.SelectorsRefresh",

    async beforeRegisterNodeDef(nodeType, nodeData, appInstance) {
        const config = SELECTORS[nodeData.name];
        if (!config) return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (origOnNodeCreated) origOnNodeCreated.apply(this, arguments);

            const node = this;
            const widget = node.widgets.find(w => w.name === config.widgetName);
            if (!widget) return;

            // Fetch fresh file list and update the dropdown
            fetch(config.endpoint)
                .then(r => r.json())
                .then(names => {
                    if (!names || names.length === 0) return;
                    const current = widget.value;
                    widget.options.values = names;
                    // Keep current selection if it still exists, otherwise pick first
                    widget.value = names.includes(current) ? current : names[0];
                    node.setDirtyCanvas(true, true);
                });
        };
    },
});
