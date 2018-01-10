# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.account_reconcile.tests.test_account_reconcile import suite
except ImportError:
    from .test_account_reconcile import suite

__all__ = ['suite']
