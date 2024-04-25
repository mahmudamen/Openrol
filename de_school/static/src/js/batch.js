odoo.define('de_school.menu_hide', function (require) {
    'use strict';

    var core = require('web.core');
    var session = require('web.session');

    var company_id = session.company_id;

    if (company_id) {
        var use_batch = session.user_companies.allowed_companies.find(c => c.id === company_id).use_batch;
        if (!use_batch) {
            $('.o_menu_sections .dropdown-menu a[data-menu-xmlid="de_school.menu_school_courses_course_batch"]').hide();
        }
    }
});
