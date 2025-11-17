import pandas as pd
import os
import numpy as np

data_path = r'C:\Users\fadia\OneDrive\Desktop\Ody\Scripts\Transformed Data\Master Combined\Master_Sales_Data_2021-08-19_to_2025-07-22.csv'
df=pd.read_csv(data_path)

original_happy_hour_path =r"C:\Users\fadia\OneDrive\Desktop\Ody\Data\original_daily_happy_hour.csv"
df_happy_hour = pd.read_csv(original_happy_hour_path)
df_happy_hour["Date"] = pd.to_datetime(df_happy_hour["Date"])

df['Date'] = pd.to_datetime(df['Date'])


items_file_path = r"C:\Users\fadia\OneDrive\Desktop\Ody\Data\beverage_items_excluding_btl_by_gls.xlsx"
df_items = pd.read_excel(items_file_path)

df = df[["Date","Item","Price"]]
df= df[df['Item'].isin(df_items['Item'])]


output_folder = r"C:\Users\fadia\OneDrive\Desktop\Ody\Scripts\Beverage by Glass Price History"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)



def assign_time_slot(hour):
    if pd.to_datetime("12:00").time() <= hour < pd.to_datetime("18:01").time():
        return 'Slot_12_to_18'
    elif pd.to_datetime("18:00").time() <= hour < pd.to_datetime("19:01").time():
        return 'Slot_18_to_19'
    else: return 'Base_Price_Hours'

