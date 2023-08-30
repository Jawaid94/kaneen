/** @odoo-module **/


import { registerNewModel } from '@mail/model/model_core';
import { attr, one2one } from '@mail/model/model_field';
import { htmlToTextContentInline } from '@mail/js/utils';

import { registerInstancePatchModel } from '@mail/model/model_core';

registerInstancePatchModel('mail.message', 'mo_kaneen/static/src/models/message/message.js', {
	/**
		* @override
	*/

	_computeFormattedDate() {
	    if (!this.date) {
	        // Without a date, we assume that it's a today message. This is
            // mainly done to avoid flicker inside the UI.
            return this.env._t("Today");
        }
        return moment(this.date).format('MMM D, YYYY hh:mm:ss A');
    },


});