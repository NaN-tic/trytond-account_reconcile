#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from itertools import combinations
from dateutil.relativedelta import relativedelta
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.transaction import Transaction
from trytond.pyson import Eval
from trytond.pool import Pool

__all__ = ['ReconcileMovesStart', 'ReconcileMoves']


class ReconcileMovesStart(ModelView):
    'Reconcile Moves'
    __name__ = 'account.move_reconcile.start'

    company = fields.Many2One('company.company', 'Company', required=True,
        readonly=True)
    accounts = fields.Many2Many('account.account', None, None, 'Accounts',
        domain=[
            ('company', '=', Eval('company')),
            ('reconcile', '=', True),
            ('kind', '!=', 'view'),
            ],
        depends=['company'])
    parties = fields.Many2Many('party.party', None, None, 'Parties')
    max_lines = fields.Selection([
            ('2', 'Two'),
            ('3', 'Three'),
            ('4', 'Four'),
            ('5', 'Five'),
            ('6', 'Six'),
        ], 'Maximum Lines', sort=False, required=True,
        help=('Maximum number of lines to include on a reconciliation'))
    max_months = fields.Integer('Maximum Months', required=True, help='Maximum '
        'difference in months of lines to reconcile.')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_max_lines():
        return '2'

    @staticmethod
    def default_max_months():
        return 6


class ReconcileMoves(Wizard):
    'Reconcile Moves'
    __name__ = 'account.move_reconcile'
    start = StateView('account.move_reconcile.start',
        'account_reconcile.reconcile_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Ok', 'reconcile', 'tryton-ok', default=True),
            ])
    reconcile = StateAction('account.act_move_line_form')

    def reconciliation(self, start_date, end_date):
        pool = Pool()
        Line = pool.get('account.move.line')
        Account = pool.get('account.account')
        cursor = Transaction().connection.cursor()
        table = Line.__table__()

        domain = [
            ('account.company', '=', self.start.company.id),
            ('account.reconcile', '=', True),
            ('reconciliation', '=', None),
            ]

        if self.start.accounts:
            domain.append(('account', 'in', self.start.accounts))
        if self.start.parties:
            domain.append(('party', 'in', self.start.parties))
        if start_date:
            domain.append(('date', '>=', start_date))
        if end_date:
            domain.append(('date', '<=', end_date))

        max_lines = int(self.start.max_lines)

        reconciled = set()

        #Get grouped by account and party in order to not fetch all the moves
        #in memory and only fetch the ones that can be reconciled.
        query = Line.search(domain, query=True)
        cursor.execute(*table.select(table.account, table.party,
                where=(table.id.in_(query)),
                group_by=(table.account, table.party)))

        currency = self.start.company.currency
        for account, party in cursor.fetchall():
            simple_domain = domain + [
                ('account', '=', account),
                ('party', '=', party),
                ]
            order = self._get_lines_order()
            lines = Line.search(simple_domain, order=order)
            for size in range(2, max_lines + 1):
                for to_reconcile in combinations(lines, size):
                    if set([l.id for l in to_reconcile]) & reconciled:
                        continue
                    pending_amount = sum([l.debit - l.credit for l in
                            to_reconcile])
                    if currency.is_zero(pending_amount):
                        Line.reconcile(to_reconcile)
                        for line in to_reconcile:
                            reconciled.add(line.id)
                            lines.remove(line)
        return list(reconciled)

    def do_reconcile(self, action):
        pool = Pool()
        Line = pool.get('account.move.line')

        domain = [
            ('account.reconcile', '=', True),
            ('reconciliation', '=', None),
        ]

        if self.start.start_date:
            domain.append(('date', '>=', self.start.start_date))
        if self.start.end_date:
            domain.append(('date', '<=', self.start.end_date))

        start_date = self.start.start_date
        if not start_date:
            lines = Line.search([], order=[('date', 'ASC')], limit=1)
            if not lines:
                return action, {}
            start_date = lines[0].date
        end_date = self.start.end_date
        if not end_date:
            lines = Line.search([], order=[('date', 'DESC')], limit=1)
            if not lines:
                return action, {}
            end_date = lines[0].date
        start = start_date
        reconciled = []
        while start <= end_date and start_date and end_date:
            end = start + relativedelta(months=self.start.max_months)
            if end > end_date:
                end = end_date
            reconciled += self.reconciliation(start, end)
            start += relativedelta(months=max(1, self.start.max_months // 2))
        data = {'res_id': reconciled}
        return action, data

    def _get_lines_order(self):
        'Return the order on which the lines to reconcile will be returned'
        return [
            ('date', 'ASC')
            ]
