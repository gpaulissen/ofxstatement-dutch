import os
from unittest import TestCase
from decimal import Decimal
import pytest
from datetime import datetime

from ofxstatement.exceptions import ParseError

from ofxstatement.plugins.nl.ing import Plugin


class ParserTest(TestCase):

    def check(self, parser):
        # And parse csv:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "INGBNL2A")
        self.assertEqual(statement.account_id, "NL99INGB9999999999")
        self.assertEqual(statement.account_type, "CHECKING")

        self.assertIsNone(statement.start_balance)
        self.assertEqual(statement.start_date,
                         datetime.strptime("20191213",
                                           parser.date_format))

        self.assertIsNone(statement.end_balance)
        self.assertEqual(statement.end_date,
                         datetime.strptime("20200214",
                                           parser.date_format))

        # Amount of 0 is skipped
        self.assertEqual(len(statement.lines), 5)
        self.assertEqual(statement.lines[0].amount, Decimal('-1.25'))
        self.assertFalse(statement.lines[0].payee)
        # "Naam / Omschrijving" is prepended to "Mededelingen"
        self.assertEqual(statement.lines[0].memo,
                         "Kosten OranjePakket met korting, \
1 jan t/m 31 jan 2020 ING BANK N.V. Valutadatum: 13-02-2020")

        self.assertEqual(statement.lines[1].amount, Decimal('1.25'))
        self.assertFalse(statement.lines[1].payee)
        # "Naam / Omschrijving" is prepended to "Mededelingen"
        self.assertEqual(statement.lines[1].memo,
                         "Kwijtschelding, Valutadatum: 13-02-2020")

        self.assertEqual(statement.lines[2].amount, Decimal('20.00'))
        # "Naam / Omschrijving" is prepended to "Tegenrekening"
        self.assertEqual(statement.lines[2].payee,
                         "PAULISSEN G J L M (NL99ASNB9999999999)")
        # "Naam / Omschrijving" is NOT prepended to "Mededelingen"
        self.assertEqual(statement.lines[2].memo,
                         "Naam: PAULISSEN G J L M Omschrijving: \
Kosten rekening IBAN: NL99ASNB9999999999 Valutadatum: 13-12-2019")

        self.assertEqual(statement.lines[3].amount, Decimal('-0.31'))
        self.assertFalse(statement.lines[3].payee)
        # "Naam / Omschrijving" is prepended to "Mededelingen"
        self.assertEqual(statement.lines[3].memo,
                         "Kosten OranjePakket, \
25 nov t/m 30 nov 2019 ING BANK N.V. Valutadatum: 13-12-2019")

        self.assertEqual(statement.lines[4].amount, Decimal('-0.31'))
        self.assertFalse(statement.lines[4].payee)
        # "Naam / Omschrijving" is prepended to "Mededelingen"
        self.assertEqual(statement.lines[4].memo,
                         "Kosten OranjePakket, \
25 nov t/m 30 nov 2019 ING BANK N.V. Valutadatum: 13-12-2019 #2")

    def test_ok(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'ing_ok.csv')
        self.check(Plugin(None, None).get_parser(text_filename))

    def test_ok_Mutatiesoort(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'ing_ok_Mutatiesoort.csv')
        self.check(Plugin(None, None).get_parser(text_filename))

    def test_ok_Mutatiesoort_Extra(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'ing_ok_Mutatiesoort_Extra.csv')
        self.check(Plugin(None, None).get_parser(text_filename))

    def test_ok_Mutatiesoort_Extra_Unquoted(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'ing_ok_Mutatiesoort_Extra_Unquoted.csv')
        self.check(Plugin(None, None).get_parser(text_filename))

    @pytest.mark.xfail(raises=ParseError)
    def test_fail(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'ing_fail.csv')
        parser = Plugin(None, None).get_parser(text_filename)
        # Lets define some sample csv to parse and write it to file-like object

        # And parse csv:
        parser.parse()

    @pytest.mark.xfail(raises=ParseError)
    def test_no_header(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'empty.csv')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse csv:
        parser.parse()

    def test_balance(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'NL99INGB9999999999_25-11-2019_30-05-2020.csv')
        parser = Plugin(None, None).get_parser(text_filename)
        # Lets define some sample csv to parse and write it to file-like object

        # And parse csv:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "INGBNL2A")
        self.assertEqual(statement.account_id, "NL99INGB9999999999")
        self.assertEqual(statement.account_type, "CHECKING")

        self.assertIsNone(statement.start_balance)
        self.assertIsNone(statement.start_date)

        self.assertEqual(statement.end_balance, Decimal('13.20'))
        self.assertEqual(statement.end_date,
                         datetime.strptime("2020-05-31",  # plus 1 day
                                           parser.date_format))

        self.assertEqual(len(statement.lines), 0)
