# -*- coding: utf-8 -*-
"""G_RandonForest_terrorism.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1qQrvGjJEGsAZ2K3wWAnqZVmbhG5WoVEj

## Importing libraries
"""

from pandas.plotting import scatter_matrix
import warnings
import seaborn as sns
import os
import mpl_toolkits
import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn import datasets
from matplotlib import pyplot
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import pickle

"""## Load Data"""

df = pd.read_csv('/content/drive/MyDrive/Seismic_Consult/globalterrorismdb_0718dist.csv', encoding='ISO-8859-1')

df.head()

"""## Get columns names with mixed data types"""

# List of column indices with mixed types
mixed_type_indices = [4, 6, 31, 33, 61, 62, 63, 76, 79, 90, 92, 94, 96, 114, 115, 121]

# Get column names
column_names = df.columns

# Retrieve column names based on indices
mixed_type_columns = [column_names[i] for i in mixed_type_indices]

# Print the column names with mixed types
print(mixed_type_columns)

df.describe()

"""## **Data Cleaning**

## Checking for data type with the highest percentage (i.e the most predominant) in columns containing mixed data types
"""

# List of columns to check data types
columns_to_check = ['approxdate', 'resolution', 'attacktype2_txt', 'attacktype3_txt', 'gsubname2', 'gname3', 'gsubname3',
                    'claimmode2_txt', 'claimmode3_txt', 'weaptype3_txt', 'weapsubtype3_txt', 'weaptype4_txt',
                    'weapsubtype4_txt', 'divert', 'kidhijcountry', 'ransomnote']

# Function to determine the most frequent data type in a column
def most_frequent_dtype(column):
    dtype_counts = column.apply(lambda x: type(x)).value_counts(normalize=True)
    return dtype_counts.idxmax(), dtype_counts.max()

# Iterate through the specified columns and get the most frequent data type
dtype_info = {col: most_frequent_dtype(df[col]) for col in columns_to_check}

# Print the results
for col, (dtype, percentage) in dtype_info.items():
    print(f"Column '{col}': Most frequent data type is {dtype} with {percentage:.2%} of the values")

df.shape

"""## Dropping rows containg the least predominant datatypes (i.e less than 2 %)"""

# List of columns to check data types
columns_to_check = ['approxdate', 'resolution', 'attacktype2_txt', 'attacktype3_txt', 'gsubname2', 'gname3', 'gsubname3',
                    'claimmode2_txt', 'claimmode3_txt', 'weaptype3_txt', 'weapsubtype3_txt', 'weaptype4_txt',
                    'weapsubtype4_txt', 'divert', 'kidhijcountry', 'ransomnote']

# Function to determine the most frequent data type in a column
def most_frequent_dtype(column):
    dtype_counts = column.apply(lambda x: type(x)).value_counts(normalize=True)
    return dtype_counts.idxmax()

# Identify the most frequent data type for each specified column
most_frequent_dtypes = {col: most_frequent_dtype(df[col]) for col in columns_to_check}

# Function to filter rows based on the most frequent data type
def filter_rows_by_dtype(df, columns_to_check, most_frequent_dtypes):
    for col in columns_to_check:
        predominant_dtype = most_frequent_dtypes[col]
        df = df[df[col].apply(lambda x: isinstance(x, predominant_dtype))]
    return df

# Filter the DataFrame
df = filter_rows_by_dtype(df, columns_to_check, most_frequent_dtypes)

# Display the filtered DataFrame
print(df)

df.shape

"""## Create a heatmap of missing values

"""

plt.figure(figsize=(10, 6))
sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
plt.title('Missing Values Heatmap')
plt.show()

df.shape

"""## Drop columns with more than 80% of missing values"""

# Drop columns with a high percentage of missing values
threshold = 0.8 # Drop columns with more than 80% missing values
df.dropna(thresh=len(df) * threshold, axis=1, inplace=True)
print("\nColumns after dropping those with more than {}% missing values:".format(threshold * 100))
print(df.columns)

df.shape

plt.figure(figsize=(10, 6))
sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
plt.title('Missing Values Heatmap')
plt.show()

"""## Check percentage of missing values in each column and filter them out"""

# Calculate the percentage of missing values for each column
missing_percentage = df.isnull().mean() * 100

