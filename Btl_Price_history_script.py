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

# save the items in a csv file
items_df = pd.DataFrame(items, columns=['Item'])
items_df.to_csv(r'C:\Users\fadia\OneDrive\Desktop\Ody\sampel DataBase\Product_History_Reports\Btl\Btl_Items.csv', index=False)
print(f"Product history reports for {len(items)} items have been generated and saved to {output_path}.")
print(f"List of items has been saved to {output_path}\\Btl_Items.csv.")
# The code generates product history reports for items containing 'Btl' in their names from a sales dataset.
# It filters the data, identifies price changes, and saves individual reports for each item in a specified directory.
# Additionally, it saves a list of all processed items to a separate CSV file.
# The output files are saved in the specified directory, and a confirmation message is printed.
# The code is designed to handle the generation of product history reports for items that contain 'Btl' in their names.
# The reports include the date of price changes and the new price for each item.
# The code ensures that the output directory exists before saving the files.
# The generated reports can be used for further analysis or record-keeping of product price history.
# The code is structured to be reusable for any item containing 'Btl' in its name, making it flexible for similar tasks.
# The output files are saved in a specified directory, and a confirmation message is printed to indicate successful completion.
# The code is designed to be run in a Python environment with the necessary libraries installed, such as pandas and matplotlib.




# read me file# This script generates product history reports for items containing 'Btl' in their names from a sales
# dataset. It filters the data, identifies price changes, and saves individual reports for each item in a specified directory.
# Additionally, it saves a list of all processed items to a separate CSV file. The output files are saved in the specified directory, and a confirmation message is printed.
# The code is designed to handle the generation of product history reports for items that contain 'Btl' in their names.
# The reports include the date of price changes and the new price for each item. The code ensures that the output directory exists before saving the files.
# The generated reports can be used for further analysis or record-keeping of product price history.    
# The code is structured to be reusable for any item containing 'Btl' in its name, making it flexible for similar tasks.
# The output files are saved in a specified directory, and a confirmation message is printed to indicate successful completion.
# The code is designed to be run in a Python environment with the necessary libraries installed, such as pandas and matplotlib.
# The script is intended for users who need to analyze product price history and track changes over time.
# It can be adapted for other product categories by modifying the filtering criteria.   