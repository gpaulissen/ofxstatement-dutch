# -*- coding: utf-8 -*-
from typing import Iterable, Set, Optional, List, Iterator, Any, Union

import sys
import locale
import re
import io
from decimal import Decimal
from datetime import datetime
from subprocess import check_output, CalledProcessError
import logging

from ofxstatement.plugin import Plugin as BasePlugin
from ofxstatement.parser import StatementParser as BaseStatementParser

from ofxstatement.plugins.nl.statement import Statement, StatementLine

# Need Python 3 for super() syntax
assert sys.version_info[0] >= 3, "At least Python 3 is required."

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Parser(BaseStatementParser):  # type: ignore
    unique_id_set: Set[str]

    def __init__(self, fin: Iterable[str]) -> None:
        super().__init__()
        self.statement = Statement(bank_id=None,
                                   account_id=None,
                                   currency='EUR')  # My Statement
        self.fin = fin
        self.unique_id_set = set()

    def parse(self) -> Statement:
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """
        logger.debug("self before: type: %s; contents: %s", type(self), self)
        stmt: Optional[Statement] = None
        # Save locale
        current_locale = locale.setlocale(category=locale.LC_ALL)
        # Need to parse "05 mei" i.e. "05 may"
        locale.setlocale(category=locale.LC_ALL, locale="nl_NL")
        try:
            logger.debug("self.statement (1): type: %s; contents: %s", type(self.statement), self.statement)

            # Python 3 needed
            stmt = super().parse()

            logger.debug("stmt (2): type: %s; contents: %s", type(stmt), stmt)
            logger.debug("self.statement (2): type: %s; contents: %s", type(self.statement), self.statement)

            if stmt and stmt.lines:
                self.statement.start_date = min(sl.date for sl in stmt.lines if sl.date)
            logger.debug("self.statement (3): type: %s; contents: %s", type(self.statement), self.statement)
            stmt.assert_valid()
        finally:
            locale.setlocale(category=locale.LC_ALL, locale=current_locale)

        return stmt

    @staticmethod
    def get_amount(amount_in: str, transaction_type_in: str) -> Decimal:
        sign_out: int = 1
        amount_out: Union[str, Decimal]

        # determine sign_out
        assert isinstance(transaction_type_in, str)
        assert transaction_type_in in ['Af', 'Bij']

        if transaction_type_in == 'Af':
            sign_out = -1

        # determine amount_out
        assert isinstance(amount_in, str)
        # Amount something like 1.827,97, € 1.827,97 (both dutch) or 1,827.97?
        # Since April 2025 it may be €1.827,97 as well
        m = re.search(r'^(\S+\s|\D)?([0-9,.]+)$', amount_in)
        assert m is not None
        amount_out = m.group(2)
        if amount_out[-3] == ',':
            amount_out = amount_out.replace('.', '').replace(',', '.')

        # convert to str to keep just the last two decimals
        amount_out = sign_out * Decimal(str(amount_out))
        logger.debug("get_amount(%s, %s) = %s", amount_in, transaction_type_in, amount_out)
        return amount_out

    def split_records(self) -> Iterator[Any]:
        """Return iterable object consisting of a line per transaction
        """
        def convert_str_to_list(str: str,
                                max_items: Optional[int] = None,
                                sep: str = r'\s\s+|\t|\n') -> List[str]:
            return [x for x in re.split(sep, str)[0:max_items]]

        first_line = True
        first_line_row = ['International Card Services BV', 'www.icscards.nl']

        new_page = False
        new_page_row = ['Datum', 'ICS-klantnummer', 'Volgnummer', 'Bladnummer']

        balance = False
        balance_row = ['Vorig openstaand saldo', 'Totaal ontvangen betalingen',
                       'Totaal nieuwe uitgaven', 'Nieuw openstaand saldo']

        # 01 sep          01 sep            IDEAL BETALING, DANK U                                                                                                          1.311,73       Bij
        # 21 feb         22 feb            APPLE.COM/BILL                                  ITUNES.COM                       IE                                                  0,99   Af
        # Since April 2025 (period after month):
        # 21 mrt.        22 mrt.           APPLE.COM/BILL                                  ITUNES.COM                       IE                                                  0,99   Af
        statement_expr = \
            re.compile(r'^\d\d [a-z]{3}\.?\s+\d\d [a-z]{3}\.?.+[0-9,.]+\s+(Af|Bij)$')
        country = re.compile("^[A-Z][A-Z]$")

        for line in self.fin:
            line = line.strip()

            logger.debug('line: %s', line)

            # to ease the parsing pain
            row: List[str] = convert_str_to_list(line)

            logger.debug('row: %s', row)
            logger.debug("before parsing line: self.statement: %s; first_line: %s; new_page: %s; balance: %s",
                         self.statement,
                         first_line,
                         new_page,
                         balance)

            if first_line and len(row) > 1:
                assert row == first_line_row, \
                    "Expected: {0}\nActual: {1}".format(first_line_row, row)
                first_line = False

            if len(row) == 2 and row[1][0:5] == 'BIC: ':
                self.statement.bank_id = row[1][5:]

            elif row == new_page_row:
                new_page = True
            elif new_page:
                new_page = False
                # exclusive in ICSCards
                self.statement.end_date = \
                    datetime.strptime(row[0],
                                      '%d %B %Y')
                self.statement.account_id = row[1]

            elif row == balance_row:
                balance = True
            elif balance:
                balance = False
                self.statement.start_balance = Parser.get_amount(row[0],
                                                                 row[1])
                self.statement.end_balance = Parser.get_amount(row[-2],
                                                               row[-1])

            elif re.search(statement_expr, line):
                # payee, place and country may be something like:
                #
                # THY|2357312380512|Istanbul|US
                #
                # hence four columns instead of three, so combine the first two
                for i in reversed(range(len(row))):
                    if country.match(row[i]):
                        # Should have 4 columns to the left. If not: reduce.
                        while i > 4:
                            row[2] += ' ' + row[3]
                            del row[3]
                            i -= 1
                        break

                if len(row) >= 6 and len(row) <= 7 and len(row[2]) > 25:
                    # 04 sep | 05 sep | NEWREST WAGONS LITS FRANCPARIS ...
                    # =>
                    # 04 sep | 05 sep | NEWREST WAGONS LITS FRANC ...

                    row.insert(2, row[2][0:25])
                    row[3] = row[3][25:]
                logger.debug('yield row: %s', row)
                yield row
            logger.debug("after parsing line : self.statement: %s; first_line: %s; new_page: %s; balance: %s",
                         self.statement,
                         first_line,
                         new_page,
                         balance)

    def parse_record(self, row: List[str]) -> Optional[StatementLine]:
        """Parse given transaction line and return StatementLine object
        """

        def add_years(dt: datetime, years: int) -> datetime:
            """Return a date that's `years` years after the date (or datetime)
            object `d`. Return the same calendar date (month and day) in the
            destination year, if it exists, otherwise use the following day
            (thus changing February 29 to March 1).

            """
            result: datetime = dt.replace(year=dt.year + years, month=3, day=1) \
                if dt.month == 2 and dt.day == 29 \
                else dt.replace(year=dt.year + years)
            logger.debug("add_years(%s, %d) = %s", dt, years, result)
            return result

        def get_date(d_m: str) -> Optional[datetime]:
            # Without a year it will be 1900 so add the year
            assert self.statement.end_date and self.statement.end_date.year
            d_m_y = "{} {}".format(d_m, self.statement.end_date.year)
            dt: Optional[datetime] = datetime.strptime(d_m_y, '%d %b %Y')
            # But now the resulting date may be more than the end date
            # (d_m in december and end date in january)
            if dt and dt > self.statement.end_date:
                dt = add_years(dt, -1)
            assert dt is None or dt <= self.statement.end_date
            return dt

        logger.debug('row: %s', str(row))
        assert len(row) in [5, 7, 8]

        stmt_line: Optional[StatementLine] = None
        # GJP 2020-03-01
        # Skip transaction date (index 0) since it gives a wrong balance.
        # Use booking date (index 1) in order to get a correct balance.
        # Since April 2025 the month will end in a period ('.').
        date = get_date(row[1][:-1] if row[1].endswith('.') else row[1])

        payee = None
        memo = None
        if len(row) >= 7:
            # payee (2), place (3) and country (4)
            payee = row[2]
            memo = "{0} ({1})".format(row[3], row[4])
        else:
            # description (2)
            memo = row[2]

        # Skip amount in foreign currency
        amount = Parser.get_amount(row[-2], row[-1])

        # Remove zero-value notifications
        if amount != 0:
            stmt_line = StatementLine(date=date,
                                      memo=memo,
                                      amount=amount)
            stmt_line.payee = payee
            stmt_line.adjust(self.unique_id_set)

        logger.debug('stmt_line: %s', stmt_line)
        return stmt_line


class Plugin(BasePlugin):
    """ICSCards, The Netherlands, PDF (https://icscards.nl/)
    """

    def get_file_object_parser(self, fh: Iterable[str]) -> Parser:
        return Parser(fh)

    def get_parser(self, filename: str) -> Parser:
        pdftotext = ["pdftotext", "-layout", filename, '-']
        fh: Iterable[str]

        # Is it a PDF or an already converted file?
        try:
            fh = io.StringIO(check_output(pdftotext).decode())
            # No exception: apparently it is a PDF.
        except CalledProcessError:
            fh = open(filename, "r")

        return self.get_file_object_parser(fh)
