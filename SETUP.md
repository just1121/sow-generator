## Prerequisites
- Python 3.9+
- Virtual Environment
- Google Cloud credentials

## Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/just1121/sow-generator.git
   cd sow-generator
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv fresh_env_newest
   source fresh_env_newest/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install numpy==1.24.3 --no-deps
   pip install pandas==1.5.3
   pip install streamlit==1.24.0
   pip install protobuf==3.20.3
   pip install -r config/requirements.txt
   ```

4. Set up Google Cloud credentials:
   - Place Speech_key.json in the config directory
   - Create .env file with:
     GOOGLE_APPLICATION_CREDENTIALS=config/Speech_key.json

5. Run the application:
   ```bash
   streamlit run water_recycling_app.py
   ```

## Directory Structure
/sow-generator
├── app.py                    # Flask application
├── water_recycling_app.py    # Main Streamlit application
├── static/                   # Static assets
├── templates/                # HTML templates
├── config/                   # Configuration files
│   ├── requirements.txt
│   └── constraints.txt
└── .env                      # Environment variables