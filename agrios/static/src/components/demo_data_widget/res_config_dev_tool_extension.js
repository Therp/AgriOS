/** @odoo-module **/
import { patch } from '@web/core/utils/patch';
import {ResConfigDevTool} from '@web/webclient/settings_form_view/widgets/res_config_dev_tool';

patch(ResConfigDevTool.prototype, {
  /**
   * Server‐side handler for the “Load New Data” button.
   */
  onClickLoadAgriosData() {
    this.action.doAction('agrios.agrios_force_install_action');
  },
});