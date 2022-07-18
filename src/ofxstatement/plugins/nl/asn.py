# -*- coding: utf-8 -*-
from typing import Iterable, Set, Optional, List, Iterator, Any, Dict

import re
import csv
import sys
import datetime
import logging
from decimal import Decimal

from ofxstatement.plugin import Plugin as BasePlugin
from ofxstatement.parser import CsvStatementParser
from ofxstatement.exceptions import ParseError
from ofxstatement.statement import BankAccount

from ofxstatement.plugins.nl.statement import Statement, StatementLine

# Need Python 3 for super() syntax
assert sys.version_info[0] >= 3, "At least Python 3 is required."

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Parser(CsvStatementParser):
    """

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

    date_format: str = "%d-%m-%Y"

    # 0-based
    mappings: Dict[str, int] = {
        # id (determined later)
        'date': 0,
        'memo': 17,
        'start_balance': 8,
        'amount': 10,
        'payee': 3,  # if bank_account_to is filled
        # date_user
        # check_no
        # refnum
        # trntype (determined later)
        'bank_account_to': 2,
    }

    # variables
    unique_id_set: Set[str]

    def __init__(self,
                 fin: Iterable[str],
                 account_id: Optional[str] = None) -> None:
        # Python 3 needed
        super().__init__(fin)
        # Use the BIC code for ASN Bank
        self.statement = Statement(bank_id="ASNBNL21",
                                   account_id=account_id,
                                   currency="EUR")  # My Statement
        self.unique_id_set = set()

    def parse(self) -> Statement:
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """

        # Python 3 needed
        stmt: Statement = super().parse()

        # GJP 2020-03-03
        # No need to (re)calculate the balance since there is no history.
        # But set the dates.
        stmt.start_date = min(sl.date for sl in stmt.lines)
        # end date is exclusive for OFX
        stmt.end_date = max(sl.date for sl in stmt.lines)
        stmt.end_date += datetime.timedelta(days=1)

        stmt.start_balance = Decimal(stmt.lines[0].start_balance)
        stmt.end_balance = Decimal(stmt.lines[-1].start_balance) + stmt.lines[-1].amount

        return stmt

    def split_records(self) -> Iterator[Any]:
        """Return iterable object consisting of a line per transaction
        """
        return csv.reader(self.fin, delimiter=',')

    def parse_record(self,
                     line: List[Optional[str]]) -> Optional[StatementLine]:
        """Parse given transaction line and return StatementLine object
        """

        stmt_line: Optional[StatementLine] = None

        try:
            logger.debug('line #%d: %s',
                         self.cur_record,
                         line)

            stmt_line = self.parse_transaction(line)

        except Exception as e:
            raise ParseError(self.cur_record, str(e))

        return stmt_line

    def parse_transaction(self,
                          line: List[Optional[str]]) -> Optional[StatementLine]:
        # line[1] contains the account number
        if self.statement.account_id:
            assert self.statement.account_id == line[1],\
                "Only one account is allowed; previous account: {}, \
this line's account: {}".format(self.statement.account_id, line[1])
        else:
            self.statement.account_id = line[1]

        if line[self.mappings['bank_account_to']]:
            line[self.mappings['payee']] =\
                "{} ({})".format(line[self.mappings['payee']],
                                 line[self.mappings['bank_account_to']])
        else:
            line[self.mappings['payee']] = None

        # Python 3 needed
        stmt_line: StatementLine = super().parse_record(line)

        # Remove zero-value notifications
        if stmt_line.amount == 0:
            return None

        # Determine some fields not in the self.mappings
        # A hack but needed to use the adjust methods
        stmt_line.__class__ = StatementLine
        stmt_line.adjust(self.unique_id_set)

        if stmt_line.amount < 0:
            stmt_line.trntype = "DEBIT"
        else:
            stmt_line.trntype = "CREDIT"

        if stmt_line.bank_account_to:
            stmt_line.bank_account_to = \
                BankAccount(bank_id=None,
                            acct_id=stmt_line.bank_account_to)
        else:
            stmt_line.bank_account_to = None

        # strip quotes around memo
        if len(stmt_line.memo) >= 2 and stmt_line.memo[0] == "'" and stmt_line.memo[-1] == "'":
            stmt_line.memo = stmt_line.memo[1:-1]

        return stmt_line


class Plugin(BasePlugin):
    """ASN Bank, The Netherlands, CSV (https://www.asnbank.nl/)
    """
    def get_parser(self, filename: str) -> Parser:
        p = re.compile('transactie-historie_(NL\\d+ASNB\\d+)_\\d+\\.csv')
        m = p.search(filename)
        account_id: Optional[str] = None
        if m:
            account_id = m.group(1)
        fin = open(filename, "r")  # , encoding="ISO-8859-1")
        return Parser(fin, account_id)
