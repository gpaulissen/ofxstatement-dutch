# -*- coding: utf-8 -*-
from typing import Iterable, Set, Optional, List, Iterator, Any

import csv
import sys
import datetime
import logging

from ofxstatement.plugin import Plugin as BasePlugin
from ofxstatement.parser import CsvStatementParser
from ofxstatement.exceptions import ParseError, ValidationError
from ofxstatement.statement import BankAccount

from ofxstatement.plugins.nl.statement import Statement, StatementLine

# Need Python 3 for super() syntax
assert sys.version_info[0] >= 3, "At least Python 3 is required."

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Parser(CsvStatementParser):
    """

    These are the first three lines of a KNAB CSV file:

    KNAB EXPORT;;;;;;;;;;;;;;;;
    Rekeningnummer;Transactiedatum;Valutacode;CreditDebet;Bedrag;\
Tegenrekeningnummer;Tegenrekeninghouder;Valutadatum;Betaalwijze;\
Omschrijving;Type betaling;Machtigingsnummer;Incassant ID;Adres;Referentie;\
Boekdatum;
    "NL99KNAB9999999999";"21-06-2019";"EUR";"D";"827,75";\
"FR9999999999999999999999999";"Gert Janssen (FR)";"21-06-2019";"Overboeking";\
"Tresorie";"";"";"";"";"XXXXXXXXXXXXXXXX";\
"21-06-2019";

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
        'date': 15,  # Boekdatum
        'memo': 9,  # Omschrijving
        'amount': 4,  # Bedrag
        'payee': 6,  # Tegenrekeninghouder
        'date_user': 1,  # Transactiedatum
        # check_no
        'refnum': 14,  # Referentie
        # trntype (determined later)
        'bank_account_to': 5,  # Tegenrekeningnummer
    }

    unique_id_set: Set[str]

    # Other mappings not used by parser.CsvStatementParser
    ACCOUNT = 0  # Rekeningnummer
    CD = 3  # CreditDebit

    def __init__(self, fin: Iterable[str]) -> None:
        # Python 3 needed
        super().__init__(fin)
        # Use the BIC code for KNAB Online, The Netherlands
        self.statement = Statement(bank_id="KNABNL2H",
                                   account_id=None,
                                   currency="EUR")  # My Statement
        self.unique_id_set = set()
        self.header = [['KNAB EXPORT'],
                       ['Rekeningnummer',
                        'Transactiedatum',
                        'Valutacode',
                        'CreditDebet',
                        'Bedrag',
                        'Tegenrekeningnummer',
                        'Tegenrekeninghouder',
                        'Valutadatum',
                        'Betaalwijze',
                        'Omschrijving',
                        'Type betaling',
                        'Machtigingsnummer',
                        'Incassant ID',
                        'Adres',
                        'Referentie',
                        'Boekdatum']]

    def parse(self) -> StatementLine:
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """

        # Python 3 needed
        stmt: StatementLine = super().parse()

        try:
            assert len(self.header) == 0,\
                "Header not completely read: {}".format(str(self.header))
        except Exception as e:
            raise ParseError(0, str(e))

        try:
            assert len(stmt.lines) > 0, "No statement lines read"

            # GJP 2020-03-03
            # No need to (re)calculate the balance since there is no history.
            # But set the dates.
            stmt.start_balance = stmt.end_balance = None
            stmt.start_date = min(sl.date for sl in stmt.lines)
            # end date is exclusive for OFX
            stmt.end_date = max(sl.date for sl in stmt.lines)
            stmt.end_date += datetime.timedelta(days=1)
        except Exception as e:
            raise ValidationError(str(e), stmt)

        return stmt

    def split_records(self) -> Iterator[Any]:
        """Return iterable object consisting of a line per transaction
        """
        return csv.reader(self.fin, delimiter=';')

    def parse_record(self, line: List[str]) -> Optional[StatementLine]:
        """Parse given transaction line and return StatementLine object
        """

        try:
            logger.debug('header count: %d; line #%d: %s',
                         len(self.header),
                         self.cur_record,
                         line)

            # First record(s) must be the header
            if len(self.header) >= 1:
                # Remove it since it need not be checked anymore
                hdr = self.header.pop(0)
                line = list(filter(None, line))
                logger.debug('header: %s', hdr)
                assert line == hdr,\
                    "Expected: {}\ngot: {}".format(hdr, line)
                return None

            # line[self.ACCOUNT] contains the account number
            if self.statement.account_id:
                assert self.statement.account_id == \
                    line[self.ACCOUNT],\
                    "Only one account is allowed; previous account: {}, \
this line's account: {}".format(self.statement.account_id,
                                line[self.ACCOUNT])
            else:
                self.statement.account_id = line[self.ACCOUNT]

            assert line[self.CD] in ['D', 'C'],\
                "Element {} is not D/C in line {}".format(self.CD, str(line))

            if line[self.CD] == 'D':
                line[self.mappings['amount']] =\
                    '-' + line[self.mappings['amount']]

            if line[self.mappings['bank_account_to']]:
                line[self.mappings['payee']] =\
                    "{} ({})".format(line[self.mappings['payee']],
                                     line[self.mappings['bank_account_to']])

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
        except Exception as e:
            raise ParseError(self.cur_record, str(e))

        return stmt_line


class Plugin(BasePlugin):
    """KNAB Online Bank, The Netherlands, CSV (https://www.knab.nl/)
    """
    def get_parser(self, f: str) -> Parser:
        fin = open(f, "r", encoding="ISO-8859-1") if isinstance(f, str) else f
        return Parser(fin)
