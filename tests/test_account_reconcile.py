# This file is part of the account_reconcile module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
import unittest
from trytond.pool import Pool
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.modules.company.tests import create_company, set_company
from trytond.modules.account.tests import create_chart, get_fiscalyear


class AccountReconcileTestCase(ModuleTestCase):
    'Test Account Reconcile module'
    module = 'account_reconcile'

    def create_fiscalyear_and_chart(self, company=None):
        'Test fiscalyear'
        pool = Pool()
        FiscalYear = pool.get('account.fiscalyear')
        if not company:
            company = create_company()
        with set_company(company):
            create_chart(company)
            fiscalyear = get_fiscalyear(company)
            fiscalyear.save()
            FiscalYear.create_period([fiscalyear])
            self.assertEqual(len(fiscalyear.periods), 12)
            return fiscalyear

    def get_journals(self):
        pool = Pool()
        Journal = pool.get('account.journal')
        return dict((j.code, j) for j in Journal.search([]))

    def get_accounts(self, company):
        pool = Pool()
        Account = pool.get('account.account')
        accounts = Account.search([
                ('kind', 'in',
                    ['receivable', 'payable', 'revenue', 'expense']),
                ('company', '=', company.id),
                ])
        accounts = {a.kind: a for a in accounts}
        cash, = Account.search([
                ('kind', '=', 'other'),
                ('name', '=', 'Main Cash'),
                ('company', '=', company.id),
                ])
        accounts['cash'] = cash
        tax, = Account.search([
                ('kind', '=', 'other'),
                ('name', '=', 'Main Tax'),
                ('company', '=', company.id),
                ])
        accounts['tax'] = tax
        return accounts

    def create_parties(self, company):
        pool = Pool()
        Party = pool.get('party.party')
        with set_company(company):
            return Party.create([{
                            'name': 'customer1',
                        }, {
                            'name': 'customer2',
                        }, {
                            'name': 'supplier1',
                        }, {
                            'name': 'supplier2',
                        }])

    def create_moves(self, company):
        'Create moves some moves for the test'
        pool = Pool()
        Move = pool.get('account.move')
        fiscalyear = self.create_fiscalyear_and_chart(company)
        period = fiscalyear.periods[0]
        journals = self.get_journals()
        journal_revenue = journals['REV']
        journal_expense = journals['EXP']
        journal_cash = journals['CASH']
        accounts = self.get_accounts(company)
        revenue = accounts['revenue']
        receivable = accounts['receivable']
        expense = accounts['expense']
        payable = accounts['payable']
        cash = accounts['cash']
        #Create some parties
        customer1, customer2, supplier1, supplier2 = self.create_parties(
            company)
        # Create some moves
        vlist = [
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_revenue.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': revenue.id,
                                'credit': Decimal(100),
                                }, {
                                'party': customer1.id,
                                'account': receivable.id,
                                'debit': Decimal(100),
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_revenue.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': revenue.id,
                                'credit': Decimal(200),
                                }, {
                                'party': customer2.id,
                                'account': receivable.id,
                                'debit': Decimal(200),
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(100),
                                }, {
                                'party': customer1.id,
                                'account': receivable.id,
                                'credit': Decimal(100),
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(100),
                                }, {
                                'party': customer2.id,
                                'account': receivable.id,
                                'credit': Decimal(100),
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(100),
                                }, {
                                'party': customer2.id,
                                'account': receivable.id,
                                'credit': Decimal(100),
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_expense.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': expense.id,
                                'debit': Decimal(30),
                                }, {
                                'party': supplier1.id,
                                'account': payable.id,
                                'credit': Decimal(30),
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'credit': Decimal(30),
                                }, {
                                'party': supplier1.id,
                                'account': payable.id,
                                'debit': Decimal(30),
                                }]),
                    ],
                },
            ]
        moves = Move.create(vlist)
        Move.post(moves)

    def create_complex_moves(self, company):
        pool = Pool()
        Move = pool.get('account.move')
        FiscalYear = pool.get('account.fiscalyear')
        fiscalyear, = FiscalYear.search([])
        period = fiscalyear.periods[0]
        journals = self.get_journals()
        journal_revenue = journals['REV']
        journal_cash = journals['CASH']
        accounts = self.get_accounts(company)
        revenue = accounts['revenue']
        receivable = accounts['receivable']
        cash = accounts['cash']
        #Create some parties
        party = self.create_parties(company)[0]
        # Create some moves
        vlist = [
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_revenue.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': revenue.id,
                                'credit': Decimal(100),
                                }, {
                                'account': receivable.id,
                                'debit': Decimal(100),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_revenue.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': revenue.id,
                                'credit': Decimal(200),
                                }, {
                                'account': receivable.id,
                                'debit': Decimal(200),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(50),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(50),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(75),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(75),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(30),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(30),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(50),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(50),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(45),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(45),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(50),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(50),
                                'party': party.id,
                                }]),
                    ],
                },
            ]
        moves = Move.create(vlist)
        Move.post(moves)

    @with_transaction()
    def test_basic_reconciliation(self):
        'Test basic reconciliation'
        pool = Pool()
        Line = pool.get('account.move.line')
        MoveReconcile = pool.get('account.move_reconcile', type='wizard')
        company = create_company()
        self.create_moves(company)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(to_reconcile), 7)
        #Reconcile with no dates should affect all periods.
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '2'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 4)
        self.assertEqual(len(to_reconcile), 3)
        #Reconcile with two moves affect all periods.
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '3'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 3)
        self.assertEqual(len(to_reconcile), 0)

    @with_transaction()
    def test_filtered_reconciliation(self):
        'Test filtered reconciliation'
        pool = Pool()
        FiscalYear = pool.get('account.fiscalyear')
        Line = pool.get('account.move.line')
        MoveReconcile = pool.get('account.move_reconcile', type='wizard')
        Account = pool.get('account.account')
        Party = pool.get('party.party')
        company = create_company()
        self.create_moves(company)
        fiscalyear, = FiscalYear.search([])
        last_period = fiscalyear.periods[-1]
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(to_reconcile), 7)
        #Reconcile last period should not change anything.
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '2'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = last_period.start_date
        move_reconcile.start.end_date = last_period.end_date
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 0)
        self.assertEqual(len(to_reconcile), 7)
        #Reconcile filtered by account.
        receivables = Account.search([
                ('kind', '=', 'receivable')
                ])
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '2'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = receivables
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 2)
        receivable, = receivables
        self.assertEqual(all([l.account == receivable for l in
                    Line.browse(data['res_id'])]), True)
        self.assertEqual(len(to_reconcile), 5)
        #Reconcile filtered by party.
        suppliers = Party.search([
                ('name', '=', 'supplier1'),
                ])
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '2'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = suppliers
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 2)
        supplier, = suppliers
        self.assertEqual(all([l.party == supplier for l in
                    Line.browse(data['res_id'])]), True)
        self.assertEqual(len(to_reconcile), 3)

    @with_transaction()
    def test_combined_reconciliation(self):
        'Test combined reconciliation'
        pool = Pool()
        Line = pool.get('account.move.line')
        MoveReconcile = pool.get('account.move_reconcile', type='wizard')
        company = create_company()
        self.create_fiscalyear_and_chart(company)
        self.create_complex_moves(company)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(to_reconcile), 8)
        #Reconcile with two moves should not reconcile anyting
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '2'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 0)
        self.assertEqual(len(to_reconcile), 8)
        #Reconcile with three moves should reconcile first move
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '3'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 3)
        self.assertEqual(len(to_reconcile), 5)
        #Reconcile with four moves should not reconcile anything
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '4'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 0)
        self.assertEqual(len(to_reconcile), 5)
        #Reconcile with five moves should reconcile second moves
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '5'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 5)
        self.assertEqual(len(to_reconcile), 0)

    @with_transaction()
    def test_full_reconciliation(self):
        'Test full reconciliation'
        pool = Pool()
        Line = pool.get('account.move.line')
        MoveReconcile = pool.get('account.move_reconcile', type='wizard')
        company = create_company()
        self.create_moves(company)
        self.create_complex_moves(company)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(to_reconcile), 15)
        #This should reconcile all moves
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '5'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 15)
        self.assertEqual(len(to_reconcile), 0)

    @with_transaction()
    def test_balanced_reconciliation(self):
        'Test balanced (3 moves each side) reconciliation'
        pool = Pool()
        Line = pool.get('account.move.line')
        Move = pool.get('account.move')
        MoveReconcile = pool.get('account.move_reconcile', type='wizard')
        company = create_company()
        fiscalyear = self.create_fiscalyear_and_chart(company)
        period = fiscalyear.periods[0]
        journals = self.get_journals()
        journal_revenue = journals['REV']
        journal_cash = journals['CASH']
        accounts = self.get_accounts(company)
        revenue = accounts['revenue']
        receivable = accounts['receivable']
        cash = accounts['cash']
        party = self.create_parties(company)[0]
        # Create some moves
        vlist = [
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_revenue.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': revenue.id,
                                'credit': Decimal(100),
                                }, {
                                'account': receivable.id,
                                'debit': Decimal(100),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_revenue.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': revenue.id,
                                'credit': Decimal(50),
                                }, {
                                'account': receivable.id,
                                'debit': Decimal(50),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_revenue.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': revenue.id,
                                'credit': Decimal(150),
                                }, {
                                'account': receivable.id,
                                'debit': Decimal(150),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(75),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(75),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(120),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(120),
                                'party': party.id,
                                }]),
                    ],
                },
            {
                'company': company.id,
                'period': period.id,
                'journal': journal_cash.id,
                'date': period.start_date,
                'lines': [
                    ('create', [{
                                'account': cash.id,
                                'debit': Decimal(105),
                                }, {
                                'account': receivable.id,
                                'credit': Decimal(105),
                                'party': party.id,
                                }]),
                    ],
                },
            ]
        moves = Move.create(vlist)
        Move.post(moves)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(to_reconcile), 6)
        #This should reconcile all moves
        session_id, _, _ = MoveReconcile.create()
        move_reconcile = MoveReconcile(session_id)
        move_reconcile.start.company = company
        move_reconcile.start.max_lines = '6'
        move_reconcile.start.max_months = 12
        move_reconcile.start.start_date = None
        move_reconcile.start.end_date = None
        move_reconcile.start.accounts = []
        move_reconcile.start.parties = []
        _, data = move_reconcile.do_reconcile(None)
        to_reconcile = Line.search([
                    ('account.reconcile', '=', True),
                    ('reconciliation', '=', None),
                    ])
        self.assertEqual(len(data['res_id']), 6)
        self.assertEqual(len(to_reconcile), 0)
        reconciliations = set([l.reconciliation for l in Line.browse(
                data['res_id'])])
        #All moves should be on the same reconciliation
        self.assertEqual(len(reconciliations), 1)


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountReconcileTestCase))
    return suite
