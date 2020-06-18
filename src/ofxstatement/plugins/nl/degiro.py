# -*- coding: utf-8 -*-
from typing import Iterable, Set, Optional, List, Any
import csv
import sys
import datetime
import logging
from decimal import Decimal

from ofxstatement.plugin import Plugin as BasePlugin
from ofxstatement.parser import CsvStatementParser
from ofxstatement.exceptions import ParseError
from ofxstatement.plugins.nl.statement import Statement, StatementLine

# Need Python 3 for super() syntax
assert sys.version_info[0] >= 3, "At least Python 3 is required."

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Parser(CsvStatementParser):
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

    unique_id_set: Set[str]

    def __init__(self, fin: Iterable[str], account_id: str) -> None:
        # Python 3 needed
        super().__init__(fin)
        # Use the BIC code for ING Netherlands
        self.statement = Statement(bank_id="STDGNL21",
                                   account_id=account_id,
                                   currency="EUR",
                                   # Not yet, just a CHECKING account
                                   # self.statement.account_type = "MONEYMRKT"
                                   account_type="CHECKING")  # My Statement
        self.unique_id_set = set()
        self.header = [["Datum",
                        "Tijd",
                        "Valutadatum",
                        "Product",
                        "ISIN",
                        "Omschrijving",
                        "FX",
                        "Mutatie",
                        "",
                        "Saldo",
                        "",
                        "Order Id"]]

    def parse(self) -> Statement:
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """

        # Python 3 needed
        stmt: Statement = super().parse()

        try:
            assert len(self.header) == 0,\
                "Header not completely read: {}".format(str(self.header))
        except Exception as e:
            raise ParseError(0, str(e))

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

    def split_records(self) -> Iterable[Any]:
        """Return iterable object consisting of a line per transaction
        """
        return csv.reader(self.fin, delimiter=',')

    def parse_record(self, line: List[str]) -> Optional[StatementLine]:
        """Parse given transaction line and return StatementLine object
        """

        logger.debug('header count: %d; line #%d: %s',
                     len(self.header),
                     self.cur_record,
                     line)

        # First record(s) must be the header
        if len(self.header) >= 1:
            # Remove it since it need not be checked anymore
            hdr = self.header.pop(0)
            logger.debug('header: %s', hdr)
            assert line == hdr,\
                "Expected: {}\ngot: {}".format(hdr, line)
            return None

        # Python 3 needed
        stmt_line: StatementLine = super().parse_record(line)

        # Remove zero-value notifications
        if stmt_line.amount is None or stmt_line.amount == 0:
            return None

        # Forget conversions
        if line[self.mappings['amount'] - 1] != 'EUR':
            return None

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
        elif stmt_line.amount < 0:  # pragma: no cover
            stmt_line.trntype = "DEBIT"
        else:
            stmt_line.trntype = "CREDIT"

        if stmt_line.trntype not in ["XFER", "DEP"]:
            return None

        # Determine some fields not in the self.mappings
        # A hack but needed to use the adjust method
        stmt_line.__class__ = StatementLine
        stmt_line.adjust(self.unique_id_set)

        # Product known?
        if line[self.mappings['memo'] - 2]:  # pragma: no cover
            stmt_line.memo += ' ' + line[self.mappings['memo'] - 2]
            # ISIN known?
            if line[self.mappings['memo'] - 1]:
                stmt_line.memo +=\
                    ' (' + line[self.mappings['memo'] - 1] + ')'

        return stmt_line

    def parse_decimal(self, value: Optional[str]) -> Optional[Decimal]:
        logger.debug('value: %s', value)
        return super().parse_decimal(value) if value else None


class Plugin(BasePlugin):
    """DEGIRO trader platform, The Netherlands, CSV (https://www.degiro.nl/)
    """
    def get_parser(self, f: str) -> Parser:
        fin = open(f, "r", encoding="ISO-8859-1") if isinstance(f, str) else f
        try:
            account_id = self.settings['account_id']
        except Exception:
            raise RuntimeError("""
Please define an 'account_id' in the ofxstatement configuration.

Run

$ ofxstatement edit-config

for more information.
""")
        return Parser(fin, account_id)
