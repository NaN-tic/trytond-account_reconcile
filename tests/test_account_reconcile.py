#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import sys
import os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import trytond.tests.test_tryton
from decimal import Decimal
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class AccountReconcileTestCase(unittest.TestCase):
    'Test AccountReconcile module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('account_reconcile')
        self.account = POOL.get('account.account')
        self.company = POOL.get('company.company')
        self.user = POOL.get('res.user')
        self.party = POOL.get('party.party')
        self.party_address = POOL.get('party.address')
        self.fiscalyear = POOL.get('account.fiscalyear')
        self.move = POOL.get('account.move')
        self.line = POOL.get('account.move.line')
        self.journal = POOL.get('account.journal')
        self.period = POOL.get('account.period')
        self.move_reconcile = POOL.get('account.move_reconcile',
            type='wizard')

    def test0005views(self):
        'Test views'
        test_view('account_reconcile')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def create_moves(self):
        'Create moves some moves for the test'
        fiscalyear, = self.fiscalyear.search([])
        period = fiscalyear.periods[0]
        journal_revenue, = self.journal.search([
                ('code', '=', 'REV'),
                ])
        journal_expense, = self.journal.search([
                ('code', '=', 'EXP'),
                ])
        journal_cash, = self.journal.search([
                ('code', '=', 'CASH'),
                ])
        revenue, = self.account.search([
                ('kind', '=', 'revenue'),
                ])
        receivable, = self.account.search([
                ('kind', '=', 'receivable'),
                ])
        expense, = self.account.search([
                ('kind', '=', 'expense'),
                ])
        payable, = self.account.search([
                ('kind', '=', 'payable'),
                ])
        cash, = self.account.search([
                ('name', '=', 'Main Cash'),
                ])
        chart, = self.account.search([
                ('parent', '=', None),
                ])
        self.account.create([{
                    'name': 'View',
                    'code': '1',
                    'kind': 'view',
                    'parent': chart.id,
                    }])
        #Create some parties
        customer1, customer2, supplier1, supplier2 = self.party.create([{
                        'name': 'customer1',
                    }, {
                        'name': 'customer2',
                    }, {
                        'name': 'supplier1',
                    }, {
                        'name': 'supplier2',
                    }])
        # Create some moves
        vlist = [
            {
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
        moves = self.move.create(vlist)
        self.move.post(moves)

    def create_complex_moves(self):
        fiscalyear, = self.fiscalyear.search([])
        period = fiscalyear.periods[0]
        journal_revenue, = self.journal.search([
                ('code', '=', 'REV'),
                ])
        journal_cash, = self.journal.search([
                ('code', '=', 'CASH'),
                ])
        revenue, = self.account.search([
                ('kind', '=', 'revenue'),
                ])
        receivable, = self.account.search([
                ('kind', '=', 'receivable'),
                ])
        cash, = self.account.search([
                ('name', '=', 'Main Cash'),
                ])
        #Create some parties
        party, = self.party.create([{
                        'name': 'Party',
                    }])
        # Create some moves
        vlist = [
            {
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
        moves = self.move.create(vlist)
        self.move.post(moves)

    def test0010_basic_reconciliation(self):
        'Test basic reconciliation'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_moves()
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin')])
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(to_reconcile), 7)
            #Reconcile with no dates should affect all periods.
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '2'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 4)
            self.assertEqual(len(to_reconcile), 3)
            #Reconcile with two moves affect all periods.
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '3'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 3)
            self.assertEqual(len(to_reconcile), 0)

    def test0020_filtered_reconciliation(self):
        'Test filtered reconciliation'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_moves()
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin')])
            fiscalyear, = self.fiscalyear.search([])
            last_period = fiscalyear.periods[-1]
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(to_reconcile), 7)
            #Reconcile last period should not change anything.
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '2'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = last_period.start_date
            move_reconcile.start.end_date = last_period.end_date
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 0)
            self.assertEqual(len(to_reconcile), 7)
            #Reconcile filtered by account.
            receivables = self.account.search([
                    ('kind', '=', 'receivable')
                    ])
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '2'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = receivables
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 2)
            receivable, = receivables
            self.assertEqual(all([l.account == receivable for l in
                        self.line.browse(data['res_id'])]), True)
            self.assertEqual(len(to_reconcile), 5)
            #Reconcile filtered by party.
            suppliers = self.party.search([
                    ('name', '=', 'supplier1'),
                    ])
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '2'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = suppliers
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 2)
            supplier, = suppliers
            self.assertEqual(all([l.party == supplier for l in
                        self.line.browse(data['res_id'])]), True)
            self.assertEqual(len(to_reconcile), 3)

    def test0030_combined_reconciliation(self):
        'Test combined reconciliation'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin')])
            self.create_complex_moves()
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(to_reconcile), 8)
            #Reconcile with two moves should not reconcile anyting
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '2'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 0)
            self.assertEqual(len(to_reconcile), 8)
            #Reconcile with three moves should reconcile first move
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '3'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 3)
            self.assertEqual(len(to_reconcile), 5)
            #Reconcile with four moves should not reconcile anything
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '4'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 0)
            self.assertEqual(len(to_reconcile), 5)
            #Reconcile with five moves should reconcile second moves
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '5'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 5)
            self.assertEqual(len(to_reconcile), 0)

    def test0040_full_reconciliation(self):
        'Test full reconciliation'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin')])
            self.create_moves()
            self.create_complex_moves()
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(to_reconcile), 15)
            #This should reconcile all moves
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '5'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 15)
            self.assertEqual(len(to_reconcile), 0)

    def test0050_balanced_reconciliation(self):
        'Test balanced (3 moves each side) reconciliation'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            fiscalyear, = self.fiscalyear.search([])
            period = fiscalyear.periods[0]
            journal_revenue, = self.journal.search([
                    ('code', '=', 'REV'),
                    ])
            journal_cash, = self.journal.search([
                    ('code', '=', 'CASH'),
                    ])
            revenue, = self.account.search([
                    ('kind', '=', 'revenue'),
                    ])
            receivable, = self.account.search([
                    ('kind', '=', 'receivable'),
                    ])
            cash, = self.account.search([
                    ('name', '=', 'Main Cash'),
                    ])
            #Create some parties
            party, = self.party.create([{
                            'name': 'Party',
                        }])
            # Create some moves
            vlist = [
                {
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
            moves = self.move.create(vlist)
            self.move.post(moves)
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin')])
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(to_reconcile), 6)
            #This should reconcile all moves
            session_id, _, _ = self.move_reconcile.create()
            move_reconcile = self.move_reconcile(session_id)
            move_reconcile.start.company = company
            move_reconcile.start.max_lines = '6'
            move_reconcile.start.max_months = 12
            move_reconcile.start.start_date = None
            move_reconcile.start.end_date = None
            move_reconcile.start.accounts = []
            move_reconcile.start.parties = []
            _, data = move_reconcile.do_reconcile(None)
            to_reconcile = self.line.search([
                        ('account.reconcile', '=', True),
                        ('reconciliation', '=', None),
                        ])
            self.assertEqual(len(data['res_id']), 6)
            self.assertEqual(len(to_reconcile), 0)
            reconciliations = set([l.reconciliation for l in self.line.browse(
                    data['res_id'])])
            #All moves should be on the same reconciliation
            self.assertEqual(len(reconciliations), 1)


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.account.tests import test_account
    for test in test_account.suite():
        #Skip doctest
        class_name = test.__class__.__name__
        if test not in suite and class_name != 'DocFileCase':
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            AccountReconcileTestCase))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
