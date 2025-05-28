import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set the title of the app
st.title("Analysis of Peace Agreement Implementation on Local Economic Activity")

# Load your dataset
@st.cache_data
def load_data(file):
    return pd.read_csv(file)

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    data = load_data(uploaded_file)
    st.write("Data Preview:", data.head())

    # Select variables for analysis
    variables = st.multiselect("Select variables for analysis", data.columns)

    # Select years for comparison
    years = st.multiselect("Select years for comparison", data['year'].unique())

    if len(variables) > 0 and len(years) == 2:
        year1, year2 = years
        data_year1 = data[data['year'] == year1]
        data_year2 = data[data['year'] == year2]

        # Calculate means
        means_year1 = data_year1[variables].mean()
        means_year2 = data_year2[variables].mean()

        # Plot distributions
        st.write("### Distribution Comparison")
        for var in variables:
            fig, ax = plt.subplots()
            sns.histplot(data_year1[var], kde=True, ax=ax, label=f'Year {year1}')
            sns.histplot(data_year2[var], kde=True, ax=ax, label=f'Year {year2}')
            ax.set_title(f'Distribution of {var}')
            ax.legend()
            st.pyplot(fig)

        # Display means
        st.write("### Mean Comparison")
        means_df = pd.DataFrame({'Year 1': means_year1, 'Year 2': means_year2})
        st.write(means_df)

        # Hypothesis and Model Explanation
        st.write("""
        ### Hypothesis
        The implementation of the peace agreement has influenced economic growth in the regions most affected by the conflict.

        ### Variables
        - Regional GDP growth
        - Unemployment rates
        - Foreign direct investment

        ### Model
        Differences-in-differences or panel data models can be used to assess the effects over time.
        """)

        # Guide for PR
        st.write("""
        ### Guide for PR
        1. **Data Collection**: Ensure data is collected consistently across years and regions.
        2. **Variable Selection**: Choose relevant economic indicators that reflect local economic activity.
        3. **Model Selection**: Use differences-in-differences or panel data models to control for time-invariant characteristics and isolate the effect of the peace agreement.
        4. **Interpretation**: Analyze the results to understand the impact of the peace agreement on economic growth and other indicators.
        """)

