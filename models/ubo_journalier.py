# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class UboJournalier(models.Model):
    _name = 'ubo.journalier'
    _description = 'Ubo Journalier'
    _inherit = ['portal.mixin','mail.thread', 'mail.activity.mixin','utm.mixin']

    name = fields.Char('Noms', required=True,tracking=1)
    active = fields.Boolean('Active',default=True)
