/** @odoo-module */

import { registry } from "@web/core/registry";

const actionRegistry = registry.category("actions");

const CHATTER_NOTE_ACTION_TAG = "chatter_note_action";
const CHATTER_NOTE_ACTION_MODEL = "helpdesk.ticket";
const CHATTER_REGISTER_NOTE_SELECTOR = ".o_ChatterTopbar_button.o_ChatterTopbar_buttonLogNote";

const goChatterNoteAction = async (action, env) => {
    if (!action || !env) return;

    const scrollToChatterTop = () => {
        const chatterTop = document.querySelector(CHATTER_REGISTER_NOTE_SELECTOR);
        if (chatterTop) {
            chatterTop.scrollIntoView({ behavior: "smooth", block: "start" });
            chatterTop.click();
        }
    }

    if (
        env.tag === CHATTER_NOTE_ACTION_TAG
        && env.params?.model === CHATTER_NOTE_ACTION_MODEL
    ) scrollToChatterTop();
}

actionRegistry.add("chatter_note_action", goChatterNoteAction);
