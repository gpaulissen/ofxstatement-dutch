# -*- coding: utf-8 -*-
import csv
import sys
import re
import datetime
import logging

from ofxstatement import plugin, parser
from ofxstatement.statement import generate_unique_transaction_id

# Need Python 3 for super() syntax
assert sys.version_info[0] >= 3, "At least Python 3 is required."

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Plugin(plugin.Plugin):
    """deGiro platform, The Netherlands, CSV (https://www.degiro.nl/)
    """
    def get_parser(self, f):
        fin = open(f, "r", encoding="ISO-8859-1") if isinstance(f, str) else f
        return Parser(fin, self.settings['account_id'])


class Parser(parser.CsvStatementParser):
    """

    These are the first two lines of a DEGIRO CSV file:

    Datum,Tijd,Valutadatum,Product,ISIN,Omschrijving,FX,Mutatie,,Saldo,,\
Order Id
    30-12-2019,15:58,30-12-2019,MORGAN STANLEY EUR LIQUIDITY FUND,\
LU1959429272,"Conversie geldmarktfonds: Koop 0,000016 @ 9.961,4715 EUR",,,,\
EUR,"13,87",


    These fields are from the Statement class:

    id = ""

    # Date transaction was posted to account (booking date)
    date = datetime.now()

    memo = ""

    # Amount of transaction
    amount = D(0)

    # additional fields
    payee = ""

    # Date user initiated transaction, if known (transaction date)
    date_user = datetime.now()

    # Check (or other reference) number
    check_no = ""

    # Reference number that uniquely identifies the transaction. Can be used in
    # addition to or instead of a check_no
    refnum = ""

    # Transaction type, must be one of TRANSACTION_TYPES
    "CREDIT",       # Generic credit
    "DEBIT",        # Generic debit
    "INT",          # Interest earned or paid
    "DIV",          # Dividend
    "FEE",          # FI fee
    "SRVCHG",       # Service charge
    "DEP",          # Deposit
    "ATM",          # ATM debit or credit
    "POS",          # Point of sale debit or credit
    "XFER",         # Transfer
    "CHECK",        # Check
    "PAYMENT",      # Electronic payment
    "CASH",         # Cash withdrawal
    "DIRECTDEP",    # Direct deposit
    "DIRECTDEBIT",  # Merchant initiated debit
    "REPEATPMT",    # Repeating payment/standing order
    "OTHER"         # Other

    trntype = "CHECK"

    # Optional BankAccount instance
    bank_account_to = None

    """

    date_format = "%d-%m-%Y"

    # 0-based
    mappings = {
        # id (determined later)
        'date': 0,
        'memo': 5,
        'amount': 8,  # Without a header
        # payee
        # date_user
        # check_no
        # refnum
        # trntype (determined later)
        # bank_account_to
    }

    def __init__(self, fin, account_id):
        # Python 3 needed
        super().__init__(fin)
        # Use the BIC code for ING Netherlands
        self.statement.bank_id = "STDGNL21"
        self.statement.currency = "EUR"
        self.unique_id_set = set()
        self.account_id = account_id

    def parse(self):
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """

        # Python 3 needed
        stmt = super().parse()

        stmt.account_id = self.account_id
        stmt.account_type = "MONEYMRKT"

        # GJP 2020-03-03
        # No need to (re)calculate the balance since there is no history.
        # But set the dates.
        stmt.start_balance = stmt.end_balance = None
        stmt.start_date = min(sl.date for sl in stmt.lines)
        # end date is exclusive for OFX
        stmt.end_date = max(sl.date for sl in stmt.lines)
        stmt.end_date += datetime.timedelta(days=1)

        logger.debug('stmt: %r', stmt)

        return stmt

    def split_records(self):
        """Return iterable object consisting of a line per transaction
        """
        return csv.reader(self.fin, delimiter=',')

    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object
        """

        logger.debug('line: %r', str(line))

        # Skip header
        if line == ["Datum", "Tijd", "Valutadatum", "Product", "ISIN",
                    "Omschrijving", "FX", "Mutatie", "", "Saldo", "",
                    "Order Id"]:
            return None

        # Python 3 needed
        stmt_line = super().parse_record(line)

        # Remove zero-value notifications
        if stmt_line.amount is None or stmt_line.amount == 0:
            return None

        # Forget conversions
        if line[self.mappings['amount'] - 1] != 'EUR':
            return None

        # Determine some fields not in the self.mappings

        stmt_line.id = \
            generate_unique_transaction_id(stmt_line, self.unique_id_set)
        m = re.search(r'-(\d+)$', stmt_line.id)
        if m:
            counter = int(m.group(1))
            # include counter so the memo gets unique
            stmt_line.memo = stmt_line.memo + ' #' + str(counter + 1)

        if stmt_line.memo in ['Dividend', 'Dividendbelasting']:
            stmt_line.trntype = "DIV"
        elif stmt_line.memo == 'Rente':
            stmt_line.trntype = "INT"
        elif stmt_line.memo == 'DEGIRO transactiekosten':
            stmt_line.trntype = "FEE"
        elif stmt_line.memo[0:25] == 'DEGIRO Aansluitingskosten':
            stmt_line.trntype = "SRVCHG"
        elif stmt_line.memo == 'Terugstorting':
            stmt_line.trntype = "XFER"
        elif stmt_line.memo in ['Storting', 'iDEAL storting']:
            stmt_line.trntype = "DEP"
        elif stmt_line.amount < 0:
            stmt_line.trntype = "DEBIT"
        else:
            stmt_line.trntype = "CREDIT"

        # Product known?
        if line[self.mappings['memo'] - 2]:
            stmt_line.memo += ' ' + line[self.mappings['memo'] - 2]
            # ISIN known?
            if line[self.mappings['memo'] - 1]:
                stmt_line.memo +=\
                    ' (' + line[self.mappings['memo'] - 1] + ')'

        return stmt_line if stmt_line.trntype in ["XFER", "DEP"] else None

    def parse_decimal(self, value):
        logger.debug('value: %s', value)
        return super().parse_decimal(value) if value else None
