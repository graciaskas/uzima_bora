# -*- coding: utf-8 -*-
import logging

from zk import ZK, const
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
ERREUR_FUSEAU = 'Definissez votre fuseau horaire dans les préférences'


class UboDevice(models.Model):
    _name = 'ubo.device'
    _description = 'Empreintes'
    _inherit = ['portal.mixin','mail.thread', 'mail.activity.mixin','utm.mixin']

    name = fields.Char('Model',required=True,copy=False,tracking=1)
    ip_adress= fields.Char('Adresse IP',required=True,copy=False,tracking=1)
    states = fields.Selection([('not_connected','Non Connecté'),('connected','Connecté')],'State',default='not_connected')
    port_number= fields.Integer('Numéro de PORT',required=True,tracking=1,default=4370)
    active = fields.Boolean(default=True)

    # def setZkTime(self,conn):
    #     if not self.env.user.tz:
    #         raise Warning(ERREUR_FUSEAU)
    #     # update new time to machine
    #     newtime = datetime.now(self.env.user.tz)
    #     conn.set_time(newtime)

    def test_connection(self):
        conn = None
        zk = ZK(self.ip_adress, port=4370, timeout=10)
        try:
            print('Connecting to device ...')
            conn = zk.connect()
            print ('Disabling device ...')
            conn.disable_device()
            # self.setZkTime(conn)

            # attendances = conn.get_attendance()
            
            # for attendance in attendances:
            #     print({
            #         'uid':attendance.uid,
            #         'user_id':attendance.user_id,
            #         "timestamp":attendance.timestamp.strftime("%d/%m/%Y, %H:%M:%S"),
            #         "status":attendance.status,
            #         "punch":attendance.punch
            #     })
               


            print ('Enabling device ...')
            conn.enable_device()
            self.write({
                'states':'connected'
            })
            return  {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Test de Connexion !'),
                    'message': 'La connexion de l\'empreinte digitale a été établie avec succès',
                    'sticky': False,
                }
            }
        except Exception as e:
            print ("Process terminate : {}".format(e))
        finally:
            if conn:
                conn.disconnect()
    
    def clear_attendance(self):
        conn = None
        zk = ZK(self.ip_adress, port=4370, timeout=10)
        try:
            print('Connecting to device ...')
            conn = zk.connect()
            print ('Disabling device ...')
            conn.disable_device()
            print('Firmware Version: : {}'.format(conn.get_firmware_version()))

            attendances = conn.clear_attendance()
            print(attendances);
            print('Présences effacées avec success !')
            print ('Enabling device ...')
            conn.enable_device()
            self.write({
                'states':'connected'
            })
        except Exception as e:
            print ("Process terminate : {}".format(e))
        finally:
            if conn:
                conn.disconnect()
    
