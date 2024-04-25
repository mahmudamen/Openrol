/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { PlanningCalendarController } from "@de_school_timetable/views/planning_calendar_controller";

export const planningCalendarView = {
    ...calendarView,
    Controller: PlanningCalendarController,
};

registry.category("views").add("planning_calendar", planningCalendarView);
