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
    LazySubjectSceneAutomation: {
        endpoints: [
            { endpoint: "/vsaan212/lazy-subject-scene/subjects", widgetName: "subject" },
            { endpoint: "/vsaan212/lazy-subject-scene/subjects", widgetName: "subject_2" },
            { endpoint: "/vsaan212/lazy-subject-scene/subjects", widgetName: "subject_3" },
            { endpoint: "/vsaan212/lazy-subject-scene/scenarios", widgetName: "scenario" },
            { endpoint: "/vsaan212/lazy-subject-scene/scenarios", widgetName: "scenario_2" },
        ],
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
            const jobs =
                config.endpoints ||
                (config.endpoint
                    ? [{ endpoint: config.endpoint, widgetName: config.widgetName }]
                    : []);

            for (const job of jobs) {
                const widget = node.widgets.find(w => w.name === job.widgetName);
                if (!widget) continue;

                fetch(job.endpoint)
                    .then(r => r.json())
                    .then((payload) => {
                        const names = job.mapValues
                            ? job.mapValues(payload)
                            : payload;
                        if (!names || names.length === 0) return;
                        const current = widget.value;
                        widget.options.values = names;
                        widget.value = names.includes(current) ? current : names[0];
                        node.setDirtyCanvas(true, true);
                    });
            }
        };
    },
});
