
import pandas as pd
import streamlit as st

from dashboard.data_service import fetch_allocations, fetch_parcels


def get_value(record, *keys, default="—"):
    """Safely get the first available value from a database record."""
    if not hasattr(record, "get"):
        return default

    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return value

    return default


def build_records(allocations, parcels):
    """Combine allocation information with registered parcel details."""

    parcel_map = {}

    for parcel in parcels:
        parcel_id = get_value(parcel, "parcel_id", "id", default="")
        if parcel_id:
            parcel_map[str(parcel_id)] = parcel

    rows = []
    matched_parcels = set()

    for allocation in allocations:
        parcel_id = str(
            get_value(allocation, "parcel_id", default="")
        )
        parcel = parcel_map.get(parcel_id, {})

        if parcel_id:
            matched_parcels.add(parcel_id)

        status = get_value(
            allocation,
            "status",
            default=get_value(parcel, "status", default="UNKNOWN"),
        )

        rows.append({
            # "Allocation ID": get_value(
            #     allocation, "allocation_id", "id"
            # ),
            "Parcel ID": parcel_id or get_value(parcel, "parcel_id"),
            "Courier ID": get_value(
                allocation,
                "courier_id",
                "assigned_courier",
                "courier",
            ),
            "Sender Name": get_value(
                parcel, "sender_name", "sender"
            ),
            "Receiver Name": get_value(
                parcel, "recipient_name", "receiver_name", "recipient"
            ),
            "From": get_value(
                parcel, "pickup_location", "from_location", "origin"
            ),
            "To": get_value(
                parcel, "delivery_location", "to_location", "destination"
            ),
            "Weight (kg)": get_value(
                parcel, "weight_kg", "weight"
            ),
            "Size": str(get_value(parcel, "size")).title(),
            "Priority": str(get_value(parcel, "priority")).title(),
            "Courier Capacity": get_value(
                allocation,
                "courier_capacity",
                "capacity_kg",
                "max_capacity",
                "max_weight_kg",
                "capacity",
                default="Not recorded",
            ),
            "Remaining Capacity": get_value(
                allocation,
                "remaining_capacity",
                "remaining_capacity_kg",
                default="Not recorded",
            ),
            "Status": str(status).upper(),
            "Allocated At": get_value(
                allocation,
                "allocated_at",
                "created_at",
                "timestamp",
            ),
        })

    # Include parcels without an allocation record.
    for parcel_id, parcel in parcel_map.items():
        if parcel_id in matched_parcels:
            continue

        rows.append({
            # "Allocation ID": "—",
            "Parcel ID": parcel_id,
            "Courier ID": "Not assigned",
            "Sender Name": get_value(parcel, "sender_name"),
            "Receiver Name": get_value(
                parcel, "recipient_name", "receiver_name"
            ),
            "From": get_value(parcel, "pickup_location"),
            "To": get_value(parcel, "delivery_location"),
            "Weight (kg)": get_value(parcel, "weight_kg"),
            "Size": str(get_value(parcel, "size")).title(),
            "Priority": str(get_value(parcel, "priority")).title(),
            "Courier Capacity": "Not recorded",
            "Remaining Capacity": "Not recorded",
            "Status": str(
                get_value(parcel, "status", default="REQUESTED")
            ).upper(),
            "Allocated At": "—",
        })

    return pd.DataFrame(rows)


