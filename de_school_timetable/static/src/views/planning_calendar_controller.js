/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { CalendarController } from "@web/views/calendar/calendar_controller";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";

export class PlanningCalendarController extends CalendarController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.user = useService("user");
        this.orm = useService("orm");
        onWillStart(async () => {
            this.isSystemUser = await this.user.hasGroup('base.group_system');
        });
    }

    async onClickAddButton() {
        const action = {
            type: 'ir.actions.act_window',
            res_model: 'calendar.event',
            views: [[false, 'form']],
        };
        await this.actionService.doAction(action, {
            additionalContext: this.props.context,
        });
    }
}
