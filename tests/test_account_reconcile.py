# This file is part of the account_reconcile module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class AccountReconcileTestCase(ModuleTestCase):
    'Test Account Reconcile module'
    module = 'account_reconcile'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        AccountReconcileTestCase))
    return suite