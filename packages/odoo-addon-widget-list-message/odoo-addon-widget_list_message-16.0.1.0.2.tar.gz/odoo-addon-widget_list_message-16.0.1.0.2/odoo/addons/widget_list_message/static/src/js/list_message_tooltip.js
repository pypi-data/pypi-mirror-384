/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";


/**
 * Function to format the message field value
 * @param {string} value - The value to format.
 * @return {string} - The formatted value.
 *  
 * This function takes a string of email addresses and names, splits them by commas,
 * and formats them into a more readable string.
 * It handles cases where the email address is enclosed in angle brackets
 */
export function formatMessageField(value) {
    // TODO: Refactor this function to be more readable and also it shouldn't be here
    let unique_emails = {};
    let unsanitized_addresses = value.split(",");
    for (let i = 0; i < unsanitized_addresses.length; i++) {
        if (unsanitized_addresses[i].includes("<")) {
            let name = unsanitized_addresses[i].split("<")[0].replaceAll("\"", "").trim();
            let email = unsanitized_addresses[i].split("<")[1].split(">")[0].trim();
            unique_emails[email] = name;
        } else {
            unique_emails[unsanitized_addresses[i].trim()] = "";
        }
    }
    let result = "";
    for (const [key, value] of Object.entries(unique_emails)) {
        if (key === "False" || value === "False") continue;
        if (value) {
            result += ` ${value} <${key}>, `;
        } else {
            result += key ? ` ${key}, `: "";
        }
    }
    return result.slice(0, -2);
}


export class ListMessageTooltip extends Component {
    static template = "widget_list_message.ListMessageTooltip";
    static props = {
        message: Object,
    };
}


registry.category("fields").add("list_message_tooltip", ListMessageTooltip);


export default {
    ListMessageTooltip,
    formatMessageField,
};
