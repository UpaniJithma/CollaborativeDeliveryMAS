
import pandas as pd
import streamlit as st

from dashboard.data_service import (
    fetch_allocations,
    fetch_parcels,
)


def _get_value(record, *keys, default="—"):
    """Safely retrieve a field from a database record."""
    if not hasattr(record, "get"):
        return default

    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return value

    return default


def render_allocation_page():
    st.markdown(
        '<div class="page-title">Allocation History</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-subtitle">'
        "Review parcel allocation decisions and courier assignments."
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([4, 1])

    with col1:
        st.caption(
            "Records are loaded from your existing database. "
            "This page does not initiate new allocation requests."
        )

    with col2:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    try:
        allocations = fetch_allocations() or []
        parcels = fetch_parcels() or []
    except Exception as exc:
        st.error(f"Unable to load allocation history: {exc}")
        return

    # Convert records into a DataFrame for filtering and display.
    allocation_rows = []

    for allocation in allocations:
        if not hasattr(allocation, "get"):
            continue

        allocation_rows.append({
            "Allocation ID": _get_value(
                allocation, "allocation_id", "id"
            ),
            "Parcel ID": _get_value(
                allocation, "parcel_id"
            ),
            "Courier ID": _get_value(
                allocation,
                "courier_id",
                "assigned_courier",
            ),
            "Status": str(
                _get_value(
                    allocation,
                    "status",
                    default="UNKNOWN",
                )
            ).upper(),
            "Allocated At": _get_value(
                allocation,
                "allocated_at",
                "created_at",
                "timestamp",
            ),
        })

    df = pd.DataFrame(allocation_rows)

    # Summary counts.
    total_records = len(df)

    if total_records:
        statuses = df["Status"].astype(str).str.upper()
        successful = int((statuses == "ALLOCATED").sum())
        rejected = int(
            statuses.isin(["REJECTED", "UNALLOCATED"]).sum()
        )
        other = total_records - successful - rejected
    else:
        successful = 0
        rejected = 0
        other = 0

    st.markdown("### Allocation overview")

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("Total Records", total_records)
    metric2.metric("Allocated", successful)
    metric3.metric("Rejected / Unallocated", rejected)
    metric4.metric("Other Statuses", other)

    if df.empty:
        st.info(
            "No allocation records are currently available. "
            "Allocation records will appear here when the MAS "
            "processes requests."
        )
        return

    st.markdown("---")
    st.markdown("### Search and filters")

    filter1, filter2, filter3 = st.columns(3)

    with filter1:
        search_text = st.text_input(
            "Search",
            placeholder="Parcel, courier or allocation ID",
        ).strip().lower()

    with filter2:
        status_options = ["All"] + sorted(
            df["Status"].dropna().astype(str).unique().tolist()
        )
        selected_status = st.selectbox(
            "Allocation status",
            status_options,
        )

    with filter3:
        courier_options = ["All"] + sorted(
            df["Courier ID"].dropna().astype(str).unique().tolist()
        )
        selected_courier = st.selectbox(
            "Courier",
            courier_options,
        )

    filtered = df.copy()

    if search_text:
        search_columns = [
            "Allocation ID",
            "Parcel ID",
            "Courier ID",
        ]

        mask = pd.Series(False, index=filtered.index)

        for column in search_columns:
            mask |= (
                filtered[column]
                .astype(str)
                .str.lower()
                .str.contains(search_text, regex=False, na=False)
            )

        filtered = filtered[mask]

    if selected_status != "All":
        filtered = filtered[
            filtered["Status"].astype(str) == selected_status
        ]

    if selected_courier != "All":
        filtered = filtered[
            filtered["Courier ID"].astype(str) == selected_courier
        ]

    st.markdown("### Allocation records")
    st.caption(f"{len(filtered)} record(s) match your filters.")

    st.dataframe(
        filtered,
        hide_index=True,
        use_container_width=True,
    )

    # Status distribution chart.
    st.markdown("---")
    st.markdown("### Allocation status distribution")

    status_counts = (
        filtered["Status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Records")
    )

    if not status_counts.empty:
        st.bar_chart(
            status_counts,
            x="Status",
            y="Records",
            horizontal=True,
        )

    # Parcel records provide additional context for troubleshooting.
    with st.expander("View registered parcel records"):
        parcel_rows = []

        for parcel in parcels:
            if not hasattr(parcel, "get"):
                continue

            parcel_rows.append({
                "Parcel ID": _get_value(parcel, "parcel_id"),
                "Sender": _get_value(parcel, "sender_name"),
                "Recipient": _get_value(parcel, "recipient_name"),
                "Pickup": _get_value(parcel, "pickup_location"),
                "Delivery": _get_value(parcel, "delivery_location"),
                "Status": _get_value(parcel, "status"),
                "Weight (kg)": _get_value(parcel, "weight_kg"),
            })

        if parcel_rows:
            st.dataframe(
                parcel_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No parcel records are available.")
