"""
ssie a module for a Simple SpreadSheet Importer/Exporter.
"""

import importlib
import pathlib
from . import parse_nested_dict

NOT_SUPPORTED = '{filepath} is not supported'
DEFAULT_SHEET = 'Sheet1'


class FileType:
    """
    Enumeration of supported file types for spreadsheet I/O.
    """
    CSV = '.csv'
    XLS = '.xls'
    XLSX = '.xlsx'
    JSON = '.json'


class SpreadSheet:
    """
    Represents a simple spreadsheet consisting of column headers and row data.

    Provides methods to export to .csv, .xls, and .xlsx formats,
    and to manipulate or extract data from the sheet.
    """

    def __init__(self, data: list[list], columns: list[str]):
        """
        Initialize a new SpreadSheet instance.

        :param data: List of row data (each row is a list of values).
        :param columns: List of column names.
        """
        self.columns = columns
        self.data = data

    def to_file(self, filepath: str) -> None:
        """
        Export the spreadsheet to a file.

        Supported formats: .csv, .xls, .xlsx.
        Ensure that the required libraries are installed:
          - `xlwt` for .xls
          - `openpyxl` for .xlsx

        :param filepath: Destination file path including extension.
        :raises ValueError: If file extension is unsupported.
        """
        path = pathlib.Path(filepath)
        match path.suffix.lower():
            case FileType.CSV:
                self.to_csv(filepath)
            case FileType.XLS:
                self.to_xls(filepath)
            case FileType.XLSX:
                self.to_xlsx(filepath)
            case FileType.JSON:
                self.to_json(filepath)
            case _:
                raise ValueError(NOT_SUPPORTED.format(filepath=filepath))

    def to_csv(self, filepath: str):
        """
        Export the spreadsheet as a CSV file.

        :param filepath: Destination .csv file path.
        """
        import csv
        with open(filepath, mode='w', newline='', encoding='utf8') as file:
            writer = csv.writer(file)
            if self.columns:
                writer.writerow(self.columns)
            writer.writerows(self.data)

    def to_xls(self, filepath: str):
        """
        Export the spreadsheet as a legacy Excel (.xls) file.

        Requires: `xlwt` package.

        :param filepath: Destination .xls file path.
        """
        xlwt = importlib.import_module('xlwt')
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet(DEFAULT_SHEET)

        row_to_start = 0
        if self.columns:
            for col_idx, col_name in enumerate(self.columns):
                sheet.write(0, col_idx, col_name)
            row_to_start = 1

        for row_idx, row in enumerate(self.data, start=row_to_start):
            for col_idx, value in enumerate(row):
                sheet.write(row_idx, col_idx, value)

        workbook.save(filepath)

    def to_xlsx(self, filepath: str):
        """
        Export the spreadsheet as an Excel .xlsx file.

        Requires: `openpyxl` package.

        :param filepath: Destination .xlsx file path.
        """
        openpyxl = importlib.import_module('openpyxl')
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = DEFAULT_SHEET

        if self.columns:
            sheet.append(self.columns)

        for row in self.data:
            sheet.append(row)

        font = openpyxl.styles.Font()  # The default font has a hardcoded color
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cell.font = font

        workbook.save(filepath)

    def to_json(self, filepath: str):
        """
        Export to .json file.

        :param filepath: Destination .json file path.
        """
        import json
        # Create a list of dictionaries for each row, using column names as keys
        dict_data = [
            {self.columns[i]: row[i] for i in range(len(self.columns))}
            for row in self.data
        ]
        with open(filepath, 'w') as f:
            json.dump(dict_data, f, indent=2)

    def to_dict_records(self) -> list[dict]:
        """
        Returns a list of dicts, each dict containing the columns as keys.

        :return: List of dicts representing rows.
        """
        result = []
        for row in self.data:
            record = {self.columns[i]: cell for i, cell in enumerate(row)}
            result.append(record)
        return result

    def get_column(self, name: str) -> list:
        """
        Extract a single column by name.

        :param name: Column header name.
        :return: List of values in the specified column.
        """
        col = self.columns.index(name)
        result = [row[col] for row in self.data]
        return result

    def __len__(self) -> int:
        """
        Return the number of data rows in the spreadsheet.
        """
        return len(self.data)

    def __repr__(self):
        """
        Developer-friendly string representation.
        """
        return f'SpreadSheet(columns={self.columns}, rows={self.data[:3]}...)'


