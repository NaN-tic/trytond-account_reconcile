#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from decimal import Decimal
from itertools import combinations
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.transaction import Transaction
from trytond.pyson import Eval
from trytond.pool import Pool
from trytond.backend.sqlite.database import Cursor as SQLiteCursor

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
            ('1', 'One'),
            ('2', 'Two'),
            ('3', 'Three'),
            ('4', 'Four'),
            ('5', 'Five'),
            ('6', 'Six'),
        ], 'Maximum lines', sort=False, help=('Maximum number of lines to '
            'search for balanced amount'))
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_max_lines():
        return '1'


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

        #Separate lines with credit and lines with debit to avoid generating
        #too much combinations and get better performance
        credit_lines = Line.search(domain + [('debit', '=', 0)],
            order=self._get_lines_order())
        reconciled_ids = self.reconcile_lines(credit_lines, max_lines)
        debit_lines = Line.search(domain + [('credit', '=', 0)],
            order=self._get_lines_order())
        reconciled_ids = self.reconcile_lines(debit_lines, max_lines,
            reconciled_ids)

        data = {'res_id': reconciled_ids}
        return action, data

    def reconcile_lines(self, lines, max_lines, reconciled_ids=None):
        '''
        Find reconciliation for the given lines
        Returns the line ids which have been reconciled
        '''
        pool = Pool()
        Line = pool.get('account.move.line')

        if not reconciled_ids:
            reconciled_ids = []

        for line in lines:
            #Line may be already reconciled as a result of another line.
            if line.id in reconciled_ids:
                continue
            currency = line.account.company.currency
            matching_lines = self._get_matching_lines(line)
            if not matching_lines:
                continue
            reconciled = False
            for size in range(max_lines):
                if reconciled:
                    break
                for to_reconcile in combinations(matching_lines, size + 1):
                    #To improve performance fail if reconcile amount is less
                    #than line amount, as with one line will never reconcile.
                    if size == 0:
                        reconcile_line, = to_reconcile
                        if (line.debit != Decimal('0.0') and
                                line.debit > reconcile_line.credit):
                            break
                        if (line.credit != Decimal('0.0') and line.credit >
                                reconcile_line.debit):
                            break
                    to_reconcile = list(to_reconcile)
                    to_reconcile.append(line)
                    pending_amount = sum([l.debit - l.credit for l in
                            to_reconcile])
                    if currency.is_zero(pending_amount):
                        Line.reconcile(to_reconcile)
                        reconciled_ids.extend([l.id for l in to_reconcile])
                        reconciled = True
                        break
        return reconciled_ids

    def _get_matching_lines(self, line):
        'Return the lines that can be reconciled with the current line'
        pool = Pool()
        Line = pool.get('account.move.line')
        cursor = Transaction().cursor
        reconcile_domain = self._get_reconcile_domain(line)
        reconcile_order = self._get_reconcile_order(line)
        if isinstance(cursor, SQLiteCursor):
            #Cast debit and credit as sqlite doesn't compute it well.
            #See https://bugs.tryton.org/issue3733
            sql, params = Line.search(reconcile_domain, order=reconcile_order,
                query=True)

            sql = sql.replace('"a"."debit" <= ?',
                'cast("a"."debit" as float) <= cast(? as float)')
            sql = sql.replace('"a"."debit" != ?',
                'cast("a"."debit" as float) != cast(? as float)')
            sql = sql.replace('"a"."credit" <= ?',
                'cast("a"."credit" as float) <= cast(? as float)')
            sql = sql.replace('"a"."credit" != ?',
                'cast("a"."credit" as float) != cast(? as float)')
            cursor.execute(sql, params)
            return Line.browse([x['id'] for x in cursor.dictfetchall()])
        return Line.search(reconcile_domain, order=reconcile_order)

    def _get_lines_order(self):
        'Return the order on which the lines to reconcile will be returned'
        return [
            ('credit', 'DESC'),
            ('debit', 'DESC'),
            ]

    def _get_reconcile_domain(self, line):
        'Return the domain to search a line for reconciliation'
        zero = Decimal('0.0')
        domain = [
            ('id', '!=', line.id),
            ('reconciliation', '=', None),
            ('account', '=', line.account),
        ]
        if line.credit != zero:
            domain.append(('debit', '<=', line.credit))
            domain.append(('debit', '!=', 0))
        elif line.debit != zero:
            domain.append(('credit', '<=', line.debit))
            domain.append(('credit', '!=', 0))
        if line.party:
            domain.append(('party', '=', line.party))
        return domain

    def _get_reconcile_order(self, line):
        '''
        Return the order on which the possible reconciliation lines will be
        returned.
        '''
        order = []
        if line.credit != Decimal('0.0'):
            order.append(('debit', 'DESC'))
        elif line.debit != Decimal('0.0'):
            order.append(('credit', 'DESC'))
        order.append(('maturity_date', 'ASC'))
        return order
