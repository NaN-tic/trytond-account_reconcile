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
        trytond.tests.test_tryton.install_module('account')
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
                                }]),
                    ],
                },
            ]
        moves = self.move.create(vlist)
        self.move.post(moves)


    def test0030_numeric_search(self):
        'Test combined reconciliation'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([('rec_name', '=', 'B2CK')])
            self.create_complex_moves()
            to_reconcile, = self.line.search([
                        ('credit', '=', Decimal('75.0')),
                        ('reconciliation', '=', None),
                        ])
            for line in self.lines.search([
                        ('account', '=', to_reconcile.account),
                        ('credit', '<=', to_reconcile.credit),
                        ]):
                print line.debit
                self.assertTrue(line.credit <= to_reconcile.credit)

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
