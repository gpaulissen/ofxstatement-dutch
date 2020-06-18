# -*- coding: utf-8 -*-
import re
from typing import Set

from ofxstatement import statement
from ofxstatement.exceptions import ValidationError
from ofxstatement.statement import generate_unique_transaction_id


class Statement(statement.Statement):
    def assert_valid(self) -> None:
        try:
            super().assert_valid()
            assert self.end_date, "The statement end date should be set"
            min_date = min(sl.date for sl in self.lines)
            max_date = max(sl.date for sl in self.lines)
            assert self.start_date <= min_date,\
                "The statement start date ({}) should at most the smallest \
statement line date ({})".format(self.start_date, min_date)
            assert self.end_date > max_date,\
                "The statement end date ({}) should be greater than the \
largest statement line date ({})".format(self.end_date, max_date)
        except Exception as e:
            raise ValidationError(str(e), self)


class StatementLine(statement.StatementLine):
    """Statement line data with an adjust method.
    """
    def adjust(self, unique_id_set: Set[str]) -> None:
        if self.id:  # type: ignore
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
