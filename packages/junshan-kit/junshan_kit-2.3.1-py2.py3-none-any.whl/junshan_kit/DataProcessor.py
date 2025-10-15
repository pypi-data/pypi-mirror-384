"""
----------------------------------------------------------------------
>>> Author       : Junshan Yin
>>> Last Updated : 2025-10-12
----------------------------------------------------------------------
"""

import pandas as pd


class CSV_TO_Pandas:
    def __init__(self):
        pass

    def preprocess_dataset(
        self,
        csv_path,
        drop_cols: list,
        label_col: str,
        label_map: dict,
        data_name: str,
        print_info=False,
    ):
        """
        Preprocess a CSV dataset by performing data cleaning, label mapping, and feature encoding.

        This function loads a dataset from a CSV file, removes specified non-feature columns,
        drops rows with missing values, maps the target label to numerical values, and
        one-hot encodes categorical features. Optionally, it can print dataset statistics
        before and after preprocessing.

        Args:
            csv_path (str):
                Path to the input CSV dataset.
            drop_cols (list):
                List of column names to drop from the dataset.
            label_col (str):
                Name of the target label column.
            label_map (dict):
                Mapping dictionary for label conversion (e.g., {"yes": 1, "no": -1}).
            print_info (bool, optional):
                Whether to print preprocessing information and dataset statistics.
                Defaults to False.

        Returns:
            pandas.DataFrame:
                The cleaned and preprocessed dataset ready for model input.

        Steps:
            1. Load the dataset from CSV.
            2. Drop non-informative or irrelevant columns.
            3. Remove rows with missing values.
            4. Map label column to numerical values according to `label_map`.
            5. One-hot encode categorical (non-label) text features.
            6. Optionally print dataset information and summary statistics.

        Example:
            >>> label_map = {"positive": 1, "negative": -1}
            >>> df = data_handler.preprocess_dataset(
            ...     csv_path="data/raw.csv",
            ...     drop_cols=["id", "timestamp"],
            ...     label_col="sentiment",
            ...     label_map=label_map,
            ...     print_info=True
            ... )
        """
        # Step 0: Load the dataset
        df = pd.read_csv(csv_path)

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

        df = pd.get_dummies(df, columns=text_feature_cols, dtype=int)
        m_cleaned, n_cleaned = df.shape

        # print info
        if print_info:
            pos_count = (df[label_col] == 1).sum()
            neg_count = (df[label_col] == -1).sum()

            # Step 6: Print dataset information
            print("\n" + "=" * 80)
            print(f"{'{data_name} - Info':^70}")
            print("=" * 80)
            print(f"{'Original size:':<40} {m_original} rows x {n_original} cols")
            print(
                f"{'Size after dropping NaN & non-feature cols:':<40} {m_cleaned} rows x {n_cleaned} cols"
            )
            print(f"{'Positive samples (+1):':<40} {pos_count}")
            print(f"{'Negative samples (-1):':<40} {neg_count}")
            print(
                f"{'Size after one-hot encoding:':<40} {m_encoded} rows x {n_encoded} cols"
            )
            print("-" * 80)
            print(f"Note:")
            print(f"{'Label column:':<40} {label_col}")
            print(
                f"{'Dropped non-feature columns:':<40} {', '.join(drop_cols) if drop_cols else 'None'}"
            )
            print(
                f"{'text fetaure columns:':<40} {', '.join(list(text_feature_cols)) if list(text_feature_cols) else 'None'}"
            )
            print("=" * 80 + "\n")

        return df
