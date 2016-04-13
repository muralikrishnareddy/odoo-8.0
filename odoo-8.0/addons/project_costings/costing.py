from openerp.osv import osv, fields
import time


class ProjectCostings(osv.osv):
    
    _name = 'project.costings'
    
    _description = 'Project Costings'
    
    def _get_budget_amount(self, cr, uid, ids, field, arg, context=None):
        res = {}
        for pj_ct in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in pj_ct.construction_costing_lines:
                total += line.amount
            for line in pj_ct.operation_costing_lines:
                total += line.amount
            for line in pj_ct.support_costing_lines:
                total += line.amount
            res[pj_ct.id] = total
        return res
    
    _columns = {
                'name':fields.char('Name',size=120,readonly=True,states={'draft':[('readonly',False)]}),
                'partner_id':fields.many2one('res.partner','Customer',readonly=True,states={'draft':[('readonly',False)]}),
                'date':fields.date('Date',readonly=True,states={'draft':[('readonly',False)]}),
                'projected_amount':fields.float('Total Projected Amount',readonly=True,states={'draft':[('readonly',False)]}),
                'budgeted_amount':fields.function(_get_budget_amount,type="float",string='Total Budget Amount'),
                'state':fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancel')],string="State"),
                'construction_revenue_lines':fields.one2many('rate.lines','construction_revenue_id','Construction Revenue Lines',readonly=True,states={'draft':[('readonly',False)]}),
                'operation_revenue_lines':fields.one2many('rate.lines','operation_revenue_id','Operation Revenue Lines',readonly=True,states={'draft':[('readonly',False)]}),
                'support_revenue_lines':fields.one2many('rate.lines','support_revenue_id','Support Revenue Lines',readonly=True,states={'draft':[('readonly',False)]}),
                'construction_costing_lines':fields.one2many('rate.lines','construction_costing_id','Costruction Costing Lines',readonly=True,states={'draft':[('readonly',False)]}),
                'operation_costing_lines':fields.one2many('rate.lines','operation_costing_id','Operation Costing Lines',readonly=True,states={'draft':[('readonly',False)]}),
                'support_costing_lines':fields.one2many('rate.lines','support_costing_id','Support Costing Lines',readonly=True,states={'draft':[('readonly',False)]}),
                'user_ids':fields.many2many('res.users','proj_cost_users_rel','costing_id','user_id',string="Users",readonly=True,states={'draft':[('readonly',False)]}),
                'date_from':fields.date('Date From',readonly=True,states={'draft':[('readonly',False)]}),
                'date_to':fields.date('Date To',readonly=True,states={'draft':[('readonly',False)]}),
                'responsible_user_id':fields.many2one('res.users','Responsible User',readonly=True,states={'draft':[('readonly',False)]}),
                'validated_user_id':fields.many2one('res.users','Validated By',readonly=True,states={'draft':[('readonly',False)]}),
                'project_id':fields.many2one('project.project','Project',readonly=True,states={'draft':[('readonly',False)]}),
                'budget_id':fields.many2one('crossovered.budget','Budget'),
                'analytic_account_ids':fields.many2many('account.analytic.account','analytic_project_costings_rel','proj_cost','anal_account','Analytic Accounts'),
                }
    
    _defaults = {
                 'state':'draft',
                 'date':time.strftime('%Y-%m-%d'),
                 'responsible_user_id': lambda s,cr,uid,c:uid,
                 }
    
    
    def copy(self, cr, uid, ids, default, context=None):
        if not default:
            default = {}
            
        default['state'] = 'draft'
        default['validated_user_id'] = False
        default['project_id'] = False
        default['budget_id'] = False
        default['analytic_account_ids'] = [(6,0,[])]
        
        return super(ProjectCostings, self).copy(cr, uid, ids, default, context=context)
    
    def action_confirm(self, cr, uid, ids, context=None):
        analytic_account_ids = []
        for pj_ct in self.browse(cr, uid, ids, context=context):
            project = {
                       'name':pj_ct.name,
                       'partner_id':pj_ct.partner_id.id,
                       'user_id':pj_ct.responsible_user_id.id,
                       'date_start':pj_ct.date_from,
                       'date':pj_ct.date_to,
                       }
            project_id = self.pool.get('project.project').create(cr, uid, project, context=context)
            budget = {
                      'name':'Budget for Project %s'%pj_ct.name,
                      'creating_user_id':pj_ct.responsible_user_id.id,
                      'code':'ABC',
                      'date_from':pj_ct.date_from,
                      'date_to':pj_ct.date_to,
                      }
            budget_id = self.pool.get('crossovered.budget').create(cr, uid, budget, context=context)
            budget_purchase_post_id = self.pool.get('account.budget.post').search(cr, uid, [('name','=','Purchases')])
            analytic_account_id = self.pool.get('project.project').read(cr, uid, project_id, ['analytic_account_id'], context=context)['analytic_account_id'][0]
            analytic_account_ids.append(analytic_account_id)
            con_analytic_account_id = self.pool.get('account.analytic.account').create(cr, uid, {'name':'Constructions',
                                                                                                 'parent_id':analytic_account_id,
                                                                                                 'date_start':pj_ct.date_from,
                                                                                                 'date':pj_ct.date_to})
            analytic_account_ids.append(con_analytic_account_id)
            op_analytic_account_id = self.pool.get('account.analytic.account').create(cr, uid, {'name':'Operations',
                                                                                                 'parent_id':analytic_account_id,
                                                                                                 'date_start':pj_ct.date_from,
                                                                                                 'date':pj_ct.date_to})
            analytic_account_ids.append(op_analytic_account_id)
            for line in pj_ct.construction_costing_lines:
                data = {
                        'name':line.name,
                        'parent_id':con_analytic_account_id,
                        'date_start':pj_ct.date_from,
                        'date':pj_ct.date_to,
                        'crossovered_budget_line':[(0,0,{'crossovered_budget_id':budget_id,
                                                         'general_budget_id':budget_purchase_post_id and budget_purchase_post_id[0],
                                                         'date_from':pj_ct.date_from,
                                                         'date_to':pj_ct.date_to,
                                                         'planned_amount':-line.amount})]
                        }
                child_account = self.pool.get('account.analytic.account').create(cr, uid, data, context)
                analytic_account_ids.append(child_account)
            for line in pj_ct.operation_costing_lines:
                data = {
                        'name':line.name,
                        'parent_id':op_analytic_account_id,
                        'date_start':pj_ct.date_from,
                        'date':pj_ct.date_to,
                        'crossovered_budget_line':[(0,0,{'crossovered_budget_id':budget_id,
                                                         'general_budget_id':budget_purchase_post_id and budget_purchase_post_id[0],
                                                         'date_from':pj_ct.date_from,
                                                         'date_to':pj_ct.date_to,
                                                         'planned_amount':-line.amount})]
                        }
                child_account = self.pool.get('account.analytic.account').create(cr, uid, data, context)
                analytic_account_ids.append(child_account)
            self.write(cr, uid, [pj_ct.id], {'state':'confirmed','validated_user_id':uid,'project_id':project_id,'budget_id':budget_id,'analytic_account_ids':[(6,0,analytic_account_ids)]}, context=context)
        return True
    
    def action_cancel(self,cr,uid,ids,context=None):
        self.write(cr,uid,ids,{'state':'cancel'},context=context)
        return True
    
    def view_budget(self,cr,uid,ids,context=None):
        for pr_ct in self.browse(cr,uid,ids[0],context=context):
            if pr_ct.budget_id:
                return {
                'type': 'ir.actions.act_window',
                'name': ('Budget'),
                'res_model': 'crossovered.budget',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_id':pr_ct.budget_id.id,
                'target': 'new',
                'nodestroy': True,
                'context': {},
                  }
                
    def view_analytic_account(self,cr,uid,ids,context=None):
        for pr_ct in self.browse(cr,uid,ids[0],context=context):
            an_acc_ids = [account.id for account in pr_ct.analytic_account_ids]
            return {
                'type': 'ir.actions.act_window',
                'name': ('Analytic Accounts'),
                'res_model': 'account.analytic.account',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'target': 'current',
                'domain': [('id','in',an_acc_ids)],
                'nodestroy': True,
                'context': {},
                  }
        
