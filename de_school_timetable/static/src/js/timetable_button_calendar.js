odoo.define('de_school_timetable.calendar_timetable_button', function (require) {
    "use strict";
    
    var CalendarController = require('web.CalendarController');
    var CalendarView = require('web.CalendarView');
    var viewRegistry = require('web.view_registry');
    
    
    var CalendarButton = CalendarController.extend({
        buttons_template: 'de_school_timetable.timetable_button_calendar',
        events: _.extend({}, CalendarController.prototype.events, {
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

    var TimetableCalendarView = CalendarView.extend({
        config: _.extend({}, CalendarView.prototype.config, {
            Controller: CalendarButton,
        }),
    });

    viewRegistry.add('timetable_button_in_calendar', TimetableCalendarView);
});
