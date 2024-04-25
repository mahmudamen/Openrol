odoo.define('de_school_timetable.tree_timetable_button', function (require) {
    "use strict";
    
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    
    
    var TreeButtons = ListController.extend({
        buttons_template: 'de_school_timetable.timetable_button_tree',
        events: _.extend({}, ListController.prototype.events, {
            'click .open_wizard_action_timetable': '_OpenTimetableWizard',
        }),
        _OpenTimetableWizard: function () {
            this._openWizard('oe.school.timetable.wizard', 'Timetable');
        },
        
        _openWizard: function (resModel, name) {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: resModel,
                name: name,
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: false,
            });
        },
    });

    var TimetableListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: TreeButtons,
        }),
    });

    viewRegistry.add('timetable_button_in_tree', TimetableListView);
});
