# -*- coding: utf-8 -*-
import csv
import datetime
import logging
import re
import sys
from decimal import Decimal
from typing import Any, Dict, Iterator, List, Optional, TextIO

from ofxstatement.exceptions import ParseError
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin as BasePlugin
from ofxstatement.statement import (
    BankAccount,
    StatementLine,
)
from ofxstatement.statement import (
    Statement as BaseStatement,
)

from ofxstatement_dutch.statement import Statement

# Need Python 3 for super() syntax
if not sys.version_info[0] >= 3:
    raise ValueError("At least Python 3 is required.")

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Parser(CsvStatementParser):
    """

    Nr  Veldnaam                     Formaat        Omschrijving                                                                            Voorbeeld
    --  --------                     -------        ------------                                                                            ---------
     0  Boekingsdatum                dd­mm­jjjj     Dit veld geeft de datum weer waarop de transactie daadwerkelijk heeft plaatsgevonden.   3­4­2000
     1  Opdrachtgeversrekening       X (18)         Uw ASN­Rekening (IBAN).                                                                 NL01ASNB0123456789
     2  Tegenrekeningnummer          X (34)         Dit veld bevat het rekeningnummer (IBAN) naar of waarvan de transactie afkomstig is.    NL01BANK0123456789
                                                    Het IBAN telt maximaal 34 alfanumerieke tekens en heeft een vaste lengte per land
                                                    Het IBAN bestaat uit een landcode (twee letters), een controlegetal (twee cijfers)
                                                    en een (voor bepaalde landen aangevuld) nationaal rekeningnummer.
     3  Naam tegenrekening           X (70)         Hier wordt de naam van de tegenrekening vermeld.                                        jansen
                                                    De naam is maximaal 70 posities lang en wordt in kleine letters weergegeven.
     4  Adres                                       Dit veld is niet in gebruik.
     5  Postcode                                    Dit veld is niet in gebruik.
     6  Plaats                                      Dit veld is niet in gebruik
     7  Valutasoort rekening         XXX            Dit veld geeft de ISO valutasoort van de rekening weer.                                 EUR
                                                    Een bestand kan verschillende valutasoorten bevatten.
     8  Saldo rekening voor mutatie  ­999999999.99  Geeft het saldo weer van de rekening voordat de mutatie is verwerkt.                    122800.83 of ­123.30
                                                    Als decimaal scheidingsteken wordt een punt gebruikt. Er wordt geen duizend separator
                                                    gebruikt. In het geval van een negatieve waarde wordt het bedrag voorafgegaan van een
                                                    - (min) teken.
     9  Valutasoort mutatie          XXX            Dit veld geeft de ISO valutasoort van de mutatie weer.                                  EUR
                                                    Een bestand kan verschillende valutasoorten bevatten.
    10  Transactiebedrag             ­999999999.99  Geeft het transactiebedrag weer. Als decimaal scheidingsteken wordt een punt gebruikt.  238.45 of ­43.90
                                                    Een negatief bedrag wordt voorafgegaan door een - (min) teken.
    11  Journaaldatum                dd­mm­jjjj     De journaaldatum is de datum waarop een transactie in de systemen van ASN Bank wordt    21­01­2000
                                                    geboekt. Dit hoeft niet noodzakelijkerwijs gelijk te zijn aan de boekingsdatum.
    12  Valutadatum                  dd­mm­jjjj     Dit veld geeft de valutadatum weer. De valutadatum is de datum waarop een bedrag        01­04­2001
                                                    rentedragend wordt.
    13  Interne transactiecode       9999           Dit is een interne transactiecode zoals die door de ASN Bank wordt gebruikt. Deze       8810 of 9820
                                                    transactiecodes kunnen gebruikt worden om heel verfijnd betaalde transacties te
                                                    herkennen. Zoals een bijboeking van een geldautomaat opname. Er kan geen garantie
                                                    worden gegeven dat deze codes in de toekomst hetzelfde blijven en/of dat er codes
                                                    vervallen en/of toegevoegd zullen worden.
    14  Globale transactiecode       XXX            De globale transactiecode is een vertaling van de interne transactiecode. Gebruikte     GEA of BEA of VV
                                                    afkortingen zijn bijvoorbeeld BEA voor een betaalautomaat opname of GEA voor een
                                                    geldautomaat opname. In de bijlage wordt een overzicht gegeven van alle gebruikte
                                                    afkortingen.
                                                    Zie ook Bijlage 1: Gebruikte boekingscodes
    15  Volgnummer transactie        N (8)          Geeft het transactievolgnummer van de transactie weer. Dit volgnummer vormt samen met   90043054
                                                    de journaaldatum een uniek transactie id.
    16  Betalingskenmerk             X (16)         Het betalingskenmerk bevat de meest relevante gegevens zoals die door de betaler zijn   ’factuur 9234820’
                                                    opgegeven. Zoals debiteuren nummer en/of factuurnummer. Het betalingskenmerk wordt
                                                    tussen enkele quotes (’) geplaatst.
    17  Omschrijving                 X (140)        De omschrijving zoals die bij de overboeking is opgegeven. De omschrijving kan          ’02438000140032extra trekking werelddierendag 4info’
                                                    maximaal 140 posities beslaan.
    18  Afschriftnummer              N (3)          Het nummer van het afschrift waar de betreffende boeking op staat vermeld.              42

    ===

    Bijlage 1: Gebruikte boekingscodes

    ACC Acceptgirobetaling AF Afboeking
    AFB Afbetalen
    BEA Betaalautomaat BIJ Bijboeking
    BTL Buitenlandse Overboeking
    CHP Chipknip
    CHQ Cheque
    COR Correctie
    DIV Diversen
    EFF Effectenboeking
    ETC Euro traveller cheques GBK GiroBetaalkaart
    GEA Geldautomaat
    INC Incasso
    IDB iDEAL betaling
    IMB iDEAL betaling via mobiel IOB Interne Overboeking
    KAS Kas post
    KTN Kosten/provisies
    KST Kosten/provisies
    OVB Overboeking
    PRM Premies
    PRV Provisies
    RNT Rente
    STO Storno
    TEL Telefonische Overboeking VV Vreemde valuta

    ===

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
        "date": 11,
        "memo": 17,
        "amount": 10,
        "payee": 3,  # if bank_account_to is filled
        "date_user": 0,
        # check_no
        # refnum
        # trntype (determined later)
        "bank_account_to": 2,
    }

    def __init__(self, fin: TextIO, account_id: Optional[str] = None) -> None:
        # Python 3 needed
        super().__init__(fin)
        # Use the BIC code for ASN Bank
        self.statement = Statement(
            bank_id="ASNBNL21", account_id=account_id, currency="EUR"
        )  # My Statement

    def parse(self) -> BaseStatement:
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """

        # Python 3 needed
        stmt: BaseStatement = super().parse()

        # GJP 2020-03-03
        # No need to (re)calculate the balance since there is no history.
        # But set the dates.
        if stmt.lines:
            stmt.start_date = min(sl.date for sl in stmt.lines if sl.date)
            stmt.end_date = max(sl.date for sl in stmt.lines if sl.date)
            # end date is exclusive for OFX
            if stmt.end_date:
                stmt.end_date += datetime.timedelta(days=1)
            Statement.start_balance = stmt.lines[0].start_balance
            Statement.end_balance = stmt.lines[-1].start_balance + stmt.lines[-1].amount

        return stmt

    def split_records(self) -> Iterator[Any]:
        """Return iterable object consisting of a line per transaction"""
        # strip quotes around memo
        return csv.reader(self.fin, delimiter=",", quotechar="'")

    def parse_record(self, line: List[str]) -> Optional[StatementLine]:
        """Parse given transaction line and return StatementLine object"""

        stmt_line: Optional[StatementLine]

        try:
            logger.debug("line #%d: %s", self.cur_record, line)

            stmt_line = self.parse_transaction(line)

        except Exception as e:
            raise ParseError(self.cur_record, str(e)) from None

        return stmt_line

    def parse_transaction(self, line: List[str]) -> Optional[StatementLine]:
        start_balance: int = 8
        transaction_nr: int = 15

        # line[1] contains the account number
        if self.statement.account_id:
            if not self.statement.account_id == line[1]:
                raise ValueError(
                    "Only one account is allowed; previous account: {}, \
this line's account: {}".format(self.statement.account_id, line[1])
                )
        else:
            self.statement.account_id = line[1]

        if line[self.mappings["bank_account_to"]]:
            line[self.mappings["payee"]] = "{} ({})".format(
                line[self.mappings["payee"]], line[self.mappings["bank_account_to"]]
            )
        else:
            line[self.mappings["payee"]] = ""

        # Python 3 needed
        stmt_line: Optional[StatementLine] = super().parse_record(line)

        # Remove zero-value notifications
        if stmt_line is None or stmt_line.amount is None or stmt_line.amount == 0:
            return None

        # The unique id is a combination of 'Journaaldatum' and 'Volgnummer transactie'
        # Let id be <Journaaldatum in yyyymmdd format>.<Volgnummer transactie>
        if not self.mappings["date"] == 11:  # Journaaldatum
            raise ValueError("Journaaldatum must be column 11")
        if not transaction_nr == 15:  # Volgnummer transactie
            raise ValueError(f"transaction_nr ({transaction_nr}) must be 15")

        if not line[self.mappings["date"]]:
            raise ValueError("Journaaldatum is not found")

        dd_mm_yyyy: str = str(line[self.mappings["date"]])
        stmt_line.id = "{}{}{}.{}".format(
            dd_mm_yyyy[6:], dd_mm_yyyy[3:5], dd_mm_yyyy[0:2], line[transaction_nr]
        )

        # We can not use stmt_line.start_balance since that does not exist
        stmt_line.start_balance = (
            Decimal(str(line[start_balance]))
            if line[start_balance] is not None
            else Decimal(0)
        )

        if stmt_line.amount < 0:
            stmt_line.trntype = "DEBIT"
        else:
            stmt_line.trntype = "CREDIT"

        if isinstance(stmt_line.bank_account_to, str) and stmt_line.bank_account_to:
            stmt_line.bank_account_to = BankAccount(
                bank_id="", acct_id=stmt_line.bank_account_to
            )
        else:
            stmt_line.bank_account_to = None

        return stmt_line


class Plugin(BasePlugin):
    """ASN Bank, The Netherlands, CSV (https://www.asnbank.nl/)"""

    def get_parser(self, filename: str) -> Parser:
        p = re.compile("transactie-historie_(NL\\d+ASNB\\d+)_\\d+\\.csv")
        m = p.search(filename)
        account_id: Optional[str] = None
        if m:
            account_id = m.group(1)
        with open(filename, "r") as fin:  # , encoding="ISO-8859-1")
            return Parser(fin, account_id)
