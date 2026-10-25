
import streamlit as st

from dashboard.data_service import (
    fetch_parcel,
    fetch_parcel_allocations,
)


def _display_value(record, *keys, default="Not available"):
    """Return the first populated field from a database record."""
    if not record:
        return default

    for key in keys:
        value = record.get(key) if hasattr(record, "get") else None

        if value is not None and str(value).strip():
            return value

    return default


def _status_label(status):
    """Normalize parcel status for consistent display."""
    return str(status or "UNKNOWN").strip().upper()


def _render_parcel_details(parcel):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Sender and recipient")
        st.write("**Sender:**", _display_value(parcel, "sender_name"))
        st.write("**Recipient:**", _display_value(parcel, "recipient_name"))

        st.markdown("#### Route")
        st.write(
            "**Pickup:**",
            _display_value(parcel, "pickup_location"),
        )
        st.write(
            "**Delivery:**",
            _display_value(parcel, "delivery_location"),
        )

    with col2:
        st.markdown("#### Parcel information")
        st.write(
            "**Weight:**",
            f"{_display_value(parcel, 'weight_kg')} kg",
        )
        st.write("**Size:**", _display_value(parcel, "size"))
        st.write("**Priority:**", _display_value(parcel, "priority"))

        st.markdown("#### Current status")
        status = _status_label(
            _display_value(parcel, "status", default="UNKNOWN")
        )

        if status == "ALLOCATED":
            st.success(status)
        elif status in {"PENDING", "REQUESTED", "REGISTERED"}:
            st.info(status)
        elif status in {"UNALLOCATED", "REJECTED"}:
            st.warning(status)
        else:
            st.write(status)


def _render_allocation_history(parcel_id):
    st.markdown("### Allocation history")

    try:
        allocations = fetch_parcel_allocations(parcel_id) or []
    except Exception as exc:
        st.error(f"Could not load allocation history: {exc}")
        return

    if not allocations:
        st.info("No allocation records were found for this parcel.")
        return

    rows = []

    for allocation in allocations:
        if hasattr(allocation, "keys"):
            rows.append({
                "Allocation ID": allocation.get(
                    "allocation_id",
                    allocation.get("id", "—"),
                ),
                "Courier": allocation.get(
                    "courier_id",
                    allocation.get("assigned_courier", "—"),
                ),
                "Status": allocation.get("status", "—"),
                "Allocated At": allocation.get(
                    "allocated_at",
                    allocation.get("created_at", "—"),
                ),
            })
        else:
            rows.append({"Details": str(allocation)})

    st.dataframe(
        rows,
        hide_index=True,
        use_container_width=True,
    )


def render_tracking_page():
    st.markdown(
        '<div class="page-title">Parcel Tracking</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-subtitle">'
        "Search parcel records and review allocation progress."
        "</div>",
        unsafe_allow_html=True,
    )

    with st.form("parcel_tracking_search"):
        col1, col2 = st.columns([4, 1])

        with col1:
            parcel_id = st.text_input(
                "Parcel reference",
                placeholder="Enter a parcel ID, e.g. PKG-1234ABCD",
            ).strip()

        with col2:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            search_clicked = st.form_submit_button(
                "Search",
                type="primary",
                use_container_width=True,
            )

    if search_clicked:
        if not parcel_id:
            st.warning("Enter a parcel reference to search.")
            st.session_state.pop("tracking_parcel_id", None)
        else:
            st.session_state["tracking_parcel_id"] = parcel_id

    selected_id = st.session_state.get("tracking_parcel_id")

    if not selected_id:
        st.info(
            "Enter a parcel reference above to view its details."
        )
        return

    if st.button("Refresh parcel details", key="refresh_tracking"):
        st.rerun()

    try:
        parcel = fetch_parcel(selected_id)
    except Exception as exc:
        st.error(f"Unable to retrieve parcel details: {exc}")
        return

    if not parcel:
        st.warning(f"No parcel was found with reference `{selected_id}`.")
        return

    actual_id = _display_value(
        parcel,
        "parcel_id",
        default=selected_id,
    )

    st.markdown("---")
    st.markdown(f"### Parcel: `{actual_id}`")

    _render_parcel_details(parcel)
    _render_allocation_history(actual_id)
