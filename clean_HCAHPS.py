import pandas as pd
import numpy as np

# load dataset
df = pd.read_csv('HCAHPS-Hospital.csv')

# clean not applicalbe string
df.replace('Not Applicable', np.nan, inplace=True)

# create answer column based on the question type
df['Measure_Value'] = df['HCAHPS Answer Percent'].fillna(
    df['HCAHPS Linear Mean Value']
).fillna(
    df['Patient Survey Star Rating']
)

# Define core attributes for a facility
facility_cols = [
    'Facility ID', 'Facility Name', 'Address', 'City/Town', 
    'State', 'ZIP Code', 'County/Parish', 'Telephone Number', 
    'Number of Completed Surveys', 'Survey Response Rate Percent',
    'Start Date', 'End Date'
]

# Create pivot table
df_wide = df.pivot_table(
    index=facility_cols,
    columns='HCAHPS Measure ID',
    values='Measure_Value',
    aggfunc='first'
).reset_index()

# Set column names
df_wide.columns.name = None

# Save dataset to CSV
print(df_wide.head())
df_wide.to_csv('HCAHPS-Hospital_cleaned.csv', index=False)

df = df.loc[df['Facility ID'] == '010001']
df = df[["HCAHPS Measure ID","HCAHPS Question"]]
df.to_csv('HCAHPS-Hospital_dictionary.csv', index=False)