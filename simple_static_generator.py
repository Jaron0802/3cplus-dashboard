import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly
from flask import Flask, render_template_string
from flask_frozen import Freezer
import re
from collections import Counter
import nltk
from datetime import datetime
from markupsafe import Markup

# Download NLTK data if needed
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
from nltk.corpus import stopwords

class SurveyAnalyzer:
    """Simple class to analyze the 3C+ survey data"""
    
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load and clean the CSV data"""
        try:
            # Load the CSV data, skipping the question text row
            self.df = pd.read_csv(self.csv_path, skiprows=[1])
            
            # Add completion flag
            if 'Finished' in self.df.columns:
                self.df['completed_survey'] = self.df['Finished'] == 'True'
            
            # Clean up ImportId entries if Q1 exists
            if 'Q1' in self.df.columns:
                self.df = self.df[~self.df['Q1'].str.contains('ImportId', na=False)].copy()
            
            # Clean gender data if Q2 exists
            if 'Q2' in self.df.columns:
                self.df['Gender'] = self.df['Q2'].apply(
                    lambda x: 'Woman' if isinstance(x, str) and 'Woman' in x else
                             ('Man' if isinstance(x, str) and 'Man' in x else
                             ('Non-binary' if isinstance(x, str) and 'Non-binary' in x else
                             ('Gender Diverse' if isinstance(x, str) and 'Gender Diverse' in x else x)))
                )
            else:
                self.df['Gender'] = 'Unknown'
            
            # Clean duration data
            if 'Duration (in seconds)' in self.df.columns:
                self.df['Duration (in seconds)'] = pd.to_numeric(
                    self.df['Duration (in seconds)'], errors='coerce')
            
            print(f"Data loaded successfully. {len(self.df)} total responses found.")
        
        except Exception as e:
            print(f"Error loading data: {e}")
            self.df = pd.DataFrame()
    
    def get_stats(self):
        """Get basic statistics about the survey data"""
        if self.df.empty:
            return {
                'total_responses': 0,
                'completion_rate': 0,
                'avg_duration_minutes': 0
            }
        
        total = len(self.df)
        completion_rate = 0
        if 'Finished' in self.df.columns:
            completion_rate = (self.df['Finished'] == 'True').mean() * 100
        
        avg_duration = 0
        if 'Duration (in seconds)' in self.df.columns:
            avg_duration = self.df['Duration (in seconds)'].mean() / 60  # Convert to minutes
        
        return {
            'total_responses': total,
            'completion_rate': completion_rate,
            'avg_duration_minutes': avg_duration
        }
    
    def get_charts_data(self):
        """Generate all the charts data needed for the dashboard"""
        charts = {}
        
        # Gender distribution
        if 'Gender' in self.df.columns:
            gender_counts = self.df['Gender'].value_counts().reset_index()
            gender_counts.columns = ['Gender', 'Count']
            gender_fig = px.pie(gender_counts, values='Count', names='Gender', 
                              title='Gender Distribution',
                              color_discrete_sequence=px.colors.qualitative.Set3)
            gender_fig.update_traces(textposition='inside', textinfo='percent+label')
            charts['gender'] = gender_fig
        
        # Role distribution
        if 'Q6' in self.df.columns:
            role_counts = self.df['Q6'].value_counts().reset_index().head(10)
            role_counts.columns = ['Role', 'Count']
            role_fig = px.bar(role_counts, x='Count', y='Role', 
                             title='Top 10 Roles on Campus',
                             color_discrete_sequence=['#3498db'],
                             orientation='h')
            charts['role'] = role_fig
        
        # Faculty distribution
        if 'Q5' in self.df.columns:
            faculty_counts = self.df['Q5'].value_counts().reset_index()
            faculty_counts.columns = ['Faculty', 'Count']
            if 'Not Applicable' in faculty_counts['Faculty'].values:
                faculty_counts = faculty_counts[faculty_counts['Faculty'] != 'Not Applicable']
            faculty_fig = px.bar(faculty_counts, x='Faculty', y='Count', 
                                title='Faculty Distribution',
                                color_discrete_sequence=['#2ecc71'])
            faculty_fig.update_layout(xaxis_tickangle=-45)
            charts['faculty'] = faculty_fig
        
        # Misogyny observations
        if all(col in self.df.columns for col in ['Q10_1', 'Q10_2', 'Q10_3', 'Q10_4']):
            # Prepare observation data
            contexts = [
                {'id': 'Q10_1', 'label': 'Campus Community'},
                {'id': 'Q10_2', 'label': 'Classroom'},
                {'id': 'Q10_3', 'label': 'Conversations with Peers'},
                {'id': 'Q10_4', 'label': 'Conversations with Staff/Faculty'}
            ]
            misogyny_data = []
            for ctx in contexts:
                counts = self.df[ctx['id']].value_counts().reset_index()
                counts.columns = ['Response', 'Count']
                counts['Context'] = ctx['label']
                misogyny_data.append(counts)
            
            if misogyny_data:
                misogyny_df = pd.concat(misogyny_data)
                misogyny_fig = px.bar(misogyny_df, x='Context', y='Count', color='Response',
                                    title='Observations of Misogyny in Different Contexts',
                                    color_discrete_map={'Yes': 'green', 'No': 'red', 'Unsure': 'gold'})
                charts['misogyny'] = misogyny_fig
        
        # Queerphobia observations
        if all(col in self.df.columns for col in ['Q19_1', 'Q19_2', 'Q19_3', 'Q19_4']):
            # Prepare observation data
            contexts = [
                {'id': 'Q19_1', 'label': 'Campus Community'},
                {'id': 'Q19_2', 'label': 'Classroom'},
                {'id': 'Q19_3', 'label': 'Conversations with Peers'},
                {'id': 'Q19_4', 'label': 'Conversations with Staff/Faculty'}
            ]
            queerphobia_data = []
            for ctx in contexts:
                counts = self.df[ctx['id']].value_counts().reset_index()
                counts.columns = ['Response', 'Count']
                counts['Context'] = ctx['label']
                queerphobia_data.append(counts)
            
            if queerphobia_data:
                queerphobia_df = pd.concat(queerphobia_data)
                queerphobia_fig = px.bar(queerphobia_df, x='Context', y='Count', color='Response',
                                        title='Observations of Queerphobia in Different Contexts',
                                        color_discrete_map={'Yes': 'purple', 'No': 'red', 'Unsure': 'gold'})
                charts['queerphobia'] = queerphobia_fig
        
        # Comparative analysis
        contexts = [
            {'misogyny': 'Q10_1', 'queerphobia': 'Q19_1', 'name': 'Campus Community'},
            {'misogyny': 'Q10_2', 'queerphobia': 'Q19_2', 'name': 'Classroom'},
            {'misogyny': 'Q10_3', 'queerphobia': 'Q19_3', 'name': 'Conversations with Peers'},
            {'misogyny': 'Q10_4', 'queerphobia': 'Q19_4', 'name': 'Conversations with Staff/Faculty'}
        ]
        
        comparison_data = []
        for ctx in contexts:
            if all(col in self.df.columns for col in [ctx['misogyny'], ctx['queerphobia']]):
                m_yes = self.df[ctx['misogyny']].value_counts().get('Yes', 0)
                m_total = self.df[ctx['misogyny']].notna().sum()
                
                q_yes = self.df[ctx['queerphobia']].value_counts().get('Yes', 0)
                q_total = self.df[ctx['queerphobia']].notna().sum()
                
                if m_total > 0 and q_total > 0:
                    comparison_data.append({
                        'Context': ctx['name'],
                        'Misogyny Yes %': (m_yes / m_total) * 100,
                        'Queerphobia Yes %': (q_yes / q_total) * 100,
                        'Difference': (m_yes / m_total) * 100 - (q_yes / q_total) * 100
                    })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            # Bar chart
            comp_bar_fig = px.bar(comparison_df, x='Context', 
                                y=['Misogyny Yes %', 'Queerphobia Yes %'],
                                title='Comparison of Misogyny and Queerphobia by Context',
                                barmode='group',
                                color_discrete_map={'Misogyny Yes %': 'green', 'Queerphobia Yes %': 'purple'})
            
            # Radar chart
            radar_fig = go.Figure()
            radar_fig.add_trace(go.Scatterpolar(
                r=comparison_df['Misogyny Yes %'].tolist(),
                theta=comparison_df['Context'].tolist(),
                fill='toself',
                name='Misogyny',
                line_color='green'
            ))
            radar_fig.add_trace(go.Scatterpolar(
                r=comparison_df['Queerphobia Yes %'].tolist(),
                theta=comparison_df['Context'].tolist(),
                fill='toself',
                name='Queerphobia',
                line_color='purple'
            ))
            radar_fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                title="Radar Chart: Misogyny vs Queerphobia by Context"
            )
            
            charts['comparison_bar'] = comp_bar_fig
            charts['comparison_radar'] = radar_fig
            charts['comparison_data'] = comparison_df.to_dict('records')
            charts['misogyny_mean'] = comparison_df['Misogyny Yes %'].mean()
            charts['queerphobia_mean'] = comparison_df['Queerphobia Yes %'].mean()
            greatest_diff_idx = (comparison_df['Misogyny Yes %'] - comparison_df['Queerphobia Yes %']).abs().idxmax()
            charts['greatest_diff_context'] = comparison_df.loc[greatest_diff_idx, 'Context']
        
        return charts
    
    def analyze_text(self, field_name):
        """Analyze a text field for frequency and themes"""
        if field_name not in self.df.columns:
            return None
        
        # Get valid responses
        valid_responses = self.df[
            self.df[field_name].notna() & 
            (self.df[field_name].str.len() > 20) &
            (~self.df[field_name].str.contains('ImportId', na=False))
        ]
        
        if len(valid_responses) < 1:
            return None
        
        # Clean text
        stop_words = set(stopwords.words('english'))
        additional_stops = {'please', 'specify', 'text', 'importid', 'qid', 'yes', 'no', 'that', 'things', 'also'}
        stop_words = stop_words.union(additional_stops)
        
        def clean_text(text):
            if not isinstance(text, str):
                return ""
            text = re.sub(r'[^\w\s]', '', text.lower())
            text = re.sub(r'\d+', '', text)
            words = text.split()
            filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
            return ' '.join(filtered_words)
        
        cleaned_texts = valid_responses[field_name].apply(clean_text)
        all_text = ' '.join(cleaned_texts)
        
        # Word frequency
        words = all_text.split()
        word_counts = Counter(words).most_common(20) if words else []
        
        if word_counts:
            words, counts = zip(*word_counts)
            word_df = pd.DataFrame({'Word': words, 'Frequency': counts})
            word_freq_fig = px.bar(word_df, x='Word', y='Frequency', 
                                 title='Most Common Words',
                                 color_discrete_sequence=['#3498db'])
        else:
            word_freq_fig = None
        
        # Theme analysis
        themes = {
            "Classroom Experiences": ["class", "classroom", "professor", "faculty", "lecture", "student", "course", "teaching"],
            "Social Interactions": ["friend", "peer", "social", "group", "talk", "conversation", "interact"],
            "Harassment & Discrimination": ["harass", "discriminat", "bias", "attack", "target", "threat", "abuse", "aggressive"],
            "Online Experiences": ["online", "email", "social media", "facebook", "twitter", "instagram", "reddit", "zoom", "message"],
            "Institutional Issues": ["policy", "report", "complaint", "response", "administration", "university", "system", "support", "resource"],
            "Gender & Identity": ["gender", "woman", "man", "trans", "queer", "identity", "lgbtq", "sexuality", "female", "male"]
        }
        
        theme_counts = {}
        for theme_name, keywords in themes.items():
            theme_count = sum(1 for text in cleaned_texts if any(keyword in text for keyword in keywords))
            if len(valid_responses) > 0:
                theme_percentage = (theme_count / len(valid_responses)) * 100
                theme_counts[theme_name] = theme_percentage
        
        if theme_counts:
            theme_df = pd.DataFrame({'Theme': list(theme_counts.keys()), 
                                     'Percentage': list(theme_counts.values())})
            theme_df = theme_df.sort_values('Percentage', ascending=True)
            theme_fig = px.bar(theme_df, x='Percentage', y='Theme', 
                              title='Theme Prevalence in Responses',
                              color_discrete_sequence=['#2ecc71'],
                              orientation='h')
        else:
            theme_fig = None
        
        # Get sample responses
        sample_responses = valid_responses[field_name].head(3).tolist()
        sample_responses = [resp[:300] + "..." if len(resp) > 300 else resp for resp in sample_responses]
        
        return {
            'word_freq_fig': word_freq_fig,
            'theme_fig': theme_fig,
            'sample_responses': sample_responses
        }

# Flask app for generating the static HTML
app = Flask(__name__)
freezer = Freezer(app)

# Define the HTML template as a single complete template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3C+ Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { padding-top: 20px; }
        .chart-container { margin-bottom: 30px; }
        .tab-content { padding: 20px 0; }
        .navbar { margin-bottom: 20px; }
        .card { margin-bottom: 20px; }
        .stat-box { text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }
        .sample-response { padding: 10px; background-color: #f8f9fa; border-radius: 5px; 
                          margin-bottom: 10px; border: 1px solid #e0e0e0; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center">3C+ Dashboard</h1>
        <h5 class="text-center text-muted mb-4">Results as of {{ current_date }}</h5>
        
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
            <div class="container-fluid">
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'index' %}active{% endif %}" href="index.html">Demographics</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'misogyny' %}active{% endif %}" href="misogyny.html">Misogyny Analysis</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'queerphobia' %}active{% endif %}" href="queerphobia.html">Queerphobia Analysis</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'text-analysis' %}active{% endif %}" href="text-analysis.html">Text Analysis</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'comparative' %}active{% endif %}" href="comparative.html">Comparative Analysis</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
        
        <!-- Main content -->
        <div class="tab-content">
            {{ content|safe }}
        </div>
        
        <!-- Footer -->
        <footer class="mt-5 pt-3 border-top text-center text-muted">
            <p>3C+ Survey Dashboard</p>
            <p><small>Data refreshes automatically every hour</small></p>
        </footer>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {{ scripts|safe }}
</body>
</html>"""

