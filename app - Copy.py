import streamlit as st
import pandas as pd
import json


def load_desc_map() -> dict:
    try:
        with open("desc.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_desc_map(desc_map: dict) -> None:
    with open("desc.json", "w", encoding="utf-8") as f:
        json.dump(desc_map, f, indent=2, ensure_ascii=False)


# Set page configuration
st.set_page_config(
    page_title="Beagle Log Viewer",
    page_icon="📊",
    layout="wide"
)

# Load current description mapping once per run
desc_map = load_desc_map()

# Sidebar navigation and controls
with st.sidebar:
    # Compact Features header to reduce vertical spacing
    st.markdown("**📦 Features**")
    page = st.radio(
        "Page",
        ["Log Viewer", "Desc Config"],
        index=0,
        label_visibility="collapsed",
    )
    if page == "Log Viewer":
        st.subheader("⚙️ Controls")
        uploaded_file = st.file_uploader("Upload a Beagle log CSV file", type=['csv'])
        use_default = st.checkbox("Use default file (./data/beagle_log.csv)", value=True)

# Show main title only on Log Viewer page
if page == "Log Viewer":
    st.title("🔍 Beagle Log Viewer")

if page == "Desc Config":
    st.subheader("🔧 Desc.json Configuration")

    # Always reload latest mapping from file for this page
    desc_map = load_desc_map()

    # Two-column layout: left 70% table, right 30% forms
    col_left, col_right = st.columns([7, 3])

    with col_left:
        # Show current mapping as a table
        if desc_map:
            keys = sorted(desc_map.keys())
            desc_df = pd.DataFrame(
                {
                    "Key": keys,
                    "Value": [str(desc_map[k]) for k in keys],
                }
            )
            st.dataframe(desc_df, width="stretch", height=800)
            st.caption(f"Total entries: {len(keys)}")
        else:
            st.info("desc.json is currently empty.")

    with col_right:
        # Add / update entry
        st.subheader("Add / Update Entry")
        with st.form("add_update_desc"):
            new_key = st.text_input("Key (e.g. WR 7F)")
            new_value = st.text_input("Value (description)")
            submitted = st.form_submit_button("Save / Update")
            if submitted:
                key = new_key.strip()
                if not key:
                    st.error("Key cannot be empty.")
                else:
                    desc_map[key] = new_value.strip()
                    save_desc_map(desc_map)
                    st.success(f"Saved mapping for '{key}'.")

        st.subheader("Delete Entry")
        if desc_map:
            keys_for_delete = sorted(desc_map.keys())
            with st.form("delete_desc"):
                del_key = st.selectbox("Select key to delete", options=keys_for_delete)
                del_submitted = st.form_submit_button("Delete")
                if del_submitted:
                    desc_map.pop(del_key, None)
                    save_desc_map(desc_map)
                    st.success(f"Deleted mapping for '{del_key}'.")
        else:
            st.info("No entries to delete.")

elif page == "Log Viewer" and (use_default or uploaded_file):
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
        
        # Compute Idle column (in microseconds) based on start time and duration
        def _parse_time_to_us(t):
            try:
                t_str = str(t).strip()
                if not t_str:
                    return None
                m_part, rest = t_str.split(":")
                s_part, ms_part, us_part = rest.split(".")
                total_us = ((int(m_part) * 60) + int(s_part)) * 1_000_000
                total_us += int(ms_part) * 1_000
                total_us += int(us_part)
                return total_us
            except Exception:
                return None

        def _parse_dur_to_us(d):
            """Parse duration strings like '278.100 us' or '1.23 ms' into microseconds."""
            try:
                d_str = str(d).strip()
                if not d_str:
                    return None

                lower = d_str.lower()
                factor = 1.0

                if lower.endswith("us"):
                    num_str = lower[:-2].strip()
                    factor = 1.0
                elif lower.endswith("ms"):
                    num_str = lower[:-2].strip()
                    # beagle 原始为 13.3 ms，导出 csv 后为 13.389.200 ms
                    # 规则：第二个点后的数字可忽略，即 13.389.200 -> 13.389
                    parts = num_str.split(".")
                    if len(parts) > 2:
                        num_str = ".".join(parts[:2])
                    factor = 1_000.0  # ms -> us
                elif lower.endswith("s"):
                    num_str = lower[:-1].strip()
                    factor = 1_000_000.0  # s -> us
                else:
                    # No explicit unit, assume value is already in microseconds
                    num_str = lower

                return float(num_str) * factor
            except Exception:
                return None

        if "m:s.ms.us" in df.columns and "Dur" in df.columns:
            start_us = df["m:s.ms.us"].map(_parse_time_to_us)
            dur_us = df["Dur"].map(_parse_dur_to_us)

            idle_values = ["-"] * len(df)
            # Idle rule:
            # - 如果本条启动时间为 0:00.000.000 -> '-'
            # - 否则 Idle = 下条启动时间 - 本条启动时间 - 本条持续时间
            for i in range(len(df) - 1):
                su = start_us.iloc[i]
                next_su = start_us.iloc[i + 1]
                du = dur_us.iloc[i]
                if (
                    pd.notna(su)
                    and pd.notna(next_su)
                    and pd.notna(du)
                    and su != 0
                ):
                    idle = next_su - su - du
                    idle_values[i] = f"{idle:.3f}"

            df["Idle"] = idle_values

        # Compute Act column based on S/P and Data
        if "S/P" in df.columns and "Data" in df.columns:
            act_values = ["-"] * len(df)
            sp_series = df["S/P"].astype(str).str.strip()
            data_series = df["Data"].astype(str).str.strip()

            for i in range(len(df)):
                sp = sp_series.iloc[i]

                # 如果本条 S/P = S: Act = "RD " + 本条 Data + " " + 下条 Data
                if sp == "S":
                    if i + 1 < len(df):
                        cur_data = data_series.iloc[i]
                        next_data = data_series.iloc[i + 1]
                        act_values[i] = f"RD {cur_data} {next_data}"
                    continue

                # 如果本条 S/P = SP
                if sp == "SP":
                    # 没有上一条，保持 '-'
                    if i == 0:
                        continue
                    prev_sp = sp_series.iloc[i - 1]

                    # 上一条 S/P = S -> '-'
                    if prev_sp == "S":
                        continue

                    # 上一条 S/P = SP -> "WR " + 本条 Data
                    if prev_sp == "SP":
                        cur_data = data_series.iloc[i]
                        act_values[i] = f"WR {cur_data}"

            df["Act"] = act_values

        # Compute Desc column based on Act and desc.json mapping
        if "Act" in df.columns:
            desc_values = []
            for act in df["Act"]:
                act_str = str(act).strip()
                # Act 为 '-' 或空，Desc 也为 '-'
                if not act_str or act_str == "-":
                    desc_values.append("-")
                    continue

                # 使用 Act 前 5 个字符作为 KEY，例如 'WR 7F', 'RD 02'
                key = act_str[:5]
                desc_values.append(desc_map.get(key, "-"))

            df["Desc"] = desc_values
        
        # Display file info in sidebar as a table
        with st.sidebar:
            st.subheader("📈 Data Overview")
            overview_df = pd.DataFrame(
                {
                    "Metric": ["Total Records", "Columns", "Data Size (KB)"],
                    "Value": [
                        len(df),
                        len(df.columns),
                        f"{df.memory_usage(deep=True).sum() / 1024:.2f}",
                    ],
                }
            )
            st.table(overview_df)
        
        # st.markdown("---")

        # Prepare dataframe for display: drop first column (# Level) and ASCII
        df_display = df.copy()

        # Drop ASCII column (name may include # or spaces)
        cols_to_drop = []
        for col in df_display.columns:
            normalized = col.strip().lstrip('#').lower()
            if normalized == "ascii":
                cols_to_drop.append(col)
        if cols_to_drop:
            df_display = df_display.drop(columns=cols_to_drop)

        # Drop the first column (e.g., '# Level')
        if df_display.shape[1] > 0:
            df_display = df_display.iloc[:, 1:]

        # Display dataframe with nice formatting (hide redundant index)
        st.dataframe(
            df_display,
            width="stretch",
            height=800,
            hide_index=True,
        )

        # Download button for filtered data
        csv = df_display.to_csv(index=False).encode('utf-8')
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
elif page == "Log Viewer":
    st.info("👆 Please upload a file or check the box to use the default file.")
    st.markdown("""
    ### About
    This application displays Beagle I2C/SPI protocol analyzer log files in a clear, tabular format.
    
    **Expected format:**
    - Lines 1-6: Header/metadata (will be skipped)
    - Line 7: Column headers
    - Line 8+: Data records
    """)
