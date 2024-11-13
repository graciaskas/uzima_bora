# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime
from datetime import datetime

_logger = logging.getLogger(__name__)

class UboPresence(models.Model):
    _name = 'ubo.presence'
    _description = 'Présences de journaliers'
    _inherit = ['portal.mixin','mail.thread', 'mail.activity.mixin','utm.mixin']
    _order= 'checkin desc'
    name = fields.Char('ID',readonly=True, copy=False,default=(_('New')))
    journalier_id = fields.Many2one("ubo.journalier",string='Journalier',required=True)
    checkin = fields.Datetime('Heure d\'entrée',readonly=True,default=fields.Datetime.now)
    checkout = fields.Datetime('Heure de sortie',readonly=True,tracking=1)
    worked_hours = fields.Float(string='Heure travaillées', compute='_compute_worked_hours', store=True, readonly=True)
    states = fields.Selection([
        ('running','En cours'),
        ('done','Fait')
    ],string='Etat',default='running',tracking=1)

    site = fields.Selection([
        ('tangawisi','Tangawisi'),
        ('ihango','Ihango')
    ],string='Site',required=True,related='journalier_id.site')
    

    company_id = fields.Many2one('res.company', default= lambda self : self.env.user.company_id,readonly=True)
    active = fields.Boolean('Active',default=True)

    @api.depends('checkin', 'checkout')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.checkout:
                delta = attendance.checkout - attendance.checkin
                attendance.worked_hours = delta.total_seconds() / 3600.0
            else:
                attendance.worked_hours = False

    @api.constrains('checkin', 'checkout')
    def _check_validity_checkin_checkout(self):
        """ verifies if checkin is earlier than checkout. """
        for attendance in self:
            if attendance.checkin and attendance.checkout:
                if attendance.checkout < attendance.checkin:
                    raise ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))


    @api.constrains('checkin', 'checkout', 'journalier_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same journalier.
            For the same journalier we must have :
                * maximum 1 "open" attendance record (without checkout)
                * no overlapping time slices with previous journalier records
        """
        for attendance in self:
            # we take the latest attendance before our checkin time and check it doesn't overlap with ours
            last_attendance_before_checkin = self.env['ubo.presence'].search([
                ('journalier_id', '=', attendance.journalier_id.id),
                ('checkin', '<=', attendance.checkin),
                ('id', '!=', attendance.id),
            ], order='checkin desc', limit=1)
            if last_attendance_before_checkin and last_attendance_before_checkin.checkout and last_attendance_before_checkin.checkout > attendance.checkin:
                raise ValidationError(_("Cannot create new attendance record for %(empl_name)s, the journalier was already checked in on %(datetime)s") % {
                    'empl_name': attendance.journalier_id.name,
                    'datetime': format_datetime(self.env, attendance.checkin, dt_format=False),
                })

            if not attendance.checkout:
                # if our attendance is "open" (no checkout), we verify there is no other "open" attendance
                no_checkout_attendances = self.env['ubo.presence'].search([
                    ('journalier_id', '=', attendance.journalier_id.id),
                    ('checkout', '=', False),
                    ('id', '!=', attendance.id),
                ], order='checkin desc', limit=1)
                if no_checkout_attendances:
                    raise ValidationError(_("Cannot create new attendance record for %(empl_name)s, the journalier hasn't checked out since %(datetime)s") % {
                        'empl_name': attendance.journalier_id.name,
                        'datetime': format_datetime(self.env, no_checkout_attendances.checkin, dt_format=False),
                    })
            else:
                # we verify that the latest attendance with checkin time before our checkout time
                # is the same as the one before our checkin time computed before, otherwise it overlaps
                last_attendance_before_checkout = self.env['ubo.presence'].search([
                    ('journalier_id', '=', attendance.journalier_id.id),
                    ('checkin', '<', attendance.checkout),
                    ('id', '!=', attendance.id),
                ], order='checkin desc', limit=1)
                if last_attendance_before_checkout and last_attendance_before_checkin != last_attendance_before_checkout:
                    raise ValidationError(_("Impossible de créer un nouvel enregistrement de présence pour %(empl_name)s, le journalier était déjà enregistré le %(datetime)s") % {
                        'empl_name': attendance.journalier_id.name,
                        'datetime': format_datetime(self.env, last_attendance_before_checkout.checkin, dt_format=False),
                    })

    def action_done(self):
        self.write({
            'checkout':datetime.now(),
            'states':'done'
        })

    @api.returns('self', lambda value: value.id)
    def copy(self):
        raise UserError(_('Vous ne pouvez pas dupliquer une présence.'))

    def unlink(self):
        raise UserError(_('Impossible de supprimer !'))

    @api.model
    def create(self, vals):
        vals["name"] = (
            self.env["ir.sequence"].next_by_code("ubo.presence")
        )
        return super(UboPresence, self).create(vals)