# Create routes for each page
@app.route('/')
def index():
    analyzer = SurveyAnalyzer('data/survey_data.csv')
    stats = analyzer.get_stats()
    charts = analyzer.get_charts_data()
    
    # Create the demographics page content
    content = """
        <!-- Key stats -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="stat-box">
                    <h4>{{ stats.total_responses }}</h4>
                    <p>Total Responses</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-box">
                    <h4>{{ "%.1f"|format(stats.completion_rate) }}%</h4>
                    <p>Completion Rate</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-box">
                    <h4>{{ "%.1f"|format(stats.avg_duration_minutes) }} min</h4>
                    <p>Avg. Duration</p>
                </div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="row">
            <div class="col-md-6 chart-container">
                <div id="gender-chart"></div>
            </div>
            <div class="col-md-6 chart-container">
                <div id="role-chart"></div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-12 chart-container">
                <div id="faculty-chart"></div>
            </div>
        </div>
    """
    
    # Create the scripts for charts
    scripts = """
    <script>
        // Render the gender chart
        var genderData = {{ gender_chart|safe }};
        Plotly.newPlot('gender-chart', genderData.data, genderData.layout);
        
        // Render the role chart
        var roleData = {{ role_chart|safe }};
        Plotly.newPlot('role-chart', roleData.data, roleData.layout);
        
        // Render the faculty chart
        var facultyData = {{ faculty_chart|safe }};
        Plotly.newPlot('faculty-chart', facultyData.data, facultyData.layout);
    </script>
    """
    
    # First render content and scripts with their context
    rendered_content = render_template_string(content, stats=stats)
    rendered_scripts = render_template_string(scripts,
        gender_chart=json.dumps(charts.get('gender', go.Figure()), cls=plotly.utils.PlotlyJSONEncoder),
        role_chart=json.dumps(charts.get('role', go.Figure()), cls=plotly.utils.PlotlyJSONEncoder),
        faculty_chart=json.dumps(charts.get('faculty', go.Figure()), cls=plotly.utils.PlotlyJSONEncoder)
    )
    
    # Then render the main template with the rendered content/scripts
    return render_template_string(
        HTML_TEMPLATE,
        active_page='index',
        current_date=datetime.now().strftime('%B %d, %Y'),
        content=Markup(rendered_content),
        scripts=Markup(rendered_scripts)
    )

