import { Link } from "react-router-dom";

import "./DataMethodologyPage.css";

const dataSources = [
  {
    title: "CMS Timely and Effective Care",
    description:
      "Twenty-four measures describe how often hospitals provide recommended care, including emergency department wait times, timely test results, preventive services, and adherence to treatment guidelines. Measure direction is considered because lower values are sometimes better.",
  },
  {
    title: "CMS Complications and Deaths",
    description:
      "Twenty measures cover complications, mortality, and other adverse events related to hospital care. In general, lower complication and mortality rates indicate better performance.",
  },
  {
    title: "Hospital Consumer Assessment of Healthcare Providers and Systems (HCAHPS)",
    description:
      "This standardized patient survey covers communication with doctors and nurses, staff responsiveness, medication information, discharge instructions, and overall hospital ratings.",
  },
  {
    title: "Ambulatory Surgical Center Quality Reporting (ASCQR)",
    description:
      "CMS reports quality measures for ambulatory surgical centers, including unplanned hospital visits after certain procedures. Facility identifiers could not be consistently matched to the hospital datasets, so these data are more useful for geographic comparisons than for rating individual hospitals.",
  },
  {
    title: "Google Places reviews",
    description:
      "Public star ratings and written reviews can add context about staff interactions, administrative experiences, and wait times. Reviews complement clinical and survey data; they are not a direct measure of clinical quality.",
  },
];

const scoreWeights = [
  ["Patient Safety", "25%"],
  ["Survival", "25%"],
  ["Emergency Care", "15%"],
  ["Effective Care", "15%"],
  ["Patient Experience", "20%"],
];

const limitations = [
  {
    title: "Incomplete reporting",
    text: "Hospitals have different amounts of data available. Missing measures affect which information contributes to a score, and missing data does not necessarily mean poor performance.",
  },
  {
    title: "Reporting delays",
    text: "CMS data may be 6–18 months behind current conditions, so recent changes in hospital performance may not yet be reflected.",
  },
  {
    title: "Population coverage",
    text: "CMS reporting primarily reflects Medicare and Medicaid populations, so hospitals serving other patient populations may be less fully represented.",
  },
  {
    title: "Google review limitations",
    text: "Google Places shows a limited number of reviews per location, and its review-sampling process is not publicly specified. The available reviews may not represent every patient's experience.",
  },
  {
    title: "Hospital matching",
    text: "Google Places does not provide CMS facility identifiers. Hospital names and ZIP codes, fuzzy name matching, and manual checks were used to connect reviews to CMS facilities; some mismatches may remain.",
  },
  {
    title: "Differences between measures",
    text: "Measures can cover different aspects of care, populations, and reporting methods. Standardizing values makes comparisons easier but does not remove every difference.",
  },
];

