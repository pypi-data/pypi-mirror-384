ERROR = 'Input must be a list of dictionaries with a mix of strings and nested lists of dictionaries.'


class SSIENestedDictStructureError(Exception):
    """Exception raised when the input nested dict has an inconsistent structure."""
    pass


def get_columns(first_row: dict) -> list[str]:
    columns = []
    for key, value in first_row.items():
        if isinstance(value, str):
            columns.append(key)
        elif isinstance(value, list):
            cs = get_columns(value[0])
            columns.extend(cs)
        else:
            raise SSIENestedDictStructureError(ERROR)
    return columns


def parse_matrix(json_data: list[dict], columns: list[str], repeat_when_flattening=False) -> list:
    data = []
    for row in json_data:
        data_row_dict = {}
        for key, value in row.items():
            if isinstance(value, str):
                if key in columns:
                    data_row_dict[key] = value
                else:
                    raise SSIENestedDictStructureError(
                        f'Wrong structure in column: "{key}"')
            elif isinstance(value, list):
                # Checks that only str and list are present,
                # if not then the next line will catch the error
                pass
            else:
                raise SSIENestedDictStructureError(ERROR)

        has_list = False
        for key, value in row.items():
            if isinstance(value, list):
                has_list = True
                remaining_columns = [
                    c for c in columns if c not in data_row_dict]
                matrix = parse_matrix(value, remaining_columns)
                cloned_data_row_dict = data_row_dict.copy()
                for ma_row in matrix:
                    for ma_index, ma_col in enumerate(remaining_columns):
                        cloned_data_row_dict[ma_col] = ma_row[ma_index]
                    data_row = []
                    for col in columns:
                        data_row.append(cloned_data_row_dict[col])
                    data.append(data_row)
                    if not repeat_when_flattening:
                        cloned_data_row_dict = {key: '' for key in data_row_dict}
        if not has_list:
            data_row = []
            for col in columns:
                data_row.append(data_row_dict[col])
            data.append(data_row)
    return data
