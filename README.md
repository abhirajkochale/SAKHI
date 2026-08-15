# SAKHI — Smart Assistance for keeping HER informed

SAKHI is a journey-level contextual safety intelligence layer over routing.

## Project Structure

- `frontend/`: React Native + Expo application (To be implemented)
- `backend/`: FastAPI backend
- `ml/`: Machine learning models and notebooks (To be implemented)
- `data/`: Datasets and local databases (To be implemented)
- `docs/`: Documentation (To be implemented)

## Running the Backend Locally

### Prerequisites
- Python 3.9+

### Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server
```bash
uvicorn app.main:app --reload
```
The server will be available at http://127.0.0.1:8000
API documentation will be at http://127.0.0.1:8000/docs

### Running Tests
```bash
pytest tests/
```

## Architecture

### Routing Phase (Phase 2)
SAKHI currently utilizes an abstraction for routing services to remain uncoupled from specific third-party routing APIs.
- **Provider:** OpenStreetMap / OSRM (Public Demo API)
- **Profile:** Walking (`foot` profile)
- **Segmentation Strategy:** SAKHI parses OSRM "steps" and maps them directly into discrete `JourneySegment`s. These segments hold detailed GeoJSON `LineString` coordinates and act as our stable domain objects for later risk evaluation.

*Note: This prototype currently uses walking routes. Multimodal walking + transit journey support will be added in a later phase.*

### API Endpoints

#### `POST /api/v1/journeys`
Creates a journey by calling the routing provider and returns an ordered list of `JourneySegment`s.

**Example Request:**
```json
{
  "origin": { "latitude": 18.922, "longitude": 72.827 },
  "destination": { "latitude": 18.930, "longitude": 72.835 }
}
```

**Example Response:**
```json
{
  "journey_id": "84c8a299-1bd1-4d10-94e8-42217c2be6d5",
  "origin": { "latitude": 18.922, "longitude": 72.827 },
  "destination": { "latitude": 18.930, "longitude": 72.835 },
  "distance_m": 2174.6,
  "duration_s": 167.0,
  "segments": [
    {
      "segment_id": "48b6c008-dbef-4a1d-a02b-8a8b1a8d052d",
      "journey_id": "84c8a299-1bd1-4d10-94e8-42217c2be6d5",
      "sequence": 1,
      "mode": "foot",
      "start_location": { "latitude": 18.931757, "longitude": 72.827036 },
      "end_location": { "latitude": 18.932862, "longitude": 72.827888 },
      "distance_m": 165.2,
      "duration_s": 118.9,
      "geometry": {
        "type": "LineString",
        "coordinates": [[72.827036, 18.931757], [72.827888, 18.932862]]
      }
    }
  ]
}
```

### Contextual Safety Risk Model (Phase 3A)

SAKHI's contextual safety risk score estimates safety-relevant contextual conditions for a journey segment. **It is not a crime probability, individual crime prediction, or guarantee of safety.**

The current prototype follows this logical flow:
JourneySegment -> extracted features -> historical baseline -> prototype heuristic -> isk score + confidence`n
#### Key Principles:
- **Historical Baseline**: Aggregate historical data acts as a regional prior/context signal, not a street-level ground truth.
- **Confidence**: Confidence is independent from risk. Missing context deterministically decreases the confidence score.
- **Prototype Heuristics**: The weights currently combining spatial, temporal, and dynamic factors into a final 0-100 score are simple heuristic proxies. They are NOT scientifically validated and will be replaced/augmented by ML models in future phases.
- **Synthetic Data**: If synthetic granular data is used in future phases for ML demonstration, it will be explicitly labelled.

