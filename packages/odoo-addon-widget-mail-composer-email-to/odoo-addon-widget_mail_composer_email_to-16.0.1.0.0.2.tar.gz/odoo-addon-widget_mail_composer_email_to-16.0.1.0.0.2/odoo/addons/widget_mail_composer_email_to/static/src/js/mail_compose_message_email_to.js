/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { useState } from "@odoo/owl";

export class MailComposeMessageEmailTo extends CharField {
	static components = { AutoComplete };

	setup() {
		super.setup();
		this.state = useState({
			search: this.props.value || "",
			supportContacts: [],
			ticketPartners: [],
			visibleSuggestions: false,
		});

		this.onOptionSelected = this.onOptionSelected.bind(this);
	}

	/**
	 * Extract the last comma-separated segment for autocomplete
	 */
	getLastSegment(value) {
		if (!value) return "";
		const parts = value.split(",");
		return parts[parts.length - 1].trim();
	}

	async fetchSuggestions(search, toExclude) {
		const record = this.props.record;

        const activeModel = record.context.active_model;
        const activeId = record.context.active_id;

		if (
			activeModel !== "helpdesk.ticket" ||
			!activeId
		) {
			this.state.supportContacts = [];
			this.state.ticketPartners = [];
			this.state.visibleSuggestions = false;
			return;
		}

		const suggestions = await record.model.orm.call(
			activeModel,
			"get_helpdesk_email_to_suggestions",
			[activeId, search, toExclude]
		);

		this.state.supportContacts = suggestions.support_contacts;
		this.state.ticketPartners = suggestions.ticket_partners;
		this.state.visibleSuggestions =
			(this.state.supportContacts?.length || 0) > 0 ||
			(this.state.ticketPartners?.length || 0) > 0;
	}

	async onInput(ev) {
		const fullValue = ev.target.value || "";
		const segment = this.getLastSegment(fullValue);

		this.state.search = fullValue;
		this.state.lastSegment = segment;

		// Ensure the record is updated with the current value, even if not selected from autocomplete
		this.props.record.update({ email_to: fullValue });

		const toExclude = fullValue
			.split(",")
			.map((s) => s.trim())
			.filter((s) => s !== segment)
			.join(",");

		if (segment) {
			await this.fetchSuggestions(segment, toExclude);
		} else {
			this.state.supportContacts = [];
			this.state.ticketPartners = [];
			this.state.visibleSuggestions = false;
		}
	}

	onOptionSelected(option) {
		if (!option || !option.value) {
			return;
		}
		const current = this.state.search || "";
		const parts = current.split(",");
		parts[parts.length - 1] = `${option.label}`; // replace last segment
		const newValue = parts.join(",").trim();

		this.props.record.update({ email_to: newValue });
		this.state.search = newValue;
		this.state.supportContacts = [];
		this.state.ticketPartners = [];
		this.state.visibleSuggestions = false;
	}

	// ✅ Correct format for Odoo AutoComplete sources
	get autocompleteSources() {
		const options = [];

		if (
			this.state.supportContacts &&
			this.state.supportContacts.length > 0
		) {
			options.push({
				label: this.env._t("Support Contacts"),
				value: false,
				classList: "o_mail_composer_x_autocomplete_category",
			});
			this.state.supportContacts.forEach((s) => {
				options.push({
					label: `"${s.name}" <${s.email}>`,
					value: s.email,
				});
			});
		}

		if (this.state.ticketPartners && this.state.ticketPartners.length > 0) {
			options.push({
				label: this.env._t("Ticket Partners"),
				value: false,
				classList: "o_mail_composer_x_autocomplete_category",
			});
			this.state.ticketPartners.forEach((p) => {
				options.push({
					label: `"${p.name}" <${p.email}>`,
					value: p.email,
				});
			});
		}

		return [{ options }];
	}
}

MailComposeMessageEmailTo.template =
	"widget_mail_composer_email_to.MailComposeMessageEmailToTemplate";

registry
	.category("fields")
	.add("mail_compose_message_email_to", MailComposeMessageEmailTo);
