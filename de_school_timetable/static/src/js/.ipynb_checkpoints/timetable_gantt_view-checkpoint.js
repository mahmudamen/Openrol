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