@app.route('/misogyny.html')
def misogyny():
    analyzer = SurveyAnalyzer('data/survey_data.csv')
    charts = analyzer.get_charts_data()
    text_analysis = analyzer.analyze_text('Q11_10_TEXT')
    
    # Default values for the template
    chart = go.Figure()
    text_examples = []
    
    if 'misogyny' in charts:
        chart = charts['misogyny']
    
    if text_analysis:
        text_examples = text_analysis['sample_responses']
    # test
    # Create the misogyny page content
    content = """
        <h2 class="mb-4">Misogyny Analysis</h2>
        
        <!-- Main chart -->
        <div class="row mb-4">
            <div class="col-12 chart-container">
                <div id="misogyny-chart"></div>
            </div>
        </div>
        
        <!-- Text examples -->
        <h4 class="mb-3">Selected Response Examples</h4>
        {% if text_examples %}
            {% for example in text_examples %}
                <div class="sample-response">
                    <h5>Response Example {{ loop.index }}</h5>
                    <p>{{ example }}</p>
                </div>
            {% endfor %}
        {% else %}
            <p>No text responses available for the selected filters.</p>
        {% endif %}
    """
    
    # Create the scripts for charts
    scripts = """
    <script>
        // Render the misogyny observations chart
        var misogynyData = {{ misogyny_chart|safe }};
        Plotly.newPlot('misogyny-chart', misogynyData.data, misogynyData.layout);
    </script>
    """
    
    # Render content and scripts
    rendered_content = render_template_string(content, text_examples=text_examples)
    rendered_scripts = render_template_string(scripts,
        misogyny_chart=json.dumps(chart, cls=plotly.utils.PlotlyJSONEncoder)
    )
    
    # Render the main template
    return render_template_string(
        HTML_TEMPLATE,
        active_page='misogyny',
        current_date=datetime.now().strftime('%B %d, %Y'),
        content=Markup(rendered_content),
        scripts=Markup(rendered_scripts)
    )

