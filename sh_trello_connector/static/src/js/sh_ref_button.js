odoo.define("sh_import_product_var_gs.import", function (require) {
    "use strict";

    var core = require("web.core");
    var ListController = require("web.ListController");
    var session = require("web.session");

    var QWeb = core.qweb;

    var _t = core._t;

    ListController.include({
        init: function (parent, model, renderer, params) {
            var context = renderer.state.getContext();
            this.sh_trello_connector_project_id = context.active_id;
            return this._super.apply(this, arguments);
        },


        renderButtons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);

            var data = this.model.get(this.handle);
            if (this.modelName != "project.task") {
                this.$buttons.find("button.js_cls_btn_sh_import_product_var_gs").hide();
            }
            if (this.$buttons) {
                let filter_button = this.$buttons.find(".js_cls_btn_sh_import_product_var_gs");
                filter_button && filter_button.click(this.proxy("sh_import_product_var_gs_action"));
            }
        },

        sh_import_product_var_gs_action: function () {
            $.blockUI();
            var self = this;
            var data = this.model.get(this.handle);
            return self._rpc({
                model: "sh.trello.credentials",
                method: "trello_refresh",
                args: [self.sh_trello_connector_project_id, data.res_ids],
                context: self.context,
            }).then(function (res) {
                alert(res)
                self.trigger_up("reload");
                $.unblockUI();
            });
        },
    });
});
