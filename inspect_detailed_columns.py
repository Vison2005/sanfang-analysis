
import pandas as pd
import os

file = '10月福州三坊七巷店报表（袁、林）.xlsx'
# Check both potential sheets
sheets = ['三坊七巷管理费用', '三坊七巷成本费用详记']

if os.path.exists(file):
    xl = pd.ExcelFile(file)
    print(f"Sheets: {xl.sheet_names}")
    
    for sheet in sheets:
        if sheet in xl.sheet_names:
            print(f"\n--- Inspecting {sheet} ---")
            df = pd.read_excel(file, sheet_name=sheet, header=None)
            print(df.iloc[:20, :].to_string())
