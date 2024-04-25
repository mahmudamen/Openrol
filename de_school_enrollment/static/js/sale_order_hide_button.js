odoo.define('de_school_enrollment.custom_button_hide', function (require) {
    "use strict";

    var FormView = require('web.FormView');
    var core = require('web.core');
    
    FormView.include({
        render_buttons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons && this.viewType === 'form' && this.model === 'sale.order') {
                // Hide the 'action_confirm' and 'action_quotation_send' buttons
                this.$buttons.find('button[name="action_confirm"]').hide();
                this.$buttons.find('button[name="action_quotation_send"]').hide();
            }
        }
    });
});
