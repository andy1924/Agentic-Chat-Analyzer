# Agentic Chat Analyzer

Agentic Chat Analyzer is a Python project for turning raw chat exports into **relationship health signals** and **LLM-powered behavioral profiles**.

It includes:
- A data-cleaning and feature-engineering pipeline for chat logs.
- A deterministic relationship scoring engine (recency, frequency, responsiveness, engagement, balance).
- An LLM analyzer that builds per-user communication profiles.
- A Streamlit dashboard for exploring contact-level health and message trends.

## Repository Structure

- `cleaningFile.py` – Cleans raw chat CSVs and creates `processed_chat_dataset.csv`.
- `relationCalculator.py` – Calculates relationship health scores and risk buckets.
- `jsonConverter.py` – Converts processed CSV to contact timelines JSON.
- `analyzer.py` – Uses LangChain + OpenAI structured output to generate behavioral profiles.
- `webUI.py` – Streamlit dashboard with filters, score table, trends, and chat preview.
- `app.py` – Alternate Streamlit entry script (includes mock UI scaffold and calls `webUI.main()`).
- `mainData/` – Input/output data artifacts used by the pipeline.
- `mockData/` – Example JSON chat data for the dashboard.

## Data Flow

1. **Raw chats** (`mainData/whatsapp_unique_chats_5000.csv`)  
2. `cleaningFile.py` → **processed dataset** (`mainData/processed_chat_dataset.csv`)  
3. `relationCalculator.py` → **relationship health JSON** (`mainData/relationship_health.json`)  
4. `jsonConverter.py` → **timelines JSON** (`mainData/timelines.json`)  
5. `analyzer.py` → **behavioral profile JSON** (`mainData/analyzedResults.json`)  
6. `webUI.py` / `app.py` → interactive dashboard

## Setup

### 1) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

> Note: `requirements.txt` in this repo appears to be encoded with non-UTF-8 characters in some environments. If `pip` fails, re-save it as UTF-8 first, then retry.

### 3) Configure environment variables

Create a `.env` file in the project root for LLM analysis:

```env
OPENAI_API_KEY=your_openai_api_key
```

## Running the Pipeline

From project root:

```bash
# Step 1: Clean and engineer features from raw chat export
python cleaningFile.py

# Step 2: Compute relationship health score per contact
python relationCalculator.py

# Step 3: Build per-contact timeline JSON
python jsonConverter.py

# Step 4: Generate LLM behavioral profiles
python analyzer.py
```

## Launching the Dashboard

Preferred:

```bash
streamlit run webUI.py
```

Alternative entry point:

```bash
streamlit run app.py
```

## Input/Output Expectations

### Raw input CSV (expected by `cleaningFile.py`)
Expected columns include:
- `date`
- `time`
- `sender`
- `receiver`
- `message`

### Processed output (`processed_chat_dataset.csv`)
Contains engineered fields such as:
- `timestamp`
- `contact_name`
- `is_user_sender`
- `message_length`
- `word_count`
- `day_of_week`
- `hour`
- `is_weekend`
- `inactivity_hours`

## Scoring Logic (Current)

`relationCalculator.py` computes five normalized components per contact:
- **Recency** (days since last interaction)
- **Frequency** (messages per active day)
- **Responsiveness** (average inactivity gap)
- **Engagement** (average word count)
- **Balance** (message count parity between participants)

Final health score is the mean of those components, scaled to 0–100, then labeled:
- `Strong` (>= 75)
- `Stable` (>= 55)
- `At Risk` (>= 35)
- `Critical` (< 35)

## LLM Behavioral Profiling

`analyzer.py` profiles each sender and returns structured fields:
- `communication_style`
- `emotional_baseline`
- `engagement_trend`
- `behavioral_flags`
- `interaction_advice`

It processes up to the last 50 messages per sender to control token usage.

## Notes

- This project currently mixes deterministic scoring and LLM inference; health scores do not require OpenAI access, but behavioral profiling does.
- The dashboard supports loading a JSON file via sidebar upload to override default mock data.
- Existing files in `mainData/` include sample outputs to help you verify the expected structure quickly.
