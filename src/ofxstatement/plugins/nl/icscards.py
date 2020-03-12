# -*- coding: utf-8 -*-
import sys
import locale
import re
import io
from decimal import Decimal
from datetime import datetime
from subprocess import check_output, CalledProcessError
import logging

from ofxstatement import plugin, parser
from ofxstatement.statement import StatementLine

# Need Python 3 for super() syntax
assert sys.version_info[0] >= 3, "At least Python 3 is required."

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Plugin(plugin.Plugin):
    """ICSCards, The Netherlands, PDF (https://icscards.nl/)
    """

    def get_file_object_parser(self, fh):
        return Parser(fh)

    def get_parser(self, filename):
        pdftotext = ["pdftotext", "-layout", filename, '-']
        fh = None

        # Is it a PDF or an already converted file?
        try:
            fh = io.StringIO(check_output(pdftotext).decode())
            # No exception: apparently it is a PDF.
        except CalledProcessError:
            fh = open(filename, "r")

        return self.get_file_object_parser(fh)


class Parser(parser.StatementParser):
    def __init__(self, fin):
        super().__init__()
        self.fin = fin

    def parse(self):
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """
        stmt = None
        # Save locale
        current_locale = locale.setlocale(category=locale.LC_ALL)
        # Need to parse "05 mei" i.e. "05 may"
        locale.setlocale(category=locale.LC_ALL, locale="Dutch")
        try:
            # Python 3 needed
            stmt = super().parse()

            stmt.currency = 'EUR'
            stmt.bank_id = self.bank_id
            stmt.account_id = self.account_id

            # for stmt.start_date
            stmt.recalculate_balance()
            stmt.start_balance = self.start_balance
            stmt.end_date = self.page_date
            stmt.end_balance = self.end_balance
        finally:
            locale.setlocale(category=locale.LC_ALL, locale=current_locale)

        return stmt

    @staticmethod
    def get_amount(amount_in, transaction_type_in):
        sign_out, amount_out = 1, None

        # determine sign_out
        assert isinstance(transaction_type_in, str)
        assert transaction_type_in in ['Af', 'Bij']

        if transaction_type_in == 'Af':
            sign_out = -1

        # determine amount_out
        assert isinstance(amount_in, str)
        # Amount something like 1.827,97, € 1.827,97 (both dutch) or 1,827.97?
        m = re.search(r'^(\S+\s)?([0-9,.]+)$', amount_in)
        assert m is not None
        amount_out = m.group(2)
        if amount_out[-3] == ',':
            amount_out = amount_out.replace('.', '').replace(',', '.')

        # convert to str to keep just the last two decimals
        amount_out = Decimal(str(amount_out))

        return sign_out * amount_out

    def split_records(self):
        """Return iterable object consisting of a line per transaction
        """
        def convert_str_to_list(str, max_items=None, sep=r'\s\s+|\t|\n'):
            return [x for x in re.split(sep, str)[0:max_items]]

        global logger

        first_line = True
        first_line_row = ['International Card Services BV', 'www.icscards.nl']

        new_page = False
        new_page_row = ['Datum', 'ICS-klantnummer', 'Volgnummer', 'Bladnummer']

        balance = False
        balance_row = ['Vorig openstaand saldo', 'Totaal ontvangen betalingen',
                       'Totaal nieuwe uitgaven', 'Nieuw openstaand saldo']

        statement_expr = \
            re.compile(r'^\d\d [a-z]{3}\s+\d\d [a-z]{3}.+[0-9,.]+\s+(Af|Bij)$')

        # breakpoint()
        for line in self.fin:
            line = line.strip()

            logger.debug('line: ' + line)

            # to ease the parsing pain
            row = convert_str_to_list(line)

            if first_line and len(row) > 1:
                assert row == first_line_row,\
                    "Expected: {0}\nActual: {1}".format(first_line_row, row)
                first_line = False

            if len(row) == 2 and row[1][0:5] == 'BIC: ':
                self.bank_id = row[1][5:]

            elif row == new_page_row:
                new_page = True
            elif new_page:
                new_page = False
                self.page_date = row[0]
                self.account_id = row[1]
                self.page_date = \
                    datetime.strptime(self.page_date, '%d %B %Y').date()

            elif row == balance_row:
                balance = True
            elif balance:
                balance = False
                self.start_balance = Parser.get_amount(row[0], row[1])
                self.end_balance = Parser.get_amount(row[-2], row[-1])

            elif re.search(statement_expr, line):
                # payee (column 2), place and contry may be something like:
                #
                # THY|2357312380512|Istanbul|US
                #
                # hence four columns instead of three, so combine the first two
                country = re.compile("^[A-Z][A-Z]$")
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
                yield row

    def parse_record(self, row):
        """Parse given transaction line and return StatementLine object
        """

        def add_years(d, years):
            """Return a date that's `years` years after the date (or datetime)
            object `d`. Return the same calendar date (month and day) in the
            destination year, if it exists, otherwise use the following day
            (thus changing February 29 to March 1).

            """
            return d.replace(year=d.year + years, month=3, day=1) \
                if d.month == 2 and d.day == 29 \
                else d.replace(year=d.year + years)

        def get_date(s: str):
            d = datetime.strptime(s, '%d %b').date()
            # Without a year it will be 1900 so augment
            while d <= self.page_date:
                d = add_years(d, 1)
            return add_years(d, -1)

        global logger

        logger.debug('row: ' + str(row))
        assert(len(row) in [5, 7, 8])

        stmt_line = None
        # GJP 2020-03-01
        # Skip transaction date (index 0) since it gives a wrong balance.
        # Use booking date (index 1) in order to get a correct balance.
        date = get_date(row[1])

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
            try:
                stmt_line.generate_transaction_id()
            except:
                # include record number so the memo gets unique
                stmt_line.memo = stmt_line.memo + ' #' + str(self.cur_record)
                stmt_line.generate_transaction_id()

        return stmt_line
