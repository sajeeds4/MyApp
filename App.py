import streamlit as st
import pandas as pd
import altair as alt
import os

# Define file paths
INTAKE_FILE = "intake.csv"
RETURN_FILE = "return.csv"

# Function to initialize CSV files if they don't exist
def init_csv(file, columns):
    if not os.path.exists(file):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)

# Initialize CSV files with necessary columns
init_csv(INTAKE_FILE, ["timestamp", "name", "category", "details"])
init_csv(RETURN_FILE, ["timestamp", "name", "status"])

# Load data
def load_data(file):
    df = pd.read_csv(file)
    # Convert timestamp column to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

intake_df = load_data(INTAKE_FILE)
return_df = load_data(RETURN_FILE)

# Streamlit UI
st.title("Inventory Management Dashboard")

# Sidebar for date filtering
st.sidebar.header("Filter by Date")
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("2024-12-31"))

# Convert sidebar date inputs to datetime
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filter data
intake_filtered = intake_df[
    intake_df["timestamp"].between(start_date, end_date)
]
return_filtered = return_df[
    return_df["timestamp"].between(start_date, end_date)
]

# Display filtered intake data
st.subheader("Intake Records")
st.write(intake_filtered)

# Display filtered return data
st.subheader("Return Records")
st.write(return_filtered)

# Visualization: Count of items by category
st.subheader("Category Distribution")
if not intake_filtered.empty:
    chart = alt.Chart(intake_filtered).mark_bar().encode(
        x="category",
        y="count()",
        tooltip=["category", "count()"],
        color="category"
    ).interactive()
    st.altair_chart(chart, use_container_width=True)
else:
    st.write("No data available for the selected date range.")

# Option to add new records
st.sidebar.header("Add New Record")
record_type = st.sidebar.selectbox("Select Record Type", ["Intake", "Return"])
name = st.sidebar.text_input("Item Name")
category = st.sidebar.text_input("Category") if record_type == "Intake" else None
details = st.sidebar.text_area("Details") if record_type == "Intake" else None
status = st.sidebar.selectbox("Status", ["Pending", "Completed"]) if record_type == "Return" else None
add_record = st.sidebar.button("Add Record")

# Save new record
if add_record:
    new_entry = {
        "timestamp": pd.Timestamp.now(),
        "name": name,
        "category": category if record_type == "Intake" else None,
        "details": details if record_type == "Intake" else None,
        "status": status if record_type == "Return" else None,
    }
    file = INTAKE_FILE if record_type == "Intake" else RETURN_FILE
    df = intake_df if record_type == "Intake" else return_df
    df = df.append(new_entry, ignore_index=True)
    df.to_csv(file, index=False)
    st.sidebar.success("Record added successfully! Refresh to see the update.")

st.write("📌 **Note:** Any changes made will be saved automatically.")
