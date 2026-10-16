import { useEffect, useMemo, useState } from "react";
import Plot from "react-plotly.js";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = "https://dtlwchocgmwnoiflwibd.supabase.co";
const supabaseKey =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR0bHdjaG9jZ213bm9pZmx3aWJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk3NTU2OTMsImV4cCI6MjEwNTMzMTY5M30.YNp-17-2fs2CwdqXItXlndHgl4BEyukG7tLK4OHaQvo";
const supabase = createClient(supabaseUrl, supabaseKey);

// ---------------------------------------------------------------------------
// Table names (edit here if yours differ)
// ---------------------------------------------------------------------------
const GENERAL_TABLE = "cms_hospitals"; // facility_id, facility_name, state, zip_code
const HCAHPS_TABLE = "hcahps_scores"; // facility_id + the HCAHPS columns below
const GOOGLE_TABLE = "google_hospital_reviews"; // needs a facility_id column to join

// ---------------------------------------------------------------------------
// Metrics shown in the dropdown. `column` is the column in hcahps_scores.
// Stars use a fixed 1-5 color range; percent metrics use the data's range.
// ---------------------------------------------------------------------------
const METRICS = [
  { key: "google", label: "Google hospital rating (1-5 stars)", legend: "Google rating", source: "google", unit: "stars", min: 1, max: 5 },
  { key: "h_star_rating", label: "HCAHPS summary star rating (1-5 stars)", legend: "Summary stars", source: "hcahps", column: "h_star_rating", unit: "stars", min: 1, max: 5 },
  { key: "h_hsp_rating_9_10", label: "Patients giving hospital a 9-10 rating (%)", legend: "% rated 9-10", source: "hcahps", column: "h_hsp_rating_9_10", unit: "percent" },
  { key: "h_recmnd_dy", label: "Patients who would definitely recommend (%)", legend: "% definitely recommend", source: "hcahps", column: "h_recmnd_dy", unit: "percent" },
  { key: "h_comp_1_a_p", label: "Nurses always communicated well (%)", legend: "% nurses always", source: "hcahps", column: "h_comp_1_a_p", unit: "percent" },
  { key: "h_comp_2_a_p", label: "Doctors always communicated well (%)", legend: "% doctors always", source: "hcahps", column: "h_comp_2_a_p", unit: "percent" },
  { key: "h_comp_5_a_p", label: "Staff always explained medicines (%)", legend: "% medicines explained", source: "hcahps", column: "h_comp_5_a_p", unit: "percent" },
  { key: "h_clean_hsp_a_p", label: "Room and bathroom always clean (%)", legend: "% always clean", source: "hcahps", column: "h_clean_hsp_a_p", unit: "percent" },
  { key: "h_quiet_hsp_a_p", label: "Area around room always quiet at night (%)", legend: "% always quiet", source: "hcahps", column: "h_quiet_hsp_a_p", unit: "percent" },
  { key: "h_comp_6_y_p", label: "Given discharge information (%)", legend: "% got discharge info", source: "hcahps", column: "h_comp_6_y_p", unit: "percent" },
];

const HCAHPS_METRICS = METRICS.filter((m) => m.source === "hcahps");

function formatValue(metric, v) {
  return metric.unit === "stars" ? v.toFixed(2) : `${v.toFixed(1)}%`;
}

// ZIP -> {lat, lon}, loaded from a file you host yourself.
// Download https://download.geonames.org/export/zip/US.zip, unzip it, and put
// the resulting US.txt in your app's /public folder so it is served at /US.txt.
// (Tab-separated; col 1 = ZIP, col 9 = latitude, col 10 = longitude.)
const ZIP_FILE_URL = "/US.txt";

