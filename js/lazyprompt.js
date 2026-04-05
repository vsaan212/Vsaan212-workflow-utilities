/**
 * LazyPrompt — clear system_prompt override so the node uses auto templates per target_model.
 */
import { app } from "../../scripts/app.js";

function clearSystemPromptOverride(node) {
  const w = node.widgets?.find((x) => x.name === "system_prompt");
  if (!w) return;
  w.value = "";
  if (typeof w.callback === "function") w.callback("");
  node.setDirty?.(true);
}

app.registerExtension({
  name: "vsaan212.LazyPrompt",

  getNodeMenuItems(node) {
    if (node?.comfyClass !== "LazyPromptEngineer") return [];
    return [
      {
        content: "Use auto system prompt (clear override)",
        callback: () => clearSystemPromptOverride(node),
      },
    ];
  },

  async nodeCreated(node) {
    if (node?.comfyClass !== "LazyPromptEngineer") return;
    const sysPromptWidget = node.widgets?.find((w) => w.name === "system_prompt");
    if (!sysPromptWidget) return;
    let parent = null;
    try {
      if (sysPromptWidget.parentEl) {
        parent = sysPromptWidget.parentEl.parentElement ?? sysPromptWidget.parentEl;
      }
      if (!parent && node.domElement) {
        const rows = node.domElement.querySelectorAll?.(".widget-row, .widget");
        parent = rows?.length ? rows[rows.length - 1].parentElement : node.domElement;
      }
      if (parent) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = "Auto system prompt (clear override)";
        btn.className = "btn btn-sm";
        btn.style.marginTop = "4px";
        btn.style.width = "100%";
        btn.onclick = () => clearSystemPromptOverride(node);
        parent.appendChild(btn);
      }
    } catch (_) {}
  },
});
