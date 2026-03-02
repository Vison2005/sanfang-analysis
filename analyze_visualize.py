import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.dates as mdates

# Set Chinese font
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False # Fix minus sign

def load_data():
    df = pd.read_csv('consolidated_data.csv')
    df['Month'] = pd.to_datetime(df['Month'])
    return df.sort_values('Month')

def perform_eda(df):
    print("\n--- Basic Statistics ---")
    print(df.describe())
    
    # Calculate margins
    df['Gross_Margin'] = df['Gross_Profit'] / df['Revenue']
    df['Net_Margin'] = df['Net_Profit'] / df['Revenue']
    
    print("\n--- Margins ---")
    print(df[['Month', 'Gross_Margin', 'Net_Margin']])
    
    return df

def plot_trends(df):
    plt.figure(figsize=(12, 6))
    plt.plot(df['Month'], df['Revenue'], marker='o', label='主营收入 (Revenue)')
    plt.plot(df['Month'], df['COGS'], marker='s', label='主营业务成本 (COGS)')
    plt.plot(df['Month'], df['Net_Profit'], marker='^', label='净利润 (Net Profit)')
    
    plt.title('月度营收与利润趋势 (Monthly Revenue & Profit Trend)')
    plt.xlabel('月份 (Month)')
    plt.ylabel('金额 (Amount)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.tight_layout()
    plt.savefig('trend_analysis.png')
    print("Saved trend_analysis.png")

def plot_revenue_composition(df):
    plt.figure(figsize=(12, 6))
    
    # Fill NaN with 0
    cols = ['Revenue_InStore', 'Revenue_Douyin', 'Revenue_Meituan', 'Revenue_Dianping']
    df[cols] = df[cols].fillna(0)
    
    # Plot stacked bar
    bottom = np.zeros(len(df))
    labels = ['到店收入', '抖音收入', '美团收入', '大众点评收入']
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
    
    for i, col in enumerate(cols):
        plt.bar(df['Month'], df[col], bottom=bottom, label=labels[i], color=colors[i], width=20)
        bottom += df[col]
        
    plt.title('营收构成分析 (Revenue Composition)')
    plt.xlabel('月份 (Month)')
    plt.ylabel('金额 (Amount)')
    plt.legend()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.tight_layout()
    plt.savefig('revenue_composition.png')
    print("Saved revenue_composition.png")

def predict_future(df):
    # Prepare data for regression
    # Convert dates to ordinal or numeric (e.g., months since start)
    start_date = df['Month'].iloc[0]
    df['Month_Num'] = (df['Month'].dt.year - start_date.year) * 12 + \
                      (df['Month'].dt.month - start_date.month)
    
    X = df[['Month_Num']]
    y_revenue = df['Revenue']
    y_profit = df['Net_Profit']
    
    # Linear Regression for Revenue
    model_rev = LinearRegression()
    model_rev.fit(X, y_revenue)
    
    # Linear Regression for Profit
    model_prof = LinearRegression()
    model_prof.fit(X, y_profit)
    
    # Predict next 2 months (Feb, Mar 2026 -> index 8, 9)
    future_X = pd.DataFrame({'Month_Num': [8, 9]})
    pred_rev = model_rev.predict(future_X)
    pred_prof = model_prof.predict(future_X)
    
    print("\n--- Predictions (Linear Regression) ---")
    months = ['2026-02', '2026-03']
    for i, m in enumerate(months):
        print(f"{m}: Predicted Revenue = {pred_rev[i]:.2f}, Predicted Profit = {pred_prof[i]:.2f}")
        
    # Plot Prediction
    plt.figure(figsize=(10, 6))
    
    # Plot actuals
    plt.scatter(df['Month_Num'], y_revenue, color='blue', label='实际营收 (Actual Revenue)')
    plt.scatter(df['Month_Num'], y_profit, color='green', label='实际净利润 (Actual Profit)')
    
    # Plot regression lines
    plt.plot(df['Month_Num'], model_rev.predict(X), color='blue', linestyle='--', alpha=0.5)
    plt.plot(df['Month_Num'], model_prof.predict(X), color='green', linestyle='--', alpha=0.5)
    
    # Plot predictions
    plt.scatter([8, 9], pred_rev, color='red', marker='x', s=100, label='预测营收 (Predicted Revenue)')
    plt.scatter([8, 9], pred_prof, color='orange', marker='x', s=100, label='预测净利润 (Predicted Profit)')
    
    plt.title('营收与利润预测 (Revenue & Profit Prediction)')
    plt.xlabel('月份索引 (Month Index, 0=2025-06)')
    plt.ylabel('金额 (Amount)')
    plt.legend()
    plt.grid(True)
    plt.savefig('prediction.png')
    print("Saved prediction.png")

def main():
    df = load_data()
    df = perform_eda(df)
    plot_trends(df)
    plot_revenue_composition(df)
    predict_future(df)

if __name__ == "__main__":
    main()
