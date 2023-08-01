odoo.define('pos_multi_user.auto_login', function (require) {
    "use strict";
    var gui = require('point_of_sale.gui');

    gui.Gui.include({
        _show_first_screen: function () {
            if (this.pos.config.module_pos_hr) {
                debugger
                var screen = (this.chrome.gui.pos.get_order() ? this.chrome.gui.pos.get_order().get_screen_data('previous-screen') : this.chrome.gui.startup_screen) || this.chrome.gui.startup_screen;
                this.chrome.gui.show_screen(screen);
            } else {
                this._super();
            }
        },
    })
})