
import math
import streamlit as st

from dashboard.data_service import (
    fetch_couriers,
    get_courier_capacity,
)

from services.database import (
    save_courier,
    delete_courier,
    set_courier_availability,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

LOCATIONS = ["Colombo", "Kandy", "Galle", "Jaffna"]


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def _value(record, *keys, default="—"):
    """Return the first non-empty field from a record."""
    if not hasattr(record, "get"):
        return default

    for key in keys:
        value = record.get(key)

        if value is not None and str(value).strip():
            return value

    return default


def _is_available(courier):
    """Interpret common database availability values."""
    value = _value(
        courier,
        "available",
        "is_available",
        "status",
        "availability",
        default="",
    )

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value == 1

    return str(value).strip().lower() in {
        "available",
        "true",
        "yes",
        "1",
        "active",
    }


def _capacity_metrics(courier):
    """Use the actual keys returned by get_courier_capacity()."""
    capacity = get_courier_capacity(courier)

    total = float(capacity.get("capacity_kg", 0) or 0)
    remaining = float(
        capacity.get("remaining_capacity_kg", 0) or 0
    )
    used = float(capacity.get("used_capacity_kg", 0) or 0)

    utilisation = (
        used / total * 100
        if total > 0
        else 0.0
    )

    return {
        "total": total,
        "used": used,
        "remaining": remaining,
        "utilisation": max(0.0, min(utilisation, 100.0)),
    }


def _courier_id(courier):
    return str(
        _value(courier, "courier_id", "id", default="")
    ).strip().upper()


def _service_locations(courier):
    """Return normalized service locations from a courier record."""
    locations = courier.get("delivery_locations", [])

    if isinstance(locations, str):
        import json

        try:
            locations = json.loads(locations)
        except (ValueError, TypeError):
            locations = [
                item.strip()
                for item in locations.split(",")
                if item.strip()
            ]

    if not isinstance(locations, (list, tuple)):
        return []

    return [
        str(location).strip()
        for location in locations
        if str(location).strip()
    ]


def _load_couriers():
    """Load current courier records with an error message on failure."""
    try:
        return fetch_couriers()
    except Exception as exc:
        st.error(f"Could not load courier records: {exc}")
        return None


def _get_courier_by_id(couriers, courier_id):
    for courier in couriers:
        if _courier_id(courier) == courier_id:
            return courier
    return None


# ---------------------------------------------------------
# Add courier
# ---------------------------------------------------------

def _render_add_courier(couriers):
    st.markdown("### Add a courier")
    st.caption(
        "Register a courier agent, define its XMPP address, "
        "service areas and carrying capacity."
    )

    with st.form("add_courier_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            courier_id = st.text_input(
                "Courier ID *",
                placeholder="e.g. C002",
            )

            jid = st.text_input(
                "XMPP JID *",
                placeholder="e.g. courier2@localhost",
            )

        with col2:
            total_capacity = st.number_input(
                "Total capacity (kg) *",
                min_value=0.1,
                max_value=10000.0,
                value=10.0,
                step=0.5,
            )

            initial_available = st.checkbox(
                "Mark courier as available",
                value=True,
            )

        service_locations = st.multiselect(
            "Service areas *",
            options=LOCATIONS,
            default=["Colombo"],
            help="Select every destination this courier can serve.",
        )

        submitted = st.form_submit_button(
            "Add courier",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    courier_id = courier_id.strip().upper()
    jid = jid.strip()

    if not courier_id:
        st.error("Enter a courier ID.")
        return

    if not jid or "@" not in jid:
        st.error("Enter a valid XMPP JID, such as courier2@localhost.")
        return

    if not service_locations:
        st.error("Select at least one service area.")
        return

    if _get_courier_by_id(couriers, courier_id):
        st.error(f"Courier ID {courier_id} already exists.")
        return

    if any(
        str(courier.get("jid", "")).strip().lower() == jid.lower()
        for courier in couriers
    ):
        st.error("That XMPP JID is already registered.")
        return

    try:
        save_courier(
            {
                "courier_id": courier_id,
                "jid": jid,
                "available": initial_available,
                "capacity_kg": float(total_capacity),
                "remaining_capacity_kg": float(total_capacity),
                "delivery_locations": service_locations,
            }
        )

        st.session_state["courier_notice"] = (
            "success",
            f"Courier {courier_id} was added to the database.",
        )
        st.rerun()

    except Exception as exc:
        st.error(f"Could not add courier: {exc}")


# ---------------------------------------------------------
# Edit courier
# ---------------------------------------------------------

def _render_edit_courier(couriers):
    st.markdown("### Edit courier details")

    if not couriers:
        st.info("There are no couriers to edit.")
        return

    courier_options = {
        f"{_courier_id(c)} — {c.get('jid', '')}": _courier_id(c)
        for c in couriers
    }

    selected_label = st.selectbox(
        "Select courier to edit",
        list(courier_options.keys()),
        key="edit_courier_selector",
    )

    selected_id = courier_options[selected_label]
    courier = _get_courier_by_id(couriers, selected_id)

    if courier is None:
        st.error("The selected courier could not be found.")
        return

    capacity = _capacity_metrics(courier)
    current_locations = _service_locations(courier)

    st.info(
        f"Current capacity usage: {capacity['used']:.1f} kg used "
        f"of {capacity['total']:.1f} kg."
    )

    with st.form(f"edit_courier_form_{selected_id}"):
        new_jid = st.text_input(
            "XMPP JID *",
            value=str(courier.get("jid", "")),
        )

        new_total = st.number_input(
            "Total capacity (kg) *",
            min_value=0.1,
            max_value=10000.0,
            value=max(0.1, capacity["total"]),
            step=0.5,
        )

        new_locations = st.multiselect(
            "Service areas *",
            options=LOCATIONS,
            default=[
                location
                for location in current_locations
                if location in LOCATIONS
            ],
        )

        save_changes = st.form_submit_button(
            "Save changes",
            type="primary",
            use_container_width=True,
        )

    if not save_changes:
        return

    new_jid = new_jid.strip()

    if not new_jid or "@" not in new_jid:
        st.error("Enter a valid XMPP JID.")
        return

    if not new_locations:
        st.error("Select at least one service area.")
        return

    duplicate_jid = any(
        _courier_id(other) != selected_id
        and str(other.get("jid", "")).strip().lower()
        == new_jid.lower()
        for other in couriers
    )

    if duplicate_jid:
        st.error("That XMPP JID belongs to another courier.")
        return

    # Preserve used capacity rather than resetting usage.
    used_capacity = capacity["used"]

    if new_total < used_capacity:
        st.error(
            f"Capacity cannot be less than the existing "
            f"{used_capacity:.1f} kg already in use."
        )
        return

    new_remaining = max(0.0, new_total - used_capacity)

    try:
        save_courier(
            {
                "courier_id": selected_id,
                "jid": new_jid,
                "available": _is_available(courier),
                "capacity_kg": float(new_total),
                "remaining_capacity_kg": float(new_remaining),
                "delivery_locations": new_locations,
            }
        )

        st.session_state["courier_notice"] = (
            "success",
            f"Courier {selected_id} was updated.",
        )
        st.rerun()

    except Exception as exc:
        st.error(f"Could not update courier: {exc}")


# ---------------------------------------------------------
# Activate / deactivate courier
# ---------------------------------------------------------

def _render_availability_management(couriers):
    st.markdown("### Availability management")
    st.caption(
        "Deactivate couriers that should not receive new assignments. "
        "This updates the database record."
    )

    if not couriers:
        st.info("There are no couriers to manage.")
        return

    for courier in couriers:
        courier_id = _courier_id(courier)
        available = _is_available(courier)

        with st.container(border=True):
            info_col, status_col, action_col = st.columns(
                [3, 1, 1],
                vertical_alignment="center",
            )

            with info_col:
                st.markdown(f"**{courier_id}**")
                st.caption(courier.get("jid", "No JID"))

            with status_col:
                if available:
                    st.success("Available")
                else:
                    st.warning("Unavailable")

            with action_col:
                action_label = (
                    "Deactivate" if available else "Activate"
                )

                if st.button(
                    action_label,
                    key=f"availability_{courier_id}",
                    use_container_width=True,
                ):
                    try:
                        updated = set_courier_availability(
                            courier_id,
                            not available,
                        )

                        if not updated:
                            st.error("Courier record was not updated.")
                        else:
                            st.session_state["courier_notice"] = (
                                "success",
                                f"{courier_id} is now "
                                f"{'available' if not available else 'unavailable'} "
                                "in the database.",
                            )
                            st.rerun()

                    except Exception as exc:
                        st.error(
                            f"Could not update availability: {exc}"
                        )


# ---------------------------------------------------------
# Delete courier
# ---------------------------------------------------------

def _render_delete_courier(couriers):
    st.markdown("### Remove a courier")
    st.caption(
        "Couriers with allocation history are protected from deletion. "
        "Deactivate them instead to retain historical records."
    )

    if not couriers:
        st.info("There are no couriers to remove.")
        return

    options = {
        f"{_courier_id(c)} — {c.get('jid', '')}": _courier_id(c)
        for c in couriers
    }

    selected_label = st.selectbox(
        "Courier to remove",
        list(options.keys()),
        key="delete_courier_selector",
    )

    selected_id = options[selected_label]

    confirm = st.checkbox(
        f"I understand that deleting {selected_id} cannot be undone.",
        key=f"confirm_delete_{selected_id}",
    )

    if st.button(
        "Delete courier",
        type="secondary",
        disabled=not confirm,
        key=f"delete_button_{selected_id}",
    ):
        try:
            success, message = delete_courier(selected_id)

            if success:
                st.session_state["courier_notice"] = (
                    "success",
                    message,
                )
                st.rerun()
            else:
                st.error(message)

        except Exception as exc:
            st.error(f"Could not delete courier: {exc}")


# ---------------------------------------------------------
# Main page
# ---------------------------------------------------------

def render_courier_page():
    st.markdown(
        '<div class="page-title">Courier Management</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-subtitle">'
        "Manage courier agents, service areas, availability "
        "and carrying capacity."
        "</div>",
        unsafe_allow_html=True,
    )

    notice = st.session_state.pop("courier_notice", None)
    if notice:
        level, message = notice
        if level == "success":
            st.success(message)
        else:
            st.info(message)

    top_left, top_right = st.columns([4, 1])

    with top_left:
        st.caption(
            "Changes here are saved to SQLite. A running SPADE agent "
            "may require synchronization or restart to apply them."
        )

    with top_right:
        if st.button(
            "Refresh data",
            type="secondary",
            use_container_width=True,
        ):
            st.rerun()

    couriers = _load_couriers()

    if couriers is None:
        return

    # -----------------------------------------------------
    # Fleet overview
    # -----------------------------------------------------

    courier_rows = []

    for courier in couriers:
        try:
            capacity = _capacity_metrics(courier)
        except Exception:
            capacity = {
                "total": 0.0,
                "used": 0.0,
                "remaining": 0.0,
                "utilisation": 0.0,
            }

        courier_rows.append(
            {
                "Courier ID": _courier_id(courier),
                "XMPP JID": str(courier.get("jid", "—")),
                "Service Areas": ", ".join(
                    _service_locations(courier)
                ),
                "Status": (
                    "Available"
                    if _is_available(courier)
                    else "Unavailable"
                ),
                "Total Capacity (kg)": capacity["total"],
                "Used Capacity (kg)": capacity["used"],
                "Remaining Capacity (kg)": capacity["remaining"],
                "Utilisation (%)": capacity["utilisation"],
            }
        )

    total_couriers = len(courier_rows)
    available_count = sum(
        row["Status"] == "Available"
        for row in courier_rows
    )
    unavailable_count = total_couriers - available_count

    fleet_total = sum(
        row["Total Capacity (kg)"]
        for row in courier_rows
    )
    fleet_used = sum(
        row["Used Capacity (kg)"]
        for row in courier_rows
    )
    fleet_remaining = sum(
        row["Remaining Capacity (kg)"]
        for row in courier_rows
    )

    fleet_utilisation = (
        fleet_used / fleet_total * 100
        if fleet_total > 0
        else 0.0
    )
    fleet_utilisation = max(0.0, min(fleet_utilisation, 100.0))

    st.markdown("### Fleet overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Couriers", total_couriers)
    col2.metric("Available", available_count)
    col3.metric("Unavailable", unavailable_count)
    col4.metric("Remaining Capacity", f"{fleet_remaining:.1f} kg")

    cap1, cap2, cap3 = st.columns(3)
    cap1.metric("Fleet Capacity", f"{fleet_total:.1f} kg")
    cap2.metric("Capacity Used", f"{fleet_used:.1f} kg")
    cap3.metric("Fleet Utilisation", f"{fleet_utilisation:.1f}%")

    st.progress(
        fleet_utilisation / 100,
        text=f"Fleet capacity utilisation: {fleet_utilisation:.1f}%",
    )

    # -----------------------------------------------------
    # Courier directory
    # -----------------------------------------------------

    st.markdown("---")
    st.markdown("### Courier directory")

    search = st.text_input(
        "Search by courier ID or JID",
        placeholder="e.g. C001 or courier1@localhost",
        key="courier_search",
    ).strip().lower()

    status_filter = st.selectbox(
        "Availability filter",
        ["All", "Available", "Unavailable"],
        key="courier_status_filter",
    )

    filtered_rows = [
        row
        for row in courier_rows
        if (
            not search
            or search in row["Courier ID"].lower()
            or search in row["XMPP JID"].lower()
            or search in row["Service Areas"].lower()
        )
        and (
            status_filter == "All"
            or row["Status"] == status_filter
        )
    ]

    if filtered_rows:
        st.dataframe(
            filtered_rows,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Total Capacity (kg)": st.column_config.NumberColumn(
                    format="%.1f kg"
                ),
                "Used Capacity (kg)": st.column_config.NumberColumn(
                    format="%.1f kg"
                ),
                "Remaining Capacity (kg)": st.column_config.NumberColumn(
                    format="%.1f kg"
                ),
                "Utilisation (%)": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                ),
            },
        )
    else:
        st.info("No couriers match your filters.")

    # -----------------------------------------------------
    # Individual capacity
    # -----------------------------------------------------

    with st.expander("View individual courier capacity"):
        for row in courier_rows:
            with st.container(border=True):
                st.markdown(
                    f"**{row['Courier ID']}** — {row['XMPP JID']}"
                )
                st.caption(
                    f"Service areas: {row['Service Areas'] or 'None'}"
                )

                m1, m2, m3 = st.columns(3)
                m1.metric(
                    "Total",
                    f"{row['Total Capacity (kg)']:.1f} kg",
                )
                m2.metric(
                    "Used",
                    f"{row['Used Capacity (kg)']:.1f} kg",
                )
                m3.metric(
                    "Remaining",
                    f"{row['Remaining Capacity (kg)']:.1f} kg",
                )

                st.progress(
                    row["Utilisation (%)"] / 100,
                    text=(
                        f"Utilisation: {row['Utilisation (%)']:.1f}%"
                    ),
                )

    # -----------------------------------------------------
    # Management workspace
    # -----------------------------------------------------

    st.markdown("---")
    st.markdown("## Manage couriers")

    add_tab, edit_tab, availability_tab, delete_tab = st.tabs(
        [
            "Add courier",
            "Edit courier",
            "Availability",
            "Remove courier",
        ]
    )

    with add_tab:
        _render_add_courier(couriers)

    with edit_tab:
        _render_edit_courier(couriers)

    with availability_tab:
        _render_availability_management(couriers)

    with delete_tab:
        _render_delete_courier(couriers)