def read_file(filepath: str, has_columns=True) -> SpreadSheet:
    """
    Import a spreadsheet file (.csv, .xls, or .xlsx) into a SpreadSheet object.

    Required packages:
      - `xlrd` for .xls
      - `openpyxl` for .xlsx

    :param filepath: Path to the file.
    :param has_columns: If True, the first row is treated as column headers.
    :return: SpreadSheet instance.
    :raises ValueError: If file extension is unsupported.
    """
    path = pathlib.Path(filepath)
    match path.suffix.lower():
        case FileType.CSV:
            return import_csv(filepath, has_columns)
        case FileType.XLS:
            return import_xls(filepath, has_columns)
        case FileType.XLSX:
            return import_xlsx(filepath, has_columns)
        case FileType.JSON:
            return import_json(filepath)
        case _:
            raise ValueError(NOT_SUPPORTED.format(filepath=filepath))


def import_csv(filepath: str, has_columns=True) -> SpreadSheet:
    """
    Import a CSV file into a SpreadSheet object.

    :param filepath: Path to the .csv file.
    :param has_columns: If True, treats the first row as headers.
    :return: SpreadSheet instance.
    """
    import csv
    with open(filepath, newline='', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile)

        if has_columns:
            columns = next(reader)
        else:
            columns = []

        data = [row for row in reader]
        return SpreadSheet(data, columns)


def import_xls(filepath: str, has_columns=True) -> SpreadSheet:
    """
    Import a legacy Excel (.xls) file into a SpreadSheet object.

    Requires: `xlrd` package.

    :param filepath: Path to the .xls file.
    :param has_columns: If True, treats the first row as headers.
    :return: SpreadSheet instance.
    """
    xlrd = importlib.import_module('xlrd')
    book = xlrd.open_workbook(filepath)
    sheet = book.sheet_by_index(0)

    row_to_start = 0
    if has_columns:
        columns = [sheet.cell_value(0, col) for col in range(sheet.ncols)]
        row_to_start = 1
    else:
        columns = []

    data = []
    for row_idx in range(row_to_start, sheet.nrows):
        row = [sheet.cell_value(row_idx, col) for col in range(sheet.ncols)]
        data.append(row)

    return SpreadSheet(data=data, columns=columns)


def import_xlsx(filepath: str, has_columns=True) -> SpreadSheet:
    """
    Import a modern Excel (.xlsx) file into a SpreadSheet object.

    Requires: `openpyxl` package.

    :param filepath: Path to the .xlsx file.
    :param has_columns: If True, treats the first row as headers.
    :return: SpreadSheet instance.
    """
    openpyxl = importlib.import_module('openpyxl')
    workbook = openpyxl.load_workbook(filename=filepath, data_only=True)
    sheet = workbook.active

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return SpreadSheet(data=[], columns=[])

    row_to_start = 0
    if has_columns:
        columns = list(rows[0])
        row_to_start = 1
    else:
        columns = []

    data = [list(row) for row in rows[row_to_start:]]

    return SpreadSheet(data=data, columns=columns)


def import_json(filepath: str) -> SpreadSheet:
    """
    Import a JSON file into a SpreadSheet object.

    Requires: `json` module and `from_nested_dict` function.

    :param filepath: Path to the JSON file.
    :return: SpreadSheet instance containing the parsed data.
    """
    import json
    with open(filepath) as f:
        return from_nested_dict(json.load(f))


def from_records(data: list[dict]) -> SpreadSheet:
    """
    Create a SpreadSheet object from a list of dictionaries.

    Each dictionary should represent a row, using column names as keys.

    :param data: List of dictionaries.
    :return: SpreadSheet instance.
    """
    if not data:
        return SpreadSheet(data=[], columns=[])
    columns = list(data[0].keys())
    rows = [list(d.values()) for d in data]
    return SpreadSheet(data=rows, columns=columns)


def from_nested_dict(nested_dict: list[dict], repeat_when_flattening=False) -> SpreadSheet:
    """
    Convert a nested dictionary (like JSON) to a flat SpreadSheet.

    >>> input = [
         {
             'ColA': 'ValueA1',
             'Nested': [
                 {'ColB': 'ValueB1', 'ColC': 'ValueC1'},
                 {'ColB': 'ValueB2', 'ColC': 'ValueC2'}
             ]
         },
         {
             'ColA': 'newA',
             'Nested': [
                 {'ColB': 'newB', 'ColC': 'newC'}
             ]
         }
     ]
    >>> from_nested_dict(input)
    SpreadSheet(columns=['ColA', 'ColB', 'ColC'], rows=[['ValueA1', 'ValueB1', 'ValueC1'], ['ValueA1', 'ValueB2', 'ValueC2'], ['newA', 'newB', 'newC']]...)
    """
    columns = parse_nested_dict.get_columns(nested_dict[0])
    data = parse_nested_dict.parse_matrix(nested_dict, columns, repeat_when_flattening)
    return SpreadSheet(data, columns)