async function loadZipCoords() {
  const res = await fetch(ZIP_FILE_URL);
  if (!res.ok) throw new Error(`Could not load ${ZIP_FILE_URL} (HTTP ${res.status})`);
  const text = await res.text();
  if (text.trim().startsWith("<")) {
    // Dev servers return index.html for missing files
    throw new Error(`${ZIP_FILE_URL} not found - put US.txt in your /public folder`);
  }
  const lookup = {};
  text.split(/\r?\n/).forEach((line) => {
    const cols = line.split("\t");
    if (cols.length < 11) return;
    const lat = parseFloat(cols[9]);
    const lon = parseFloat(cols[10]);
    if (cols[1] && !isNaN(lat) && !isNaN(lon)) {
      lookup[cols[1].trim().padStart(5, "0")] = { lat, lon };
    }
  });
  return lookup;
}

// Map full state names to two-letter postal codes
const STATE_NAME_TO_CODE = {
  ALABAMA: "AL", ALASKA: "AK", ARIZONA: "AZ", ARKANSAS: "AR", CALIFORNIA: "CA",
  COLORADO: "CO", CONNECTICUT: "CT", DELAWARE: "DE", FLORIDA: "FL", GEORGIA: "GA",
  HAWAII: "HI", IDAHO: "ID", ILLINOIS: "IL", INDIANA: "IN", IOWA: "IA",
  KANSAS: "KS", KENTUCKY: "KY", LOUISIANA: "LA", MAINE: "ME", MARYLAND: "MD",
  MASSACHUSETTS: "MA", MICHIGAN: "MI", MINNESOTA: "MN", MISSISSIPPI: "MS", MISSOURI: "MO",
  MONTANA: "MT", NEBRASKA: "NE", NEVADA: "NV", NEW_HAMPSHIRE: "NH", NEW_JERSEY: "NJ",
  NEW_MEXICO: "NM", NEW_YORK: "NY", NORTH_CAROLINA: "NC", NORTH_DAKOTA: "ND", OHIO: "OH",
  OKLAHOMA: "OK", OREGON: "OR", PENNSYLVANIA: "PA", RHODE_ISLAND: "RI", SOUTH_CAROLINA: "SC",
  SOUTH_DAKOTA: "SD", TENNESSEE: "TN", TEXAS: "TX", UTAH: "UT", VERMONT: "VT",
  VIRGINIA: "VA", WASHINGTON: "WA", WEST_VIRGINIA: "WV", WISCONSIN: "WI", WYOMING: "WY",
};

function normalizeStateCode(rawState) {
  if (!rawState) return null;
  const clean = String(rawState).trim().toUpperCase().replace(/\s+/g, "_");
  if (clean.length === 2) return clean;
  return STATE_NAME_TO_CODE[clean] || null;
}

