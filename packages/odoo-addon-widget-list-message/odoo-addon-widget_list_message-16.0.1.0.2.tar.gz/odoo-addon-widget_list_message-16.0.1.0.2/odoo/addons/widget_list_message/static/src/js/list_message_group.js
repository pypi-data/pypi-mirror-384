/** @odoo-module */

import { Field } from '@web/views/fields/field';
import { markup } from "@odoo/owl";
import { registry } from "@web/core/registry";


/**
 * Function to format message fields
 * @param {string|object} value - Value to format.
 * @return {string} - Formatted value.
 */
const formatValue = (value) => {
    if (
        (typeof value === 'object' && value.constructor.name === 'Markup')
        || (
            typeof value === 'string'
            && ["</", "/>"].some(token => value.includes(token)
            ))
    ) {
        return `<p></p><div>${value.toString().replace(/style\s*=\s*(['"])(.*?)\1/gi, '')}</div>`;
    }
    if (typeof value === 'object' && value.constructor.name === 'DateTime') {
        return `${value.c.day}/${value.c.month}/${value.c.year} `
            + `${value.c.hour}:${value.c.minute}:${value.c.second} `;
    }
    if (typeof value === 'object' && value.constructor.name === 'Date') {
        return `${value.getDate()}/${value.getMonth() + 1}/${value.getFullYear()} `;
    }
    if (typeof value === 'string' && value.includes("@")) {
        const name = value.replace(/<[^>]*>|['"]/g, '');
        const email = value.match(/<([^>]+)>/)
        if (!email || email === 'False') return `${name} `;
        if (email.length > 0 && email[1]) {
            return `${name} &lt;${email[1]}&gt; `;
        }
        return `${name} `;
    }
    return `${value.toString()}`;
}


export class ListMessageGroupField extends Field {
    async setup() {
        super.setup(...arguments);

        this.applyToField = this.props.name;
        this.fieldGroups = [];
        this.setGroupAttribute();
        this.groupData();

        this.validateWidgetSetup();
    }

    validateWidgetSetup() {
        if (!this.fieldGroups) {
            throw 'Failed to initialize widget for grouped message data.'
        }
        this.fieldGroups.flat().forEach((field) => {
            if (!(field in this.props.record.activeFields)) {
                throw `One or more fields in your widget options are missing from view`;
            }
        })
    }

    setGroupAttribute() {
        const activeFields = this.props.record.activeFields;
        if (this.applyToField in activeFields) {
            const field = activeFields[this.applyToField]
            // search options first since it is going to be already parsed
            if (field.options && 'field_groups' in field.options) {
                this.fieldGroups = field.options.field_groups || [];
                return;
            }
            const context = field.context
            if (context && context.includes('field_groups')) {
                try {
                    this.fieldGroups = JSON.parse(context)?.field_groups || [];
                } catch (err) {
                    let msg = `
                        Invalid or missing context/options for widget:\n
                        ${err}
                    `;
                    throw msg;
                }
            }
        }
    }

    groupData() {
        this.groupedData = Object.entries(this.fieldGroups).map(([groupIndex, group]) => {
            const renderedFields = [];
            group.forEach((field) => {
                const data = this.props.record.data;
                if (!data || !data[field]
                    || (data.message_type === 'comment' && field === 'subject')) return;

                const fieldValue = formatValue(data[field]);
                renderedFields.push(markup(fieldValue));
            });

            return {
                key: `group_${groupIndex}`,
                groupName: group,
                fields: renderedFields.map((val, i) => ({ key: `field_${i}`, val })),
            };
        });
    }
}


ListMessageGroupField.template = 'widget_list_message.ListMessageGroupField';


registry.category("fields").add("list_message_group_field", ListMessageGroupField);
