import streamlit as st
import pandas as pd

from utils.status import ui_status_from_db

def bulk_ticket_comparison_page(conn):
    st.markdown("## 🔍 Bulk Ticket Comparison")
    st.write("""
        Paste a list of ticket numbers (one per line) to see how they compare 
        with tickets in the database:
        - **Missing in DB**: In your pasted list but not in the DB.
        - **Extra in DB**: In the DB but not in your pasted list.
        - **Matches**: Found in both.
    """)

    pasted_tickets_text = st.text_area(
        "Paste ticket numbers here (one per line)",
        height=200,
        placeholder="e.g.\n12345\n12346\nABC999"
    )

    if st.button("Compare"):
        user_tickets = set()
        lines = pasted_tickets_text.strip().splitlines()
        for line in lines:
            line = line.strip()
            if line:
                user_tickets.add(line)

        if not user_tickets:
            st.warning("No valid ticket numbers found in the text area.")
            return

        df_db_tickets = pd.read_sql("SELECT ticket_number FROM tickets", conn)
        db_tickets = set(df_db_tickets["ticket_number"].tolist())

        missing_in_db = user_tickets - db_tickets
        extra_in_db = db_tickets - user_tickets
        matches = user_tickets & db_tickets

        colA, colB, colC = st.columns(3)
        with colA:
            st.metric("Missing in DB", len(missing_in_db))
        with colB:
            st.metric("Extra in DB", len(extra_in_db))
        with colC:
            st.metric("Matches", len(matches))

        st.write("---")
        st.subheader("Details")

        # Missing in DB
        if missing_in_db:
            st.write("### Tickets Missing in DB")
            st.write(", ".join(sorted(missing_in_db)))
        else:
            st.info("No missing tickets in DB.")

        # Extra in DB
        if extra_in_db:
            st.write("### Tickets in DB But Not in Your List")
            st.write(", ".join(sorted(extra_in_db)))
            placeholders = ",".join(["?"] * len(extra_in_db))
            query_extra = f"SELECT * FROM tickets WHERE ticket_number IN ({placeholders})"
            df_extra = pd.read_sql(query_extra, conn, params=list(extra_in_db))
            df_extra["status"] = df_extra["status"].apply(ui_status_from_db)
            st.dataframe(df_extra, use_container_width=True)
        else:
            st.info("No extra tickets found in DB.")

        # Matches
        if matches:
            st.write("### Matched Tickets (In Both Lists)")
            placeholders = ",".join(["?"] * len(matches))
            query = f"SELECT * FROM tickets WHERE ticket_number IN ({placeholders})"
            df_matched = pd.read_sql(query, conn, params=list(matches))
            df_matched["status"] = df_matched["status"].apply(ui_status_from_db)
            st.dataframe(df_matched, use_container_width=True)
        else:
            st.info("No tickets were found in both lists.")
