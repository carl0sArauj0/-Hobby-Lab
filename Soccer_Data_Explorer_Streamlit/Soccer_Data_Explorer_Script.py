# Wassup, to run this file you'll have to create an account on https://www.football-data.org/ and get an API key for it
# Then you'll have to create a new file and copy the code from here
# Finally you'll have to run the file with streamlit run Soccer_Data_Explorer_Script.py
# carl0sArauj0 was here

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

#Api key for Football-Data.org
API_BASE_URL = "https://api.football-data.org/v4/"



@st.cache_data(ttl=3600) # Cache data for 1 hour
def fetch_from_api(endpoint, api_key, params=None):
    """Fetches data from the Football-Data.org API."""
    headers = {'X-Auth-Token': api_key}
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, params=params)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Request Error: {e}")
        if response is not None and response.status_code == 403:
            st.error("This might be due to an invalid API key or exceeding API rate limits.")
        elif response is not None and response.status_code == 404:
            st.error(f"Resource not found at endpoint: {endpoint}. The league or team might not be available.")
        return None
    except ValueError: 
        st.error("Failed to decode JSON from API response.")
        return None

def get_competitions(api_key):
    """Fetches a list of available competitions (leagues/cups)."""
    competitions_data = {
        "PL": "Premier League (England)",
        "BL1": "Bundesliga (Germany)",
        "SA": "Serie A (Italy)",
        "PD": "La Liga (Spain)",
        "FL1": "Ligue 1 (France)",
        "CL": "UEFA Champions League"
    }
    
    return competitions_data

@st.cache_data(ttl=3600)
def get_matches(api_key, competition_code, date_from=None, date_to=None):
    """Fetches matches for a specific competition."""
    params = {}
    if date_from:
        params['dateFrom'] = date_from
    if date_to:
        params['dateTo'] = date_to

    data = fetch_from_api(f"competitions/{competition_code}/matches", api_key, params=params)
    if data and "matches" in data:
        return data["matches"]
    return []

def process_matches_data(matches):
    """Processes match data into a pandas DataFrame."""
    if not matches:
        return pd.DataFrame()

    processed_data = []
    for match in matches:
        if match['status'] == 'FINISHED' and match['score']['fullTime']['home'] is not None and match['score']['fullTime']['away'] is not None:
            processed_data.append({
                'id': match['id'],
                'date': pd.to_datetime(match['utcDate']).strftime('%Y-%m-%d %H:%M'),
                'home_team': match['homeTeam']['name'],
                'home_team_id': match['homeTeam']['id'],
                'away_team': match['awayTeam']['name'],
                'away_team_id': match['awayTeam']['id'],
                'home_goals': match['score']['fullTime']['home'],
                'away_goals': match['score']['fullTime']['away'],
                'total_goals': match['score']['fullTime']['home'] + match['score']['fullTime']['away'],
                'winner': match['score']['winner']
            })
    return pd.DataFrame(processed_data)

def get_team_stats(df_matches, team_id):
    """Calculates stats for a specific team."""
    team_matches = df_matches[
        (df_matches['home_team_id'] == team_id) | (df_matches['away_team_id'] == team_id)
    ]
    if team_matches.empty:
        return None, None

    results = []
    for _, row in team_matches.iterrows():
        if row['home_team_id'] == team_id:
            if row['winner'] == 'HOME_TEAM':
                results.append('Win')
            elif row['winner'] == 'AWAY_TEAM':
                results.append('Loss')
            else:
                results.append('Draw')
        else: # Away team
            if row['winner'] == 'AWAY_TEAM':
                results.append('Win')
            elif row['winner'] == 'HOME_TEAM':
                results.append('Loss')
            else:
                results.append('Draw')

    results_df = pd.DataFrame({'outcome': results})
    outcome_counts = results_df['outcome'].value_counts().reindex(['Win', 'Draw', 'Loss'], fill_value=0)
    outcome_probs = results_df['outcome'].value_counts(normalize=True).reindex(['Win', 'Draw', 'Loss'], fill_value=0) * 100

    return outcome_counts, outcome_probs

# Streamlit magic lol
st.set_page_config(layout="wide")
st.title("⚽ Soccer Data Explorer & Probabilities by Carlos Araújo")

st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Football-Data.org API Key:", type="password")

if not api_key:
    st.sidebar.warning("Please enter your API key to fetch data.")
    st.info("Welcome! Please enter your Football-Data.org API key in the sidebar to load soccer data.")
    st.stop()

# Data fetching 
competitions = get_competitions(api_key)
if not competitions:
    st.error("Could not fetch competitions. Check your API key or network.")
    st.stop()