@app.route('/queerphobia.html')
def queerphobia():
    analyzer = SurveyAnalyzer('data/survey_data.csv')
    charts = analyzer.get_charts_data()
    text_analysis = analyzer.analyze_text('Q20_10_TEXT')
    
    # Default values for the template
    chart = go.Figure()
    text_examples = []
    
    if 'queerphobia' in charts:
        chart = charts['queerphobia']
    
    if text_analysis:
        text_examples = text_analysis['sample_responses']
    
    # Create the queerphobia page content
    content = """
        <h2 class="mb-4">Queerphobia Analysis</h2>
        
        <!-- Main chart -->
        <div class="row mb-4">
            <div class="col-12 chart-container">
                <div id="queerphobia-chart"></div>
            </div>
        </div>
        
        <!-- Text examples -->
        <h4 class="mb-3">Selected Response Examples</h4>
        {% if text_examples %}
            {% for example in text_examples %}
                <div class="sample-response">
                    <h5>Response Example {{ loop.index }}</h5>
                    <p>{{ example }}</p>
                </div>
            {% endfor %}
        {% else %}
            <p>No text responses available for the selected filters.</p>
        {% endif %}
    """
    
    # Create the scripts for charts
    scripts = """
    <script>
        // Render the queerphobia observations chart
        var queerphobiaData = {{ queerphobia_chart|safe }};
        Plotly.newPlot('queerphobia-chart', queerphobiaData.data, queerphobiaData.layout);
    </script>
    """
    
    # Render content and scripts
    rendered_content = render_template_string(content, text_examples=text_examples)
    rendered_scripts = render_template_string(scripts,
        queerphobia_chart=json.dumps(chart, cls=plotly.utils.PlotlyJSONEncoder)
    )
    
    # Render the main template
    return render_template_string(
        HTML_TEMPLATE,
        active_page='queerphobia',
        current_date=datetime.now().strftime('%B %d, %Y'),
        content=Markup(rendered_content),
        scripts=Markup(rendered_scripts)
    )

