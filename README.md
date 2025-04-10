# 3C+ Dashboard

This repository hosts the 3C+ Survey Analysis Dashboard, which provides visual insights into survey data about campus experiences with misogyny and queerphobia.

## Dashboard Features

- **Demographics Analysis**: Explore the demographics of survey respondents, including gender, role, and faculty distributions.
- **Misogyny Analysis**: Investigate observations of misogyny across different campus contexts.
- **Queerphobia Analysis**: Examine observations of queerphobia across different campus contexts.
- **Demographic Experience**: Analyze which demographic groups report experiencing misogyny or queerphobia.
- **Text Analysis**: Explore themes and patterns in open-text responses.
- **Comparative Analysis**: Compare misogyny and queerphobia observations side by side.

## How It Works

This dashboard is implemented as a static website hosted on GitHub Pages, with data updates triggered via GitHub Actions:

1. The survey data is fetched from either a local CSV file or an API endpoint (when available).
2. A Python script processes the data and generates static HTML/CSS/JS files.
3. GitHub Actions automatically deploys these files to GitHub Pages.
4. The data is refreshed periodically through scheduled GitHub Actions workflow runs.

## Local Development

To set up the dashboard for local development:

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/3cplus-dashboard.git
   cd 3cplus-dashboard
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Place your survey data CSV in the `data` directory as `survey_data.csv`.

4. Generate the static dashboard:
   ```
   python static_generator.py
   ```

5. Open the generated HTML file in your browser:
   ```
   open static_dashboard/index.html  # On Windows: start static_dashboard\index.html
   ```

## Updating Data

### Automatic Updates

The dashboard is configured to automatically update every hour via GitHub Actions. This can be adjusted in the `.github/workflows/update-dashboard.yml` file.

### Manual Updates

To manually trigger an update:

1. Go to the "Actions" tab of your GitHub repository.
2. Select the "Update Dashboard" workflow.
3. Click "Run workflow".

### Connecting to an API

To connect the dashboard to an API for data fetching:

1. Edit `update_data.py` and set the `API_URL` variable to your API endpoint.
2. Update the GitHub workflow file as needed to include any authentication secrets.

## License

[Your chosen license here]

## Contact

[Your contact information here]
