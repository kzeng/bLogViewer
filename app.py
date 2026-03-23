import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="Beagle Log Viewer",
    page_icon="📊",
    layout="wide"
)

st.title("🔍 Beagle Log Viewer")
st.markdown("---")

# File uploader
uploaded_file = st.file_uploader("Upload a Beagle log CSV file", type=['csv'])

# Default file option
use_default = st.checkbox("Use default file (./data/beagle_log.csv)", value=True)

if use_default or uploaded_file:
    try:
        # Read the CSV file
        if use_default:
            # Read from default path, skipping first 6 lines
            # Line 7 (index 6) contains headers
            # Data starts from line 8 (index 7)
            df = pd.read_csv(
                './data/beagle_log.csv',
                skiprows=6,
                skipinitialspace=True
            )
        else:
            df = pd.read_csv(
                uploaded_file,
                skiprows=6,
                skipinitialspace=True
            )
        
        # Display file info
        st.subheader("📈 Data Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            st.metric("Data Size", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        
        st.markdown("---")
        
        # Display the dataframe
        st.subheader("📋 Log Data Table")
        
        # Display dataframe with nice formatting
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            hide_index=False
        )
        
        # Expandable section for raw data
        with st.expander("🔍 View Raw Data (without formatting)"):
            st.dataframe(df, use_container_width=True)
        
        # Download button for filtered data
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name="beagle_log_export.csv",
            mime="text/csv",
        )
        
    except FileNotFoundError:
        st.error("❌ Default file not found at './data/beagle_log.csv'")
        st.info("Please upload a file using the file uploader above.")
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
        st.info("Please check the file format and try again.")
else:
    st.info("👆 Please upload a file or check the box to use the default file.")
    st.markdown("""
    ### About
    This application displays Beagle I2C/SPI protocol analyzer log files in a clear, tabular format.
    
    **Expected format:**
    - Lines 1-6: Header/metadata (will be skipped)
    - Line 7: Column headers
    - Line 8+: Data records
    """)
