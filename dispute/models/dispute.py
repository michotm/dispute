from odoo import api, fields, models, _


class Dispute(models.Model):
    _name = "dispute"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Dispute"

    @api.depends("line_ids")
    def _compute_total(self):
        for r in self:
            r.total = sum(self.mapped("line_ids.total"))

    @api.depends("model_ref_id")
    def _compute_partner_id(self):
        for r in self:
            r.partner_id = r.model_ref_id and r.model_ref_id.partner_id or False

    @api.depends("model_ref_id")
    def _compute_type(self):
        for r in self:
            r.dispute_type = (
                r.model_ref_id
                and self.env["ir.model"]
                .search([("model", "=", r.model_ref_id._name)])
                .name
                or False
            )

    def _selection_model(self):
        return []

    
    @api.depends('model_ref_id')
    def _compute_model_ref_id_model_name(self):
        self.model_ref_id_model_name = self.model_ref_id and self.model_ref_id._name or False

    @api.depends('model_ref_id')
    def _compute_model_ref_id_selected_id(self):
        self.model_ref_id_selected_id = self.model_ref_id and self.model_ref_id.id or False

    @api.onchange("model_ref_id")
    def _on_change_model_ref_id(self):
        self.line_ids = [(5, 0, 0)]
        
    def get_line_model_info(self, model_name):
        """return a list of dictionary with all the informations to handle the lines reference field

        :param
            char model_name: model_name of the dispute to limit the return to only compatible the lines model linked

        :return list of dict return: {'model': model_name, 'domain': odoo domain to apply on the field reference, 'product_id': name of the field product_id on the referenced model)
        """
        return []
    
    def get_related_models(self):
        return []
        
    name = fields.Char(
        copy=False,
        readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("dispute"),
    )
    state = fields.Selection(
        default="draft",
        selection=[
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("sent", "Sent"),
            ("accepted", "Accepted"),
            ("refused", "Refused"),
        ],
        tracking=True,
    )

    READONLY_STATES = {
        'accepted': [('readonly', True)],
        'refused': [('readonly', True)],
    }

    dispute_type = fields.Char(compute="_compute_type", store=True, states=READONLY_STATES)
    color = fields.Integer("Color Index", default=0)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        default=lambda self: self.env.company.id,
    )
    company_currency = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )
    date_planned = fields.Date()
    
    description = fields.Html(states=READONLY_STATES)
    line_ids = fields.One2many(
        comodel_name="dispute.line", inverse_name="dispute_id", states=READONLY_STATES)
    model_ref_id = fields.Reference(
        selection="_selection_model", string="Reference", required=True, states=READONLY_STATES
    )
    model_ref_id_model_name = fields.Char(compute='_compute_model_ref_id_model_name')
    model_ref_id_selected_id = fields.Integer(compute='_compute_model_ref_id_selected_id')
    partner_id = fields.Many2one(
        comodel_name="res.partner", compute="_compute_partner_id"
    )
    related_document_ids = fields.One2many(
        comodel_name="dispute.related.document", inverse_name="dispute_id", states=READONLY_STATES)
    responsible_id = fields.Many2one(comodel_name="res.users")
    summary = fields.Text(states=READONLY_STATES)
    total = fields.Monetary(
        compute="_compute_total",
        currency_field="company_currency",
        store=True,
        tracking=True,
    )

    def action_dispute_send(self):
        '''
        This function opens a window to compose an email, with the dispute template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('dispute', 'email_template_dispute')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'dispute',
            'active_model': 'dispute',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            # 'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_dispute_as_sent': True,
        })
        # In the case of a dispute, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Dispute')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }        

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_dispute_as_sent'):
            self.filtered(lambda o: o.state in ['draft', 'in_progress']).write({'state': 'sent'})
        return super(Dispute, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


class DisputeLine(models.Model):
    _name = "dispute.line"
    _parent_field = "_undefined"
    _description = "Dispute line"

    def _selection_model(self):
        # if self:
        selection = []
        for info in self.env["dispute"].get_line_model_info(None):
            line_model_name = info.get("model_name")
            selection.append((line_model_name, _(self.env[line_model_name]._description)))

        return selection

    @api.depends("model_ref_id")
    def _compute_product_id(self):
        for r in self:
            product_id = False
            if r.dispute_id and r.model_ref_id:
                line_model_info = r.dispute_id.get_line_model_info(None)
                product_field = next((info['product_id_field_name'] for info in line_model_info if info["model_name"] == r.model_ref_id._name), None)
                if product_field:
                    product_id = r.model_ref_id[product_field]
            r.product_id = product_id

    @api.depends("dispute_price", "qty")
    def _compute_total(self):
        for r in self:
            r.total = r.qty * r.dispute_price

    @api.onchange("standard_price")
    def _on_change_product_id(self):
        self.dispute_price = self.standard_price

    dispute_id = fields.Many2one(comodel_name="dispute")
    dispute_price = fields.Float(required=True)
    company_currency = fields.Many2one(
        "res.currency",
        string="Currency",
        related="dispute_id.company_id.currency_id",
        readonly=True,
    )
    comment = fields.Text()
    model_ref_id = fields.Reference(
        selection="_selection_model", string="Reference", required=True
    )
    product_id = fields.Many2one(
        comodel_name="product.product", compute="_compute_product_id"
    )
    qty = fields.Float(required=True)
    reason = fields.Selection(
        [
            ("qty", "Quantity"),
            ("quality", "Quality"),
            ("other", "Others"),
        ],
        required=True,
    )
    standard_price = fields.Float(related="product_id.standard_price")
    total = fields.Monetary(compute="_compute_total",
                            currency_field="company_currency")

    @api.depends('dispute_id.model_ref_id')
    def fields_get(self, allfields=None, attributes=None):
        context_dispute_id = self._context.get("dispute_id", False)
        context_model_ref_id_model_name = self._context.get("model_ref_id_model_name", False)
        context_model_ref_id_selected_id = self._context.get("model_ref_id_selected_id", [])

        model_name = context_model_ref_id_model_name
        dispute_model_ref_id = model_name and context_model_ref_id_selected_id and self.env[model_name].browse(context_model_ref_id_selected_id) or False

        # fields = self.fields_get(allfields, attributes)
        fields = super(DisputeLine, self).fields_get(
            allfields, attributes=attributes)
        dispute = self.env['dispute'].browse(context_dispute_id or [])
        line_model_info = dispute.get_line_model_info(model_name)
        fields["model_ref_id"]["selection"] = [
            (info.get("model_name", ()), _(self.env[info.get("model_name", ())]._description)) for info in line_model_info
        ]
        if dispute_model_ref_id:
            domain = []
            for info in line_model_info:
                if len(domain):
                    domain.append("|")
                for dom in eval(info.get("domain", [])):
                    domain.append(dom)
            fields["model_ref_id"]["domain"] = domain

        return fields


class DisputeRelatedDocument(models.Model):
    _name = "dispute.related.document"
    _description = "Document related to a dispute"

    def _selection_model(self):
        models = self.env['dispute'].get_related_models()

        return [(model, _(self.env[model]._description)) for model in models]


    dispute_id = fields.Many2one(comodel_name='dispute')
    model_ref_id = fields.Reference(
        selection="_selection_model", string="Reference", required=True
    )


class DisputeLineMixin(models.AbstractModel):
    _name = "dispute.line.mixin"
    _parent_field = "_undefined"
    _description = "Mixin to add dispute functionality"

    dispute_comment = fields.Text(
        related="dispute_line_id.comment", readonly=False)
    dispute_line_id = fields.Many2one(comodel_name="dispute.line")
    dispute_id = fields.Many2one(related="dispute_line_id.dispute_id")
    dispute_qty = fields.Float(related="dispute_line_id.qty", readonly=False)
    dispute_reason = fields.Selection(
        related="dispute_line_id.reason", store=True, readonly=False
    )

    def update_dispute(self, values):
        for r in self.filtered(lambda r: r.dispute_reason):
            if not r.dispute_line_id:
                r.dispute_line_id = r.dispute_line_id.create(
                    {"product_id": r.product_id.id}
                ).id
            if not r.dispute_line_id.dispute_id:
                if r._parent_field and r[r._parent_field].dispute_id:
                    dispute_id = r[r._parent_field].dispute_id
                else:
                    dispute_id = r.dispute_id.create(
                        {
                            "model_ref_id": "{},{}".format(
                                r[r._parent_field]._name, r[r._parent_field].id
                            )
                        }
                    )
                    r[r._parent_field].dispute_id = dispute_id.id
                r.dispute_line_id.dispute_id = dispute_id.id


    # @api.model_create_multi
    # def create(self, vals_list):
    #     #TODO adapt ....
    #     for values in vals_list:
    #         new_line = super().create(values)
    #         new_line.update_dispute(values)

    #     return new_line

    def write(self, values):
        res = super().write(values)
        if "dispute_id" not in values and "dispute_line_id" not in values:
            self.update_dispute(values)
        return res
