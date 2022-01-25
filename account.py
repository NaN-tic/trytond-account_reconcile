# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from itertools import combinations
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging
import re

from trytond.model import ModelSQL, ModelView, fields
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.transaction import Transaction
from trytond.pyson import Bool, Eval
from trytond.pool import Pool

__all__ = ['ReconcileMovesStart', 'ReconcileMoves']
logger = logging.getLogger(__name__)


class ReconcileMovesStart(ModelView):
    'Reconcile Moves'
    __name__ = 'account.move_reconcile.start'

    company = fields.Many2One('company.company', 'Company', required=True,
        readonly=True)
    accounts = fields.Many2Many('account.account', None, None, 'Accounts',
        domain=[
            ('company', '=', Eval('company')),
            ('reconcile', '=', True),
            ('type', '!=', None),
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
            help=('Maximum number of lines to include on a reconciliation'),
            states={'invisible': ~Bool(Eval('use_combinations'))},
            depends=['use_combinations'])
    max_days = fields.Integer('Maximum days', required=True,
        help='Maximum difference in months of lines to reconcile.')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    timeout = fields.TimeDelta('Maximum Computation Time', required=True)
    use_combinations = fields.Boolean("Use Combinations")
    use_rules = fields.Boolean("Use Rules")

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_max_lines():
        return '2'

    @staticmethod
    def default_max_days():
        return 6

    @staticmethod
    def default_timeout():
        return timedelta(minutes=5)

    @staticmethod
    def default_use_combinations():
        return True


class ReconcileRule(ModelSQL, ModelView):
    'Reconcile Rule'
    __name__ = 'account.move_reconcile.rule'
    company = fields.Many2One('company.company', 'Company', required=True)
    account = fields.Many2One('account.account', 'Account', required=True,
        domain=[('company', '=', Eval('company', -1))], depends=['company'])
    expression = fields.Char('Regular Expression',
        help='Example: Invoice nº((\\d|\\s)+)')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class ReconcileMoves(Wizard):
    'Reconcile Moves'
    __name__ = 'account.move_reconcile'
    start = StateView('account.move_reconcile.start',
        'account_reconcile.reconcile_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Ok', 'reconcile', 'tryton-ok', default=True),
            ])
    reconcile = StateAction('account.act_move_line_form')

    def reconciliation(self, start_date, end_date, timeout):
        pool = Pool()
        Line = pool.get('account.move.line')
        ReconcileRule = pool.get('account.move_reconcile.rule')
        cursor = Transaction().connection.cursor()
        table = Line.__table__()

        domain = [
            ('account.company', '=', self.start.company.id),
            ('account.reconcile', '=', True),
            ('reconciliation', '=', None),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ]

        if self.start.accounts:
            domain.append(('account', 'in', self.start.accounts))
        if self.start.parties:
            domain.append(('party', 'in', self.start.parties))

        max_lines = int(self.start.max_lines)
        reconciled = set()

        # Get grouped by account and party in order to not fetch all the moves
        # in memory and only fetch the ones that can be reconciled.
        query = Line.search(domain, query=True)
        cursor.execute(*table.select(table.account, table.party,
                where=(table.id.in_(query)),
                group_by=(table.account, table.party)))

        #currency = self.start.company.currency
        for account, party in cursor.fetchall():
            simple_domain = domain + [
                ('account', '=', account),
                ('party', '=', party),
                ]
            order = self._get_lines_order()
            lines = Line.search(simple_domain, order=order)
            if self.start.use_rules:
                user_company = Transaction().context.get('company')
                rules = ReconcileRule.search([
                    ('account', '=', account),
                    ('company', '=', user_company)
                    ])
                regexes = [re.compile(x.expression) for x in rules]
                if regexes:
                    numbers = {}
                    for line in lines:
                        if line.description:
                            for regex in regexes:
                                match = regex.search(line.description)
                                if match:
                                    id = match.group().replace(' ', '')
                                    numbers.setdefault(id, [])
                                    numbers[id].append(line)
                                    break
                    for lines in numbers.values():
                        if len(lines) > 1:
                            amount = sum([x.debit - x.credit for x in lines])
                            if amount == 0:
                                Line.reconcile(lines)
                                for line in lines:
                                    reconciled.add(line.id)
            if self.start.use_combinations:
                lines = Line.search(simple_domain, order=order)
                lines = [(x.id, x.debit - x.credit) for x in lines]
                count = 0
                for size in range(2, max_lines + 1):
                    if datetime.now() > timeout:
                        logger.info('Timeout reached.')
                        return list(reconciled)
                    logger.info(
                        'Reconciling %d in %d batches' % (len(lines), size))
                    for to_reconcile in combinations(lines, size):
                        count += 1
                        if count % 10000000 == 0:
                            logger.info(
                                '%d combinations processed with %d lines '
                                'reconciled' % (count, len(reconciled)))
                            if datetime.now() > timeout:
                                logger.info('Timeout reached.')
                                return list(reconciled)
                        pending_amount = sum([x[1] for x in to_reconcile])
                        if pending_amount == 0:
                            ids = [x[0] for x in to_reconcile]
                            if set(ids) & reconciled:
                                continue
                            Line.reconcile(Line.browse(ids))
                            for line in to_reconcile:
                                reconciled.add(line[0])
                                lines.remove(line)
        return list(reconciled)

    def do_reconcile(self, action):
        pool = Pool()
        Line = pool.get('account.move.line')

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
        logger.info('Starting moves reconciliation')
        timeout = datetime.now() + self.start.timeout
        while start <= end_date and start_date and end_date:
            end = start + relativedelta(days=self.start.max_days)
            if end > end_date:
                end = end_date
            logger.info('Reconciling lines between %s and %s', start,
                end)
            result = self.reconciliation(start, end, timeout)
            reconciled += result
            logger.info('Reconciled %d lines', len(result))
            if datetime.now() > timeout:
                break
            start += relativedelta(days=max(1, self.start.max_days // 2))
        logger.info('Finished. Reconciled %d lines', len(reconciled))
        data = {'res_id': reconciled}
        return action, data

    def _get_lines_order(self):
        'Return the order on which the lines to reconcile will be returned'
        return [
            ('date', 'ASC')
            ]
