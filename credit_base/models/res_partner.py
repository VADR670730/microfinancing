# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
import base64
from odoo.modules.module import get_module_resource
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
import logging

_logger = logging.getLogger(__name__)
class ResPartnerSuffix(models.Model):
    _name = 'res.partner.suffix'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    _mail_post_access = 'read'

    _sql_constraints = [('unique_name', 'unique(name)', 'Suffix Already exists.')]
    name = fields.Char(string="Suffix", required=True, index=True)
    shortcut = fields.Char(string="Abbreviation", required=True)

    @api.constrains('name')
    def _validate_name(self):
        id = self.id
        name = self.name
        res = self.search([['name', '=ilike', name], ['id', '!=', id]])
        if res:
            raise ValidationError(_("Suffix Name already exists."))

    @api.constrains('shortcut')
    def _validate_name(self):
        id = self.id
        shortcut = self.shortcut
        res = self.search([['shortcut', '=ilike', shortcut], ['id', '!=', id]])
        if res:
            raise ValidationError(_("Suffix Abbreviation already exists."))

class LoanClient(models.Model):
    _inherit = 'res.partner'


    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)
    code = fields.Char(readonly=True)
    short_code = fields.Char(readonly=True)
    index = fields.Integer()
    type = fields.Selection([('member','Member'),
                             ('do','Development Officer'),
                             ('ds','Development Supervisor'),
                             ('ao','Account Officer'),
                             ('bm','Branch Manager'),
                             ('gm','General Manager')], default='member', string='User Type')
    type_str = fields.Char(default=lambda self:self.default_type())
    branch_id = fields.Many2one('res.branch','Branch', required_if_type=['bm','ao','ds','do'],default= lambda self: self.default_branch(), store=True)
    area_id = fields.Many2one('res.area','Area', required_if_type='do')
    area = fields.Char(related='area_id.name', string='Area')
    parent_id = fields.Many2one('res.partner','Supervisor', required_if_type='do', domain=[('type','in',['ds','bm','gm'])])



    # @api.model
    # def hash_code(self, code):
    #     return str(base64.b64encode(str(code).encode('UTF-8')), 'UTF-8')
    #
    # @api.model
    # def decode_hash(self, code):
    #     return int(base64.b64decode(code if code else self.hash_code(0)))
    #
    # @api.model
    # def create(self, values):
    #     values['code'] = self.hash_code((int(self.decode_hash(self.search([], order='code asc', limit=1).code)) +1))
    #     return super(LoanClient, self).create(values)4

    @api.depends('name')
    def _compute_display_name(self):
        for partner in self:
            partner.display_name = partner.name

    @api.onchange('type')
    def _set_type(self):
        self.type_str = dict(self._fields['type'].selection).get(self.type)

    @api.multi
    def default_type(self):
        return dict(self._fields['type'].selection).get(self.type)

    @api.multi
    def default_branch(self):
        if self.type == 'do':
            return self.parent_id.branch_id
        else:
            return self.env['res.branch'].search([('street2','=',self.street2),('city','=', self.city)], limit=1)

    @api.onchange('street2', 'city', 'type')
    def _get_branch(self):
        if self.type == 'do':
            self.branch_id = self.parent_id.branch_id
        else:
            self.branch_id = self.env['res.branch'].search([('street2','=',self.street2),('city','=', self.city)], limit=1)

    @api.model
    def create(self, values):

        values['index'] = int(self.search([('type','=', values.get('type'))], order='index desc', limit=1).index)+1

        if values['type'] == 'gm':
            values['code'] = '%s' % ("{0:0=2d}".format(values['index']))
            values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))
        else:
            values['code'] = '%s-%s' % ("{0:0=2d}".format(self.env['res.branch'].search([('id','=',values.get('branch_id'))], limit=1).index),"{0:0=2d}".format(values['index']))
            values['short_code'] = '%s' % ("{0:0=2d}".format(values['index']))


        return super(LoanClient, self).create(values)
