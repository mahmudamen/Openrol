odoo.define('de_school_timetable.TaskGanttView', function (require) {
'use strict';
var GanttView = require('web_gantt.GanttView');
var GanttController = require('web_gantt.GanttController');
var GanttRenderer = require('web_gantt.GanttRenderer');
var TaskGanttModel = require('project_enterprise.TaskGanttModel');

var view_registry = require('web.view_registry');

var TaskGanttView = GanttView.extend({
    config: _.extend({}, GanttView.prototype.config, {
        Controller: GanttController,
        Renderer: GanttRenderer,
        Model: TaskGanttModel,
    }),
});

view_registry.add('timetable_gantt', TaskGanttView);
return TaskGanttView;
});


/** @odoo-module **/

import { HelpdeskDashBoard } from '@de_school_timetable/views/helpdesk_dashboard';
import { registry } from '@web/core/registry';
import { kanbanView } from '@web/views/kanban/kanban_view';
import { KanbanRenderer } from '@web/views/kanban/kanban_renderer';

export class HelpdeskDashBoardRenderer extends KanbanRenderer {};

HelpdeskDashBoardRenderer.template = 'de_helpdesk.HelpdeskKanbanView';
HelpdeskDashBoardRenderer.components = Object.assign({}, KanbanRenderer.components, { HelpdeskDashBoard });

export const HelpdeskDashBoardKanbanView = {
    ...kanbanView,
    Renderer: HelpdeskDashBoardRenderer,
};

registry.category("views").add("helpdesk_dashboard_kanban", HelpdeskDashBoardKanbanView);