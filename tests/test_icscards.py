# -*- coding: utf-8 -*-
import os
from unittest import TestCase
from decimal import Decimal
import pytest
from datetime import datetime

from ofxstatement.plugins.nl.icscards import Plugin


class ParserTest(TestCase):

    def test_missing_column(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'icscards.txt')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "ABNANL2A")
        self.assertEqual(statement.account_id, "99999999999")
        self.assertEqual(statement.account_type, "CHECKING")
        self.assertEqual(statement.start_balance, Decimal('-1311.73'))
        self.assertEqual(statement.start_date,
                         datetime.strptime("2019-08-21",
                                           parser.date_format).date())
        self.assertEqual(statement.end_balance, Decimal('-1320.55'))
        self.assertEqual(statement.end_date,
                         datetime.strptime("2019-09-17",
                                           parser.date_format).date())

        self.assertEqual(len(statement.lines), 25)
        self.assertEqual(statement.lines[0].amount, Decimal('1311.73'))
        self.assertEqual(statement.lines[1].date,
                         datetime.strptime("2019-08-21",
                                           parser.date_format).date())
        self.assertEqual(statement.lines[1].amount, Decimal('-7.99'))
        self.assertEqual(statement.lines[12].payee, "HOTEL MERCURE")
        self.assertEqual(statement.lines[12].memo, "MONTIGNY LE B (FR)")
        self.assertEqual(statement.lines[13].payee,
                         "NEWREST WAGONS LITS FRANC")
        self.assertEqual(statement.lines[13].memo, "PARIS (FR)")
        self.assertEqual(statement.lines[14].payee, "SNCF")
        self.assertEqual(statement.lines[14].memo, "PARIS 8 (FR)")
        self.assertEqual(statement.lines[24].amount, Decimal('-6.15'))

    def test_big(self):
        # Create and configure parser:
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'icscards_big.txt')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "ABNANL2A")
        self.assertEqual(statement.account_id, "99999999999")
        self.assertEqual(statement.account_type, "CHECKING")
        self.assertEqual(statement.start_balance, Decimal('-893.31'))
        self.assertEqual(statement.start_date,
                         datetime.strptime("2018-12-21",
                                           parser.date_format).date())
        self.assertEqual(statement.end_balance, Decimal('-1156.34'))
        self.assertEqual(statement.end_date,
                         datetime.strptime("2019-01-17",
                                           parser.date_format).date())

    def test_error(self):
        # Create and configure parser:
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'icscards_error.txt')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "ABNANL2A")
        self.assertEqual(statement.account_id, "99999999999")
        self.assertEqual(statement.account_type, "CHECKING")
        self.assertEqual(statement.start_balance, Decimal('-1753.69'))
        self.assertEqual(statement.end_balance, Decimal('-1325.11'))

        self.assertEqual(statement.lines[6].payee, "THY 2357312380512")
        self.assertEqual(statement.lines[6].memo, "Istanbul (US)")
        self.assertEqual(statement.lines[16].payee, "TOTAL 4375462")
        self.assertEqual(statement.lines[16].memo, "33PESSAC (FR)")

    def test_equal_transactions(self):
        # Create and configure parser:
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here,
                                     'samples',
                                     'icscards_equal_transactions.txt')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "ABNANL2A")
        self.assertEqual(statement.account_id, "99999999999")
        self.assertEqual(statement.account_type, "CHECKING")
        self.assertEqual(statement.start_balance, Decimal('-1311.73'))
        self.assertEqual(statement.end_balance, Decimal('-1320.55'))

        self.assertEqual(statement.lines[7].amount, Decimal('-5.05'))
        self.assertEqual(statement.lines[7].memo, 'MONTIGNY LE B (FR)')
        self.assertEqual(statement.lines[8].amount, Decimal('-5.05'))
        self.assertEqual(statement.lines[8].memo, 'MONTIGNY LE B (FR) #2')
        self.assertNotEqual(statement.lines[7].id, statement.lines[8].id)

    @pytest.mark.xfail(raises=AttributeError)
    def test_fail(self):
        """'Parser' object has no attribute 'bank_id'
        """
        here = os.path.dirname(__file__)
        pdf_filename = os.path.join(here, 'samples', 'blank.pdf')
        parser = Plugin(None, None).get_parser(pdf_filename)

        # And parse:
        parser.parse()
        if parser.bank_id:
            pass
