import math
from datetime import datetime

import pandas as pd
from PyQt6.QtCore import QDate, QDateTime, QTime
from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QDateEdit


class QuarterEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps_new = 3
        self.separator = ' - Q'
        self.setDisplayFormat('yyyy{0}MM')

        self.setDate(datetime.now())

    def dateTimeFromText(self, text: str | None) -> QDateTime:

        year, month = self._stringToDate(text=text)

        add_months = math.ceil((month - 1) * 3)

        date = QDateTime(QDate(year, 1, 1).addMonths(add_months), QTime(self.time()))

        return date

    def textFromDateTime(self, dt: QDateTime | datetime) -> str:
        # derive the quarter from the current date time value and display it

        year = dt.date().year()
        month = dt.date().month()

        quarter = math.ceil(month / 3)

        return f"{year}{self.separator}{quarter:0>1}"

    def stepBy(self, steps: int) -> None:
        if self.currentSection() == QDateEdit.Section.MonthSection:  # custom stepping for the month section to account for quarter
            steps = self.steps_new * steps
            date = self.date()
            self.setDate(date.addMonths(steps))

        else:
            super().stepBy(steps)

    def stepEnabled(self) -> QDateEdit.StepEnabledFlag:
        if self.currentSection() == QDateEdit.Section.MonthSection:
            date = self.date()
            flag = QDateEdit.StepEnabledFlag.StepNone

            if date.month() < 10:  # enable stepping only if Quarter < Q4
                flag = QDateEdit.StepEnabledFlag.StepUpEnabled

            if date.month() > 3:  # enable stepping only if Quarter > Q1
                flag |= QDateEdit.StepEnabledFlag.StepDownEnabled

            return flag

        else:
            return super().stepEnabled()

    def validate(self, input: str | None, pos: int):
        # user input validation
        year_str = False

        year, month = self._stringToDate(text=input)

        new_date = QDate(year, 1, 1).addMonths(month - 1)

        has_separator = input.count(self.separator) == 1
        range_valid = self.minimumDate() < new_date and new_date < self.maximumDate()
        month_in_range = month <= 4

        if has_separator and month_in_range and range_valid:
            state = QValidator.State.Acceptable

        elif has_separator and year_str and len(year_str) < 4:
            state = QValidator.State.Intermediate

        else:
            state = QValidator.State.Intermediate

        return state, input, pos

    def getQuarterLimits(self) -> tuple[datetime, datetime]:
        """Get endpoints of the quarter range, return tuple of the start, end dates"""

        start_date = pd.date_range(end=pd.to_datetime(self.date().toPyDate()), periods=1, freq='QS').date[0]
        end_date = (pd.date_range(start=pd.to_datetime(self.date().toPyDate()), periods=1,
                                  freq='QE') + pd.tseries.offsets.DateOffset(days=1)).date[0]

        return start_date, end_date

    def getYearQuarter(self) -> str:
        """Convert date into string formatted as YYYYQQ"""
        return f'{self.date().year()}Q{self.getQuarter()}'

    def getQuarter(self) -> int:
        """Convert date into integer of quarter"""
        return pd.to_datetime(self.date().toPyDate()).quarter

    def getYQ(self) -> tuple[int, int]:
        """Convert date into tuple of (year,quarter)"""
        return pd.to_datetime(self.date().toPyDate()).year, pd.to_datetime(self.date().toPyDate()).quarter

    def _stringToDate(self, text) -> tuple[int, int]:

        try:
            year_str, month_str = text.split(self.separator)
            month, year = int(month_str), int(year_str)
        except ValueError:
            year, month = 1, 1

        return year, month
