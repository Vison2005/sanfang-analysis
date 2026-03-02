import pandas as pd
import os
import glob

print("Script started.")

# Use glob to find files to ensure we have correct paths
# Files seem to be in parent or sibling folder now?
# Based on LS, they are in ../AnalyzeWeb
import os
files_found = []
search_dirs = [".", "../AnalyzeWeb"]
for d in search_dirs:
    if os.path.exists(d):
        files = glob.glob(os.path.join(d, "*.xlsx"))
        files_found.extend(files)

print(f"Files found: {files_found}")

# Configuration
FILES_MAPPING = [
    {
        'pattern': '10月福州三坊七巷店报表',
        'months': ['8月', '9月'],
        'year': 2025,
        'profit_sheet': '三坊七巷利润表',
        'cost_sheet': '三坊七巷成本费用详记'
    },
    {
        'pattern': '福州三坊七巷店-25.12报表',
        'months': ['10月', '11月', '12月'],
        'year': 2025,
        'profit_sheet': '三坊七巷利润表',
        'cost_sheet': '三坊七巷管理费用'
    },
    {
        'pattern': '三坊七巷-2026.01报表',
        'months': ['1月'],
        'year': 2026,
        'profit_sheet': '三坊七巷利润表',
        'cost_sheet': '三坊七巷管理费用'
    }
]

# Helper to find real filename from pattern
def find_file(pattern):
    for f in files_found:
        basename = os.path.basename(f)
        if pattern in basename:
            return f
    return None

# Mapping of Output Columns to Row Keywords
PROFIT_MAP = {
    '总营收': ['一、主营收入', '主营收入'],
    '到店收入': ['到店收入'],
    '抖音收入': ['抖音收入'],
    '美团收入': ['美团收入'],
    '大众点评收入': ['大众点评收入'],
    '主营业务成本': ['二、主营业务成本', '主营业务成本'],
    '酒水成本': ['减：酒水成本', '酒水成本'],
    '毛利': ['三、主营业务利润', '主营业务利润', '毛利'],
    '营销费用': ['减：销售费用', '销售费用'],
    '管理费用': ['管理费用'],
    '财务费用': ['财务费用'],
    '净利润': ['六、净利润', '净利润', '五、净利润']
}

COST_MAP = {
    '人工成本': ['店内人员工资', '分摊人员工资', '外包财务人员工资', '工资', '人员工资'],
    '房租水电': ['物业水电费', '房屋租金', '房租', '水电']
}

# Detailed Cost Mapping for new requirements
COST_DETAIL_MAP = {
    '物业水电': ['物业水电费'],
    '店内工资': ['店内人员工资'],
    '分摊工资总额': ['分摊人员工资'],
    '日常采购成本': ['日常采购'],
    '其他成本': ['其他支出', '雇主责任险分摊'], # Removed '房屋租金' from here
    '房租成本': ['房屋租金', '房租'], # New category
    '运营备用金均摊': ['团建分摊'],
    '财务费用均摊': ['外包财务人员工资'],
    '运营工资': ['运营人员工资'] # Special handling to find this specific row
}

# New map for detailed personnel wages
PERSONNEL_MAP = {
    '李宗生': ['李宗生'],
    '艾晓川': ['艾晓川'],
    '郑昊灵': ['郑昊灵', '郑炅灵'], # Handle potential typo
    '黄尧': ['黄尧'],
    '涂友其': ['涂友其'],
    '岳籽歧': ['岳籽歧'],
    '李小琴': ['李小琴'],
    '罗宇': ['罗宇'],
    '车逸清': ['车逸清'],
    '林怡': ['林怡']
}

all_data = []

def find_header_row(df, keyword='项目'):
    for idx, row in df.iterrows():
        for val in row.values:
            if isinstance(val, str) and keyword in val:
                return idx
    return None

