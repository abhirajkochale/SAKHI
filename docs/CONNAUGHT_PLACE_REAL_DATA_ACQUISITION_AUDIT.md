# Connaught Place Real Data Acquisition Audit

## 1. Executive Summary
An exhaustive investigation was conducted across official government portals, municipal councils, and reputable public safety organizations to identify granular, incident-level crime data for Connaught Place (CP), New Delhi. 

The audit concludes that **NO SUFFICIENT REAL SEGMENT-LEVEL GROUND TRUTH FOUND.** Official law enforcement agencies (Delhi Police, NCRB) strictly aggregate crime data to the district or police-station level and explicitly withhold geocoded incident coordinates for privacy and security reasons. While third-party crowdsourced platforms (e.g., Safecity) possess some geo-tagged anecdotal reports, the volume of verified data within the specific micro-geography of Connaught Place is statistically insufficient to train or validate a segment-level machine learning model.

## 2. Candidate Real Data Sources Investigated
1. **Delhi Police Official Statistics**: Annual and monthly aggregated reports.
2. **National Crime Records Bureau (NCRB) via data.gov.in**: State and district-level crime records.
3. **New Delhi Municipal Council (NDMC) Smart City Portal**: Municipal infrastructure data.
4. **Safecity (Red Dot Foundation)**: Crowdsourced reports of sexual and gender-based harassment.
5. **Safetipin**: Crowdsourced and systematic environmental safety audits.

## 3. Source-by-Source Comparison

### A. Delhi Police / NCRB (data.gov.in)
- **Organization**: Ministry of Home Affairs / Delhi Police
- **URL**: delhipolice.gov.in / ncrb.gov.in
- **License**: Open Government Data License
- **Geographic Coverage**: All Delhi districts.
- **CP Included?**: Yes, but aggregated under "New Delhi District" or "Connaught Place PS".
- **Coordinate Availability**: None.
- **Address Availability**: None.
- **Time Availability**: Year/Month only.
- **Appropriate for ML?**: No. Cannot be mapped to road segments.

### B. NDMC Open Data
- **Organization**: New Delhi Municipal Council
- **URL**: ndmc.gov.in
- **License**: N/A
- **Coordinate Availability**: None for crime.
- **Appropriate for ML?**: No. NDMC does not publish crime or public incident datasets.

### C. Safecity (Crowdsourced Harassment Reports)
- **Organization**: Red Dot Foundation
- **URL**: maps.safecity.in
- **License**: Proprietary / Requires academic request for raw dataset.
- **Geographic Coverage**: Global, with high density in Delhi.
- **CP Included?**: Yes.
- **Coordinate Availability**: Yes (user-pinned lat/lon).
- **Time Availability**: Time of day and date available.
- **Incident Types**: Groping, stalking, catcalling, etc.
- **Appropriate for ML?**: Marginally. It is the only geo-tagged dataset, but suffers from severe sparsity and verification issues.

### D. Safetipin (Safety Audits)
- **Organization**: Safetipin
- **URL**: safetipin.com
- **License**: Proprietary / B2B/B2G data sharing.
- **Coordinate Availability**: Yes.
- **Incident Types**: Does not track crime *incidents*; tracks infrastructure (lighting, visibility, footpath quality).
- **Appropriate for ML?**: No. This is feature data, not target ground-truth data.

## 4. Best Available Candidate
The theoretically best candidate for an ML target is **Safecity**, as it is the *only* dataset containing point-level (lat/lon) incident reports categorized by time-of-day. 

## 5. Exact CP Coverage (Safecity Estimation)
- Can incidents inside CP be isolated? **Yes** (via bounding box spatial join).
- Can incidents be mapped to individual road segments? **Yes** (via nearest-neighbor snapping).
- Can incidents be assigned to time-of-day? **Yes**.

