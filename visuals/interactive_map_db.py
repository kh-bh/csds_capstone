import os
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import pgeocode
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv() 

# ---------------------------------------------------------
# 1. Supabase Credentials & Client Initialization
# ---------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dtlwchocgmwnoiflwibd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "YOUR_SERVICE_ROLE_KEY_HERE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------
# 2. Fetch Data with Pagination (Handles 1000-row REST API limit)
# ---------------------------------------------------------
def fetch_all_reviews(table_name: str = "google_hospital_reviews") -> pd.DataFrame:
    all_records = []
    batch_size = 1000
    start = 0

    while True:
        response = (
            supabase.table(table_name)
            .select("*")
            .range(start, start + batch_size - 1)
            .execute()
        )
        data = response.data
        if not data:
            break
        all_records.extend(data)
        if len(data) < batch_size:
            break
        start += batch_size

    return pd.DataFrame(all_records)

df = fetch_all_reviews()

# ---------------------------------------------------------
# 3. Clean and Standardize Data
# ---------------------------------------------------------
# Map column names if your database schema differs slightly
column_mapping = {
    'rating': 'hospital_rating',
    'google_place_id': 'place_id',
}
df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)

# Ensure hospital_rating is numeric
df['hospital_rating'] = pd.to_numeric(df['hospital_rating'], errors='coerce')

# Format ZIP codes to clean 5-digit strings
df['zip_clean'] = df['zip_clean'].astype(str).str.extract(r'(\d+)')[0].str.zfill(5)

# Deduplicate to unique hospitals so multiple reviews don't skew hospital averages
dedup_cols = ['place_id'] if 'place_id' in df.columns else ['clean_name', 'zip_clean']
hospital_df = df.dropna(subset=['hospital_rating', 'state', 'zip_clean']).drop_duplicates(
    subset=dedup_cols
).copy()

# ---------------------------------------------------------
# 4. Resolve Lat/Lon for ZIP Codes using pgeocode
# ---------------------------------------------------------
nomi = pgeocode.Nominatim('us')
unique_zips = hospital_df[['zip_clean']].drop_duplicates()

# Fetch coordinate metadata
zip_info = nomi.query_postal_code(unique_zips['zip_clean'].tolist())
unique_zips['lat'] = zip_info['latitude'].values
unique_zips['lon'] = zip_info['longitude'].values

# Merge coordinates back into hospital DataFrame
hospital_df = hospital_df.merge(unique_zips, on='zip_clean', how='left')
hospital_df = hospital_df.dropna(subset=['lat', 'lon'])

# ---------------------------------------------------------
# 5. Aggregate Data
# ---------------------------------------------------------
# State-level summary
state_df = hospital_df.groupby('state', as_index=False).agg(
    avg_hospital_rating=('hospital_rating', 'mean'),
    hospital_count=('hospital_rating', 'count')
)

# ZIP-level summary
zip_df = hospital_df.groupby(['state', 'zip_clean', 'lat', 'lon'], as_index=False).agg(
    avg_hospital_rating=('hospital_rating', 'mean'),
    hospital_count=('hospital_rating', 'count')
)

# ---------------------------------------------------------
# 6. Dash App Layout
# ---------------------------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("Average Hospital Rating by State & ZIP Code", style={'textAlign': 'center'}),
    
    html.Div([
        html.Div([
            html.H4("Select a State on the Map"),
            dcc.Graph(id='state-map')
        ], style={'width': '49%', 'display': 'inline-block'}),
        
        html.Div([
            html.H4(id='zip-header', children="ZIP Code Details"),
            dcc.Graph(id='zip-map')
        ], style={'width': '49%', 'display': 'inline-block', 'float': 'right'})
    ])
])

# ---------------------------------------------------------
# 7. Callbacks
# ---------------------------------------------------------
@app.callback(
    Output('state-map', 'figure'),
    Input('state-map', 'id')
)
def render_state_map(_):
    fig = px.choropleth(
        state_df,
        locations='state',
        locationmode="USA-states",
        color='avg_hospital_rating',
        scope="usa",
        color_continuous_scale="RdYlGn",
        labels={
            'avg_hospital_rating': 'Avg Hospital Rating',
            'hospital_count': 'Hospital Count'
        },
        hover_data={'hospital_count': True, 'avg_hospital_rating': ':.2f'}
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

@app.callback(
    [Output('zip-map', 'figure'),
     Output('zip-header', 'children')],
    Input('state-map', 'clickData')
)
def update_zip_map(clickData):
    selected_state = state_df['state'].iloc[0] if not state_df.empty else 'CA'
    
    if clickData and 'points' in clickData:
        selected_state = clickData['points'][0]['location']
        
    filtered_zips = zip_df[zip_df['state'] == selected_state]
    
    if filtered_zips.empty:
        fig = px.scatter_mapbox(zoom=3)
        return fig, f"No hospital data for {selected_state}"

    fig = px.scatter_mapbox(
        filtered_zips,
        lat="lat",
        lon="lon",
        size="hospital_count",
        color="avg_hospital_rating",
        hover_name="zip_clean",
        hover_data={
            'avg_hospital_rating': ':.2f',
            'hospital_count': True,
            'lat': False,
            'lon': False
        },
        color_continuous_scale="RdYlGn",
        zoom=6,
        size_max=25
    )
    
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    
    return fig, f"ZIP Code Hospital Ratings for {selected_state}"

if __name__ == '__main__':
    app.run(debug=True)