for entry in FILES_MAPPING:
    real_file = find_file(entry['pattern'])
    if not real_file:
        print(f"Skipping pattern {entry['pattern']} (File not found)")
        continue
        
    print(f"Processing {real_file} for months {entry['months']}...")
    
    try:
        # Read Profit Sheet
        df_profit = pd.read_excel(real_file, sheet_name=entry['profit_sheet'], header=None)
        header_idx = find_header_row(df_profit)
        
        if header_idx is not None:
            # Set columns from header row
            df_profit.columns = df_profit.iloc[header_idx]
            # Strip whitespace from columns
            df_profit.columns = df_profit.columns.astype(str).str.strip()
            df_profit = df_profit.iloc[header_idx+1:]
            
            # Find '项目' column
            proj_col = None
            for c in df_profit.columns:
                if '项目' in str(c):
                    proj_col = c
                    break
            
            if not proj_col:
                print("  '项目' column not found.")
                continue

            for month in entry['months']:
                if month in df_profit.columns:
                    print(f"  Extracting {month}...")
                    row_data = {}
                    
                    # Date
                    month_num = int(month.replace('月', ''))
                    date_str = f"{entry['year']}-{month_num:02d}-01"
                    row_data['月份'] = date_str
                    
                    # Profit Metrics
                    for field, keywords in PROFIT_MAP.items():
                        val = 0
                        for kw in keywords:
                            # Filter rows where Project Column contains keyword
                            match = df_profit[df_profit[proj_col].astype(str).str.contains(kw, na=False)]
                            if not match.empty:
                                raw_val = match.iloc[0][month]
                                if pd.notna(raw_val):
                                    val = raw_val
                                break
                        row_data[field] = val
                    
                    # Cost Detail
                    try:
                        df_cost = pd.read_excel(real_file, sheet_name=entry['cost_sheet'], header=None)
                        cost_header_idx = find_header_row(df_cost)
                        if cost_header_idx is not None:
                            # Create a clean version for column mapping
                            df_cost_clean = df_cost.copy()
                            df_cost_clean.columns = df_cost_clean.iloc[cost_header_idx]
                            df_cost_clean.columns = df_cost_clean.columns.astype(str).str.strip()
                            df_cost_clean = df_cost_clean.iloc[cost_header_idx+1:]
                            
                            # Find Project col in cost sheet
                            cost_proj_col = None
                            for c in df_cost_clean.columns:
                                if '项目' in str(c):
                                    cost_proj_col = c
                                    break
                                    
                            if cost_proj_col and month in df_cost_clean.columns:
                                # Extract Detailed Costs
                                detailed_values = {k: 0 for k in COST_DETAIL_MAP.keys()}
                                personnel_values = {k: 0 for k in PERSONNEL_MAP.keys()}
                                
                                # Iterate over all rows to find matches, including duplicate names if any
                                # But we need to be careful with '运营人员工资' which might be in breakdown
                                # We'll scan the whole sheet (df_cost_clean)
                                
                                for _, r in df_cost_clean.iterrows():
                                    item_name = str(r[cost_proj_col])
                                    
                                    # Skip empty or nan
                                    if item_name == 'nan' or not item_name.strip():
                                        continue
                                    
                                    val = r[month]
                                    if not (pd.notna(val) and isinstance(val, (int, float))):
                                        continue
                                        
                                    for key, keywords in COST_DETAIL_MAP.items():
                                        for kw in keywords:
                                            if kw in item_name:
                                                # Special case for '运营人员工资' - it appears in breakdown
                                                # If we are matching '分摊人员工资', we want the main row (usually top)
                                                # Logic: accumulate all matches?
                                                # '分摊人员工资' is usually a total. '运营人员工资' is a sub-item.
                                                # If we sum blindly, we might double count if '运营' is not in '分摊' but separate?
                                                # In the file, '分摊' is at top. '运营' is below in detail.
                                                # We should probably use the LAST match or FIRST match?
                                                # Let's sum them for now, but for '分摊' vs '运营', '分摊' is the parent.
                                                # We will handle '区店费用' calculation later.
                                                detailed_values[key] = val # Overwrite or Sum? 
                                                # For '房屋租金' and '其他', we might have multiple.
                                                if key == '其他成本':
                                                    detailed_values[key] += val
                                                    # Fix: Don't double count if we overwrite. 
                                                    # Let's change logic to += for everything, but clear first.
                                                    # Actually, '店内人员工资' is one row. '分摊' is one row.
                                                    # '运营人员工资' is one row.
                                                    # Let's just use the values found.
                                                else:
                                                    # For specific unique rows like Wages, use the value found.
                                                    # If multiple found (e.g. Total and Detail), we might have issues.
                                                    # '分摊人员工资' appears once as total.
                                                    # '运营人员工资' appears once in detail.
                                                    detailed_values[key] = val
                                                break
                                        
                                        # Check Personnel Wages
                                        for key, keywords in PERSONNEL_MAP.items():
                                            for kw in keywords:
                                                if kw in item_name:
                                                    personnel_values[key] = val
                                                    break
                                
                                # Fix for Other Costs accumulation (since we did = val above for non-others)
                                # Actually, let's refine:
                                # 1. Reset
                                for k in detailed_values: detailed_values[k] = 0
                                for k in personnel_values: personnel_values[k] = 0
                                
                                for _, r in df_cost_clean.iterrows():
                                    item_name = str(r[cost_proj_col])
                                    if item_name == 'nan' or not item_name.strip(): continue
                                    val = r[month]
                                    if not (pd.notna(val) and isinstance(val, (int, float))): continue
                                    
                                    # Check each category
                                    for key, keywords in COST_DETAIL_MAP.items():
                                        is_match = False
                                        for kw in keywords:
                                            if kw == item_name or (key == '其他成本' and kw in item_name):
                                                is_match = True
                                                break
                                        
                                        if is_match:
                                            if key == '其他成本':
                                                detailed_values[key] += val
                                            else:
                                                detailed_values[key] = val
                                    
                                    # Check Personnel Wages
                                    for key, keywords in PERSONNEL_MAP.items():
                                        for kw in keywords:
                                            if kw in item_name:
                                                personnel_values[key] = val
                                                break
                                                
                                # Assign to row_data
                                row_data['物业水电'] = detailed_values['物业水电']
                                row_data['店内工资'] = detailed_values['店内工资']
                                row_data['日常采购成本'] = detailed_values['日常采购成本']
                                row_data['房租成本'] = detailed_values['房租成本']
                                row_data['其他成本'] = detailed_values['其他成本']
                                row_data['运营备用金均摊'] = detailed_values['运营备用金均摊']
                                row_data['财务费用均摊'] = detailed_values['财务费用均摊']
                                row_data['运营工资'] = detailed_values['运营工资']
                                
                                # Add Personnel Wages to row_data
                                for k, v in personnel_values.items():
                                    row_data[k] = v
                                
                                # Calculate District Expense (区店费用)
                                # 区店费用 = 分摊工资总额 - 运营工资
                                # Note: If 运营工资 is 0 (not found), then 区店费用 = 分摊工资总额
                                row_data['区店费用'] = detailed_values['分摊工资总额'] - detailed_values['运营工资']
                                
                                # Legacy support (keep these for compatibility if needed, or update)
                                row_data['人工成本'] = detailed_values['店内工资'] + detailed_values['分摊工资总额'] + detailed_values['财务费用均摊']
                                row_data['房租水电'] = detailed_values['物业水电'] + detailed_values['其他成本'] # Rent is in Other
                                
                    except Exception as e:
                        print(f"    Cost sheet error: {e}")
                    
                    # Map Profit Sheet items to new columns
                    row_data['物料采购成本'] = row_data.get('主营业务成本', 0)
                    row_data['银行费用'] = row_data.get('财务费用', 0)
                    
                    # Recalculate Total Expense based on new breakdown to be safe?
                    # Total = Property + In-Store Wage + District + Daily Proc + Material + Other + Reserve + Financial + Operation Wage + Bank
                    # Wait, 'Material' (COGS) is NOT usually part of 'Total Expense' (Opex).
                    # Net Profit = Revenue - COGS - Expenses.
                    # So Total Expense should EXCLUDE Material.
                    # Total Expense = Property + In-Store Wage + District + Daily Proc + Other + Reserve + Financial + Operation Wage + Bank
                    
                    row_data['总费用'] = (
                        row_data.get('物业水电', 0) + 
                        row_data.get('店内工资', 0) + 
                        row_data.get('区店费用', 0) + 
                        row_data.get('日常采购成本', 0) + 
                        row_data.get('房租成本', 0) + 
                        row_data.get('其他成本', 0) + 
                        row_data.get('运营备用金均摊', 0) + 
                        row_data.get('财务费用均摊', 0) + 
                        row_data.get('运营工资', 0) + 
                        row_data.get('银行费用', 0) +
                        row_data.get('营销费用', 0) # Don't forget this from Profit Sheet
                    )
                    
                    all_data.append(row_data)
                else:
                    print(f"  Month {month} not in columns: {df_profit.columns.tolist()}")
        else:
            print("  Header row not found.")

    except Exception as e:
        print(f"Error processing {real_file}: {e}")