@app.route('/text-analysis.html')
def text_analysis():
    analyzer = SurveyAnalyzer('data/survey_data.csv')
    
    # Analyze different text fields
    text_fields = [
        {'label': 'Misogyny Experiences (Q11)', 'value': 'Q11_10_TEXT'},
        {'label': 'Queerphobia Experiences (Q20)', 'value': 'Q20_10_TEXT'},
        {'label': 'General Comments (Q40)', 'value': 'Q40'}
    ]
    
    field_viz = {}
    for field in text_fields:
        analysis = analyzer.analyze_text(field['value'])
        if analysis:
            field_viz[field['value']] = {
                'word_freq_fig': json.dumps(analysis['word_freq_fig'], cls=plotly.utils.PlotlyJSONEncoder) if analysis['word_freq_fig'] else None,
                'theme_fig': json.dumps(analysis['theme_fig'], cls=plotly.utils.PlotlyJSONEncoder) if analysis['theme_fig'] else None,
                'sample_responses': analysis['sample_responses']
            }
        else:
            field_viz[field['value']] = {
                'word_freq_fig': None,
                'theme_fig': None,
                'sample_responses': []
            }
    
    # Here we'll create the content for the page
    content_template = """
        <h2 class="mb-4">Text Analysis</h2>
        
        <!-- Field selector -->
        <div class="form-group mb-4">
            <label for="text-field-selector">Select Text Field to Analyze:</label>
            <select class="form-control" id="text-field-selector">
                {% for field in text_fields %}
                    <option value="{{ field.value }}">{{ field.label }}</option>
                {% endfor %}
            </select>
        </div>
        
        <!-- Text field containers -->
        {% for field in text_fields %}
            <div id="text-content-{{ field.value|replace('_', '-') }}" 
                 class="text-field-content" 
                 style="display: {% if loop.first %}block{% else %}none{% endif %};">
                
                {% if field_viz[field.value].word_freq_fig %}
                    <div class="chart-container mb-4">
                        <div id="word-freq-{{ field.value|replace('_', '-') }}"></div>
                    </div>
                {% endif %}
                
                {% if field_viz[field.value].theme_fig %}
                    <div class="chart-container mb-4">
                        <div id="theme-{{ field.value|replace('_', '-') }}"></div>
                    </div>
                {% endif %}
                
                <h4 class="mb-3">Sample Responses</h4>
                {% if field_viz[field.value].sample_responses %}
                    {% for example in field_viz[field.value].sample_responses %}
                        <div class="sample-response">
                            <h5>Response Example {{ loop.index }}</h5>
                            <p>{{ example }}</p>
                        </div>
                    {% endfor %}
                {% else %}
                    <p>No text responses available for the selected filters.</p>
                {% endif %}
            </div>
        {% endfor %}
    """
    
    # And the scripts for visualization
    scripts_template = """
    <script>
        // Plot the word frequency and theme charts for each field
        {% for field in text_fields %}
            {% if field_viz[field.value].word_freq_fig %}
                var wordFreqData{{ loop.index }} = {{ field_viz[field.value].word_freq_fig|safe }};
                Plotly.newPlot('word-freq-{{ field.value|replace('_', '-') }}', 
                              wordFreqData{{ loop.index }}.data, 
                              wordFreqData{{ loop.index }}.layout);
            {% endif %}
            
            {% if field_viz[field.value].theme_fig %}
                var themeData{{ loop.index }} = {{ field_viz[field.value].theme_fig|safe }};
                Plotly.newPlot('theme-{{ field.value|replace('_', '-') }}', 
                              themeData{{ loop.index }}.data, 
                              themeData{{ loop.index }}.layout);
            {% endif %}
        {% endfor %}
        
        // Handle field selection
        document.getElementById('text-field-selector').addEventListener('change', function() {
            // Hide all content divs
            var contentDivs = document.getElementsByClassName('text-field-content');
            for (var i = 0; i < contentDivs.length; i++) {
                contentDivs[i].style.display = 'none';
            }
            
            // Show the selected content
            var selectedValue = this.value;
            var selectedContentId = 'text-content-' + selectedValue.replace(/_/g, '-');
            document.getElementById(selectedContentId).style.display = 'block';
        });
    </script>
    """
    
    # Pre-render content and scripts with their context
    rendered_content = render_template_string(content_template, text_fields=text_fields, field_viz=field_viz)
    rendered_scripts = render_template_string(scripts_template, text_fields=text_fields, field_viz=field_viz)
    
    # Now insert these into the base template with Markup to prevent escaping
    return render_template_string(
        HTML_TEMPLATE,
        active_page='text-analysis',
        current_date=datetime.now().strftime('%B %d, %Y'),
        content=Markup(rendered_content),
        scripts=Markup(rendered_scripts)
    )

