
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function MapPage() {
  return (
    <main className="map-page">
      <section className="map-heading">
        <p className="eyebrow">HEALTHCARE NEAR YOU</p>
        <h1>Explore Hospitals Across the U.S.</h1>
        <p>
          Navigate the map to explore locations across
          the United States.
        </p>
      </section>

      <div className="map-container">
        <MapContainer
          center={[39.5, -98.35]}
          zoom={4}
          minZoom={3}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        </MapContainer>
      </div>
    </main>
  );
}

export default MapPage;
