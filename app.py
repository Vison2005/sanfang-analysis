
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np
import os
import datetime

# Page Configuration
st.set_page_config(page_title="三坊七巷经营数据管理系统", layout="wide")

# Constants
BASE_DATA_FILE = "standard_template_2508to2601.csv"

# --- Helper Functions ---
@st.cache_data
def load_base_data():
    if os.path.exists(BASE_DATA_FILE):
        try:
            df = pd.read_csv(BASE_DATA_FILE)
            if '月份' in df.columns:
                df['月份'] = pd.to_datetime(df['月份'])
            return df
        except Exception as e:
            st.error(f"读取核心数据失败: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def process_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df_new = pd.read_csv(uploaded_file)
        else:
            xl = pd.ExcelFile(uploaded_file)
            if '数据录入' in xl.sheet_names:
                df_new = pd.read_excel(uploaded_file, sheet_name='数据录入')
            else:
                df_new = pd.read_excel(uploaded_file)
        
        if '月份' in df_new.columns:
            df_new['月份'] = pd.to_datetime(df_new['月份'])
        
        return df_new
    except Exception as e:
        st.error(f"文件解析失败: {e}")
        return pd.DataFrame()

def merge_data(base_df, new_df):
    if new_df.empty: return base_df
    if base_df.empty: return new_df
    combined = pd.concat([base_df, new_df])
    if '月份' in combined.columns:
        combined = combined.drop_duplicates(subset=['月份'], keep='last')
        combined = combined.sort_values('月份')
    return combined

# --- Sidebar ---
st.sidebar.title("功能导航")

# Data Management
st.sidebar.subheader("数据管理")
uploaded_file = st.sidebar.file_uploader("上传新月度数据 (Excel/CSV)", type=["xlsx", "csv"])

# View Settings (Moved from Sidebar)
# st.sidebar.subheader("视图设置")
# view_mode = st.sidebar.radio("时间维度", ["月度视图", "年度视图"])

# Navigation
page = st.sidebar.radio("功能模块", ["经营总览", "收入分析", "成本支出", "数据明细", "未来预测"])

st.sidebar.markdown("---")
st.sidebar.info("核心数据: 2025.08 - 2026.01 (及更新)")

# --- Data Loading ---
base_df = load_base_data()
df = base_df.copy()

if uploaded_file:
    new_df = process_uploaded_file(uploaded_file)
    if not new_df.empty:
        st.sidebar.success(f"已加载: {uploaded_file.name}")
        df = merge_data(base_df, new_df)
    else:
        st.sidebar.warning("上传文件为空或格式错误")

if df.empty:
    st.warning("暂无数据，请检查核心数据文件或上传新数据。")
    st.stop()

if '月份' in df.columns:
    df['月份'] = pd.to_datetime(df['月份'])

# --- Main Content ---
st.header("视图设置")
c_view, c_select = st.columns([1, 2])

with c_view:
    view_mode = st.radio("时间维度", ["月度明细", "年度概况"], horizontal=True)

# --- Aggregation and Selection Logic ---
if 'Year' not in df.columns:
    df['Year'] = df['月份'].dt.year

current_data = None
previous_data = None
selected_label = ""
trend_df = None
trend_x_col = ""

if view_mode == "月度明细":
    # Prepare monthly data
    trend_df = df
    trend_x_col = '月份'
    
    # Selection Box
    available_months = df['月份'].dt.strftime('%Y-%m').unique()
    with c_select:
        selected_month_str = st.selectbox("选择月份", available_months, index=len(available_months)-1)
    
    selected_label = selected_month_str
    
    # Get current and previous data
    mask = df['月份'].dt.strftime('%Y-%m') == selected_month_str
    if mask.any():
        current_data = df.loc[mask].iloc[0]
        
        # Find previous month
        curr_date = current_data['月份']
        # Try to find exactly previous month in data
        # Sort df first
        df_sorted = df.sort_values('月份').reset_index(drop=True)
        curr_idx = df_sorted[df_sorted['月份'] == curr_date].index[0]
        
        if curr_idx > 0:
            previous_data = df_sorted.iloc[curr_idx - 1]

elif view_mode == "年度概况":
    # Aggregate by Year
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != 'Year']
    df_yearly = df.groupby('Year')[numeric_cols].sum().reset_index()
    df_yearly['月份'] = pd.to_datetime(df_yearly['Year'].astype(str) + '-01-01') # Fake date
    
    trend_df = df_yearly
    trend_x_col = 'Year'
    
    # Selection Box
    available_years = df_yearly['Year'].unique()
    with c_select:
        selected_year = st.selectbox("选择年份", available_years, index=len(available_years)-1)
        
    selected_label = f"{selected_year}年"
    
    # Get current and previous data
    mask = df_yearly['Year'] == selected_year
    if mask.any():
        current_data = df_yearly.loc[mask].iloc[0]
        
        # Find previous year
        df_yearly_sorted = df_yearly.sort_values('Year').reset_index(drop=True)
        curr_idx = df_yearly_sorted[df_yearly_sorted['Year'] == selected_year].index[0]
        
        if curr_idx > 0:
            previous_data = df_yearly_sorted.iloc[curr_idx - 1]

