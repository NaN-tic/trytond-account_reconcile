#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from itertools import combinations
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
        ],
        depends=['company'])
    parties = fields.Many2Many('party.party', None, None, 'Parties')
    max_lines = fields.Selection([
            ('2', 'Two'),
            ('3', 'Three'),
            ('4', 'Four'),
            ('5', 'Five'),
            ('6', 'Six'),
        ], 'Maximum lines', sort=False, help=('Maximum number of lines to '
            'include on a reconciliation'))
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_max_lines():
        return '2'


class ReconcileMoves(Wizard):
    'Reconcile Moves'
    __name__ = 'account.move_reconcile'
    start = StateView('account.move_reconcile.start',
        'account_reconcile.reconcile_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Ok', 'reconcile', 'tryton-ok', default=True),
            ])
    reconcile = StateAction('account.act_move_line_form')

    def do_reconcile(self, action):
        pool = Pool()
        Line = pool.get('account.move.line')
        Company = pool.get('company.company')
        transaction = Transaction()
        cursor = transaction.cursor
        table = Line.__table__()

        domain = [
            ('account.reconcile', '=', True),
            ('reconciliation', '=', None),
        ]

        if self.start.accounts:
            domain.append(('account', 'in', self.start.accounts))
        if self.start.parties:
            domain.append(('party', 'in', self.start.parties))
        if self.start.start_date:
            domain.append(('date', '>=', self.start.start_date))
        if self.start.end_date:
            domain.append(('date', '<=', self.start.end_date))

        max_lines = int(self.start.max_lines)

        currency = Company(transaction.context.get('company')).currency
        reconciled = {}

        #Get grouped by account and party in order to not fetch all the moves
        #in memory and only fetch the ones that can be reconciled.
        query = Line.search(domain, query=True)
        cursor.execute(*table.select(table.account, table.party,
                where=(table.id.in_(query)),
                group_by=(table.account, table.party)))

        for account, party in cursor.fetchall():
            simple_domain = domain + [
                ('account', '=', account),
                ('party', '=', party),
                ]
            order = self._get_lines_order()
            lines = Line.search(simple_domain, order=order)
            for size in range(2, max_lines + 1):
                for to_reconcile in combinations(lines, size):
                    if any([l.id in reconciled for l in to_reconcile]):
                        continue
                    pending_amount = sum([l.debit - l.credit for l in
                            to_reconcile])
                    if currency.is_zero(pending_amount):
                        Line.reconcile(to_reconcile)
                        for line in to_reconcile:
                            reconciled[line.id] = True
                            lines.remove(line)

        data = {'res_id': reconciled.keys()}
        return action, data

    def _get_lines_order(self):
        'Return the order on which the lines to reconcile will be returned'
        return [
            ('date', 'ASC')
            ]