// "ST. MARY'S MEDICAL CENTER" -> "St. Mary's Medical Center"
function toTitleCase(str) {
  return String(str)
    .trim()
    .toLowerCase()
    .replace(/(^|[\s\-/(])([a-z])/g, (_, sep, ch) => sep + ch.toUpperCase());
}

// CMS Facility IDs are 6 characters with leading zeros (e.g. "010001")
function normalizeFacilityId(raw) {
  if (raw === null || raw === undefined || String(raw).trim() === "") return null;
  return String(raw).trim().padStart(6, "0");
}

function normalizeZip(raw) {
  if (raw === null || raw === undefined || String(raw).trim() === "") return "N/A";
  return String(raw).trim().slice(0, 5).padStart(5, "0");
}

// HCAHPS values are stored as text and can be "Not Available", "N/A", etc.
function parseScore(raw) {
  if (raw === null || raw === undefined) return null;
  const cleaned = String(raw).replace("%", "").trim();
  if (cleaned === "") return null;
  const n = Number(cleaned);
  return isNaN(n) ? null : n;
}

// Fetch every row of a table in batches of 1000
async function fetchAll(table, columns, orderBy) {
  const batchSize = 1000;
  let all = [];
  let start = 0;
  while (true) {
    let query = supabase.from(table).select(columns);
    if (orderBy) query = query.order(orderBy);
    const { data, error } = await query.range(start, start + batchSize - 1);
    if (error) throw new Error(`${table}: ${error.message}`);
    if (!data || data.length === 0) break;
    all = all.concat(data);
    if (data.length < batchSize) break;
    start += batchSize;
  }
  return all;
}

const COLORSCALE = [
  [0.0, "#d73027"], // Red
  [0.5, "#fee08b"], // Yellow
  [1.0, "#1a9850"], // Green
];

function MapPage() {
  const [hospitals, setHospitals] = useState([]);
  const [metricKey, setMetricKey] = useState("google");
  const [selectedState, setSelectedState] = useState(null);
  const [zipCoords, setZipCoords] = useState({});
  const [zipError, setZipError] = useState("");
  const [loading, setLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState("");

  const metric = METRICS.find((m) => m.key === metricKey);

  // Load ZIP -> lat/lon lookup once
  useEffect(() => {
    loadZipCoords()
      .then(setZipCoords)
      .catch((e) => {
        console.error("ZIP lookup failed:", e);
        setZipError(e.message);
      });
  }, []);

  // Load all three tables and join them on facility_id
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const hcahpsColumns = ["facility_id", ...HCAHPS_METRICS.map((m) => m.column)].join(", ");

        const [generalRows, hcahpsRows, reviewRows] = await Promise.all([
          fetchAll(GENERAL_TABLE, "facility_id, facility_name, state, zip_code", "facility_id"),
          fetchAll(HCAHPS_TABLE, hcahpsColumns, "facility_id"),
          fetchAll(GOOGLE_TABLE, "facility_id, hospital_rating", "facility_id"),
        ]);

        if (generalRows.length === 0) {
          setStatusMsg("No rows returned from the hospital general information table.");
          setLoading(false);
          return;
        }

        // 1. Base list of hospitals from general information
        const byId = {};
        generalRows.forEach((r) => {
          const id = normalizeFacilityId(r.facility_id);
          const state = normalizeStateCode(r.state);
          if (!id || !state) return;
          byId[id] = {
            id,
            name: r.facility_name ? toTitleCase(r.facility_name) : "Hospital",
            state,
            zip: normalizeZip(r.zip_code),
            values: {}, // metricKey -> number
          };
        });

        // 2. HCAHPS scores
        hcahpsRows.forEach((r) => {
          const h = byId[normalizeFacilityId(r.facility_id)];
          if (!h) return;
          HCAHPS_METRICS.forEach((m) => {
            const v = parseScore(r[m.column]);
            if (v !== null) h.values[m.key] = v;
          });
        });

        // 3. Google rating: hospital_rating is the hospital's own overall Google
        // rating (repeated on every review row), so use it directly instead of
        // averaging the review rows. The first non-null value per hospital wins.
        reviewRows.forEach((r) => {
          const h = byId[normalizeFacilityId(r.facility_id)];
          if (!h || h.values.google !== undefined) return;
          const rating = parseScore(r.hospital_rating);
          if (rating !== null) h.values.google = rating;
        });

        setHospitals(Object.values(byId));
      } catch (err) {
        console.error("Fetch Exception:", err);
        setStatusMsg(`Database Error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // Hospitals that have a value for the selected measure
  const hospitalsWithValue = useMemo(
    () => hospitals.filter((h) => h.values[metricKey] !== undefined),
    [hospitals, metricKey]
  );

  // Color range for points: fixed for stars, data-driven for percentages
  const colorRange = useMemo(() => {
    if (metric.min !== undefined) return [metric.min, metric.max];
    const vals = hospitalsWithValue.map((h) => h.values[metricKey]);
    if (vals.length === 0) return [0, 100];
    return [Math.min(...vals), Math.max(...vals)];
  }, [metric, hospitalsWithValue, metricKey]);

  // State averages for the left-hand choropleth
  const stateMapData = useMemo(() => {
    const totals = {};
    hospitalsWithValue.forEach((h) => {
      if (!totals[h.state]) totals[h.state] = { sum: 0, count: 0 };
      totals[h.state].sum += h.values[metricKey];
      totals[h.state].count += 1;
    });

    const locations = Object.keys(totals);
    if (locations.length === 0) return [];

    const zValues = locations.map((st) =>
      Number((totals[st].sum / totals[st].count).toFixed(2))
    );
    const minZ = Math.min(...zValues);
    const maxZ = Math.max(...zValues);

    return [
      {
        type: "choropleth",
        locationmode: "USA-states",
        locations,
        z: zValues,
        colorscale: COLORSCALE,
        zmin: minZ === maxZ ? minZ - 1 : minZ,
        zmax: maxZ,
        colorbar: { title: `Avg: ${metric.legend}` },
        hovertemplate: `<b>%{location}</b><br>Avg ${metric.legend}: %{z:.2f}<extra></extra>`,
      },
    ];
  }, [hospitalsWithValue, metricKey, metric]);

  // Default the selected state to the first one with data
  const activeState =
    selectedState || (stateMapData[0] ? stateMapData[0].locations[0] : null);

  // Hospital points for the selected state, placed at their ZIP locations
  const points = useMemo(() => {
    if (!activeState || Object.keys(zipCoords).length === 0) {
      return { trace: null, missing: 0, count: 0 };
    }

    const lats = [];
    const lons = [];
    const values = [];
    const hoverTexts = [];
    const seenAtZip = {}; // spread out hospitals that share a ZIP
    let missing = 0;

    hospitalsWithValue
      .filter((h) => h.state === activeState)
      .forEach((h) => {
        const coords = zipCoords[h.zip];
        if (!coords) {
          missing += 1;
          return;
        }

        const n = seenAtZip[h.zip] || 0;
        seenAtZip[h.zip] = n + 1;

        // Golden-angle spiral gives a tiny offset for hospitals in the same ZIP
        const angle = n * 2.4;
        const r = n === 0 ? 0 : 0.01 * Math.sqrt(n);

        const v = h.values[metricKey];
        lats.push(coords.lat + r * Math.sin(angle));
        lons.push(coords.lon + r * Math.cos(angle));
        values.push(v);

        hoverTexts.push(
          `<b>${h.name}</b><br>ZIP: ${h.zip}<br>${metric.legend}: ${formatValue(metric, v)}`
        );
      });

    return {
      missing,
      count: lats.length,
      trace: {
        type: "scattermap", // real basemap tiles (MapLibre; no token needed with open-street-map style)
        mode: "markers",
        lat: lats,
        lon: lons,
        text: hoverTexts,
        hovertemplate: "%{text}<extra></extra>",
        marker: {
          size: 20,
          opacity: 0.9,
          color: values,
          colorscale: COLORSCALE,
          cmin: colorRange[0],
          cmax: colorRange[1],
          showscale: true,
          colorbar: { title: metric.legend },
        },
      },
    };
  }, [activeState, zipCoords, hospitalsWithValue, metricKey, metric, colorRange]);

  // Center/zoom the basemap on the plotted points
  let mapView = { center: { lat: 39.5, lon: -98.35 }, zoom: 3 }; // whole US fallback
  if (points.trace && points.count > 0) {
    const { lat, lon } = points.trace;
    const minLat = Math.min(...lat), maxLat = Math.max(...lat);
    const minLon = Math.min(...lon), maxLon = Math.max(...lon);
    const latSpan = Math.max(maxLat - minLat, 0.05);
    const lonSpan = Math.max(maxLon - minLon, 0.05);
    const zoom = Math.min(
      Math.log2(843 / lonSpan), // ~600px wide
      Math.log2(633 / latSpan) // ~450px tall
    ) - 0.3;
    mapView = {
      center: { lat: (minLat + maxLat) / 2, lon: (minLon + maxLon) / 2 },
      zoom: Math.max(3, Math.min(zoom, 11)),
    };
  }

  return (
    <main className="map-page" style={{ padding: "1.5rem" }}>
      <section className="map-heading">
        <p className="eyebrow">HEALTHCARE NEAR YOU</p>
        <h1>Explore Hospitals Across the U.S.</h1>
        <p>
          Pick a measure, then click any state on the left map to see individual
          hospitals on the right.
        </p>

        <label style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
          <strong>Measure:</strong>
          <select
            value={metricKey}
            onChange={(e) => setMetricKey(e.target.value)}
            style={{ padding: "0.4rem 0.6rem", fontSize: "1rem", borderRadius: "6px" }}
          >
            <optgroup label="Patient reviews">
              {METRICS.filter((m) => m.source === "google").map((m) => (
                <option key={m.key} value={m.key}>
                  {m.label}
                </option>
              ))}
            </optgroup>
            <optgroup label="HCAHPS survey scores">
              {HCAHPS_METRICS.map((m) => (
                <option key={m.key} value={m.key}>
                  {m.label}
                </option>
              ))}
            </optgroup>
          </select>
        </label>
      </section>

      {loading && (
        <p style={{ textAlign: "center", padding: "2rem" }}>
          Loading hospital records...
        </p>
      )}
      {statusMsg && !loading && hospitals.length === 0 && (
        <p style={{ color: "red", textAlign: "center", padding: "2rem" }}>
          {statusMsg}
        </p>
      )}

      {!loading && hospitals.length > 0 && stateMapData.length === 0 && (
        <p style={{ textAlign: "center", padding: "2rem", color: "#777" }}>
          No hospitals have data for this measure.
        </p>
      )}

      {!loading && hospitals.length > 0 && stateMapData.length > 0 && (
        <div
          style={{
            display: "flex",
            gap: "1.5rem",
            flexWrap: "wrap",
            marginTop: "1rem",
          }}
        >
          {/* Left Column: Interactive State Map */}
          <div
            style={{
              flex: "1 1 48%",
              minWidth: "320px",
              border: "1px solid #e0e0e0",
              borderRadius: "8px",
              padding: "1rem",
            }}
          >
            <h3 style={{ margin: "0 0 1rem 0" }}>1. Select a State</h3>
            <Plot
              data={stateMapData}
              layout={{
                geo: { scope: "usa" },
                autosize: true,
                margin: { l: 0, r: 0, t: 0, b: 0 },
              }}
              useResizeHandler={true}
              style={{ width: "100%", height: "450px" }}
              onClick={(event) => {
                if (event.points && event.points[0]) {
                  const clickedState = event.points[0].location;
                  if (clickedState) setSelectedState(clickedState);
                }
              }}
            />
          </div>

          {/* Right Column: Hospital Point Map */}
          <div
            style={{
              flex: "1 1 48%",
              minWidth: "320px",
              border: "1px solid #e0e0e0",
              borderRadius: "8px",
              padding: "1rem",
            }}
          >
            <h3 style={{ margin: "0 0 1rem 0" }}>
              {activeState
                ? `2. Hospital Points: ${activeState}`
                : "2. Hospital Points"}
            </h3>
            <Plot
              data={points.trace ? [points.trace] : []}
              layout={{
                map: {
                  style: "open-street-map",
                  center: mapView.center,
                  zoom: mapView.zoom,
                },
                uirevision: `${activeState}-${metricKey}`, // keep pan/zoom until state or measure changes
                autosize: true,
                margin: { l: 0, r: 0, t: 0, b: 0 },
              }}
              useResizeHandler={true}
              style={{ width: "100%", height: "450px" }}
            />
            {zipError && (
              <p style={{ fontSize: "0.85rem", color: "red" }}>
                ZIP lookup failed: {zipError}
              </p>
            )}
            {!zipError && Object.keys(zipCoords).length === 0 && (
              <p style={{ fontSize: "0.85rem", color: "#777" }}>
                Loading ZIP coordinates...
              </p>
            )}
            {points.trace && points.count === 0 && (
              <p style={{ fontSize: "0.85rem", color: "#777" }}>
                No hospitals in {activeState} have data for this measure.
              </p>
            )}
            {points.missing > 0 && (
              <p style={{ fontSize: "0.8rem", color: "#777" }}>
                {points.missing} hospital(s) not shown (ZIP not found).
              </p>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

export default MapPage;
