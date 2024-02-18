import os
import pytest
from unittest import TestCase
from decimal import Decimal
from datetime import datetime

from ofxstatement.statement import StatementLine
from ofxstatement.exceptions import ParseError
from ofxstatement.plugins.nl.degiro import Plugin


class ParserTest(TestCase):

    def test_ok(self):
        # Create and configure parser:
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here,
                                     'samples',
                                     'Account_20190101_20200317.csv')
        parser = Plugin(None, {'account_id': 'ABC'}).get_parser(text_filename)

        # And parse:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "STDGNL21")
        self.assertEqual(statement.account_id, "ABC")
        self.assertEqual(statement.account_type, "CHECKING")
        self.assertIsNone(statement.start_balance)
        self.assertIsNone(statement.end_balance)
        self.assertEqual(statement.start_date,
                         datetime.strptime("19-06-2019",
                                           parser.date_format))
        self.assertEqual(statement.end_date,
                         datetime.strptime("22-06-2019",
                                           parser.date_format))

        lines = []

        # ignore lines without money

        lines.append(StatementLine(date='30-12-2019',
                                   memo='Conversie geldmarktfonds: \
Koop 0,000016 @ 9.961,4715 EUR MORGAN STANLEY EUR LIQUIDITY FUND \
(LU1959429272)',
                                   amount=''))
        lines.append(StatementLine(date='27-12-2019',
                                   memo='Dividend VANECK AEX (NL0009272749)',
                                   amount='0,19'))
        lines.append(StatementLine(date='27-12-2019',
                                   memo='Dividendbelasting VANECK AEX \
(NL0009272749)',
                                   amount='-0,03'))
        lines.append(StatementLine(date='26-09-2019',
                                   memo='Conversie geldmarktfonds: \
Koop 0,000039 @ 9.975,9152 EUR MORGAN STANLEY EUR LIQUIDITY FUND \
(LU1959429272)',
                                   amount=''))
        lines.append(StatementLine(date='25-09-2019',
                                   memo='Dividend VANECK AEX (NL0009272749)',
                                   amount='0,46'))
        lines.append(StatementLine(date='25-09-2019',
                                   memo='Dividendbelasting VANECK AEX \
(NL0009272749)',
                                   amount='-0,07'))
        lines.append(StatementLine(date='27-06-2019',
                                   memo='Conversie geldmarktfonds: \
Koop 0,001337 @ 9.986,9062 EUR MORGAN STANLEY EUR LIQUIDITY FUND \
(LU1959429272)',
                                   amount=''))
        lines.append(StatementLine(date='26-06-2019',
                                   memo='Dividend VANECK AEX (NL0009272749)',
                                   amount='1,06'))
        lines.append(StatementLine(date='26-06-2019',
                                   memo='Dividendbelasting VANECK AEX \
(NL0009272749)',
                                   amount='-0,16'))
        lines.append(StatementLine(date='26-06-2019',
                                   memo='Dividend VANECK ESG EW \
(NL0010408704)',
                                   amount='4,40'))
        lines.append(StatementLine(date='26-06-2019',
                                   memo='Dividendbelasting VANECK ESG EW \
(NL0010408704)',
                                   amount='-0,66'))
        lines.append(StatementLine(date='26-06-2019',
                                   memo='Dividend ISHARES AEX (IE00B0M62Y33)',
                                   amount='8,72'))
        lines.append(StatementLine(date='21-06-2019',
                                   memo='Terugstorting',
                                   amount='-334,35'))
        lines.append(StatementLine(date='21-06-2019',
                                   memo='Terugstorting #2',
                                   amount='-334,35'))
        lines.append(StatementLine(date='21-06-2019',
                                   memo='DEGIRO transactiekosten VANECK ESG EW\
 (NL0010408704)',
                                   amount='-2,00'))
        lines.append(StatementLine(date='21-06-2019',
                                   memo='DEGIRO Aansluitingskosten',
                                   amount='-0,13'))
        lines.append(StatementLine(date='21-06-2019',
                                   memo='Verkoop 4 @ 84,12 EUR VANECK ESG EW\
 (NL0010408704)',
                                   amount='336,48'))
        lines.append(StatementLine(date='19-06-2019',
                                   memo='iDEAL storting',
                                   amount='557,10'))
        lines.append(StatementLine(date='19-06-2019',
                                   memo='Verkoop 10 @ 55,92 EUR ISHARES AEX\
 (IE00B0M62Y33)',
                                   amount='559,20'))
        lines.append(StatementLine(date='04-06-2019',
                                   memo='Rente',
                                   amount='-0,01'))
        lines.append(StatementLine(date='03-05-2019',
                                   memo='Rente',
                                   amount='-0,01'))
        lines.append(StatementLine(date='01-04-2019',
                                   memo='Rente',
                                   amount='-0,02'))
        lines.append(StatementLine(date='27-03-2019',
                                   memo='Dividend VANECK AEX (NL0009272749)',
                                   amount='0,25'))
        lines.append(StatementLine(date='27-03-2019',
                                   memo='Dividendbelasting VANECK AEX \
(NL0009272749)',
                                   amount='-0,04'))
        lines.append(StatementLine(date='27-03-2019',
                                   memo='Dividend VANECK ESG EW\
 (NL0010408704)',
                                   amount='1,00'))
        lines.append(StatementLine(date='27-03-2019',
                                   memo='Dividendbelasting VANECK ESG EW \
(NL0010408704)',
                                   amount='-0,15'))
        lines.append(StatementLine(date='27-03-2019',
                                   memo='Dividend ISHARES AEX (IE00B0M62Y33)',
                                   amount='1,97'))
        # in USD
        # lines.append(StatementLine(date='04-03-2019',
        #                            memo='Rente',
        #                            amount='-0,02'))
        lines.append(StatementLine(date='01-02-2019',
                                   memo='Rente',
                                   amount='-0,02'))
        lines.append(StatementLine(date='02-01-2019',
                                   memo='Rente #2',
                                   amount='-0,02'))

        lines = [line
                 for line in lines
                 if line.amount and line.memo in ['iDEAL storting',
                                                  'Terugstorting',
                                                  'Terugstorting #2']]
        self.assertEqual(len(statement.lines), len(lines))

        for idx, line in enumerate(statement.lines):
            self.assertEqual(line.date,
                             datetime.strptime(lines[idx].date,
                                               parser.date_format))
            self.assertEqual(line.memo, lines[idx].memo)
            self.assertEqual(line.amount,
                             Decimal(lines[idx].amount.replace(",", ".").
                                     replace(" ", "")))

    @pytest.mark.xfail(raises=RuntimeError)
    def test_no_config(self):
        """No attribute
        """
        # Create and configure parser:
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here,
                                     'samples',
                                     'Account_20190101_20200317.csv')
        Plugin(None, None).get_parser(text_filename)

    @pytest.mark.xfail(raises=RuntimeError)
    def test_no_config_account_id(self):
        """No attribute
        """
        # Create and configure parser:
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here,
                                     'samples',
                                     'Account_20190101_20200317.csv')
        Plugin(None, {'ACCOUNT_ID'}).get_parser(text_filename)

    @pytest.mark.xfail(raises=ParseError)
    def test_no_header(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'empty.csv')
        parser = Plugin(None, {'account_id': 'ABC'}).get_parser(text_filename)

        # And parse csv:
        parser.parse()