function DataMethodologyPage() {
  return (
    <main className="methodology-page">
      <header className="methodology-header">
        <Link to="/" className="methodology-back-link">
          Back to ClearCare
        </Link>
        <p className="eyebrow">TRANSPARENCY &amp; SCORING</p>
        <h1>Data &amp; Scoring Methodology</h1>
        <p>
          ClearCare combines public healthcare data and patient reviews to
          provide a broader view of hospital performance. The information below
          explains the sources, scoring approach, and limitations behind those
          comparisons.
        </p>
      </header>

      <section className="methodology-section">
        <h2>Our Approach</h2>
        <p>
          No single rating tells the whole story. ClearCare considers clinical
          quality and patient experience together so users can compare hospitals
          from more than one perspective. Data availability varies by hospital
          and location, so scores may be based on different sets of measures.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Data Sources</h2>
        <div className="methodology-card-grid">
          {dataSources.map((source) => (
            <article className="methodology-card" key={source.title}>
              <h3>{source.title}</h3>
              <p>{source.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="methodology-section">
        <h2>Data Exploration &amp; Availability</h2>
        <p>
          Before developing ClearCare&apos;s scoring system, we examined the
          available healthcare datasets to understand their completeness,
          distributions, and geographic coverage. This analysis revealed
          substantial differences in data availability across hospitals and
          states.
        </p>
        <h3>Timely and Effective Care</h3>
        <p>
          The Timely and Effective Care dataset includes 24 quality measures,
          but data availability varies considerably across facilities. As shown
          in Figure 1, most facilities are missing between 7 and 10 measures,
          with the largest groups missing 8 or 9 measures. This indicates that
          many hospitals have incomplete data across the measures included in
          this dataset.
        </p>
        <figure className="methodology-figure">
          <img
            src="/images/missing-timely-effective.png"
            alt="Bar chart showing the distribution of missing Timely and Effective Care measures across facilities; the largest groups are missing 8 or 9 of 24 measures."
            loading="lazy"
          />
          <figcaption>
            Figure 1: Distribution of Missing Timely and Effective Care Measures
            Across Facilities
          </figcaption>
        </figure>
        <p>
          Data availability also varies geographically. Figure 2 shows the
          percentage of facility-measure combinations with missing data across
          states. The results indicate substantial differences in reporting
          completeness, with some states having considerably higher
          missing-data rates than others.
        </p>
        <figure className="methodology-figure">
          <img
            src="/images/missing-timely-by-state.png"
            alt="Bar chart comparing missing Timely and Effective Care data rates across states."
            loading="lazy"
          />
          <figcaption>
            Figure 2: Overall Missing-Data Rate by State - Timely and Effective
            Care
          </figcaption>
        </figure>
        <h3>Complications and Deaths</h3>
        <p>
          The Complications and Deaths dataset includes 20 quality measures and
          exhibits a different pattern of missing data. Unlike the Timely and
          Effective Care dataset, which has a concentration of facilities
          missing 8-9 measures, the Complications and Deaths dataset has a
          U-shaped distribution. As shown in Figure 3, a relatively large
          percentage of facilities are missing few measures (0-3), while
          another substantial group is missing a large number of measures
          (16-19). Comparatively, fewer facilities fall in the middle of the
          distribution.
        </p>
        <figure className="methodology-figure">
          <img
            src="/images/missing-complications-deaths.png"
            alt="Bar chart showing a U-shaped distribution of missing Complications and Deaths measures across facilities, with groups missing 0 to 3 or 16 to 19 measures."
            loading="lazy"
          />
          <figcaption>
            Figure 3: Distribution of Missing Complications and Deaths Measures
            Across Facilities
          </figcaption>
        </figure>
        <p>
          Similar to the Timely and Effective Care dataset, missing-data rates
          vary considerably by state. Figure 4 illustrates these differences,
          showing that the availability of clinical outcome measures is not
          consistent across geographic regions.
        </p>
        <figure className="methodology-figure">
          <img
            src="/images/missing-complications-by-state.png"
            alt="Bar chart comparing missing Complications and Deaths data rates across states."
            loading="lazy"
          />
          <figcaption>
            Figure 4: Overall Missing-Data Rate by State - Complications and
            Deaths
          </figcaption>
        </figure>
        <h3>Comparing Data Availability Across Datasets</h3>
        <p>
          Comparing the two datasets reveals that missing data is not
          distributed uniformly across hospitals or geographic regions.
          Although the distribution of missing measures across facilities
          differs, five states appear among the ten states with the highest
          missing-data rates in both datasets. This overlap suggests that
          certain states experience consistently lower data availability across
          multiple CMS reporting categories.
        </p>
        <p>
          These findings highlight an important limitation of hospital quality
          comparisons: hospitals may have different amounts of available
          information contributing to their scores. Consequently, an overall
          score may be based on different sets of quality measures depending on
          the hospital.
        </p>
        <p>
          Missing data does not necessarily indicate poor hospital performance
          or a failure to report information. Measures may be unavailable
          because a hospital does not offer a particular service, does not have
          applicable patient cases, or for other data-collection and reporting
          reasons.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Scoring Methodology</h2>
        <h3>Standardizing measures</h3>
        <p>
          CMS measures use different scales and units. Numerical values are
          converted to percentiles from 0 to 100 relative to hospitals with
          available data, and directions are aligned so higher scores always
          indicate better performance. Measure percentiles are then combined
          into category scores using weighted averages. Within Patient Safety,
          the Patient Safety and Adverse Events Composite (PSI-90) receives
          twice the weight of certain other measures.
        </p>

        <h3>Category weights</h3>
        <div className="methodology-table-wrap">
          <table className="methodology-table">
            <thead>
              <tr>
                <th scope="col">Category</th>
                <th scope="col">Weight</th>
              </tr>
            </thead>
            <tbody>
              {scoreWeights.map(([category, weight]) => (
                <tr key={category}>
                  <th scope="row">{category}</th>
                  <td>{weight}</td>
                </tr>
              ))}
              <tr className="methodology-total">
                <th scope="row">Total</th>
                <td>100%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p>
          The overall composite is a weighted average of available category
          scores. A hospital must have scores in at least three of the five
          categories to receive a composite. If a category is missing, the
          remaining weights are proportionally adjusted rather than assigning
          that category a zero.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Overall Hospital Score Validation</h2>
        <p>
          <strong>Left: Composite Score vs. HCAHPS Star Rating:</strong> This
          graph compares the new composite scores with existing HCAHPS star
          ratings. The Spearman correlation is 0.43, indicating a moderate
          positive relationship. Hospitals with higher star ratings generally
          have higher composite scores, although there is considerable overlap.
          This suggests that the composite score captures additional information
          beyond patient satisfaction.
        </p>
        <p>
          <strong>Middle: Which Parts Agree With the Stars?:</strong> This graph
          compares the individual scoring categories with HCAHPS star ratings
          and the overall composite. Patient experience has the strongest
          correlation with HCAHPS stars (approximately 0.92), while clinical
          categories have much weaker correlations. This shows that patient
          satisfaction and clinical performance measure different aspects of
          hospital quality.
        </p>
        <p>
          <strong>Right: Sensitivity to Weights:</strong> This histogram
          examines how changing the weights assigned to the five scoring
          categories affects the correlation between composite scores and
          HCAHPS ratings. It uses 1,000 randomly generated weight combinations.
          The dashed line represents the correlation using the default weights
          (approximately 0.43). This analysis helps determine whether the
          scoring system is overly dependent on its selected weights.
        </p>
        <figure className="methodology-figure">
          <img
            src="/images/overall-score-validation.png"
            alt="Three charts compare composite scores with HCAHPS stars, show correlations for the scoring categories, and display sensitivity to 1,000 randomly generated weight sets."
            loading="lazy"
          />
          <figcaption>Overall Hospital Score Validation</figcaption>
        </figure>
        <p>
          <strong>Left: Composite Score Distribution:</strong> This histogram
          shows how composite scores are distributed across hospitals. Most
          hospitals receive scores between 40 and 60, with the highest
          concentration around 50. Relatively few hospitals receive extremely
          high or low scores, suggesting that most hospitals perform near the
          middle of the scoring scale.
        </p>
        <p>
          <strong>Middle: Scores by Hospital Type:</strong> This boxplot
          compares composite scores across four hospital types. Veterans
          Administration hospitals have the highest median score, followed by
          Department of Defense hospitals. Critical Access and Acute Care
          hospitals have slightly lower median scores. However, there is
          considerable variation within each group, showing that hospital type
          does not necessarily determine performance.
        </p>
        <p>
          <strong>Right: Same Star, Very Different Clinical Results:</strong>{" "}
          This heatmap compares HCAHPS star ratings with clinical performance
          quartiles. Hospitals with the same patient satisfaction rating can
          have very different clinical results. For example, 206 four-star
          hospitals fall into the lowest clinical performance quartile. This
          demonstrates that patient satisfaction ratings alone do not fully
          represent hospital quality.
        </p>
        <figure className="methodology-figure">
          <img
            src="/images/score-distribution-and-disagreement.png"
            alt="Three charts show the distribution of composite scores, score differences by hospital type, and clinical-performance quartiles within each HCAHPS star rating."
            loading="lazy"
          />
          <figcaption>
            Composite Score Distribution, Scores by Hospital Type, and Clinical
            Results by HCAHPS Star Rating
          </figcaption>
        </figure>
        <p>
          Together, these graphs demonstrate that hospital quality cannot be
          evaluated using patient satisfaction alone. Hospitals with similar
          HCAHPS ratings can have substantially different clinical performance.
          The composite scoring system addresses this limitation by combining
          patient safety, survival, emergency care, effective care, and patient
          experience into a single score.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Data Limitations</h2>
        <div className="methodology-card-grid">
          {limitations.map((limitation) => (
            <article className="methodology-card" key={limitation.title}>
              <h3>{limitation.title}</h3>
              <p>{limitation.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="methodology-callout">
        <h2>Interpreting ClearCare Scores</h2>
        <p>
          Scores summarize available information; they do not guarantee care
          quality or patient outcomes. Consider them alongside individual
          measures, reviews, and factors that matter to your needs. Clinical
          outcomes and patient experience are related but distinct, and a
          hospital may perform differently across these perspectives.
        </p>
        <p>
          ClearCare is an informational resource, not a substitute for
          professional medical advice. Consult qualified healthcare
          professionals when making decisions about your care.
        </p>
      </section>
    </main>
  );
}

export default DataMethodologyPage;
