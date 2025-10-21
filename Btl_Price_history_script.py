import matplotlib.pyplot as plt
import pandas as pd
import numpy as np # Import NumPy
import os

data_path = r'C:\Users\fadia\OneDrive\Desktop\Ody\Scripts\Transformed Data\Master Combined\Master_Sales_Data_2021-08-19_to_2025-07-22.csv'
df=pd.read_csv(data_path)
df['Day_Date'] = pd.to_datetime(df['Day_Date'])

df = df[["Date", "Item", "Price"]]

def generate_product_history_report_Btl(df, item_name):
    item = item_name
    item_df = df[df['Item'] == item]
    item_df = item_df[['Date', 'Price']]

    item_df['Date'] = pd.to_datetime(item_df['Date'])
    item_df = item_df.sort_values('Date')
    item_df['Sale_Date'] = item_df['Date'].dt.date # date without time , like 2023-01-01
    item_df["Change_in_Price"] = item_df["Price"] != item_df["Price"].shift(1)
    item_df = item_df[item_df["Change_in_Price"] == True]
    return item_df

items = df['Item'].unique()
items = [item for item in items if 'Btl' in item]
for item_name in items:
    item_df = generate_product_history_report_Btl(df, item_name)


    output_path = r'C:\Users\fadia\OneDrive\Desktop\Ody\sampel DataBase\Product_History_Reports\Btl'
    file_name = f"{item_name.replace(' ', '_')}.csv"
    output_file = f"{output_path}\{file_name}"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    item_df.to_csv(output_file, index=False)


