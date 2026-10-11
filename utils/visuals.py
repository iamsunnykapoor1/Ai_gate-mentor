import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Color Palette Definitions
BG_COLOR = "rgba(0,0,0,0)"
TEXT_COLOR = "#F8FAFC"
GRID_COLOR = "#1E293B"
NEON_INDIGO = "#6366F1"
NEON_VIOLET = "#A855F7"
NEON_EMERALD = "#10B981"
NEON_AMBER = "#F59E0B"
NEON_ROSE = "#F43F5E"

def draw_readiness_gauge(readiness_pct: float):
    """Draws a beautiful neon readiness gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=readiness_pct,
        number={'suffix': "%", 'font': {'color': TEXT_COLOR, 'size': 44, 'family': 'Outfit'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': TEXT_COLOR},
            'bar': {'color': NEON_INDIGO, 'thickness': 0.25},
            'bgcolor': 'rgba(30, 41, 59, 0.5)',
            'borderwidth': 1,
            'bordercolor': GRID_COLOR,
            'steps': [
                {'range': [0, 40], 'color': 'rgba(244, 63, 94, 0.1)'},
                {'range': [40, 75], 'color': 'rgba(245, 158, 11, 0.1)'},
                {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.1)'}
            ],
            'threshold': {
                'line': {'color': NEON_EMERALD, 'width': 3},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font={'color': TEXT_COLOR, 'family': 'Plus Jakarta Sans'},
        margin=dict(l=20, r=20, t=30, b=20),
        height=220
    )
    return fig

def draw_subject_radar(df: pd.DataFrame):
    """Draws a Radar Chart for Subject-wise Accuracy."""
    if df.empty:
        # Return empty fig with message
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=BG_COLOR,
            plot_bgcolor=BG_COLOR,
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{'text': "No data available", 'textcolor': TEXT_COLOR, 'showarrow': False}]
        )
        return fig

    # Ensure accuracy is numeric
    df['accuracy'] = pd.to_numeric(df['accuracy']).fillna(0)
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=df['accuracy'],
        theta=df['subject_name'],
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.2)',
        line=dict(color=NEON_INDIGO, width=2),
        name='Accuracy (%)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor=GRID_COLOR,
                linecolor=GRID_COLOR,
                tickfont=dict(color="#64748B", size=9)
            ),
            angularaxis=dict(
                gridcolor=GRID_COLOR,
                linecolor=GRID_COLOR,
                tickfont=dict(color=TEXT_COLOR, size=10)
            ),
            bgcolor=BG_COLOR
        ),
        showlegend=False,
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        margin=dict(l=40, r=40, t=20, b=20),
        height=320
    )
    return fig

def draw_accuracy_trend(df: pd.DataFrame):
    """Draws an interactive timeline of user accuracy trends."""
    if df.empty:
        fig = go.Figure()
        return fig
    
    # Sort by date
    df = df.sort_values('attempt_date')
    
    # Simple rolling average for smoothing
    df['rolling_accuracy'] = df['daily_accuracy'].rolling(window=3, min_periods=1).mean()
    
    fig = go.Figure()
    
    # Daily scatter points
    fig.add_trace(go.Scatter(
        x=df['attempt_date'],
        y=df['daily_accuracy'],
        mode='markers',
        marker=dict(color=NEON_VIOLET, size=6, opacity=0.4),
        name='Daily Accuracy'
    ))
    
    # Smoothed trend line
    fig.add_trace(go.Scatter(
        x=df['attempt_date'],
        y=df['rolling_accuracy'],
        mode='lines',
        line=dict(color=NEON_INDIGO, width=3, shape='spline'),
        name='Accuracy Trend'
    ))
    
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        showlegend=False,
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color="#64748B"),
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color="#64748B"),
            range=[0, 105],
            suffix="%"
        )
    )
    return fig

def draw_time_vs_accuracy(df: pd.DataFrame):
    """
    Draws a bubble chart plotting Average Time Spent vs Accuracy for each topic.
    Marker size indicates total attempts.
    """
    if df.empty:
        fig = go.Figure()
        return fig

    # Clamp time spent to reasonable limits for visualization
    df['avg_time_spent'] = pd.to_numeric(df['avg_time_spent']).fillna(0)
    df['accuracy'] = pd.to_numeric(df['accuracy']).fillna(0)
    df['total_attempts'] = pd.to_numeric(df['total_attempts']).fillna(1)
    
    # Determine colors based on accuracy
    colors = []
    for acc in df['accuracy']:
        if acc >= 75:
            colors.append(NEON_EMERALD)
        elif acc >= 50:
            colors.append(NEON_AMBER)
        else:
            colors.append(NEON_ROSE)
            
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['avg_time_spent'],
        y=df['accuracy'],
        mode='markers+text',
        marker=dict(
            size=df['total_attempts'] * 3 + 12, # scaled
            color=colors,
            opacity=0.7,
            line=dict(width=1, color=TEXT_COLOR)
        ),
        text=df['topic_name'],
        textposition="top center",
        textfont=dict(size=8, color="#94A3B8"),
        hovertemplate="<b>%{text}</b><br>Accuracy: %{y:.1f}%<br>Avg Time: %{x:.1f}s<br>Attempts: %{customdata}<br><extra></extra>",
        customdata=df['total_attempts']
    ))
    
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        xaxis=dict(
            title="Avg Time Spent per Question (seconds)",
            titlefont=dict(color="#64748B", size=11),
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color="#64748B")
        ),
        yaxis=dict(
            title="Accuracy (%)",
            titlefont=dict(color="#64748B", size=11),
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color="#64748B"),
            range=[-5, 110]
        )
    )
    return fig

def draw_solved_distribution(df: pd.DataFrame):
    """Draws a beautiful bar chart representing questions solved per subject."""
    if df.empty:
        fig = go.Figure()
        return fig
        
    df = df.sort_values('total_attempts', ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['subject_name'],
        x=df['total_attempts'],
        orientation='h',
        marker=dict(
            color=df['total_attempts'],
            colorscale='Viridis',
            line=dict(color='rgba(255,255,255,0.1)', width=1)
        ),
        hovertemplate="<b>%{y}</b><br>Solved: %{x}<br><extra></extra>"
    ))
    
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        margin=dict(l=10, r=10, t=10, b=10),
        height=300,
        xaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickfont=dict(color="#64748B")
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_COLOR, size=10)
        )
    )
    return fig

def draw_activity_heatmap(df_attempts: pd.DataFrame):
    """Draws a GitHub-style activity calendar heatmap of attempts over the last 35 days."""
    import datetime
    
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=34) # 35 days total
    
    counts = {}
    if not df_attempts.empty:
        df_attempts['attempt_date'] = pd.to_datetime(df_attempts['attempt_date']).dt.date
        counts = df_attempts.set_index('attempt_date')['total_attempts'].to_dict()
        
    z = []
    hover_texts = []
    
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    for day_idx in range(7):
        row_z = []
        row_hover = []
        for week_idx in range(5):
            date_val = start_date + datetime.timedelta(days=(week_idx * 7) + day_idx)
            val = int(counts.get(date_val, 0))
            row_z.append(val)
            row_hover.append(f"{date_val.strftime('%b %d, %Y')}<br>Solved: {val} Questions")
        z.append(row_z)
        hover_texts.append(row_hover)
        
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
        y=weekdays,
        colorscale=[
            [0.0, 'rgba(15, 23, 42, 0.4)'],
            [0.25, '#064e3b'],
            [0.5, '#047857'],
            [0.75, '#10b981'],
            [1.0, '#34d399']
        ],
        hoverinfo='text',
        hovertext=hover_texts,
        xgap=4,
        ygap=4,
        showscale=False
    ))
    
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        margin=dict(l=20, r=20, t=10, b=10),
        height=180,
        xaxis=dict(showgrid=False, tickfont=dict(color="#64748B"), showticklabels=True),
        yaxis=dict(showgrid=False, tickfont=dict(color=TEXT_COLOR), showticklabels=True),
    )
    return fig

