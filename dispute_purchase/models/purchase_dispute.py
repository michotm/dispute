from odoo import api, fields, models, _


class dispute(models.Model):
    _inherit = ["dispute"]

    def _selection_model(self):
        selection_model = super()._selection_model()
        model_name = "purchase.order"
        selection_model.append(
            (model_name, _(self.env[model_name]._description)))

        return selection_model

    def get_line_model_info(self, model_name):
        line_model_info = {'model_name': "purchase.order.line",
                           'domain': "[('order_id.id', '=', dispute_model_ref_id.id)]",
                           'product_id_field_name': 'product_id'}
        if model_name == "purchase.order":
            # Force selection to only compatible sub_model of model_name
            return [line_model_info]
        else:
            super_info = super().get_line_model_info(model_name)
            if not model_name:
                super_info.append(line_model_info)
            return super_info

    def get_related_models(self):
        models = super().get_related_models()

        models += ['purchase.order']

        return models