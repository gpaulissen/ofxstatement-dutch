import os
from unittest import TestCase
from decimal import Decimal
import pytest
from datetime import datetime

from ofxstatement.exceptions import ParseError

from ofxstatement.plugins.nl.asn import Plugin


class ParserTest(TestCase):

    def test_ok(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'transactie-historie_NL00ASNB9999999999_20220717204133.csv')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse csv:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "ASNBNL21")
        self.assertEqual(statement.account_id, "NL00ASNB9999999999")
        self.assertEqual(statement.account_type, "CHECKING")

        self.assertEqual(statement.start_balance, Decimal('130.44'))
        self.assertEqual(statement.start_date,
                         datetime.strptime("17-06-2022",
                                           parser.date_format))

        self.assertEqual(statement.end_balance, Decimal('644.24') + Decimal('-560.00'))
        self.assertEqual(statement.end_date,
                         datetime.strptime("12-07-2022",  # +1
                                           parser.date_format))

        self.assertEqual(len(statement.lines), 11)
        self.assertEqual(statement.lines[0].id, '20220617.51392971')
        self.assertEqual(statement.lines[0].amount, Decimal('223.77'))
        self.assertEqual(statement.lines[0].bank_account_to.acct_id, 'NL99ASNB0000000000')
        self.assertEqual(statement.lines[0].payee, 'XXXXXXXXX Z Z Z Z (NL99ASNB0000000000)')
        self.assertEqual(statement.lines[0].date,
                         datetime.strptime("17-06-2022",
                                           parser.date_format))
        self.assertEqual(statement.lines[0].date_user,
                         statement.lines[0].date)

        self.assertEqual(statement.lines[2].id, '20220625.50951652')
        self.assertIsNone(statement.lines[2].bank_account_to)
        self.assertIsNone(statement.lines[2].payee)
        self.assertEqual(statement.lines[2].memo,
                         "Kosten gebruik betaalrekening inclusief 1 betaalpas")

        self.assertEqual(statement.lines[5].id, '20220629.50139616')
        self.assertEqual(statement.lines[5].date,
                         datetime.strptime("29-06-2022",
                                           parser.date_format))
        self.assertEqual(statement.lines[5].date_user,
                         datetime.strptime("28-06-2022",
                                           parser.date_format))

    @pytest.mark.xfail(raises=ParseError)
    def test_fail(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'transactie-historie_fail.csv')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse csv:
        parser.parse()