st.markdown("---")

# --- Main Content ---

if page == "经营总览":
    st.title("📊 经营数据总览")
    
    if current_data is None:
        st.error("未找到选定时间段的数据")
        st.stop()
        
    st.subheader(f"{selected_label} 核心指标")
    
    c1, c2, c3, c4 = st.columns(4)
    
    def get_delta(curr, prev, col):
        if prev is None: return None
        return curr[col] - prev[col]

    c1.metric("总营收", f"¥{current_data.get('总营收', 0):,.2f}", 
              f"{get_delta(current_data, previous_data, '总营收'):,.2f}" if previous_data is not None else None)
    c2.metric("毛利", f"¥{current_data.get('毛利', 0):,.2f}",
              f"{get_delta(current_data, previous_data, '毛利'):,.2f}" if previous_data is not None else None)
    c3.metric("净利润", f"¥{current_data.get('净利润', 0):,.2f}",
              f"{get_delta(current_data, previous_data, '净利润'):,.2f}" if previous_data is not None else None)
    
    net_margin = (current_data.get('净利润', 0) / current_data.get('总营收', 1)) * 100 if current_data.get('总营收', 0) != 0 else 0
    prev_margin = (previous_data.get('净利润', 0) / previous_data.get('总营收', 1)) * 100 if previous_data is not None and previous_data.get('总营收', 0) != 0 else 0
    c4.metric("净利率", f"{net_margin:.1f}%", f"{net_margin - prev_margin:.1f}%")

    st.markdown("---")
    
    # Trend Chart
    st.subheader("核心指标趋势")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_df[trend_x_col], y=trend_df['总营收'], name='总营收', line=dict(color='#3366CC', width=3), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=trend_df[trend_x_col], y=trend_df['总费用'], name='总费用', line=dict(color='#DC3912', width=3), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=trend_df[trend_x_col], y=trend_df['净利润'], name='净利润', line=dict(color='#109618', width=3, dash='dot'), mode='lines+markers'))
    fig.update_layout(hovermode="x unified", xaxis_title="时间", yaxis_title="金额 (元)")
    st.plotly_chart(fig, use_container_width=True)