def generate_price_history_script(item_name):
    item_name = item_name
    item_df = df[df['Item'] == item_name].copy()
    start_date = item_df['Date'].min()
    end_date = item_df['Date'].max()
    item_df = item_df[['Date', 'Price']]
    item_df['Date'] = pd.to_datetime(item_df['Date'])
    item_df.sort_values(by='Date', inplace=True)
    item_df.reset_index(drop=True, inplace=True)

    item_df['Time_Slot'] = item_df['Date'].dt.time.apply(assign_time_slot)
    item_df['Sale_Date'] = item_df['Date'].dt.date

    
    daily_prices = item_df.pivot_table(index='Sale_Date', columns='Time_Slot', values='Price', aggfunc=lambda x: x.mode()[0]).reset_index()
    daily_prices["Slot_12_to_18"] = daily_prices["Slot_12_to_18"].fillna(0)
    daily_prices["Slot_18_to_19"] = daily_prices["Slot_18_to_19"].fillna(0)
    daily_prices["Base_Price_Hours"] = daily_prices["Base_Price_Hours"].fillna(0)

    all_dates = pd.date_range(start=start_date, end=end_date)
    all_dates_df = pd.DataFrame({'Sale_Date': all_dates.date})

    daily_prices_org = pd.merge(all_dates_df, daily_prices, on='Sale_Date', how='left')
    daily_prices_org = daily_prices_org.sort_values('Sale_Date')
    daily_prices_org["Base_Price_Hours"] = daily_prices_org["Base_Price_Hours"].fillna(0)
    daily_prices_org["Slot_12_to_18"] = daily_prices_org["Slot_12_to_18"].fillna(0)
    daily_prices_org["Slot_18_to_19"] = daily_prices_org["Slot_18_to_19"].fillna(0)
    
    daily_prices["Month"] = pd.to_datetime(daily_prices['Sale_Date']).dt.to_period('M')

    safe_mode = lambda x: x[x != 0].mode()[0] if not x[x != 0].mode().empty else np.nan
    monthly_prices = daily_prices.groupby('Month').agg({
        'Base_Price_Hours': safe_mode,
        'Slot_12_to_18': safe_mode,
        'Slot_18_to_19': safe_mode
    }).reset_index()

    # fill the NaN values in monthly_prices with forward fill and back fill method
    monthly_prices["Base_Price_Hours"] = monthly_prices["Base_Price_Hours"].ffill().bfill()
    monthly_prices["Slot_12_to_18"] = monthly_prices["Slot_12_to_18"].ffill().bfill()
    monthly_prices["Slot_18_to_19"] = monthly_prices["Slot_18_to_19"].ffill().bfill()

    daily_prices = pd.merge(daily_prices, monthly_prices, on='Month', suffixes=('', '_Monthly_Mode'))
    
    daily_prices["Base_Price_Hours_Changed"] = daily_prices["Base_Price_Hours"] == 0
    daily_prices["Slot_12_to_18_Changed"] = daily_prices["Slot_12_to_18"] == 0
    daily_prices["Slot_18_to_19_Changed"] = daily_prices["Slot_18_to_19"] == 0


    # now from daily_prices i want to fill the NaN values with most frequent value of that month  for base price, slot_12_to_18 and slot_18_to_19
    daily_prices['Slot_12_to_18'] = daily_prices.apply(
        lambda row: row['Slot_12_to_18_Monthly_Mode'] if row['Slot_12_to_18'] == 0 else row['Slot_12_to_18'], axis=1)
    daily_prices['Slot_18_to_19'] = daily_prices.apply(
        lambda row: row['Slot_18_to_19_Monthly_Mode'] if row['Slot_18_to_19'] == 0 else row['Slot_18_to_19'], axis=1)
    daily_prices['Base_Price_Hours'] = daily_prices.apply(
        lambda row: row['Base_Price_Hours_Monthly_Mode'] if row['Base_Price_Hours'] == 0 else row['Base_Price_Hours'], axis=1)
    # daily_prices = daily_prices.drop(columns=['Slot_12_to_18_Monthly_Mode', 'Slot_18_to_19_Monthly_Mode', 'Base_Price_Hours_Monthly_Mode', 'Month'])

    daily_prices = pd.merge(all_dates_df, daily_prices, on='Sale_Date', how='left')
    daily_prices = daily_prices.sort_values('Sale_Date')

    # fill the slot_12_to_18_Monthly_Mode , slot_18_to_19_Monthly_Mode , Base_Price_Hours_Monthly_Mode with forward fill method or back fill method
    daily_prices["Slot_12_to_18_Monthly_Mode"] = daily_prices["Slot_12_to_18_Monthly_Mode"].ffill().bfill()
    daily_prices["Slot_18_to_19_Monthly_Mode"] = daily_prices["Slot_18_to_19_Monthly_Mode"].ffill().bfill()
    daily_prices["Base_Price_Hours_Monthly_Mode"] = daily_prices["Base_Price_Hours_Monthly_Mode"].ffill().bfill()

    # fill the Base_Price_Hours , Slot_12_to_18 , Slot_18_to_19 with base_Price_hours_monthly_mode , slot_12_to_18_monthly_mode , slot_18_to_19_monthly_mode
    daily_prices['Base_Price_Hours'] = daily_prices.apply(
        lambda row: row['Base_Price_Hours_Monthly_Mode'] if pd.isna(row['Base_Price_Hours']) else row['Base_Price_Hours'], axis=1)
    daily_prices['Slot_12_to_18'] = daily_prices.apply(
        lambda row: row['Slot_12_to_18_Monthly_Mode'] if pd.isna(row['Slot_12_to_18']) else row['Slot_12_to_18'], axis=1)
    daily_prices['Slot_18_to_19'] = daily_prices.apply(
        lambda row: row['Slot_18_to_19_Monthly_Mode'] if pd.isna(row['Slot_18_to_19']) else row['Slot_18_to_19'], axis=1)


    # daily_prices["Base_Price_Hours_Changed"] = daily_prices["Base_Price_Hours_Changed"].fillna(True)
    # daily_prices["Slot_12_to_18_Changed"] = daily_prices["Slot_12_to_18_Changed"].fillna(True)
    # daily_prices["Slot_18_to_19_Changed"] = daily_prices["Slot_18_to_19_Changed"].fillna(True)

    daily_prices = daily_prices.drop(columns=['Slot_12_to_18_Monthly_Mode', 'Slot_18_to_19_Monthly_Mode', 'Base_Price_Hours_Monthly_Mode', 'Month'])

    # determine happy hour type
    daily_prices["Happy_Hour_Item"] = daily_prices.apply(
    lambda row:
    "No Happy Hour" if (row["Slot_12_to_18"] == row["Base_Price_Hours"]) and (row["Slot_18_to_19"] == row["Base_Price_Hours"]) else
    ("Happy Hour 12-7" if (row["Slot_18_to_19"] == row["Slot_12_to_18"]) and (row["Slot_18_to_19"] != row["Base_Price_Hours"]) else
    ("Happy Hour 12-6" if (row["Slot_18_to_19"] == row["Base_Price_Hours"]) and (row["Slot_18_to_19"] != row["Slot_12_to_18"])
    else
    "Unknown")), axis=1)

    # create a new column HH_Org in daily_prices to store the original happy hour type
    daily_prices["HH_Org"] = daily_prices["Happy_Hour_Item"]


    # select only the columns Sale_Date, Slot_12_to_18, Slot_18_to_19, Base_Price_Hours , HH_Org, Happy_Hour
    daily_prices = daily_prices[['Sale_Date', 'Slot_12_to_18', 'Slot_18_to_19', 'Base_Price_Hours','HH_Org', 'Happy_Hour_Item']]

    daily_prices["Discount_Item"] = daily_prices.apply(
    lambda row:
    0.0 if row["Happy_Hour_Item"] == "No Happy Hour" else
    round(((row["Base_Price_Hours"] - row["Slot_12_to_18"]) / row["Base_Price_Hours"]) * 100, 2) if row["Happy_Hour_Item"] == "Happy Hour 12-6" else
    round(((row["Base_Price_Hours"] - row["Slot_18_to_19"]) / row["Base_Price_Hours"]) * 100, 2) if row["Happy_Hour_Item"] == "Happy Hour 12-7" else
    np.nan, axis=1)

    # create a new column D_Org in daily_prices to store the original happy hour discount percentage
    daily_prices["D_Org"] = daily_prices["Discount_Item"]

    daily_prices_final = pd.merge(daily_prices, daily_prices_org, on='Sale_Date', how='left', suffixes=('', '_Org'))

    print(daily_prices_final.columns)


    # select only the columns Sale_Date, Slot_12_to_18, Slot_18_to_19, Base_Price_Hours , Slot_12_to_18_Org, Slot_18_to_19_Org, Base_Price_Hours_Org , HH_Org, Happy_Hour , D_Org , Discount_Item
    daily_prices_final = daily_prices_final[['Sale_Date', 'Slot_12_to_18', 'Slot_18_to_19', "Base_Price_Hours",
                                         "Slot_12_to_18_Org", "Slot_18_to_19_Org", "Base_Price_Hours_Org", "HH_Org",'Happy_Hour_Item','D_Org', 'Discount_Item']]
    
    # rename columns Sale_Date to Date , Happy_Hour_Discount_Percentage to Discount_Item
    daily_prices_final = daily_prices_final.rename(columns={"Sale_Date": "Date"})
    daily_prices_final["Date"] = pd.to_datetime(daily_prices_final["Date"])
    # combine the daily_prices_final with df_happy_hour to get the original happy hour and discount

    daily_prices_final = pd.merge(daily_prices_final, df_happy_hour, on='Date', how='left')
    # convert Date to date format only (yyyy-mm-dd)
    daily_prices_final["Date"] = daily_prices_final["Date"].dt.date

    # if the "happy hour of item" is equal "Unknown" then replace it with the value from backward last row not equal to "Unknown"

   
    # # replace "Unknown" with NaN
    # daily_prices_final['Happy_Hour_Item'] = daily_prices_final['Happy_Hour_Item'].replace("Unknown", np.nan)
    # # fill the NaN values with forward fill method or back fill method
    # daily_prices_final['Happy_Hour_Item'] = daily_prices_final['Happy_Hour_Item'].ffill().bfill()

    
    # determine base price as the most frequent value among the Base_Price_Hours_Org where Base_Price_Hours_Org is not equal to 0
    base_price = daily_prices_final[daily_prices_final["Base_Price_Hours_Org"] != 0]
    # daily_prices_final['Base_Price'] = base_price[f'Base_Price_Hours_Org'].mode()[0]


    # add a new column Cost_Price which is True if Slot_18_to_19_Org is less than 49% of Base_Price and not equal 0
    condition1 = (daily_prices_final["Slot_18_to_19_Org"] < (daily_prices_final['Base_Price_Hours'] * 0.49)) & (daily_prices_final["Slot_18_to_19_Org"] != 0)
    daily_prices_final["is_Slot_18_to_19_Cost"] = condition1
    # or condition2 is True if Slot_12_to_18_Org is less than 49% of Base_Price and not equal 0
    condition2 = (daily_prices_final["Slot_12_to_18_Org"] < (daily_prices_final['Base_Price_Hours'] * 0.49)) & (daily_prices_final["Slot_12_to_18_Org"] != 0)
    daily_prices_final["is_Slot_12_to_18_Cost"] = condition2
    # or condition3 is True if Base_Price_Hours_Org is less than 49% of Base_Price and not equal 0
    condition3 = (daily_prices_final["Base_Price_Hours_Org"] < (daily_prices_final['Base_Price_Hours'] * 0.49)) & (daily_prices_final["Base_Price_Hours_Org"] != 0)
    daily_prices_final["is_Base_Price_Cost"] = condition3
     # combine the three conditions into one column Cost_Price
    daily_prices_final["is_Cost_Price"] = condition1 | condition3 | condition2
    # print the number of rows where is_Cost_Price is True
    print(f"Number of rows where is_Cost_Price is True: {daily_prices_final['is_Cost_Price'].sum()}")
    
    # def function , if the is_Cost_Price is True , change the 'Base_Price' , 'Slot_12_to_18' , 'Slot_18_to_19' to values from  backward rows where is_Cost_Price is False
    def change_cost_price_to_normal(row):
        if row["is_Cost_Price"]:
            row["Base_Price_Hours"] = np.nan
            row["Slot_12_to_18"] = np.nan
            row["Slot_18_to_19"] = np.nan
            row["Happy_Hour_Item"] = np.nan
            row["Discount_Item"] = np.nan
            
        return row
    daily_prices_final = daily_prices_final.apply(change_cost_price_to_normal, axis=1)
    daily_prices_final["Base_Price_Hours"] = daily_prices_final["Base_Price_Hours"].ffill().bfill()
    daily_prices_final["Slot_12_to_18"] = daily_prices_final["Slot_12_to_18"].ffill().bfill()
    daily_prices_final["Slot_18_to_19"] = daily_prices_final["Slot_18_to_19"].ffill().bfill()
    daily_prices_final["Happy_Hour_Item"] = daily_prices_final["Happy_Hour_Item"].ffill().bfill()
    daily_prices_final["Discount_Item"] = daily_prices_final["Discount_Item"].ffill().bfill()

    # add an new colum for cost price value , get the minimum value among the three slots if is_Cost_Price is True , and make sure to ignore 0 values
    # if all values are 0  or nan return 0
    def get_cost_price(row):
        if row["is_Cost_Price"]:
            prices = []
            if row["Slot_18_to_19_Org"] != 0:
                prices.append(row["Slot_18_to_19_Org"])
            if row["Slot_12_to_18_Org"] != 0:
                prices.append(row["Slot_12_to_18_Org"])
            if row["Base_Price_Hours_Org"] != 0:
                prices.append(row["Base_Price_Hours_Org"])
            return min(prices) if prices else np.nan
        else:
            return np.nan

    daily_prices_final["Cost_Price_Value"] = daily_prices_final.apply(get_cost_price, axis=1)
    daily_prices_final["Cost_Price_Value"] = daily_prices_final["Cost_Price_Value"].ffill().bfill()

    # if Cost_Price_Value is all nan replace it with random value between 30% and 35% 
    cost_price = np.random.uniform(0.3, 0.35)
    base_price_mode = base_price[f'Base_Price_Hours_Org'].mode()[0]
    cost_price = base_price_mode * cost_price
    daily_prices_final["Cost_Price_Value"] = daily_prices_final["Cost_Price_Value"].fillna(cost_price)

    daily_prices_final = daily_prices_final.drop(columns=["is_Slot_18_to_19_Cost", "is_Slot_12_to_18_Cost", "is_Base_Price_Cost", "is_Cost_Price"])


    # some time we have error vlaue in "HH_Org"
    # the value of "HH_Org" is "Happy Hour 12-7" but the real "Happy_Hour" column is "Happy Hour 12-6"
    # that happen when there is a not value recorded in Slot_18_to_19_Org (0) 
    # and fill it with the most frequent value of that month
    # but this month it's recorded only one value wrongly , so the most frequent value become the wrong value
    # to fix that we will compare the "HH_Org" with the "Happy_Hour" column
    # if they are not equal and "Slot_18_to_19_Org" is equal 0 , this means that the value of "HH_Org" is wrong
    # so we will replace the value of "Happy_Hour_Item" with the value of "Happy_Hour" column
    # and then get the year and month from the Date column
    # then get that month data only and find the most frequent value and not equal 0 of "Base_Price_Hours_Org" , "Slot_12_to_18_Org" , "Slot_18_to_19_Org"
    # if most frequent value of "Slot_18_to_19_Org" is equal to "Slot_18_to_19" , this means that wrong value 
    # then get the most frequent value of previous month and replace it in "Slot_18_to_19" column

    # daily_prices_final["Year_Month"] = pd.to_datetime(daily_prices_final["Date"]).dt.to_period('M')
    # new_months_prices = daily_prices_final.groupby('Year_Month').agg({
    #     'Base_Price_Hours': safe_mode,
    #     'Slot_12_to_18': safe_mode,
    #     'Slot_18_to_19': safe_mode
    # }).reset_index()
    # new_months_prices["Prev_Slot_18_to_19"] = new_months_prices["Slot_18_to_19"].shift(1)
    # daily_prices_final = pd.merge(daily_prices_final, new_months_prices[['Year_Month', 'Prev_Slot_18_to_19']], on='Year_Month', how='left')

    # change the type of "D_Org" and "Discount" to float
    # to avoid error in comparison , we need to make sure all values are numeric
    daily_prices_final["D_Org"] = daily_prices_final["D_Org"].astype(float)
    daily_prices_final["Discount_Item"] = daily_prices_final["Discount_Item"].astype(float)
    daily_prices_final["Discount"] = daily_prices_final["Discount"].astype(float)
 
    # Case 1
    print("Applying Case 1 fix...")
    # fix the happy hour 12-6 recorded wrongly as 12-7 when the "Happy_Hour" is equal "Happy Hour 12-6"
    condition1 = daily_prices_final["HH_Org"] == "Happy Hour 12-7"
    condition2 = daily_prices_final["Happy_Hour"] == "Happy Hour 12-6"
    # and "Slot_18_to_19_Org" is equal 0
    condition3 = daily_prices_final["Slot_18_to_19_Org"] == 0
    # and "D_Org" is equal "Discount" column
    condition4 = daily_prices_final["D_Org"] == daily_prices_final["Discount"]
    mask = condition1 & condition2 & condition3 & condition4
    print(f"Number of rows matching all conditions for Case 1: {mask.sum()}")
    # then we will replace the value of "Happy_Hour_Item" with the value of "Happy_Hour" column
    daily_prices_final.loc[mask, "Happy_Hour_Item"] = daily_prices_final.loc[mask, "Happy_Hour"]
    # replace the value of "Slot_18_to_19" with the value of "Base_Price_Hours"
    daily_prices_final.loc[mask, "Slot_18_to_19"] = daily_prices_final.loc[mask, "Base_Price_Hours"]



    # Case 2 A
    print("Applying Case 2 fix...")
    # fix Unknown values
    # if "HH_Org" is equal "Unknown" and "Happy_Hour" is equal  "Happy Hour 12-6" or "Happy Hour 12-7"
    condition1 = daily_prices_final["HH_Org"] == "Unknown"
    condition2 = daily_prices_final["Happy_Hour"].isin(["Happy Hour 12-7", "Happy Hour 12-6"])
    # if "Base_Price_Hours_Org" is equal "Slot_12_to_18_Org" and "Slot_18_to_19_Org" is equal( 0 or previous "Slot_18_to_19_Org")
    condition3 = daily_prices_final["Base_Price_Hours_Org"] == daily_prices_final["Slot_12_to_18_Org"]
    previous_slot_18_to_19 = daily_prices_final["Slot_18_to_19_Org"].shift(1)
    condition4 = (daily_prices_final["Slot_18_to_19_Org"] == 0) | (daily_prices_final["Slot_18_to_19_Org"] == previous_slot_18_to_19)
    # and "Slot_12_to_18" is equal previous "Slot_12_to_18" value
    previous_slot_12_to_18 = daily_prices_final["Slot_12_to_18"].shift(1)
    condition5 = daily_prices_final["Slot_12_to_18"] == previous_slot_12_to_18
    mask = condition1 & condition2 & condition3 & condition4 & condition5
    print(f"Number of rows matching all conditions for Case 2: {mask.sum()}")
    # this means that the happy hour is recorded wrongly as "Unknown"
    # so we will replace the value of "Happy_Hour_Item" with the value of "Happy_Hour" column
    daily_prices_final.loc[mask, "Happy_Hour_Item"] = daily_prices_final.loc[mask, "Happy_Hour"]
    daily_prices_final.loc[mask, "Discount_Item"] = daily_prices_final.loc[mask, "Discount"]
    daily_prices_final.loc[mask, "Slot_18_to_19"] = daily_prices_final.loc[mask, "Base_Price_Hours"]
    # update the base price hours to be equal previous base price hours
    daily_prices_final.loc[mask, "Base_Price_Hours"] 

    # # Case 2 B
    # print("Applying Case 2 B fix...")
    # # fix Unknown values
    # # if "HH_Org" is equal "Unknown" and "Happy_Hour" is equal  "Happy Hour 12-7"
    # condition1 = daily_prices_final["HH_Org"] == "Unknown"
    # condition2 = daily_prices_final["Happy_Hour"] == "Happy Hour 12-7"
    # # if "Base_Price_Hours_Org" is equal "Slot_12_to_18_Org" and "Slot_18_to_19_Org" is equal 0
    # condition3 = daily_prices_final["Base_Price_Hours_Org"] == daily_prices_final["Slot_12_to_18_Org"]
    # condition4 = daily_prices_final["Slot_18_to_19_Org"] == 0
    # # and "Slot_12_to_18" is equal previous "Slot_12_to_18" value
    # previous_slot_12_to_18 = daily_prices_final["Slot_12_to_18"].shift(1)
    # condition5 = daily_prices_final["Slot_12_to_18"] == previous_slot_12_to_18
    # mask = condition1 & condition2 & condition3 & condition4 & condition5
    # print(f"Number of rows matching all conditions for Case 2: {mask.sum()}")
    # # this means that the happy hour is recorded wrongly as "Unknown"
    # # so we will replace the value of "Happy_Hour_Item" with the value of "Happy_Hour" column
    # daily_prices_final.loc[mask, "Happy_Hour_Item"] = daily_prices_final.loc[mask, "Happy_Hour"]
    # daily_prices_final.loc[mask, "Discount_Item"] = daily_prices_final.loc[mask, "Discount"]
    # daily_prices_final.loc[mask, "Slot_18_to_19"] = daily_prices_final.loc[mask, "Slot_12_to_18"]


    # def fix_unknown_happy_hour(row):
    #     current_index = daily_prices_final.index.get_loc(row.name)
    #     previous_row = daily_prices_final.iloc[current_index - 1] if current_index > 0 else None
    #     condition1 = row["HH_Org"] == "Unknown"
    #     condition2 = row["Happy_Hour"] in ["Happy Hour 12-7", "Happy Hour 12-6"]
    #     condition3 = (row["Base_Price_Hours_Org"] == row["Slot_12_to_18_Org"]) and (row["Slot_18_to_19_Org"] == 0)
    #     condition4 = previous_row is not None and (row["Slot_12_to_18"] == previous_row["Slot_12_to_18"])
    #     if condition1 and condition2 and condition3 and condition4:
    #         row["Happy_Hour_Item"] = row["Happy_Hour"]
    #         row["Discount_Item"] = row["D_Org"]
    #     return row
    # daily_prices_final = daily_prices_final.apply(fix_unknown_happy_hour, axis=1)


    # Case 3:
    print("Applying Case 3 fix...")
    # fix the happy hour 12-6 recorded wrongly as 12-7 when the "Happy_Hour" is equal "Happy Hour 12-6"
    # if the "HH_Org" is equal "Happy Hour 12-7" and "Happy_Hour" is equal "Happy Hour 12-6"
    condition1 = daily_prices_final["HH_Org"] == "Happy Hour 12-7"
    condition2 = daily_prices_final["Happy_Hour"] == "Happy Hour 12-6"
   
    # and "Base_Price_Hours_Org" is equal 0 and "Slot_12_to_18_Org" is equal 0
    condition3 = (daily_prices_final["Base_Price_Hours_Org"] == 0) & (daily_prices_final["Slot_12_to_18_Org"] == 0)

    # get the previous value of "Slot_18_to_19"
    previous_slot_18_to_19 = daily_prices_final["Slot_18_to_19"].shift(1)

    # and "Slot_18_to_19" is not equal previous "Slot_18_to_19" value and equal to previous "Slot_12_to_18" value
    condition4 = (daily_prices_final["Slot_18_to_19"] != previous_slot_18_to_19) & (daily_prices_final["Slot_18_to_19"] == daily_prices_final["Slot_12_to_18"].shift(1))

    # and "D_Org" is equal "Discount"
    condition5 = daily_prices_final["D_Org"] == daily_prices_final["Discount"]
    mask = condition1 & condition2 & condition3 & condition4 & condition5

    print(f"Number of rows matching all conditions for Case 3: {mask.sum()}")

    # then we will replace the value of "Happy_Hour_Item" with the value of "Happy_Hour" column
    daily_prices_final.loc[mask, "Happy_Hour_Item"] = daily_prices_final.loc[mask, "Happy_Hour"]

   

    # Case 4 fix (if any)
    print("Applying Case 4 fix...")
    # if the "HH_Org" is equal "Happy Hour 12-7" and "Happy_Hour" is equal "Happy Hour 12-6"
    condition1 = daily_prices_final["HH_Org"] == "Happy Hour 12-7"
    condition2 = daily_prices_final["Happy_Hour"] == "Happy Hour 12-6"
    # and "D_Org" is  equal "Discount"
    condition3 = daily_prices_final["D_Org"] == daily_prices_final["Discount"]
    # previous "HH_Org" is equal "Happy Hour 12-6" and previous "Base_Price_Hours_Org" is equal "Base_Price_Hours_Org"
    previous_row = daily_prices_final.shift(1)
    condition4 = (previous_row["HH_Org"] == "Happy Hour 12-6") & (previous_row["Base_Price_Hours_Org"] == daily_prices_final["Base_Price_Hours_Org"])
    # next "HH_Org" is equal "Happy Hour 12-6" and next "Base_Price_Hours_Org" is equal "Base_Price_Hours_Org"
    next_row = daily_prices_final.shift(-1)
    condition5 = (next_row["HH_Org"] == "Happy Hour 12-6") & (next_row["Base_Price_Hours_Org"] == daily_prices_final["Base_Price_Hours_Org"])
    mask = condition1 & condition2 & condition3 & condition4 & condition5
    print(f"Number of rows matching all conditions for Case 4: {mask.sum()}")
    # then we will replace the value of "Happy_Hour_Item" with the value of "Happy_Hour" column
    daily_prices_final.loc[mask, "Happy_Hour_Item"] = daily_prices_final.loc[mask, "Happy_Hour"]
    # then we will replace the value of "Slot_18_to_19" with the value of "Base_Price_Hours"
    daily_prices_final.loc[mask, "Slot_18_to_19"] = daily_prices_final.loc[mask, "Base_Price_Hours"]



     # Case 5 fix (if any)
    print("Applying Case 5 fix...")
    # if the "HH_Org" is equal "Happy Hour 12-6" and "Happy_Hour" is equal "Happy Hour 12-7"
    condition1 = daily_prices_final["HH_Org"] == "Happy Hour 12-6"
    condition2 = daily_prices_final["Happy_Hour"] == "Happy Hour 12-7"
    # and "D_Org" is  equal "Discount"
    condition3 = daily_prices_final["D_Org"] == daily_prices_final["Discount"]
    # previous "HH_Org" is equal "Happy Hour 12-7" and previous "Base_Price_Hours" is equal "Base_Price_Hours"
    previous_row = daily_prices_final.shift(1)
    condition4 = (previous_row["HH_Org"] == "Happy Hour 12-7") & (previous_row["Base_Price_Hours"] == daily_prices_final["Base_Price_Hours"])
    # next "HH_Org" is equal "Happy Hour 12-6" and next "Base_Price_Hours" is equal "Base_Price_Hours"
    next_row = daily_prices_final.shift(-1)
    condition5 = (next_row["HH_Org"] == "Happy Hour 12-7") & (next_row["Base_Price_Hours"] == daily_prices_final["Base_Price_Hours"])
    mask = condition1 & condition2 & condition3 & condition4 & condition5
    print(f"Number of rows matching all conditions for Case 5: {mask.sum()}")
    # then we will replace the value of "Happy_Hour_Item" with the value of "Happy_Hour" column
    daily_prices_final.loc[mask, "Happy_Hour_Item"] = daily_prices_final.loc[mask, "Happy_Hour"]
    # then we will replace the value of "Slot_18_to_19" with the value of "Slot_12_to_18"
    daily_prices_final.loc[mask, "Slot_18_to_19"] = daily_prices_final.loc[mask, "Slot_12_to_18"]









    file_name = f"{item_name.replace(' ', '_')}.xlsx"
    output_file = f"{output_folder}\{file_name}"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    daily_prices_final.to_excel(output_file, index=False)
    print(f"Price history script generated for {item_name} and saved to {output_file}")
    

generate_price_history_script("Amstel Pint")
    