# Save
if all_data:
    df_out = pd.DataFrame(all_data)
    # Fill missing cols with 0
    OUTPUT_COLUMNS = [
        '月份', '总营收', '到店收入', '抖音收入', '美团收入', '大众点评收入',
        '物料采购成本', '主营业务成本', '酒水成本', '食材成本',
        '毛利',
        '总费用', 
        '物业水电', '店内工资', '区店费用', '日常采购成本', 
        '房租成本', '其他成本', '运营备用金均摊', '财务费用均摊', '运营工资', '银行费用',
        '营销费用', '管理费用', '财务费用', # Keep original for reference?
        '李宗生', '艾晓川', '郑昊灵', '黄尧', '涂友其', '岳籽歧', '李小琴', '罗宇', '车逸清', '林怡',
        '净利润', '备注'
    ]
    for col in OUTPUT_COLUMNS:
        if col not in df_out.columns:
            df_out[col] = 0
            
    df_out = df_out[OUTPUT_COLUMNS] # Reorder
    df_out = df_out.fillna(0)
    
    # Sort
    df_out['月份'] = pd.to_datetime(df_out['月份'])
    df_out = df_out.sort_values('月份')
    
    # Save
    out_csv = 'standard_template_2508to2601.csv'
    out_xlsx = 'standard_template_2508to2601.xlsx'
    
    df_out.to_csv(out_csv, index=False, encoding='utf-8-sig')
    
    writer = pd.ExcelWriter(out_xlsx, engine='xlsxwriter')
    df_out.to_excel(writer, sheet_name='数据录入', index=False)
    # Add formatting
    wb = writer.book
    ws = writer.sheets['数据录入']
    fmt = wb.add_format({'bold': True, 'fg_color': '#D7E4BC', 'border': 1})
    for i, col in enumerate(df_out.columns):
        ws.write(0, i, col, fmt)
        ws.set_column(i, i, 12)
    writer.close()
    
    print(f"\nSaved to {out_csv} and {out_xlsx}")
    print(df_out[['月份', '总营收', '净利润', '区店费用', '运营工资']])
else:
    print("\nNo data extracted.")
