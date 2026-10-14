
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
} from "react-router-dom";
import { Activity, MapPin, Search } from "lucide-react";

import MapPage from "./pages/MapPage";
import "./App.css";

function HomePage() {
  return (
    <main>
      <section className="hero">
        <p className="eyebrow">HEALTHCARE TRANSPARENCY</p>

        <h1>
          Better information.
          <br />
          Better healthcare decisions.
        </h1>

        <p className="hero-description">
          Compare hospitals by quality, patient reviews,
          and affordability.
        </p>

        <form
          className="search-bar"
          onSubmit={(event) => event.preventDefault()}
        >
          <Search size={21} />

          <input
            type="text"
            placeholder="Enter your ZIP code"
            aria-label="Enter your ZIP code"
            maxLength={5}
          />

          <button type="submit">Find Hospitals</button>
        </form>

        <p className="search-note">
          Explore hospital information in your area.
        </p>
      </section>

      <section className="intro">
        <p className="eyebrow">YOUR HEALTHCARE, COMPARED</p>

        <h2>Make more informed decisions</h2>

        <p>
          Explore hospital quality, patient experiences,
          and pricing information in one place.
        </p>
      </section>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="navbar">
          <Link className="brand" to="/">
            <Activity size={26} />
            <span>ClearCare</span>
          </Link>

          <nav>
            <Link to="/">Hospital Rankings</Link>

            <Link to="/map">
              <MapPin size={17} />
              Nearby Hospitals
            </Link>
          </nav>
        </header>

        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/map" element={<MapPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
