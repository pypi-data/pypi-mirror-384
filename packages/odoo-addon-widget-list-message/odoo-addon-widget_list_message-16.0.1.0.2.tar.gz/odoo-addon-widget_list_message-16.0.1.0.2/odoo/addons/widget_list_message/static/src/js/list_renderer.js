/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { ListRenderer } from "@web/views/list/list_renderer";
import { useEffect, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

import { formatMessageField } from "./list_message_tooltip";

const MESSAGE_TYPE_MAIL_ACTION_MAP = {
    note: "mail_compose_message_action_note",
    email_received: "mail_compose_message_action",
    email_sent: "mail_compose_message_action_resend",
}

patch(ListRenderer.prototype, 'widget_list_message.MessageListRenderer', {
    setup() {
        this._super();

        useEffect(() => {            
            this.addMessageTooltips();
        });
    },

    addMessageTooltips() {
        this.tableRef.el.querySelectorAll('td.o_data_cell').forEach((cellEl) => {
            const cellName = cellEl.getAttribute('name');
            const cellId = cellEl.parentNode.getAttribute("data-id");
            
            if (!cellName || !cellId) return;

            const record = this.props.list.records.find(r => r.id === cellId)

            if (!record) return;

            if (cellName === 'body') {
                const message = {
                    email_from: formatMessageField(record.data.email_from),
                    email_to: formatMessageField(record.data.email_to),
                    email_cc: formatMessageField(record.data.email_cc),
                }
                cellEl.setAttribute(
                    'data-tooltip-template',
                    'widget_list_message.ListMessageTooltip'
                );
                cellEl.setAttribute('data-tooltip-props', JSON.stringify({
                    message: message
                }));
                cellEl.setAttribute('data-tooltip-info', JSON.stringify({
                    message: message
                }))
            }
        });
    },
    async onCellClicked(record, column, ev) {
        if (this.props.list.model.root.resModel === "helpdesk.ticket"
            && this.props.list.resModel === "mail.message"
            // TODO: We need something like below to be more precise
            // && ev.target.closest('.o_field_list_mail_icon_one2many')
        ) {
            this.tableRef.el.querySelectorAll('td.o_data_cell').forEach(async (cellEl) => {
                if (cellEl.parentNode.getAttribute("data-id") !== record.id) return;
                const action_name = MESSAGE_TYPE_MAIL_ACTION_MAP[record.data.message_type_mail];
                if (!action_name) {
                    console.warn(`No action mapped for message type ${record.data.message_type_mail}`);
                    return;
                }
                const action = await this.orm.call(
                    record.resModel, action_name, [record.data.id], {}
                );
                if (action) {
                    this.action.doAction(action);
                    return;
                }
            });
            return;
        }
        return await this._super(record, column, ev);
    },
});
