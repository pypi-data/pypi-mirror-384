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

def _export_csv(df, data_name):
    path = f'./data_trans_fea/{data_name}/'
    os.makedirs(path, exist_ok=True)
    df.to_csv(path + f'{data_name}.csv')
    print(path + f'{data_name}.csv')


def _run(csv_path, data_name, drop_cols, label_col, label_map, print_info, user_one_hot_cols = [], export_csv = False, ):
    if not os.path.exists(csv_path):
        print('\n' + '*'*60)
        print(f"Please download the data.")
        print(csv_path)
        _download_data(data_name)
        junshan_kit.kit.unzip_file(f'./exp_data/{data_name}/{data_name}.zip', f'./exp_data/{data_name}')   
    
    cleaner = junshan_kit.DataProcessor.CSV_TO_Pandas()
    df = cleaner.preprocess_dataset(csv_path, drop_cols, label_col, label_map, data_name,user_one_hot_cols, print_info=print_info)

    if export_csv:
        _export_csv(df, data_name)

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
    label_col = 'decision'
    label_map = {0: -1, 1: 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df


def health_lifestyle_dataset(data_name = "Health Lifestyle", print_info = False):
    csv_path = f'./exp_data/{data_name}/health_lifestyle_dataset.csv'
    drop_cols = ['id']
    label_col = 'disease_risk'
    label_map = {0: -1, 1: 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df



def medical_insurance_cost_prediction(data_name = "Medical Insurance Cost Prediction", print_info = False):
    """
    1. The missing values in this dataset are handled by directly removing the corresponding column. Since the `alcohol_freq` column contains a large number of missing values, deleting the rows would result in significant data loss, so the entire column is dropped instead.

    2. There are several columns that could serve as binary classification labels, such as `is_high_risk`, `cardiovascular_disease`, and `liver_disease`. In this case, `is_high_risk` is chosen as the label column.
    """
    csv_path = f'./exp_data/{data_name}/medical_insurance.csv'
    drop_cols = ['alcohol_freq']
    label_col = 'is_high_risk'
    label_map = {0: -1, 1: 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df


def particle_physics_event_classification(data_name = "Particle Physics Event Classification", print_info = False):
    csv_path = f'./exp_data/{data_name}/Particle Physics Event Classification.csv'
    drop_cols = []
    label_col = 'Label'
    label_map = {'s': -1, 'b': 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df



def adult_income_prediction(data_name = "Adult Income Prediction", print_info = False):
    csv_path = f'./exp_data/{data_name}/adult.csv'
    drop_cols = []
    label_col = 'income'
    label_map = {'<=50K': -1, '>50K': 1}

    df = _run(csv_path, data_name, drop_cols, label_col, label_map, print_info)

    return df




def TamilNadu_weather_2020_2025(data_name = "TN Weather 2020-2025", print_info = False, export_csv = False):
    csv_path = f'./exp_data/{data_name}/TNweather_1.8M.csv'
    label_col = 'rain_tomorrow'
    label_map = {0: -1, 1: 1}
    
    # Step 0: Load the dataset
    df = pd.read_csv(csv_path)

    df['time'] = pd.to_datetime(df['time'])
    df['year'] = df['time'].dt.year
    df['month'] = df['time'].dt.month
    df['day'] = df['time'].dt.day
    df['hour'] = df['time'].dt.hour
    
    user_one_hot_cols = ['year','month','day', 'hour']
    drop_cols = ['Unnamed: 0', 'time']

    # Save original size
    m_original, n_original = df.shape

    # Step 1: Drop non-informative columns
    df = df.drop(columns=drop_cols)

    # Step 2: Remove rows with missing values
    df = df.dropna(axis=0, how="any")
    m_encoded, n_encoded = df.shape

    # Step 3: Map target label (to -1 and +1)
    df[label_col] = df[label_col].map(label_map)

    # Step 4: Encode categorical features (exclude label column)
    text_feature_cols = df.select_dtypes(
        include=["object", "string", "category"]
    ).columns
    text_feature_cols = [
        col for col in text_feature_cols if col != label_col
    ]  # ✅ exclude label

    df = pd.get_dummies(df, columns=text_feature_cols + user_one_hot_cols, dtype=int)
    m_cleaned, n_cleaned = df.shape

    num_cols = [col for col in df.columns if col not in list(text_feature_cols) + [label_col] + user_one_hot_cols]
    scaler = StandardScaler()
    df[num_cols] = scaler.fit_transform(df[num_cols])

    if export_csv:
        _export_csv(df, data_name)

    # print info
    if print_info:
        pos_count = (df[label_col] == 1).sum()
        neg_count = (df[label_col] == -1).sum()

        # Step 6: Print dataset information
        print("\n" + "=" * 80)
        print(f"{f'{data_name} - Info':^70}")
        print("=" * 80)
        print(f"{'Original size:':<40} {m_original} rows x {n_original} cols")
        print(
            f"{'Size after dropping NaN & non-feature cols:':<40} {m_encoded} rows x {n_encoded} cols"
        )
        print(f"{'Positive samples (+1):':<40} {pos_count}")
        print(f"{'Negative samples (-1):':<40} {neg_count}")
        print(
            f"{'Size after one-hot encoding:':<40} {m_cleaned} rows x {n_cleaned} cols"
        )
        print("-" * 80)
        print(f"Note:")
        print(f"{'Label column:':<40} {label_col}") 
        print(f"{'label_map:':<40} {label_map}")
        print(
            f"{'Dropped non-feature columns:':<40} {', '.join(drop_cols) if drop_cols else 'None'}"
        )
        print(
            f"{'text fetaure columns:':<40} {', '.join(list(text_feature_cols)) if list(text_feature_cols) else 'None'}"
        )
        print("=" * 80 + "\n")

    return df
