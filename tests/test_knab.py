import io
import os
from textwrap import dedent
from unittest import TestCase
from decimal import Decimal
import pytest
from datetime import datetime

from ofxstatement.exceptions import ParseError, ValidationError

from ofxstatement.plugins.nl.knab import Parser, Plugin


class ParserTest(TestCase):

    def test_basic(self):
        # Lets define some sample csv to parse and write it to file-like object
        csv = dedent('''
KNAB EXPORT;;;;;;;;;;;;;;;;
Rekeningnummer;Transactiedatum;Valutacode;CreditDebet;Bedrag;Tegenrekeningnummer;Tegenrekeninghouder;Valutadatum;Betaalwijze;Omschrijving;Type betaling;Machtigingsnummer;Incassant ID;Adres;Referentie;Boekdatum;
"NL99KNAB9999999999";"26-03-2020";"EUR";"D";"7,02";"NL99ASNB9999999999";"JANSSEN G";"27-03-2020";"Overboeking";"Omschrijving 1";"";"";"";"";"C0C27IP2NC00000A";"28-03-2020";
"NL99KNAB9999999999";"26-03-2020";"EUR";"D";"0,00";"NL99ASNB9999999999";"JANSSEN G";"27-03-2020";"Overboeking";"";"";"";"";"";"C0C27IP2NC00000A";"28-03-2020";
"NL99KNAB9999999999";"27-03-2020";"EUR";"C";"5,00";"50022270";"Gert Janssen";"28-03-2020";"Ontvangen betaling";"Omschrijving 2";"";"";"";"";"C0C27PGFM28ERA34";"29-03-2020";
            ''')
        f = io.StringIO(csv)

        # Create and configure csv parser:
        parser = Parser(f)

        # And parse csv:
        statement = parser.parse()

        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "KNABNL2H")
        self.assertEqual(statement.account_id, "NL99KNAB9999999999")
        self.assertEqual(statement.account_type, "CHECKING")

        self.assertIsNone(statement.start_balance)
        self.assertEqual(statement.start_date, datetime.strptime("28-03-2020", parser.date_format))

        self.assertIsNone(statement.end_balance)
        self.assertEqual(statement.end_date, datetime.strptime("30-03-2020", parser.date_format))

        # Amount of 0 is skipped
        self.assertEqual(len(statement.lines), 2)
        self.assertEqual(statement.lines[0].date, datetime.strptime("28-03-2020", parser.date_format))
        self.assertEqual(statement.lines[0].date_user, datetime.strptime("26-03-2020", parser.date_format))
        self.assertEqual(statement.lines[0].amount, Decimal('-7.02'))
        self.assertEqual(statement.lines[0].payee, "JANSSEN G (NL99ASNB9999999999)")
        self.assertEqual(statement.lines[0].memo, "Omschrijving 1")
        self.assertEqual(statement.lines[0].refnum, "C0C27IP2NC00000A")

        self.assertEqual(statement.lines[1].date, datetime.strptime("29-03-2020", parser.date_format))
        self.assertEqual(statement.lines[1].date_user, datetime.strptime("27-03-2020", parser.date_format))
        self.assertEqual(statement.lines[1].amount, Decimal('5.00'))
        self.assertEqual(statement.lines[1].payee, "Gert Janssen (50022270)")
        self.assertEqual(statement.lines[1].memo, "Omschrijving 2")
        self.assertEqual(statement.lines[1].refnum, "C0C27PGFM28ERA34")

    def test_ok(self):
        # Create and configure parser:
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'Knab_transactieoverzicht_ok.csv')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse:
        statement = parser.parse()
        self.assertEqual(len(statement.lines), 28)
        self.assertEqual(statement.currency, 'EUR')
        self.assertEqual(statement.bank_id, "KNABNL2H")
        self.assertEqual(statement.account_id, "NL99KNAB9999999999")
        self.assertEqual(statement.account_type, "CHECKING")

        self.assertIsNone(statement.start_balance)
        self.assertEqual(statement.start_date, datetime.strptime("07-01-2019", parser.date_format))

        self.assertIsNone(statement.end_balance)
        self.assertEqual(statement.end_date, datetime.strptime("22-06-2019", parser.date_format))

        self.assertEqual(sum(sl.amount for sl in statement.lines), Decimal('7.01'))

    @pytest.mark.xfail(raises=ParseError)
    def test_no_header1(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'empty.csv')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse csv:
        parser.parse()

    @pytest.mark.xfail(raises=ParseError)
    def test_no_header2(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'Knab_transactieoverzicht_no_header2.csv')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse csv:
        parser.parse()

    @pytest.mark.xfail(raises=ValidationError)
    def test_no_lines(self):
        here = os.path.dirname(__file__)
        text_filename = os.path.join(here, 'samples', 'Knab_transactieoverzicht_no_lines.csv')
        parser = Plugin(None, None).get_parser(text_filename)

        # And parse csv:
        parser.parse()

    @pytest.mark.xfail(raises=ParseError)
    def test_wrong_account_no(self):
        # Lets define some sample csv to parse and write it to file-like object
        csv = dedent('''
KNAB EXPORT;;;;;;;;;;;;;;;;
Rekeningnummer;Transactiedatum;Valutacode;CreditDebet;Bedrag;Tegenrekeningnummer;Tegenrekeninghouder;Valutadatum;Betaalwijze;Omschrijving;Type betaling;Machtigingsnummer;Incassant ID;Adres;Referentie;Boekdatum;
"NL99KNAB9999999999";"26-03-2020";"EUR";"D";"7,02";"NL99ASNB9999999999";"JANSSEN G";"27-03-2020";"Overboeking";"Omschrijving 1";"";"";"";"";"C0C27IP2NC00000A";"28-03-2020";
"NL00KNAB0000000000";"27-03-2020";"EUR";"C";"5,00";"50022270";"Gert Janssen";"28-03-2020";"Ontvangen betaling";"Omschrijving 2";"";"";"";"";"C0C27PGFM28ERA34";"29-03-2020";
            ''')
        f = io.StringIO(csv)

        # Create and configure csv parser:
        parser = Parser(f)

        # And parse csv:
        parser.parse()

    @pytest.mark.xfail(raises=ParseError)
    def test_no_payee(self):
        # Lets define some sample csv to parse and write it to file-like object
        csv = dedent('''
KNAB EXPORT;;;;;;;;;;;;;;;;
Rekeningnummer;Transactiedatum;Valutacode;CreditDebet;Bedrag;Tegenrekeningnummer;Tegenrekeninghouder;Valutadatum;Betaalwijze;Omschrijving;Type betaling;Machtigingsnummer;Incassant ID;Adres;Referentie;Boekdatum;
"NL99KNAB9999999999";"26-03-2020";"EUR";"D";"7,02";"NL99ASNB9999999999";"JANSSEN G";"27-03-2020";"Overboeking";"Omschrijving 1";"";"";"";"";"C0C27IP2NC00000A";"28-03-2020";
"NL99KNAB9999999999";"27-03-2020";"EUR";"C";"5,00";"";"Gert Janssen";"28-03-2020";"Ontvangen betaling";"Omschrijving 2";"";"";"";"";"C0C27PGFM28ERA34";"29-03-2020";
            ''')
        f = io.StringIO(csv)

        # Create and configure csv parser:
        parser = Parser(f)

        # And parse csv:
        parser.parse()
