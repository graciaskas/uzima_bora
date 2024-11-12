# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning,UserError,ValidationError
from datetime import datetime
import pytz

FORMAT_DATE = "%Y-%m-%d %H:%M:%S"
ERREUR_FUSEAU = _("Définissez votre fuseau horaire dans les préférences")

def convert_UTC_TZ(self, UTC_datetime):
    if not self.env.user.tz:
        raise Warning(ERREUR_FUSEAU)
    local_tz = pytz.timezone(self.env.user.tz)
    date = datetime.strptime(str(UTC_datetime), FORMAT_DATE)
    date = pytz.utc.localize(date, is_dst=None).astimezone(local_tz)
    return date.strftime(FORMAT_DATE)



class UboPresence(models.TransientModel):
    _name = 'report.ubo.presence'
    _description = 'Report Présence'

    date_start = fields.Datetime('Début',required=True)
    date_end = fields.Datetime('Fin',required=True)

    journalier_id = fields.Many2one('ubo.journalier')

    @api.model
    def convert_UTC_TZ(self, UTC_datetime):
        if not self.env.user.tz:
            raise Warning(ERREUR_FUSEAU)
        local_tz = pytz.timezone(self.env.user.tz)
        date = datetime.strptime(str(UTC_datetime), FORMAT_DATE)
        date = pytz.utc.localize(date, is_dst=None).astimezone(local_tz)
        return date.strftime(str(FORMAT_DATE))

    def print_report(self):
        self.ensure_one()
        user_id = self.env.user
        data = {
            'date_start': self.convert_UTC_TZ(self.date_start),
            'date_end': self.convert_UTC_TZ(self.date_end),
            'user_id': user_id.name,
            'journalier_id': self.journalier_id.id
        }
        # ('state', '=', 'done')
        records = self.env["ubo.presence"].search([
            ('checkin', '>=', data["date_start"]),
            ('checkout', '<=', data['date_end']),
        ])

        if self.journalier_id:
            records = self.env["ubo.presence"].search([
            ('checkin', '>=', data["date_start"]),
            ('checkout', '<=', data['date_end']),
            ('journalier_id', '=', data['journalier_id']),
        ])

        result = []

        for record in records:
            result.append({
                'name':record.name,
                'journalier':record.journalier_id.name,
                'checkin':record.checkin,
                'checkout':record.checkout,
                'worked_hours':record.worked_hours,
                'responsible_id':record.create_uid.name
            })

        data['lines'] = result

        docargs = {
            'doc_ids': self._ids,
            'model': self._name,
            'docs': self,
            'data': data
        }



        return self.env.ref('uzima_bora.report_ubo_presence').report_action(self, data=docargs)