def render_parcel_allocation_records_page():
    """Render the separate parcel and courier records page."""

    st.markdown(
        '<div class="page-title">Parcel & Courier Records</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-subtitle">'
        "View registered parcels, courier assignments, delivery routes, "
        "capacity information and allocation outcomes."
        "</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([5, 1])

    with left:
        st.caption(
            "This page displays existing database records and does not "
            "initiate new allocation requests."
        )

    with right:
        if st.button("Refresh", use_container_width=True,
                      key="refresh_parcel_courier_records"):
            st.rerun()

    try:
        allocations = fetch_allocations() or []
        parcels = fetch_parcels() or []
    except Exception as exc:
        st.error(f"Unable to load records: {exc}")
        return

    df = build_records(allocations, parcels)

    if df.empty:
        st.info("No parcel or courier records are available yet.")
        return

    # Overview
    statuses = df["Status"].astype(str).str.upper()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Parcels", len(df))
    c2.metric(
        "Allocated",
        int(statuses.isin(["ALLOCATED", "ALREADY_ALLOCATED"]).sum()),
    )
    c3.metric(
        "Unallocated / Rejected",
        int(statuses.isin(["UNALLOCATED", "REJECTED"]).sum()),
    )
    c4.metric(
        "Pending",
        int(statuses.isin(["REQUESTED", "PENDING"]).sum()),
    )

    st.divider()
    st.markdown("### Search and filters")

    f1, f2, f3 = st.columns([2, 1, 1])

    with f1:
        search = st.text_input(
            "Search records",
            placeholder="Parcel ID, courier, name or location",
            key="parcel_courier_search",
        ).strip().lower()

    with f2:
        status_options = ["All"] + sorted(
            df["Status"].astype(str).unique().tolist()
        )
        status_filter = st.selectbox(
            "Allocation status",
            status_options,
            key="parcel_courier_status",
        )

    with f3:
        courier_options = ["All"] + sorted(
            df["Courier ID"].astype(str).unique().tolist()
        )
        courier_filter = st.selectbox(
            "Courier",
            courier_options,
            key="parcel_courier_filter",
        )

    filtered = df.copy()

    if search:
        search_columns = [
            # "Allocation ID",
            "Parcel ID",
            "Courier ID",
            "Sender Name",
            "Receiver Name",
            "From",
            "To",
        ]

        mask = pd.Series(False, index=filtered.index)

        for column in search_columns:
            mask |= filtered[column].astype(str).str.lower().str.contains(
                search, regex=False, na=False
            )

        filtered = filtered[mask]

    if status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]

    if courier_filter != "All":
        filtered = filtered[
            filtered["Courier ID"].astype(str) == courier_filter
        ]

    st.markdown("### Parcel allocation list")
    st.caption(f"{len(filtered)} record(s) found.")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        height=480,
    )

    st.download_button(
        "Download records as CSV",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="parcel_courier_records.csv",
        mime="text/csv",
        key="download_parcel_courier_records",
    )

    # Details for a selected parcel
    st.divider()
    st.markdown("### View individual parcel")

    if filtered.empty:
        st.info("No records match your current filters.")
        return

    selected_id = st.selectbox(
        "Select Parcel ID",
        filtered["Parcel ID"].astype(str).tolist(),
        key="parcel_courier_detail_id",
    )

    selected = filtered[
        filtered["Parcel ID"].astype(str) == selected_id
    ].iloc[0]

    a, b, c = st.columns(3)

    with a:
        st.markdown("**Parcel and contacts**")
        st.write(f"Parcel ID: {selected['Parcel ID']}")
        st.write(f"Sender: {selected['Sender Name']}")
        st.write(f"Receiver: {selected['Receiver Name']}")
        st.write(f"Weight: {selected['Weight (kg)']} kg")
        st.write(f"Size: {selected['Size']}")

    with b:
        st.markdown("**Delivery route**")
        st.write(f"From: {selected['From']}")
        st.write(f"To: {selected['To']}")
        st.write(f"Priority: {selected['Priority']}")

    with c:
        st.markdown("**Courier and allocation**")
        # st.write(f"Allocation ID: {selected['Allocation ID']}")
        st.write(f"Courier ID: {selected['Courier ID']}")
        st.write(f"Status: {selected['Status']}")
        st.write(f"Courier capacity: {selected['Courier Capacity']}")
        st.write(f"Remaining capacity: {selected['Remaining Capacity']}")
        st.write(f"Allocated at: {selected['Allocated At']}")
