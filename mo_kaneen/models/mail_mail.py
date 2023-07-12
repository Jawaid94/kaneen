import datetime
import logging
import threading

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def process_email_queue(self, ids=None):
        filters = ['&',
                   ('state', '=', 'outgoing'),
                   '|',
                   ('scheduled_date', '<', datetime.datetime.now()),
                   ('scheduled_date', '=', False)]
        if 'filters' in self._context:
            filters.extend(self._context['filters'])
        # TODO: make limit configurable
        filtered_ids = self.search(filters, limit=10000).ids
        if not ids:
            ids = filtered_ids
        else:
            ids = list(set(filtered_ids) & set(ids))
        ids.sort()

        res = None
        res = self.browse(ids)
        to_unlink = self
        for record in res.filtered(lambda x: x.model == 'account.move'):
            move = self.env['account.move'].sudo().browse(record.res_id)
            if not move.exists():
                res = res - record
                to_unlink |= record
                continue
            if not move or move.state != 'posted':
                res = res - record

        if to_unlink:
            to_unlink.sudo().unlink()

        try:
            # auto-commit except in testing mode
            auto_commit = not getattr(threading.currentThread(), 'testing', False)
            res.send(auto_commit=auto_commit)
        except Exception:
            _logger.exception("Failed processing mail queue")
        return res
