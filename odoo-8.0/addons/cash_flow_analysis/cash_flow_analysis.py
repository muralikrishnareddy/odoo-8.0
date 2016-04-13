from openerp.osv import osv, fields
import time
from openerp.tools import *

class CashFlowAnalysis(osv.osv):
    
    _name = 'cash.flow.analysis'
    _description = 'Cash Flow Analysis'
    _auto = False
    _columns = {
                'name':fields.char('Name',size=20),
                'partner_id':fields.many2one('res.partner','Partner'),
                'account_id':fields.many2one('account.account','Account'),
                'date_due':fields.date('Due Date'),
                'debit':fields.float('Receivable'),
                'credit':fields.float('Payable'),
                'analytic_account_id':fields.many2one('account.analytic.account','Analytic Account'),
                'state':fields.selection([('valid','Posted'),('draft','Un-Posted')],'State'),
                'type':fields.selection([('receivable','In Flows'),('payable','Out Flows')],'Flows'),
                'reconcile_id':fields.integer('Reconcile'),
                'ref':fields.char('Ref'),
                'balance':fields.float('Amount'),
                }
    
    def init(self, cr):
        drop_view_if_exists(cr, 'cash_flow_analysis')
        cr.execute('''
        create or replace view cash_flow_analysis as (select aml.id as id
            ,aml.name as name
            ,aml.partner_id as partner_id
            ,aml.account_id as account_id
            ,aml.date_maturity as date_due
            ,aml.debit as debit
            ,aml.credit as credit
            ,aml.debit - aml.credit as balance
            ,aml.analytic_account_id as analytic_account_id
            ,aml.state as state
            ,aa.type as type
            ,coalesce(aml.reconcile_id,0) as reconcile_id
            ,aml.ref as ref
            from account_move_line aml
            join account_account aa on (aa.id=aml.account_id)
            where aa.type in ('payable','receivable') and aml.date_maturity is not null and aml.reconcile_id is null)''')
    
CashFlowAnalysis()