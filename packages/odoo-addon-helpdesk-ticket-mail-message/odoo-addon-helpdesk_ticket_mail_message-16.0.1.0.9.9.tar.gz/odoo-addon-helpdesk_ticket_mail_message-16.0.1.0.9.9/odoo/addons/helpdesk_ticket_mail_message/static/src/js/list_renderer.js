/** @odoo-module */

import { registry } from '@web/core/registry';
import { useEffect } from "@odoo/owl";
import { ListRenderer } from '@web/views/list/list_renderer';
import { X2ManyField } from '@web/views/fields/x2many/x2many_field';

export class ListRendererMailIcon extends ListRenderer {
    setup() {
        super.setup();

        this.filterButtons = {
            emailSent: { icon: 'fa-long-arrow-left color-red', active: false },
            emailReceived: { icon: 'fa-long-arrow-right color-black', active: false },
            note: { icon: 'fa-file-text-o color-green', active: false }
        };

        useEffect(() => {
            if (this.tableRef.el.parentElement.parentElement.parentElement.querySelectorAll('div.btn-group').length == 0) {
                this.setupFilterButtons();
            }
            this.newFormatRender()
        });
        this.env.bus.on("message_update_ev", this, this._onMessageContentUpdated);
    }

    async _onMessageContentUpdated({ message }) {
        await this.props.list.model.load();
        this.props.list.model.notify();
        if (this.tableRef?.el) this.newFormatRender();
    }

    setupFilterButtons() {
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'btn-group';
        buttonContainer.style.padding = '10px 0px 0px 0px';

        Object.entries(this.filterButtons).forEach(([type, config]) => {
            const button = document.createElement('button');
            button.className = 'btn btn-secondary filter-custom';

            const icon = document.createElement('i');
            icon.className = `fa ${config.icon}`;
            button.appendChild(icon);

            button.addEventListener('click', () => this.onClickFilter(type));
            buttonContainer.appendChild(button);
        });

        this.tableRef.el.parentElement.parentElement.parentElement.prepend(buttonContainer);
    }

    newFormatRender() {
        const self = this;

        this.tableRef.el.querySelectorAll('th').forEach((header) => {
            if (header.getAttribute('data-name') === 'message_type_mail') {
                header.innerHTML = '';
            }
            if (self.props.list.resModel === "mail.message"
                && self.props.list.model.root.resModel === "helpdesk.ticket"
                && header.getAttribute('data-name') === 'body'
            ) {
                header.querySelectorAll('i').forEach((icon) => {
                    icon.remove();
                });
            }
        });
        this.tableRef.el.querySelectorAll('td.o_data_cell').forEach((cellEl) => {
            const cellName = cellEl.getAttribute('name');
            const cellId = cellEl.parentNode.getAttribute("data-id");
            const record = this.props.list.records.find(record => record.id === cellId)
            if (!record.data.body.toString()) {
                $(cellEl.parentElement).remove();
                return;
            }
            if (cellName === 'message_type_mail') {
                const icon = document.createElement('i');
                const email_from = record.data['email_from'];
                const message_type_mail = record.data['message_type_mail'];
                let iconClass = '';
                let title = '';
                switch (message_type_mail) {
                    case 'email_sent':
                        iconClass = 'fa fa-long-arrow-left color-red';
                        title = `To: ${email_from}`;
                        break;
                    case 'email_received':
                        iconClass = 'fa fa-long-arrow-right color-black';
                        title = `From: ${email_from}`;
                        break;
                    case 'note':
                        iconClass = 'fa fa-file-text-o color-green';
                        title = `User: ${email_from}`;
                        break;
                }
                icon.className = iconClass;
                icon.title = title;
                cellEl.replaceChildren(icon);
            }
        });
    }

    onClickFilter(selectedType) {
        Object.entries(this.filterButtons).forEach(([type, config]) => {
            if (type !== selectedType && config.active) {
                this.toggleFilter(type);
            }
        });

        this.toggleFilter(selectedType);
    }

    toggleFilter(type) {
        const rows = this.tableRef.el.querySelectorAll('tr.o_data_row');
        const button = this.tableRef.el.parentElement.parentElement.parentElement.parentElement.querySelector(`.filter-custom i.${this.filterButtons[type].icon.replaceAll(" ", ".")}`).parentElement;
        const isActive = this.filterButtons[type].active;

        rows.forEach(row => {
            const icon = row.querySelector('td:first-child i');
            const shouldHide = icon && !icon.classList.value.includes(this.filterButtons[type].icon);

            if (shouldHide && !isActive) {
                row.style.display = 'none';
                button.style.backgroundColor = '#7C7BAD';
            } else if (shouldHide && isActive) {
                row.style.display = '';
                button.style.removeProperty('background-color');
            }
        });

        this.filterButtons[type].active = !isActive;
    }

    getCellClass(column, record) {
        let classes = super.getCellClass(column, record);
        if (column.name === 'message_type_mail') {
            classes += ' text-center';
        }
        return classes;
    }
}

export class MailIconX2ManyField extends X2ManyField {
    setup() {
        super.setup();
    }
}

MailIconX2ManyField.components = {
    ...X2ManyField.components,
    ListRenderer: ListRendererMailIcon,
};

registry.category("fields").add("list_mail_icon_one2many", MailIconX2ManyField);
