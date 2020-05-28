#!/usr/bin/env python3
# pylint: disable=C0111

from typing import Callable, Dict, List, Union

from bs4 import BeautifulSoup

StrConverter = Callable[[str], str]


def extract_text_from_html(html: str, selector: str) -> Union[str, None]:
  soup = BeautifulSoup(html, 'html5lib')
  selected: BeautifulSoup = soup.select_one(selector)
  if not selected:
    return

  return selected.get_text()


def parse_table(
  html: str,
  table_selector: str,
  header_replacements: Dict[str, str] = None,
  header_converters: List[StrConverter] = None,
  val_converters: List[StrConverter] = None,
  row_data_predicate: Callable[[dict], bool] = None
) -> List[dict]:
  soup = BeautifulSoup(html, 'html5lib')
  table: BeautifulSoup = soup.select_one(table_selector)
  if not table:
    return None

  table_headers = _find_table_headers(table, header_replacements, header_converters)
  rows = _find_table_rows(table)
  results: List[dict] = []
  for row in rows:
    if not table_headers:
      table_headers = _parse_header_row(row, header_replacements, header_converters)
      continue

    table_data = row.find_all('td')
    if table_data:
      row_data = {}
      for idx, data in enumerate(table_data):
        header = table_headers.get(idx)
        if not header:
          continue

        val: str = data.get_text().strip()
        if val_converters:
          for val_converter in val_converters:
            val = val_converter(val)

        if val:
          row_data[header] = val

      if row_data_predicate and not row_data_predicate(row_data):
        continue

      results.append(row_data)

  return results


def _find_table_headers(table: BeautifulSoup, header_replacements: Dict[str, str], header_converters: List[StrConverter]) -> Dict[int, str]:
  header_row = table.select_one('thead > tr')
  if not header_row:
    return None

  return _parse_header_row(header_row, header_replacements, header_converters)


def _find_table_rows(table: BeautifulSoup) -> List[BeautifulSoup]:
  tbody: BeautifulSoup = table.select_one('tbody')
  if tbody:
    return tbody.find_all('tr')

  return table.find_all('tr')


def _parse_header_row(header_row: BeautifulSoup, header_replacements: Dict[str, str], header_converters: List[StrConverter]) -> Dict[int, str]:
  header_cols: BeautifulSoup = header_row.select('td, th')
  if not header_cols:
    return None

  table_headers = {}
  found_headers = []
  for idx, header_elem in enumerate(header_cols):
    header = header_elem.get_text().strip()

    if not header:
      continue

    if header in found_headers:
      header_vers = 2
      new_header = header + str(header_vers)
      while new_header in found_headers:
        header_vers += 1
        new_header = header + str(header_vers)
        if header_vers >= 100:
          raise Exception("Too many duplicate headers: header=%s new_header=%s header_vers=%s" % (header, new_header, header_vers))

      header = new_header

    found_headers.append(header)

    if header_replacements:
      header = header_replacements.get(header)

    if header_converters:
      for header_converter in header_converters:
        header = header_converter(header)

      if not header:
        continue

    table_headers[idx] = header

  return table_headers


def _main():
  import sys

  method_params = []
  for arg in sys.argv[2:]:
    if arg == '--':
      method_params.append(sys.stdin.read())
    else:
      method_params.append(arg)

  result = globals()[sys.argv[1]](*method_params)
  if result is not None:
    print(result)


if __name__ == "__main__":
  try:
    _main()
  except KeyboardInterrupt:
    exit(130)