ProjectCostings()


class RateLines(osv.osv):
    
    _name = 'rate.lines'
    
    _description = "Rate Lines"
    
    def _get_amount(self, cr, uid, ids, field, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.construction_revenue_id or line.operation_revenue_id or line.support_revenue_id:
                total = line.construction_revenue_id.projected_amount or line.operation_revenue_id.projected_amount or line.support_revenue_id.projected_amount or 0.0
            else:
                total = line.construction_costing_id.projected_amount or line.operation_costing_id.projected_amount or line.support_costing_id.projected_amount or 0.0
            res[line.id] = (line.rate / 100 * total)
        return res
    
    _columns = {
                'name':fields.char('Description',size=60, required=True),
                'rate':fields.float('Rate (%)', required=True),
                'amount':fields.function(_get_amount, type='float',string="Total Amount"),
                'construction_revenue_id':fields.many2one('project.costings','Construction Revenue Ref'),
                'operation_revenue_id':fields.many2one('project.costings','Operation Revenue Ref'),
                'support_revenue_id':fields.many2one('project.costings','Support Revenue Ref'),
                'construction_costing_id':fields.many2one('project.costings','Construction Cost Ref'),
                'operation_costing_id':fields.many2one('project.costings','Operation Cost Ref'),
                'support_costing_id':fields.many2one('project.costings','Support Cost Ref')
                }
    
RateLines()