selected_comp_code = st.sidebar.selectbox(
    "Select Competition:",
    options=list(competitions.keys()),
    format_func=lambda x: competitions[x]
)



# Fetching recent/upcoming matches
st.sidebar.markdown("---")
st.sidebar.markdown("Fetching recent/upcoming matches for the selected league.")
matches_data = get_matches(api_key, selected_comp_code)


if not matches_data:
    st.warning(f"No match data found for {competitions[selected_comp_code]}. This could be due to API limitations, no recent matches, or an issue with the API key/plan.")
    st.stop()

df_matches = process_matches_data(matches_data)

if df_matches.empty:
    st.warning(f"No *finished* match data with scores found for {competitions[selected_comp_code]} in the fetched range.")
    st.stop()

st.header(f"Analysis for {competitions[selected_comp_code]}")
st.dataframe(df_matches.head())

# Statistics type shi

# 1. Overall Goal Distribution
st.subheader("🥅 Overall Goal Distributions")
col1, col2 = st.columns(2)

with col1:
    fig_total_goals = px.histogram(df_matches, x="total_goals",
                                   title="Distribution of Total Goals per Match",
                                   labels={'total_goals': 'Total Goals Scored'},
                                   nbins=int(df_matches['total_goals'].max()) + 1)
    fig_total_goals.update_layout(bargap=0.2)
    st.plotly_chart(fig_total_goals, use_container_width=True)

with col2:
    
    goal_threshold = 2.5
    over_goals_prob = (df_matches['total_goals'] > goal_threshold).mean() * 100
    under_goals_prob = (df_matches['total_goals'] <= goal_threshold).mean() * 100

    st.metric(label=f"Probability of Over {goal_threshold} Goals", value=f"{over_goals_prob:.2f}%")
    st.metric(label=f"Probability of Under/Equal {goal_threshold} Goals", value=f"{under_goals_prob:.2f}%")


# 2. Team Specific Analysis
st.subheader("📊 Team-Specific Analysis")

home_teams = df_matches[['home_team_id', 'home_team']].rename(columns={'home_team_id':'id', 'home_team':'name'})
away_teams = df_matches[['away_team_id', 'away_team']].rename(columns={'away_team_id':'id', 'away_team':'name'})
all_teams_df = pd.concat([home_teams, away_teams]).drop_duplicates(subset=['id']).sort_values(by='name')
team_options = {row['id']: row['name'] for _, row in all_teams_df.iterrows()}

if not team_options:
    st.warning("No teams found in the current match data to select for team-specific analysis.")
else:
    selected_team_id = st.selectbox(
        "Select a Team:",
        options=list(team_options.keys()),
        format_func=lambda x: team_options[x]
    )

    if selected_team_id:
        team_name = team_options[selected_team_id]
        st.markdown(f"#### Performance of {team_name}")

        outcome_counts, outcome_probs = get_team_stats(df_matches, selected_team_id)

        if outcome_counts is not None and outcome_probs is not None:
            col_team1, col_team2 = st.columns(2)
            with col_team1:
                fig_team_outcomes = px.bar(
                    outcome_counts,
                    title=f"Match Outcomes for {team_name} (Counts)",
                    labels={'index': 'Outcome', 'value': 'Number of Matches'}
                )
                st.plotly_chart(fig_team_outcomes, use_container_width=True)

            with col_team2:
                st.markdown(f"**Historical Probabilities for {team_name} (based on these matches):**")
                if 'Win' in outcome_probs: st.metric(label="Win Probability", value=f"{outcome_probs['Win']:.2f}%")
                if 'Draw' in outcome_probs: st.metric(label="Draw Probability", value=f"{outcome_probs['Draw']:.2f}%")
                if 'Loss' in outcome_probs: st.metric(label="Loss Probability", value=f"{outcome_probs['Loss']:.2f}%")

            # Goal distribution when team plays
            team_matches_df = df_matches[
                (df_matches['home_team_id'] == selected_team_id) | (df_matches['away_team_id'] == selected_team_id)
            ]
            if not team_matches_df.empty:
                fig_team_total_goals = px.histogram(
                    team_matches_df, x="total_goals",
                    title=f"Distribution of Total Goals in Matches Involving {team_name}",
                    labels={'total_goals': 'Total Goals Scored'},
                    nbins=int(team_matches_df['total_goals'].max()) + 1 if not team_matches_df.empty else 10
                )
                fig_team_total_goals.update_layout(bargap=0.2)
                st.plotly_chart(fig_team_total_goals, use_container_width=True)
            else:
                st.write(f"No specific match goal data for {team_name} to plot distribution.")

        else:
            st.write(f"No match data found for {team_name} in the selected dataset.")

st.sidebar.markdown("---")
st.sidebar.info("App by AI. Data from Football-Data.org.")