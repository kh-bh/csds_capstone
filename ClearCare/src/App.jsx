
import { useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useNavigate,
} from "react-router-dom";
import { HospitalIcon, MapPin, MessageSquareText, Search } from "lucide-react";

import MapPage from "./pages/MapPage";
import RagChatPage from "./pages/RagChatPage";
import DataMethodologyPage from "./pages/DataMethodologyPage";
import { loadZipData } from "./utils/zipCodes";
import "./App.css";

function HomePage() {
  const navigate = useNavigate();
  const [zipCode, setZipCode] = useState("");
  const [searchError, setSearchError] = useState("");
  const [searching, setSearching] = useState(false);

  async function handleSearch(event) {
    event.preventDefault();
    const zip = zipCode.trim();

    if (!/^\d{5}$/.test(zip)) {
      setSearchError("Enter a valid five-digit ZIP code.");
      return;
    }

    setSearching(true);
    setSearchError("");
    try {
      const zipData = await loadZipData();
      if (!zipData[zip]?.state) {
        setSearchError("We couldn't find that ZIP code. Check it and try again.");
        return;
      }

      navigate(`/map?zip=${zip}`);
    } catch (error) {
      setSearchError(`We couldn't verify the ZIP code: ${error.message}`);
    } finally {
      setSearching(false);
    }
  }

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
          onSubmit={handleSearch}
        >
          <Search size={21} />

          <input
            type="text"
            placeholder="Enter your ZIP code"
            aria-label="Enter your ZIP code"
            inputMode="numeric"
            maxLength={5}
            value={zipCode}
            onChange={(event) => {
              setZipCode(event.target.value);
              setSearchError("");
            }}
          />

          <button type="submit" disabled={searching}>
            {searching ? "Checking..." : "Find Hospitals"}
          </button>
        </form>

        {searchError ? (
          <p className="search-note search-error" role="alert">{searchError}</p>
        ) : (
          <p className="search-note">Explore hospital information in your area.</p>
        )}
      </section>

      <section className="methodology-promo" aria-labelledby="methodology-promo-title">
        <div>
          <p className="eyebrow">HOW TO READ THE DATA</p>
          <h2 id="methodology-promo-title">Data &amp; Scoring Methodology</h2>
          <p>
            Learn where ClearCare's hospital data comes from, how scores are
            calculated, and what to keep in mind when comparing results.
          </p>
        </div>
        <Link className="methodology-link" to="/methodology">
          Explore our methodology
        </Link>
      </section>

      <section className="intro">
        <p className="eyebrow">YOUR HEALTHCARE, COMPARED</p>

        <h2>Make more informed decisions</h2>

        <p>
          Explore hospital quality, patient experiences,
          and pricing information in one place.
        </p>
      </section>

      <section className="about-section" aria-labelledby="about-title">
        <div className="about-heading">
          <p className="eyebrow">ABOUT US</p>
          <h2 id="about-title">About ClearCare</h2>
          <h3>Making healthcare decisions more transparent</h3>
          <p>
            ClearCare brings hospital quality measures and patient experience
            information together, helping people explore and compare hospitals
            based on what matters to them.
          </p>
        </div>

        <div className="about-details">
          <article>
            <h3>What We Do</h3>
            <p>
              We provide interactive hospital maps and comparison metrics,
              alongside tools to explore patient reviews and ask questions
              about hospital experiences.
            </p>
          </article>
          <article>
            <h3>Our Mission</h3>
            <p>
              Our mission is to make hospital information easier to find and
              understand, so individuals and families can make more informed
              healthcare decisions with greater confidence.
            </p>
          </article>
        </div>
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
            <HospitalIcon size={30} />
            <span>ClearCare</span>
          </Link>

          <p className="brand navbar-tagline">Get The Care That Cares About You</p>

          <nav>
            <Link to="/map">
              <MapPin size={17} />
              See Nearby Hospitals
            </Link>

            <Link to="/reviews">
              <MessageSquareText size={17} />
              Ask About Reviews
            </Link>
          </nav>
        </header>

        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/reviews" element={<RagChatPage />} />
          <Route path="/methodology" element={<DataMethodologyPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
