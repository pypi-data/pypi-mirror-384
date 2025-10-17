/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";
import { sprintf } from "@web/core/utils/strings";

/**
 * Function to format dates to strings
 * @param {moment} date - Date to format.
 * @return {string} - Formatted date.
 */
export function formatRelativeDate(date) {
    const today = moment().startOf('day');
    const diff = Math.floor(date.diff(today, 'days', true));
    if (diff === 0) {
        return _t("Today");
    } else if (diff < 0) {
        if (diff === -1) {
            return _t("Yesterday");
        }
        return sprintf(_t("%s days ago"), Math.abs(diff));
    } else {
        if (diff === 1) {
            return _t("Tomorrow");
        }
        return sprintf(_t("Due in %s days"), diff);
    }
}

export class RelativeDateField extends Component {
    static template = "widget_list_message.RelativeDateField";
    static props = {
        ...standardFieldProps,
    };

    get formattedDate() {
        if (!this.props.value) {
            return "";
        }
        const momentDate = moment(new Date(this.props.value));
        return formatRelativeDate(momentDate);
    }
}


registry.category("fields").add("relative_date", RelativeDateField);


export default {
    RelativeDateField,
    formatRelativeDate,
};
