import sqlite3
import pandas as pd
import plotly.express as px

DB_NAME = "us_hospitals_reviews.db"
MAP_OUTPUT_HTML = "hospital_ratings_by_state.html"


def create_state_rating_map():
    conn = sqlite3.connect(DB_NAME)

    # SQL query to calculate average hospital rating and totals per state
    query = """
        SELECT 
            UPPER(TRIM(h.state)) AS state,
            ROUND(AVG(h.hospital_rating), 2) AS avg_hospital_rating,
            COUNT(DISTINCT h.place_id) AS total_hospitals,
            COUNT(r.id) AS total_reviews_collected
        FROM hospitals h
        LEFT JOIN reviews r ON h.place_id = r.place_id
        WHERE h.state IS NOT NULL AND LENGTH(TRIM(h.state)) = 2
        GROUP BY UPPER(TRIM(h.state))
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("No valid state data found in the database.")
        return

    # Generate interactive US state choropleth map
    fig = px.choropleth(
        df,
        locations="state",
        locationmode="USA-states",
        color="avg_hospital_rating",
        scope="usa",
        color_continuous_scale="RdYlGn",
        range_color=[1.0, 5.0],
        title="<b>Average Hospital Review Rating by State</b>",
        labels={
            "avg_hospital_rating": "Avg Rating (1-5)",
            "state": "State",
            "total_hospitals": "Hospitals Counted",
            "total_reviews_collected": "Total Reviews"
        },
        hover_data={
            "state": True,
            "avg_hospital_rating": ":.2f",
            "total_hospitals": ":,",
            "total_reviews_collected": ":,"
        }
    )

    # Customize map layout and styling
    fig.update_layout(
        geo=dict(
            scope="usa",
            bgcolor="rgba(0,0,0,0)",
            showlakes=True,
            lakecolor="rgb(240, 248, 255)"
        ),
        margin={"r": 10, "t": 60, "l": 10, "b": 10},
        coloraxis_colorbar=dict(
            title="Avg Rating",
            ticks="outside"
        )
    )

    # Save to interactive HTML file
    fig.write_html(MAP_OUTPUT_HTML)
    print(f"Map successfully generated! Double-click '{MAP_OUTPUT_HTML}' to open it in your web browser.")

if __name__ == "__main__":
    create_state_rating_map()