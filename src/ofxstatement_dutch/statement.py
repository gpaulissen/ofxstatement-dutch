# -*- coding: utf-8 -*-
import re
from typing import Set, Union

from ofxstatement.statement import StatementLine as BaseStatementLine
from ofxstatement.statement import Statement as BaseStatement
from ofxstatement.exceptions import ValidationError
from ofxstatement.statement import generate_unique_transaction_id
from datetime import datetime, date
import logging


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _to_date(d_t: Union[date, datetime]) -> date:
    return d_t.date() if isinstance(d_t, datetime) else d_t


class Statement(BaseStatement):
    def assert_valid(self) -> None:

        logger.debug("self: type: %s; contents: %s", type(self), self)
        try:
            super().assert_valid()
            dates = [sl.date for sl in self.lines if sl.date is not None]
            # An ING CSV may be a balance file resulting in 0 lines
            if len(dates) == 0:
                return
            assert self.start_date, "The statement start date should be set"
            assert self.end_date, "The statement end date should be set"
            # check self.start_date
            min_date = _to_date(min(dates))
            start_date = _to_date(self.start_date)
            assert start_date and min_date and start_date <= min_date, \
                "The statement start date ({}) should at most be the smallest \
statement line date ({})".format(start_date, min_date)
            # check self.end_date
            max_date = _to_date(max(dates))
            end_date = _to_date(self.end_date)
            assert end_date and max_date and end_date > max_date, \
                "The statement end date ({}) should be greater than the \
largest statement line date ({})".format(end_date, max_date)
        except Exception as e:
            raise ValidationError(str(e), self)


class StatementLine(BaseStatementLine):
    """Statement line data with an adjust method.
    """
    def adjust(self, unique_id_set: Set[str]) -> None:
        if self.id:
            return

        self.id = \
            generate_unique_transaction_id(self, unique_id_set)
        m = re.match(r'([0-9a-f]+)(-\d+)?$', self.id)
        assert m, "Id should match hexadecimal digits, \
optionally followed by a minus and a counter: '{}'".format(self.id)
        if m.group(2):
            counter = int(m.group(2)[1:])
            # include counter so the memo gets unique
            self.memo = self.memo + ' #' + str(counter + 1)  # type: ignore
