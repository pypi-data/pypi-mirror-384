/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
import { escapeAndCompactTextContent } from '@mail/js/utils';

registerPatch({
    name: 'ComposerView',
    recordMethods: {
        async postMessage() {
            await this._super(...arguments);
            if (this.env?.services?.action?.currentController?.props?.resModel === 'helpdesk.ticket') {
                this.env.bus.trigger('message_update_ev', { message: this });
            }
        },
        async updateMessage() {
            await this._super(...arguments);
            if (this.env?.services?.action?.currentController?.props?.resModel === 'helpdesk.ticket') {
                this.env.bus.trigger('message_update_ev', { message: this });
            }
        },
        async openFullComposer() {
            const attachmentIds = this.composer.attachments.map(attachment => attachment.id);
            const context = {
                default_attachment_ids: attachmentIds,
                default_body: escapeAndCompactTextContent(this.composer.textInputContent),
                default_is_log: this.composer.isLog,
                default_model: this.composer.activeThread.model,
                default_partner_ids: this.composer.recipients.map(partner => partner.id),
                default_res_id: this.composer.activeThread.id,
                mail_post_autofollow: this.composer.activeThread.hasWriteAccess,
            };

            const action = {
                type: 'ir.actions.act_window',
                name: this.composer.isLog ? this.env._t('Log note') : this.env._t('Compose Email'),
                res_model: 'mail.compose.message',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: context,
            };
            const composer = this.composer;
            const options = {
                onClose: () => {
                    if (this.env?.services?.action?.currentController?.props?.resModel === 'helpdesk.ticket') {
                        this.env.bus.trigger('message_update_ev', { message: this });
                    }
                    if (!composer.exists()) {
                        return;
                    }
                    composer._reset();
                    if (composer.activeThread) {
                        composer.activeThread.fetchData(['messages']);
                    }
                },
            };
            await this.env.services.action.doAction(action, options);
        },
    },
});