@app.route('/comparative.html')
def comparative():
    analyzer = SurveyAnalyzer('data/survey_data.csv')
    charts = analyzer.get_charts_data()
    
    # Default values
    has_comparison_data = False
    bar_chart = go.Figure()
    radar_chart = go.Figure()
    comparison_data = []
    misogyny_mean = 0
    queerphobia_mean = 0
    greatest_diff_context = "N/A"
    
    # Check if comparison data is available
    if all(key in charts for key in ['comparison_bar', 'comparison_radar', 'comparison_data']):
        has_comparison_data = True
        bar_chart = charts['comparison_bar']
        radar_chart = charts['comparison_radar']
        comparison_data = charts['comparison_data']
        misogyny_mean = charts.get('misogyny_mean', 0)
        queerphobia_mean = charts.get('queerphobia_mean', 0)
        greatest_diff_context = charts.get('greatest_diff_context', "N/A")
    
    # Create the comparative analysis content
    content = """
        <h2 class="mb-4">Comparative Analysis</h2>
        
        {% if has_comparison_data %}
            <!-- Charts -->
            <div class="row mb-4">
                <div class="col-md-6 chart-container">
                    <div id="bar-chart"></div>
                </div>
                <div class="col-md-6 chart-container">
                    <div id="radar-chart"></div>
                </div>
            </div>
            
            <!-- Summary -->
            <div class="card mb-4">
                <div class="card-header">
                    <h4>Comparative Analysis Summary</h4>
                </div>
                <div class="card-body">
                    <p>
                        Overall, the data shows that 
                        <strong>
                            {% if misogyny_mean > queerphobia_mean %}
                                misogyny was reported more frequently
                            {% else %}
                                queerphobia was reported more frequently
                            {% endif %}
                        </strong>
                        across the surveyed contexts.
                    </p>
                    <p>
                        The greatest difference was observed in 
                        <strong>{{ greatest_diff_context }}</strong> context.
                    </p>
                </div>
            </div>
            
            <!-- Comparison table -->
            <h4 class="mb-3">Detailed Comparison by Context</h4>
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Context</th>
                            <th>Misogyny Observations (%)</th>
                            <th>Queerphobia Observations (%)</th>
                            <th>Difference (pp)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in comparison_data %}
                            <tr>
                                <td>{{ row.Context }}</td>
                                <td>{{ "%.1f"|format(row['Misogyny Yes %']) }}%</td>
                                <td>{{ "%.1f"|format(row['Queerphobia Yes %']) }}%</td>
                                <td>{{ "%.1f"|format(row.Difference) }}pp</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <div class="alert alert-warning">
                <h4 class="alert-heading">Not enough data for comparison</h4>
                <p>There isn't enough data to perform a comparative analysis between misogyny and queerphobia observations.</p>
            </div>
        {% endif %}
    """
    
    # Create the scripts for comparative charts
    scripts = """
    <script>
        {% if has_comparison_data %}
            // Render bar chart
            var barData = {{ bar_chart|safe }};
            Plotly.newPlot('bar-chart', barData.data, barData.layout);
            
            // Render radar chart
            var radarData = {{ radar_chart|safe }};
            Plotly.newPlot('radar-chart', radarData.data, radarData.layout);
        {% endif %}
    </script>
    """
    
    # Render content and scripts
    rendered_content = render_template_string(content, 
        has_comparison_data=has_comparison_data,
        comparison_data=comparison_data,
        misogyny_mean=misogyny_mean,
        queerphobia_mean=queerphobia_mean,
        greatest_diff_context=greatest_diff_context
    )
    
    rendered_scripts = render_template_string(scripts,
        has_comparison_data=has_comparison_data,
        bar_chart=json.dumps(bar_chart, cls=plotly.utils.PlotlyJSONEncoder),
        radar_chart=json.dumps(radar_chart, cls=plotly.utils.PlotlyJSONEncoder)
    )
    
    # Render the main template
    return render_template_string(
        HTML_TEMPLATE,
        active_page='comparative',
        current_date=datetime.now().strftime('%B %d, %Y'),
        content=Markup(rendered_content),
        scripts=Markup(rendered_scripts)
    )

