#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


import numbers

from xlsxwriter import Workbook

from iocbio.gel.repository.export_repository import ExportRepository


class XlsWriter:
    def __init__(self, repository: ExportRepository):
        self.repository = repository
        self.workbook = None
        self.header_format = None

    def write(self, file_path: str):
        self.workbook = Workbook(file_path)
        self.header_format = self.workbook.add_format({"bold": True})

        self._write("Gels", *self.repository.fetch_gels())
        self._write("Measurement Types", *self.repository.fetch_measurement_types())
        self._write("Gel Lanes", *self.repository.fetch_gel_lanes())
        self._write("Images", *self.repository.fetch_images())
        self._write("Measurements (raw)", *self.repository.fetch_measurements_raw())
        self._write("Reference Measurement", *self.repository.fetch_measurements_reference())
        self._write("Measurements (normalized)", *self.repository.fetch_measurements_relative())

        self.workbook.close()

    def _write(self, wname, keys, entries):
        sheet = self.workbook.add_worksheet(wname)

        for col, key in enumerate(keys):
            sheet.write(0, col, key, self.header_format)

        for row, entry in enumerate(entries):
            for col, value in enumerate(entry):
                value = value if isinstance(value, numbers.Number) else str(value)
                sheet.write(row + 1, col, value)