# Round up to whole numbers
missing_percentage = missing_percentage.round()

# Filter out columns with no missing values and sort in descending order
missing_percentage = missing_percentage[missing_percentage > 0].sort_values(ascending=False)

print("Percentage of missing values in each column:")
print(missing_percentage)

# List of columns to check data types for
columns_to_check = [
    'weapsubtype1', 'weapsubtype1_txt', 'nwound', 'targsubtype1', 'targsubtype1_txt',
    'nkill', 'latitude', 'longitude', 'natlty1', 'natlty1_txt'
]

# Display the data types of the specified columns
column_data_types = df[columns_to_check].dtypes

print(column_data_types)

"""## Fill missing values with mode"""

# Function to fill missing values with mode for object columns and mean for numeric columns
def fill_missing(df):
    for column in df.columns:
        if df[column].dtype == 'object':  # Check if column is categorical
            mode_value = df[column].mode()[0]  # Calculate mode
            df[column].fillna(mode_value, inplace=True)  # Fill with mode
        elif np.issubdtype(df[column].dtype, np.number):  # Check if column is numeric
            mean_value = df[column].mean()  # Calculate mean
            df[column].fillna(mean_value, inplace=True)  # Fill with mean
    return df

# Apply the function to the DataFrame
df = fill_missing(df)

plt.figure(figsize=(10, 6))
sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
plt.title('Missing Values Heatmap')
plt.show()

df.shape

"""## **Drop Outliers from columns containing numeric vaalues**"""

# Iterate over each column
for column in df.columns:
    # Check if the column is of float type
    if df[column].dtype == 'float64' or df[column].dtype == 'float32':
        # Calculate IQR
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1

        # Define thresholds for outliers
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        # Identify outliers
        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]

        # Drop rows with outliers
        df2 = df.drop(outliers.index)

df2.shape #(160503, 47)

# Drop column 'eventid' from the DataFrame
df2.drop(columns='eventid', inplace=True)

"""## Removing unknown values in the coordinates"""

df2 = df2[pd.notnull(df2.latitude)]
df2 = df2[pd.notnull(df2.longitude)]
print("Removed succcessfully")

df2.shape #(160503, 47)

"""## Check for Dublicates"""

# Number of duplicates values
df2.duplicated().sum()

# Removal of duplicates values
df2.drop_duplicates(keep=False,inplace=True)

# No more null values
df2.isnull().sum()

df2.shape

"""## Drop columns with high cardinality of categorical Features"""

categorical_features = df.select_dtypes(include=['object']).columns
high_cardinality_features = [col for col in categorical_features if df[col].nunique() > 100]
df2 = df2.drop(columns=high_cardinality_features)

df2.shape

"""## Seperate Data into feature and target"""

X = df2.drop(columns=['success'])
y = df2['success']

"""# Identify categorical and numerical columns"""

cat_features = X.select_dtypes(include=['object']).columns.tolist()
num_features = X.select_dtypes(include=['number']).columns.tolist()

"""## Preprocess categorical features and numerical features"""

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
    ])

"""## Create a pipeline that preprocesses the data and then applies RandomForest"""

pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(random_state=42))
])

"""## Split the data into training and validation sets"""

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

"""## Train Model"""

pipeline.fit(X_train, y_train)

"""## Predict on the validation set"""

y_pred = pipeline.predict(X_val)

"""## Evaluate the model"""

accuracy = accuracy_score(y_val, y_pred) * 100  # Convert to percentage
print(f"Validation Accuracy: {accuracy:.0f}%")  # Round to whole number
print("Classification Report:")
print(classification_report(y_val, y_pred))

# Get the confusion matrix
conf_matrix = confusion_matrix(y_val, y_pred)
print("Confusion Matrix:")
print(conf_matrix)

"""## Save model"""

# Define the folder path
folder_path = '/content/drive/MyDrive/Seismic_Consult'

# Ensure the folder exists, create it if necessary
os.makedirs(folder_path, exist_ok=True)

# Save the model to a file inside the folder
model_file = os.path.join(folder_path, 'model.pkl')
with open(model_file, 'wb') as f:
    pickle.dump(pipeline, f)

print(f"Model saved to {model_file}")