## 6. Exact Incident Counts (Safecity in CP)
While Safecity contains thousands of reports for the greater Delhi NCR region (1,484 sq km), Connaught Place covers approximately 3 sq km. 
- **Estimated incidents remaining after CP filtering**: < 200 historically.
- **Usable coordinates/timestamps**: Often ~60-70% complete in crowdsourced data.
- **Estimated Usable Dataset**: ~100 to 150 incidents spread over 5+ years.

## 7. Spatial Resolution
- Safecity: User-dropped pins. Often snapped to intersections or landmarks rather than exact mid-segment locations. Resolution: ~50-100 meters.

## 8. Temporal Resolution
- Safecity: Self-reported time of day (Morning, Afternoon, Evening, Night).

## 9. Data Quality (Safecity)
- **Spatial quality: 2/5** (User-generated pins are notoriously imprecise; often placed at general landmarks rather than exact occurrence points).
- **Temporal quality: 3/5** (Time-of-day is usually accurate to the user's memory, but exact timestamps are rare).
- **Incident-level quality: 2/5** (Unverified anecdotal reports; highly subjective severity).
- **Coverage: 1/5** (Massive underreporting. Highly skewed towards demographics aware of the app).
- **Provenance: 3/5** (Well-maintained by an NGO, but inherently crowdsourced).
- **License usability: 2/5** (Not open-source; requires direct negotiation for raw geo-coordinates, which are often masked for victim privacy).

## 10. License/Provenance limitations
Law enforcement data is open but unusable. Crowdsourced data is usable but proprietary and privacy-restricted. There is no openly licensed, granular crime data in India comparable to open dispatch datasets found in cities like Chicago or London.

## 11. ML Feasibility
**NOT FEASIBLE.**
If we map ~150 Safecity incidents across the road segments in CP, grouped by 4 time periods, the resulting matrix will be >95% zeros. 
- **Class imbalance**: Extreme.
- **Zero-event segments**: The vast majority of segments will show 0 incidents, not because they are perfectly safe, but because of data sparsity and underreporting.
Training an XGBoost Regressor on this dataset will result in catastrophic overfitting to the few segments that randomly received a Safecity pin.

## 12. Ground-Truth Target Options
*If data existed*, the ideal target would be:
**Segment × Time-of-Day Incident Rate** (Incidents per 100m).
However, due to extreme sparsity, this target cannot be reliably constructed. 

## 13. Real Contextual Feature Sources
While ground-truth *targets* are missing, real *feature* data for CP is highly accessible:
1. **OpenStreetMap (OSM)**: 
   - **Data**: Road types, walkability, segment length, precise geometry.
   - **Resolution**: Sub-meter. Real.
2. **Safetipin / NDMC Smart Poles**: 
   - **Data**: Actual street lighting coverage, CCTV placement.
   - **Resolution**: Segment-level. (Requires NDMC API access or Safetipin B2G integration).
3. **Google Places / MapmyIndia APIs**:
   - **Data**: Real distance to police stations, hospitals, metro stations, and active nighttime businesses (surrogate for footfall).

## 14. Major Limitations
The SAKHI model currently predicts a mathematically constructed proxy formula because empirical, street-level crime data is legally and practically inaccessible in New Delhi. Without official police dispatch coordinates, the model cannot learn true environmental correlations with crime.

## 15. Final Recommendation
**NO SUFFICIENT REAL SEGMENT-LEVEL GROUND TRUTH FOUND.**

**Recommendation**: 
1. DO NOT fabricate synthetic incident labels to train XGBoost.
2. Acknowledge that a predictive Machine Learning model is the wrong architectural approach when ground truth does not exist. 
3. SAKHI should transition from an "ML Prediction Engine" to a "Deterministic Safety Routing Algorithm." Instead of attempting to predict an unverifiable "Risk Score", the routing engine should explicitly calculate a transparent "Infrastructure Safety Cost" using real OSM features (Distance to Police, Road Type, Amenity Density). This completely eliminates the need for an XGBoost model, removes the statistical hallucination of the synthetic target, and provides users with a verifiable, empirical reason for the route recommendation.
