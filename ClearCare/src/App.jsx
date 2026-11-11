
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
} from "react-router-dom";
import { Activity, HospitalIcon, MapPin, MessageSquareText, Search } from "lucide-react";

import MapPage from "./pages/MapPage";
import RagChatPage from "./pages/RagChatPage";
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
            <HospitalIcon size={30} />
            <span>ClearCare</span>
          </Link>

          <p className="brand">Get The Care That Cares About You</p>

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
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
