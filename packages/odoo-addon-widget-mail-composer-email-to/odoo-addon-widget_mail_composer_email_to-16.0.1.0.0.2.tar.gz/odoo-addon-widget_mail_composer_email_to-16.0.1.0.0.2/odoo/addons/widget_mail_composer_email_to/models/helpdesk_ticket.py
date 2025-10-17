from odoo import api, models, tools


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    def _get_support_contact_suggestions(self, search=""):
        domain = [
            (
                "category_id",
                "in",
                self.env.company.support_contact_tag_id.ids,
            )
        ]
        if search:
            domain += ["|", ("email", "ilike", search), ("name", "ilike", search)]

        return [
            {"email": partner.email, "name": partner.name}
            for partner in self.env["res.partner"].search(domain)
        ]

    def _get_ticket_partner_suggestions(self, ticket_id, search=""):
        ticket = self.env["helpdesk.ticket"].browse(ticket_id)
        if not (ticket.exists() and ticket.partner_id):
            return []

        partners = (ticket.partner_id | ticket.partner_id.child_ids).filtered(
            lambda p: p.email
        )

        if search:
            search_lower = search.lower()
            partners = partners.filtered(
                lambda p: search_lower in (p.email or "").lower()
                or search_lower in (p.name or "").lower()
            )

        return [{"email": partner.email, "name": partner.name} for partner in partners]

    @api.model
    def get_helpdesk_email_to_suggestions(self, ticket_id, search="", filter=""):
        filter = tools.email_normalize_all(filter)

        support_contacts = self._get_support_contact_suggestions(search)
        ticket_partners = self._get_ticket_partner_suggestions(ticket_id, search)

        if filter:
            support_contacts = [s for s in support_contacts if s["email"] not in filter]
            ticket_partners = [t for t in ticket_partners if t["email"] not in filter]

        return {
            "support_contacts": support_contacts,
            "ticket_partners": ticket_partners,
        }
