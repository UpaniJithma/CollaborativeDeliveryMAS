
import streamlit as st

from dashboard.data_service import fetch_couriers


LOCATIONS = ["Colombo", "Kandy", "Galle", "Jaffna"]


def render_experiment_setup():
    st.markdown(
        '<div class="page-title">Experiment Setup</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-subtitle">'
        "Configure couriers and delivery requests."
        "</div>",
        unsafe_allow_html=True,
    )

    st.info(
        "Preview only — parcels are not saved and agents are not launched."
    )

    # 1. Experiment details
    st.subheader("1. Experiment details")

    col1, col2 = st.columns([2, 1])

    with col1:
        experiment_name = st.text_input(
            "Experiment name",
            value="Delivery Experiment 01",
            key="setup_experiment_name",
        )

    with col2:
        execution_mode = st.radio(
            "Execution mode",
            ["Single request", "Batch requests"],
            key="setup_execution_mode",
        )

    st.divider()

    # 2. Courier configuration
    st.subheader("2. Courier configuration")

    try:
        couriers = fetch_couriers() or []
        courier_error = None
    except Exception as exc:
        couriers = []
        courier_error = str(exc)

    col1, col2 = st.columns([2, 1])

    with col1:
        courier_mode = st.selectbox(
            "Courier management",
            [
                "Use existing couriers",
                "Configure existing couriers",
                "Create new courier agents",
            ],
            key="setup_courier_mode",
        )

    with col2:
        st.metric("Registered couriers", len(couriers))

    if courier_error:
        st.error(f"Unable to load courier records: {courier_error}")

    elif couriers:
        with st.expander("View registered couriers", expanded=False):
            st.dataframe(
                [
                    {
                        "Courier ID": courier.get("courier_id", "Unknown"),
                        "JID": courier.get("jid", "Unknown"),
                        "Available": courier.get("available", False),
                        "Capacity (kg)": courier.get("capacity_kg", 0),
                        "Remaining (kg)": courier.get(
                            "remaining_capacity_kg", 0
                        ),
                    }
                    for courier in couriers
                ],
                hide_index=True,
                use_container_width=True,
            )
    else:
        st.warning(
            "No couriers registered. Add or configure couriers "
            "before running a delivery experiment."
        )

    if courier_mode == "Create new courier agents":
        st.caption(
            "Dynamic agent creation is not connected yet."
        )
        st.number_input(
            "Planned number of new couriers",
            min_value=1,
            max_value=20,
            value=2,
            step=1,
            key="setup_new_courier_count",
        )

    elif courier_mode == "Configure existing couriers":
        st.caption(
            "Existing courier configuration is not connected yet."
        )

    st.divider()

    # 3. Delivery request configuration
    st.subheader("3. Delivery request configuration")

    if execution_mode == "Single request":
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            pickup = st.selectbox(
                "Pickup",
                LOCATIONS,
                key="setup_pickup",
            )

        available_destinations = [
            location for location in LOCATIONS if location != pickup
        ]

        # Reset the destination if the pickup changes.
        if st.session_state.get("setup_destination") == pickup:
            st.session_state.pop("setup_destination", None)

        with col2:
            destination = st.selectbox(
                "Delivery destination",
                available_destinations,
                key="setup_destination",
            )

        with col3:
            weight = st.number_input(
                "Weight (kg)",
                min_value=0.1,
                max_value=100.0,
                value=1.0,
                step=0.1,
                key="setup_weight",
            )

        with col4:
            priority = st.selectbox(
                "Priority",
                ["Normal", "High", "Low"],
                key="setup_priority",
            )

    else:
        batch_count = st.number_input(
            "Number of requests",
            min_value=2,
            max_value=100,
            value=5,
            step=1,
            key="setup_batch_count",
        )
        st.caption(
            f"{batch_count} requests configured. "
            "Batch execution is not connected yet."
        )

    st.divider()

    # 4. Experiment controls
    col1, col2 = st.columns([1, 2])

    with col1:
        st.button(
            "Start Experiment",
            type="primary",
            use_container_width=True,
            disabled=True,
            help="Execution will be enabled after integration "
                 "with the existing MAS workflow.",
        )

    with col2:
        st.caption(
            f"Experiment: {experiment_name.strip() or 'Unnamed experiment'}"
        )

    # Keep the configured values available for the next
    # integration step without writing to the database.
    st.session_state["experiment_config_preview"] = {
        "experiment_name": experiment_name.strip(),
        "execution_mode": execution_mode,
        "courier_mode": courier_mode,
    }

    if execution_mode == "Single request":
        st.session_state["experiment_config_preview"].update({
            "pickup": pickup,
            "destination": destination,
            "weight_kg": weight,
            "priority": priority,
        })
    else:
        st.session_state["experiment_config_preview"].update({
            "batch_count": batch_count,
        })

    if courier_mode == "Create new courier agents":
        st.session_state["experiment_config_preview"][
            "new_courier_count"
        ] = st.session_state["setup_new_courier_count"]