elif page == "收入分析":
    st.title("💰 收入结构分析")
    
    if current_data is None:
        st.stop()
    
    channels = ['到店收入', '抖音收入', '美团收入', '大众点评收入']
    valid_channels = [c for c in channels if c in df.columns] # Use original df columns as reference
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("渠道收入趋势")
        fig_bar = px.bar(trend_df, x=trend_x_col, y=valid_channels, title="渠道收入堆叠图", labels={'value': '金额', 'variable': '渠道'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c2:
        st.subheader(f"{selected_label} 收入占比")
        
        # Prepare data for pie chart
        latest_vals = current_data[valid_channels]
        latest_vals = latest_vals[latest_vals > 0]
        
        if not latest_vals.empty:
            fig_pie = px.pie(values=latest_vals.values, names=latest_vals.index, hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("该时段无渠道细分数据")

elif page == "成本支出":
    st.title("💸 成本与费用分析")
    
    if current_data is None:
        st.stop()
    
    # Detailed Cost Columns
    cost_cols = [
        '物业水电', '店内工资', '区店费用', '日常采购成本', 
        '物料采购成本', '房租成本', '其他成本', '运营备用金均摊', 
        '财务费用均摊', '运营工资', '银行费用', '营销费用'
    ]
    # Filter columns that actually exist and have data > 0 IN THE SELECTED PERIOD
    # Use current_data to check for non-zero
    valid_cost_cols = [c for c in cost_cols if c in current_data.index and current_data[c] > 0]
    
    # Personnel Breakdown
    personnel_cols = ['李宗生', '艾晓川', '郑昊灵', '黄尧', '涂友其', '岳籽歧', '李小琴', '罗宇', '车逸清', '林怡']
    valid_personnel = [c for c in personnel_cols if c in trend_df.columns and trend_df[c].sum() != 0]

    # 1. Tree Map for SELECTED Period
    st.subheader("成本结构树状图 (Tree Map)")
    
    # Prepare data for Treemap
    tm_data = []
    for col in valid_cost_cols:
        val = current_data.get(col, 0)
        if val > 0:
            tm_data.append({'Category': col, 'Value': val, 'Parent': '总成本'})
            
    if tm_data:
        tm_df = pd.DataFrame(tm_data)
        # Add root
        tm_df = pd.concat([pd.DataFrame([{'Category': '总成本', 'Value': tm_df['Value'].sum(), 'Parent': ''}]), tm_df])
        
        fig_tm = px.treemap(tm_df, names='Category', parents='Parent', values='Value', 
                            title=f"{selected_label} 成本构成", color='Value', color_continuous_scale='RdBu_r')
        fig_tm.update_traces(textinfo="label+value+percent parent")
        st.plotly_chart(fig_tm, use_container_width=True)
    else:
        st.info("该时段无详细成本数据")

    st.subheader("人员工资明细")
    if valid_personnel:
        fig_wage = px.bar(trend_df, x=trend_x_col, y=valid_personnel, title="人员工资堆叠图", labels={'value': '金额', 'variable': '人员'})
        st.plotly_chart(fig_wage, use_container_width=True)
    else:
        st.info("暂无详细人员工资数据")

    # 2. Trend Area Chart
    st.subheader("成本趋势")
    # For trend, we use valid_cost_cols based on the whole trend_df to be consistent?
    # Or just use the ones valid for this month? Better to use global valid for trend.
    global_valid_costs = [c for c in cost_cols if c in trend_df.columns and trend_df[c].sum() != 0]
    
    if global_valid_costs:
        fig_area = px.area(trend_df, x=trend_x_col, y=global_valid_costs)
        st.plotly_chart(fig_area, use_container_width=True)

elif page == "数据明细":
    st.title("📋 详细数据表")
    
    # Show detailed columns
    all_cols = ['月份'] + [c for c in df.columns if c not in ['月份', 'Year', 'Month_Num']]
    
    # Use the selected mode logic for table
    st.subheader(f"{selected_label} 数据")
    
    # Show the single row for the selected period? 
    # Or show all data filtered by date range?
    # User asked for "Check specific month data".
    # Let's show the selected period's data prominently, and maybe the full table below.
    
    if current_data is not None:
        # Convert Series to DataFrame for display
        # Transpose to show metrics as rows?
        st.dataframe(current_data.to_frame().T.style.format({col: "{:,.2f}" for col in current_data.index if isinstance(current_data[col], (int, float))}))
    
    st.subheader("所有数据明细")
    # Date Filter
    if view_mode == "月度明细":
        min_date = df['月份'].min().date()
        max_date = df['月份'].max().date()
        c1, c2 = st.columns(2)
        start_date = c1.date_input("开始日期", min_date)
        end_date = c2.date_input("结束日期", max_date)
        mask = (df['月份'].dt.date >= start_date) & (df['月份'].dt.date <= end_date)
        filtered_df = df.loc[mask]
    else:
        filtered_df = trend_df # Show yearly aggregated table
    
    st.dataframe(filtered_df.style.format({col: "{:,.2f}" for col in filtered_df.select_dtypes(include=['float', 'int']).columns}))
    
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("下载数据 (CSV)", csv, "data_export.csv", "text/csv")

elif page == "未来预测":
    st.title("📈 经营趋势预测")
    st.info("基于历史月度数据预测")
    
    # Always use monthly data for prediction
    df_pred = df.copy()
    df_pred['Month_Num'] = range(len(df_pred))
    
    X = df_pred[['Month_Num']]
    targets = ['总营收', '净利润', '总费用']
    valid_targets = [t for t in targets if t in df_pred.columns]
    
    future_months = 3
    last_num = df_pred['Month_Num'].iloc[-1]
    future_X = pd.DataFrame({'Month_Num': range(last_num + 1, last_num + 1 + future_months)})
    last_date = df_pred['月份'].iloc[-1]
    future_dates = [last_date + pd.DateOffset(months=i+1) for i in range(future_months)]
    
    predictions = {'日期': future_dates}
    fig_pred = go.Figure()
    
    for t in valid_targets:
        fig_pred.add_trace(go.Scatter(x=df_pred['月份'], y=df_pred[t], name=f'历史-{t}', mode='lines+markers', opacity=0.5))
        model = LinearRegression()
        model.fit(X, df_pred[t])
        pred = model.predict(future_X)
        predictions[t] = pred
        fig_pred.add_trace(go.Scatter(x=future_dates, y=pred, name=f'预测-{t}', line=dict(dash='dash'), mode='lines+markers'))
        
    st.dataframe(pd.DataFrame(predictions).style.format({t: "¥{:,.2f}" for t in valid_targets}))
    st.plotly_chart(fig_pred, use_container_width=True)
