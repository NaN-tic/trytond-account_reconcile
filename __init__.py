# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import account


def register():
    Pool.register(
        account.ReconcileMovesStart,
        account.ReconcileRule,
        module='account_reconcile', type_='model')
    Pool.register(
        account.ReconcileMoves,
        module='account_reconcile', type_='wizard')
