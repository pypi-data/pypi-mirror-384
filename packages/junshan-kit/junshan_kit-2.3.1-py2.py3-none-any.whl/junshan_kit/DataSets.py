"""
----------------------------------------------------------------------
>>> Author       : Junshan Yin  
>>> Last Updated : 2025-xx-xx
----------------------------------------------------------------------
"""

import os, time
import pandas as pd
import junshan_kit.DataProcessor
import junshan_kit.kit
from sklearn.preprocessing import StandardScaler

#----------------------------------------------------------
def _download_data(data_name):
    from junshan_kit.kit import JianguoyunDownloaderFirefox, JianguoyunDownloaderChrome

    # User selects download method
    while True:
        # User inputs download URL
        url = input("Enter the Jianguoyun download URL: ").strip()

        print("Select download method:")
        print("1. Firefox")
        print("2. Chrome")
        choice = input("Enter the number of your choice (1 or 2): ").strip()

        if choice == "1":
            JianguoyunDownloaderFirefox(url, f"./exp_data/{data_name}").run()
            print("✅ Download completed using Firefox")
            break
        elif choice == "2":
            JianguoyunDownloaderChrome(url, f"./exp_data/{data_name}").run()
            print("✅ Download completed using Chrome")
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.\n")

def _run(csv_path, data_name, drop_cols, label_col, label_map, print_info):
    if not os.path.exists(csv_path):
        print('\n' + '*'*60)
        print(f"Please download the data.")
        print(csv_path)
        _download_data(data_name)
        junshan_kit.kit.unzip_file(f'./exp_data/{data_name}/{data_name}.zip', f'./exp_data/{data_name}')
        
    cleaner = junshan_kit.DataProcessor.CSV_TO_Pandas()
    df = cleaner.preprocess_dataset(csv_path, drop_cols, label_col, label_map, data_name, print_info=print_info)

    return df

"""
----------------------------------------------------------------------
                            Datasets
----------------------------------------------------------------------
"""

def credit_card_fraud_detection(data_name = "Credit Card Fraud Detection", print_info = False):

    csv_path = f'./exp_data/{data_name}/creditcard.csv'
    drop_cols = []
    label_col = 'Class' 
    label_map = {0: -1, 1: 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df


def diabetes_health_indicators_dataset(data_name = "Diabetes Health Indicators", print_info = False):
    csv_path = f'./exp_data/{data_name}/diabetes_dataset.csv'
    drop_cols = []
    label_col = 'diagnosed_diabetes'
    label_map = {0: -1, 1: 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df


def electric_vehicle_population_data(data_name = "Electric Vehicle Population", print_info = False):
    csv_path = f'./exp_data/{data_name}/Electric_Vehicle_Population_Data.csv'
    drop_cols = ['VIN (1-10)', 'DOL Vehicle ID', 'Vehicle Location']
    label_col = 'Electric Vehicle Type'
    label_map = {
    'Battery Electric Vehicle (BEV)': 1,
    'Plug-in Hybrid Electric Vehicle (PHEV)': -1
    }

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df

def global_house_purchase_dataset(data_name = "Global House Purchase", print_info = False):
    csv_path = f'./exp_data/{data_name}/global_house_purchase_dataset.csv'
    drop_cols = ['property_id']
    label_col = 'Electric Vehicle Type'
    label_map = {0: -1, 1: 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df


def health_lifestyle_dataset(data_name = "Health Lifestyle", print_info = False):
    csv_path = f'./exp_data/{data_name}/health_lifestyle_dataset.csv'
    drop_cols = ['id']
    label_col = 'decision'
    label_map = {0: -1, 1: 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df





def wine_and_food_pairing_dataset():
    pass 

