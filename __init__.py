# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .account import *


def register():
    Pool.register(
        ReconcileMovesStart,
        module='account_reconcile', type_='model')
    Pool.register(
        ReconcileMoves,
        module='account_reconcile', type_='wizard')
