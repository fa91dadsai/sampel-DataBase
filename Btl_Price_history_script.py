import pandas as pd 
import os 
import re 

# --- CONFIGURATION ---
DATA_PATH = r'C:\Users\fadia\OneDrive\Desktop\Ody\Scripts\Transformed Data\Master Combined\Master_Sales_Data_2021-08-19_to_2025-07-22.csv'
OUTPUT_BASE_PATH = r'C:\Users\fadia\OneDrive\Desktop\Ody\sampel DataBase\Product_History_Reports\Btl'
ITEM_FILTER = 'Btl'
FUTURE_DATE = pd.to_datetime('2099-12-31').date() # Define the far future date once

# --- DATA PROCESSING FUNCTION ---
def generate_product_history_report(df: pd.DataFrame, item_name: str, start_date_overall: pd.Timestamp.date) -> pd.DataFrame:
    """
    Generates a price history report (ValidFrom/ValidTo) for a specific item 
    by identifying records where the price has changed.
    """
    # 1. Filter and Select necessary columns
    item_df = df[df['Item'] == item_name].copy()
    item_df = item_df[['Date', 'Price']]

    # 2. Convert and Sort
    # The 'Date' column is now a datetime object from the caller (main function)
    item_df = item_df.sort_values('Date').reset_index(drop=True)

    # 3. Identify Price Changes (Core Logic)
    item_df["Price_Changed"] = item_df["Price"] != item_df["Price"].shift(1)
    # Ensure the *very first* price in the item's history is always included
    item_df["Price_Changed"] = item_df["Price_Changed"].fillna(True)
    
    # 4. Final Filter and Cleanup
    # Filter only the change events and create a clean copy for the final report structure
    history_df = item_df[item_df["Price_Changed"] == True].copy()
    
    # Check if the history is empty before proceeding with date logic
    if history_df.empty:
        return history_df

    # 5. Define Time Validity (SCD Type 2-like structure)
    
    # ValidFrom: The date the price takes effect (converted to python date object)
    history_df["ValidFrom"] = history_df['Date'].dt.date
    
    # The first record's ValidFrom should be the overall earliest date in the dataset
    # We use .iloc[0] and explicit assignment to avoid warnings.
    history_df.loc[history_df.index[0], "ValidFrom"] = start_date_overall
    
    # ValidTo: The day *before* the next price change date.
    # Shift the date column up by 1 and subtract 1 day, then convert to python date object.
    history_df["ValidTo"] = (history_df['Date'].shift(-1) - pd.Timedelta(days=1)).dt.date
    
    # The last record's ValidTo is set to the far future date
    # FIX: Assign the result of fillna back to the column explicitly
    history_df["ValidTo"] = history_df["ValidTo"].fillna(FUTURE_DATE)
    
    # 6. Final Structure
    history_df["Item"] = item_name
    history_df["Type"] = ITEM_FILTER
    history_df["cost"] = 0 # Add cost column with default value 0
    
    # Select and reorder final columns, dropping the auxiliary columns
    final_cols = ['Item', 'Price', 'cost', 'ValidFrom', 'ValidTo', 'Type']
    return history_df[final_cols]

# --- MAIN EXECUTION ---
def main():
    """Main function to load data, process reports, and save results."""
    
    # 1. Load and Prepare Initial Data
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    # FIX: Convert the 'Date' column to datetime *here* before any operation that
    # requires date functions (like .min().date())
    df['Day_Date'] = pd.to_datetime(df['Day_Date'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce') 
    df = df[["Date", "Item", "Price"]]
    
    # Determine the overall earliest date in the dataset to use for the first ValidFrom record
    # This must be done *after* the 'Date' column is converted to datetime.
    start_date_overall = df['Date'].min().date()
    
    # df_final is used to combine all reports into one master file
    df_final = pd.DataFrame() 

    # 2. Identify Target Items
    all_items = df['Item'].unique()
    target_items = [item for item in all_items if ITEM_FILTER in item]

    # 3. Ensure Output Directory Exists
    if not os.path.exists(OUTPUT_BASE_PATH):
        os.makedirs(OUTPUT_BASE_PATH)
        print(f"Created output directory: {OUTPUT_BASE_PATH}")

    # 4. Generate and Save Individual Reports
    for item_name in target_items:
        # Pass the overall start date to the function
        item_df = generate_product_history_report(df, item_name, start_date_overall)
        
        # Combine the item's report into the master DataFrame
        df_final = pd.concat([df_final, item_df], ignore_index=True)
        
        # Sanitize filename (removes special chars and spaces)
        safe_item_name = re.sub(r'[^\w\.\-]', '', item_name.replace(' ', '_'))
        file_name = f"{safe_item_name}.csv"
        
        output_file = os.path.join(OUTPUT_BASE_PATH, file_name)
        
        # Only save if there's actual data
        if not item_df.empty:
            item_df.to_csv(output_file, index=False)
        else:
            print(f"Warning: No valid price history found for {item_name}. Skipping individual save.")

    # 5. Save List of Processed Items and Master Report
    items_df = pd.DataFrame(target_items, columns=['Item'])
    list_file_path = os.path.join(OUTPUT_BASE_PATH, f"{ITEM_FILTER}_Items.csv")
    items_df.to_csv(list_file_path, index=False)
    
    master_file_path = os.path.join(OUTPUT_BASE_PATH, f"{ITEM_FILTER}_Combined_Price_History.csv")
    df_final.to_csv(master_file_path, index=False)

    # 6. Final Confirmation
    print("\n--- Process Complete ---")
    print(f"✅ Product history reports for {len(target_items)} items have been generated and saved to {OUTPUT_BASE_PATH}.")
    print(f"📄 Master list saved to {list_file_path}.")
    print(f"📄 Combined price history saved to {master_file_path}.")

if __name__ == '__main__':
    main()