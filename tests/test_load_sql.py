"""Exercise the real loader with CSV fixtures and a recording SQL connection."""
from __future__ import annotations
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import pandas as pd

# The offline tests never connect to SQL Server. Keep them usable without ODBC.
try:
    import pyodbc
except ImportError:
    pyodbc = types.ModuleType('pyodbc')
    pyodbc.Error = type('Error', (Exception,), {})
    sys.modules['pyodbc'] = pyodbc

PROJECT = Path(os.environ.get('WALMART_PROJECT_ROOT', Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location('walmart_load_sql', PROJECT / 'python' / 'load_sql.py')
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)

FACT_COLUMNS = ['Store', 'Dept', 'Date', 'DateKey', 'ActualSales', 'IsHoliday',
                'Temperature', 'FuelPrice', 'MarkDown1', 'MarkDown2', 'MarkDown3',
                'MarkDown4', 'MarkDown5', 'MarkDownTotal', 'CPI', 'Unemployment',
                'PlanSales', 'ForecastSales', 'ForecastMethod']

class RecordingCursor:
    def __init__(self):
        self.inserts = []
        self.queries = []
        self.fast_executemany = False
    def executemany(self, sql, rows):
        # The SQL destination contract is FuelPrice, unlike the input CSV.
        if 'dbo.FactWeeklySales' in sql and '[Fuel_Price]' in sql:
            raise ValueError('Invalid column name Fuel_Price')
        self.inserts.append((sql, list(rows)))
    def execute(self, sql):
        self.queries.append(sql)
        return self
    def fetchone(self):
        return (2, 30.0)

class RecordingConnection:
    def __init__(self):
        self.recording_cursor = RecordingCursor()
        self.closed = False
    def cursor(self):
        return self.recording_cursor
    def close(self):
        self.closed = True

class LoaderTests(unittest.TestCase):
    def test_main_maps_csv_fuel_price_to_schema_and_preserves_row_values(self):
        with tempfile.TemporaryDirectory(dir=PROJECT) as folder:
            root = Path(folder)
            pd.DataFrame([{'Store': 1, 'StoreType': 'A', 'StoreSize': 150000}]).to_csv(root / 'dim_store.csv', index=False)
            pd.DataFrame([{'Dept': 2}]).to_csv(root / 'dim_department.csv', index=False)
            pd.DataFrame([{'DateKey': 20120106, 'Date': '2012-01-06', 'Year': 2012, 'Quarter': 'Q1', 'MonthNumber': 1, 'MonthName': 'January', 'WeekOfYear': 1, 'WeekEndingFriday': '2012-01-06'}]).to_csv(root / 'dim_date.csv', index=False)
            row = {column: 0 for column in FACT_COLUMNS}
            row.pop('FuelPrice')
            row.update(Store=1, Dept=2, Date='2012-01-06', DateKey=20120106,
                       ActualSales=10.0, Fuel_Price=3.125, ForecastMethod='Seasonal naive')
            other = dict(row, Date='2012-01-13', DateKey=20120113,
                         ActualSales=20.0, Fuel_Price=None)
            pd.DataFrame([row, other]).to_csv(root / 'fact_weekly_sales.csv', index=False)
            master, database = RecordingConnection(), RecordingConnection()
            args = types.SimpleNamespace(server='offline-test', driver='offline-test')
            with patch.object(loader, 'PROCESSED_DIR', root), patch.object(loader, 'parse_args', return_value=args), patch.object(loader, 'connect', side_effect=[master, database]), patch.object(loader, 'execute_script') as scripts, contextlib.redirect_stdout(io.StringIO()) as output:
                loader.main()
            writes = database.recording_cursor.inserts
            self.assertEqual(len(writes), 4)
            sql, values = writes[-1]
            self.assertIn('[FuelPrice]', sql)
            self.assertNotIn('[Fuel_Price]', sql)
            self.assertEqual(values[0][FACT_COLUMNS.index('FuelPrice')], 3.125)
            self.assertIsNone(values[1][FACT_COLUMNS.index('FuelPrice')])
            self.assertEqual([v[FACT_COLUMNS.index('ActualSales')] for v in values], [10.0, 20.0])
            self.assertEqual(scripts.call_count, 2)
            self.assertTrue(master.closed and database.closed)
            self.assertIn('Loaded 2 fact rows', output.getvalue())

    def test_insert_dataframe_keeps_all_rows_across_batch_boundary(self):
        connection = RecordingConnection()
        frame = pd.DataFrame({'Dept': range(5001)})
        loader.insert_dataframe(connection, 'DimDepartment', frame, ['Dept'])
        batches = connection.recording_cursor.inserts
        self.assertEqual([len(rows) for _, rows in batches], [5000, 1])
        self.assertEqual(batches[0][1][0], (0,))
        self.assertEqual(batches[1][1][-1], (5000,))

if __name__ == '__main__':
    unittest.main()
