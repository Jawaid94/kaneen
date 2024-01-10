/* Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('odoo_shift_key_selection.ListRenderer', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
      events: _.extend({}, ListRenderer.prototype.events, {
        'click tbody .o_list_record_selector': '_onSelectRecords',
      }),
      _renderRows: function () {
        this.index = false;
        return this._super.apply(this, arguments);
      },
      _onSelectRecords: function (event) {
        document.getSelection().removeAllRanges();
        if (event.shiftKey) {
          var $currentCheckbox = $(event.currentTarget).find('input');
          currentIndex = 0;
          if (this.index !== false) {
              if (!$currentCheckbox.prop('checked')) {
                $currentCheckbox.prop('checked', true)
              }
              var $tbody = $(event.currentTarget).closest('tbody');
              var $allInput = $tbody.find('.o_list_record_selector input');
              var currentIndex = $allInput.index($currentCheckbox);
              var $firstChecked = $tbody.find('.o_list_record_selector input:checkbox:checked:visible:first');
              var fisrtIndex = $allInput.index($firstChecked);
              fisrtIndex = Math.min(currentIndex, this.index);
              this.index = Math.max(currentIndex, this.index);
              $allInput.slice(fisrtIndex+1, this.index).prop('checked', true);
          }
          this.index = currentIndex;
        }
      },
      _onSelectRecord: function (event) {
        var $currentCheckbox = $(event.currentTarget).find('input');
        var $tbody = $(event.currentTarget).closest('tbody');
        var $allInput = $tbody.find('.o_list_record_selector input');
        this.index = $allInput.index($currentCheckbox);
        return this._super.apply(this, arguments);
      }
    });
});
