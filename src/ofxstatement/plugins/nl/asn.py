# -*- coding: utf-8 -*-
from typing import Iterable, Set, Optional, List, Iterator, Any, Dict

import re
import csv
import sys
import datetime
import logging

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

    These are the first two lines of an ING Netherlands CSV file:

    "Datum","Naam / Omschrijving","Rekening","Tegenrekening","Code",\
"Af Bij","Bedrag (EUR)","MutatieSoort",\
"Mededelingen"
    "20200213","Kosten OranjePakket met korting","NL42INGB0001085276","","DV",\
"Af","1,25","Diversen",\
"1 jan t/m 31 jan 2020 ING BANK N.V. Valutadatum: 13-02-2020"

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

    date_format: str

    # transactions / balance
    header: List[List[str]] = [["Datum",
                                "Naam / Omschrijving",
                                "Rekening",
                                "Tegenrekening",
                                "Code",
                                "Af Bij",
                                "Bedrag (EUR)",
                                "MutatieSoort",
                                "Mededelingen"],
                               ["Datum",
                                "Boeksaldo",
                                "Valutair saldo"]]
    # 0-based
    mappings_by_header: List[Dict[str, int]] = [{
        # id (determined later)
        'date': 0,
        'memo': 8,
        'amount': 6,
        'payee': 1,  # if bank_account_to is filled
        # date_user
        # check_no
        # refnum
        # trntype (determined later)
        'bank_account_to': 3,
    }, {
        'date': 0,
        'amount': 2  # valutair
    }]

    # variables
    unique_id_set: Set[str]
    header_idx: int
    mappings: Dict[str, int]

    def __init__(self,
                 fin: Iterable[str],
                 account_id: Optional[str] = None) -> None:
        # Python 3 needed
        super().__init__(fin)
        # Use the BIC code for ING Netherlands
        self.statement = Statement(bank_id="INGBNL2A",
                                   account_id=account_id,
                                   currency="EUR")  # My Statement
        self.unique_id_set = set()
        self.header_idx = -1

    def parse(self) -> Statement:
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """

        # Python 3 needed
        stmt: Statement = super().parse()

        try:
            assert self.header_idx >= 0 and self.header_idx < len(self.header),\
                "Header not read: {}".format(str(self.header))
        except Exception as e:
            raise ParseError(0, str(e))

        if self.header_idx == 0:
            # GJP 2020-03-03
            # No need to (re)calculate the balance since there is no history.
            # But set the dates.
            stmt.start_balance = stmt.end_balance = None
            stmt.start_date = min(sl.date for sl in stmt.lines)
            # end date is exclusive for OFX
            stmt.end_date = max(sl.date for sl in stmt.lines)
            stmt.end_date += datetime.timedelta(days=1)
        elif self.header_idx == 1:
            stmt.start_date = stmt.start_balance = None

            stmt.end_date = max(sl.date for sl in stmt.lines)
            assert stmt.lines[0].date == stmt.end_date or \
                stmt.lines[-1].date == stmt.end_date
            end_idx: int = 0 if stmt.lines[0].date == stmt.end_date else -1
            stmt.end_balance = stmt.lines[end_idx].amount
            # end date is exclusive for OFX
            stmt.end_date += datetime.timedelta(days=1)

            # no transaction lines
            stmt.lines = []

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
            logger.debug('header idx: %d; line #%d: %s',
                         self.header_idx,
                         self.cur_record,
                         line)

            # First record(s) must be the header
            if self.header_idx < 0:
                if line == self.header[0]:
                    self.header_idx = 0
                    self.date_format = "%Y%m%d"
                elif line == self.header[1]:
                    self.header_idx = 1
                    self.date_format = "%Y-%m-%d"

                msg: str = "Line {} does not match\n\n{}\n\nnor\n\n{}\n"

                assert self.header_idx in [0, 1],\
                    msg.format(line, self.header[0], self.header[1])

                self.mappings = self.mappings_by_header[self.header_idx]
                return None

            if self.header_idx == 0:
                stmt_line = self.parse_transaction(line)
            elif self.header_idx == 1:
                stmt_line = self.parse_balance(line)

        except Exception as e:
            raise ParseError(self.cur_record, str(e))

        return stmt_line

    def parse_transaction(self,
                          line: List[Optional[str]]) -> Optional[StatementLine]:
        # line[2] contains the account number
        if self.statement.account_id:
            assert self.statement.account_id == line[2],\
                "Only one account is allowed; previous account: {}, \
this line's account: {}".format(self.statement.account_id, line[2])
        else:
            self.statement.account_id = line[2]

        assert line[5] in ['Af', 'Bij']

        if line[5] == 'Af':
            amount: Optional[str] = line[self.mappings['amount']]
            line[self.mappings['amount']] =\
                '-' + (amount if isinstance(amount, str) else '')

        if line[self.mappings['bank_account_to']]:
            line[self.mappings['payee']] =\
                "{} ({})".format(line[self.mappings['payee']],
                                 line[self.mappings['bank_account_to']])
        else:
            line[self.mappings['memo']] =\
                "{}, {}".format(line[self.mappings['payee']],
                                line[self.mappings['memo']])
            line[self.mappings['payee']] = None

        # Python 3 needed
        stmt_line: StatementLine = super().parse_record(line)

        # Remove zero-value notifications
        if stmt_line.amount == 0:
            return None

        # Determine some fields not in the self.mappings
        # A hack but needed to use the adjust method
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
        return stmt_line

    def parse_balance(self,
                      line: List[Optional[str]]) -> Optional[StatementLine]:
        # Python 3 needed
        stmt_line: StatementLine = super().parse_record(line)
        stmt_line.trntype = "DEBIT" if stmt_line.amount < 0 else "CREDIT"
        stmt_line.id = 1
        # Determine some fields not in the self.mappings
        # A hack but needed to use the adjust method
        stmt_line.__class__ = StatementLine
        stmt_line.adjust(self.unique_id_set)
        return stmt_line


class Plugin(BasePlugin):
    """ING Bank, The Netherlands, CSV (https://www.ing.nl/)
    """
    def get_parser(self, filename: str) -> Parser:
        p = re.compile('(NL\\d+INGB\\d+)')
        m = p.search(filename)
        account_id: Optional[str] = None
        if m:
            account_id = m.group(0)
        fin = open(filename, "r", encoding="ISO-8859-1")
        return Parser(fin, account_id)