# Main function to generate the static site
def generate_static_site():
    # Configure Freezer
    app.config['FREEZER_DESTINATION'] = 'docs'#'static_dashboard'
    app.config['FREEZER_RELATIVE_URLS'] = True
    
    # Create the output directory
    os.makedirs('static_dashboard', exist_ok=True)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Check for survey data
    if not os.path.exists('data/survey_data.csv'):
        print("Warning: No survey data found at data/survey_data.csv")
        print("Creating a sample CSV file for testing...")
        
        # Create a simple sample dataset
        sample_data = {
            'Q1': ['Response 1', 'Response 2', 'Response 3'],
            'Q2': ['Woman', 'Man', 'Non-binary'],
            'Q5': ['Arts', 'Science', 'Business'],
            'Q6': ['Student', 'Faculty', 'Staff'],
            'Finished': ['True', 'True', 'True'],
            'Duration (in seconds)': [300, 450, 600],
            'Q10_1': ['Yes', 'No', 'Unsure'],
            'Q10_2': ['No', 'Yes', 'No'],
            'Q10_3': ['Yes', 'Yes', 'No'],
            'Q10_4': ['Unsure', 'No', 'Yes'],
            'Q11_10_TEXT': ['I experienced misogyny in my class.', 'N/A', 'Some students made inappropriate comments.'],
            'Q19_1': ['No', 'Yes', 'Yes'],
            'Q19_2': ['No', 'No', 'Yes'],
            'Q19_3': ['Yes', 'No', 'Unsure'],
            'Q19_4': ['No', 'Yes', 'No'],
            'Q20_10_TEXT': ['N/A', 'Heard homophobic comments in the hallway.', 'Several instances in group projects.'],
            'Q40': ['Overall good experience.', 'Need more awareness programs.', 'The survey was well designed.']
        }
        pd.DataFrame(sample_data).to_csv('data/survey_data.csv', index=False)
    
    # Generate the static site
    print("Generating static site...")
    freezer.freeze()
    print("Static site generated in the 'static_dashboard' directory!")
    print("Open 'static_dashboard/index.html' in your browser to view it.")

if __name__ == '__main__':
    generate_static_site()