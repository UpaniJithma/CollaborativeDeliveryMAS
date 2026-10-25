
import asyncio
import json
import sys
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st
import spade
from spade.behaviour import OneShotBehaviour
from spade.message import Message

# ---------------------------------------------------------
# Project paths and imports
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.database import (
    initialize_database,
    save_parcel,
    get_parcel,
    get_all_parcels,
    get_all_couriers,
    get_all_allocations,
    update_parcel_status,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

COORDINATOR_JID = "coordinator@localhost"
XMPP_PASSWORD = "TestPassword123!"
RESPONSE_TIMEOUT_SECONDS = 25

st.set_page_config(
    page_title="Collaborative Delivery MAS",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_database()


# ---------------------------------------------------------
# Professional UI styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        .stApp {
            background-color: #F5F7FB;
        }

        [data-testid="stSidebar"] {
            background-color: #10243A;
        }

        [data-testid="stSidebar"] * {
            color: #FFFFFF;
        }

        .main-title {
            color: #10243A;
            font-size: 2rem;
            font-weight: 750;
            margin-bottom: 0.2rem;
        }

        .sub-title {
            color: #64748B;
            font-size: 0.95rem;
            margin-bottom: 1.4rem;
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 18px;
            border-radius: 12px;
        }

        div[data-testid="stForm"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            padding: 22px;
            border-radius: 12px;
        }

        .section-heading {
            color: #10243A;
            font-size: 1.2rem;
            font-weight: 700;
        }

        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button {
            background-color: #1769AA;
            border-color: #1769AA;
            color: white;
            border-radius: 8px;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Data helpers
# ---------------------------------------------------------

def load_data():
    """Read current records from the existing SQLite database."""
    return (
        get_all_parcels(),
        get_all_couriers(),
        get_all_allocations(),
    )


def allocation_status_for_parcel(parcel_id, allocations):
    """Return the newest allocation status for a parcel."""
    records = [
        record
        for record in allocations
        if str(record.get("parcel_id")) == str(parcel_id)
    ]

    if not records:
        return "Not allocated"

    records.sort(
        key=lambda record: (
            record.get("updated_at")
            or record.get("created_at")
            or ""
        ),
        reverse=True,
    )

    return records[0].get("status", "Unknown")


def format_dataframe(records):
    """Create a display-friendly DataFrame."""
    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


# ---------------------------------------------------------
# SPADE request client
# ---------------------------------------------------------

class AllocationRequestAgent(spade.agent.Agent):

    def __init__(self, jid, password, parcel):
        super().__init__(jid, password)
        self.parcel = parcel
        self.result = None
        self.error = None

    class RequestBehaviour(OneShotBehaviour):

        async def run(self):
            agent = self.agent
            parcel_id = agent.parcel["parcel_id"]

            request = Message(to=COORDINATOR_JID)
            request.set_metadata("performative", "request")
            request.set_metadata("ontology", "parcel-delivery")
            request.body = json.dumps(agent.parcel)

            try:
                await agent.send(request)
                print(
                    f"[UI] Allocation request sent for {parcel_id}"
                )

                deadline = (
                    asyncio.get_running_loop().time()
                    + RESPONSE_TIMEOUT_SECONDS
                )

                while True:
                    remaining = (
                        deadline
                        - asyncio.get_running_loop().time()
                    )

                    if remaining <= 0:
                        agent.error = (
                            "Timed out waiting for the Coordinator. "
                            "The request may still have been processed."
                        )
                        return

                    response = await self.receive(
                        timeout=min(5, remaining)
                    )

                    if response is None:
                        continue

                    sender = (
                        str(response.sender).split("/")[0].lower()
                        if response.sender
                        else ""
                    )

                    if sender != COORDINATOR_JID.lower():
                        continue

                    if (
                        response.get_metadata("ontology")
                        != "parcel-delivery"
                        or response.get_metadata("performative")
                        != "inform"
                    ):
                        continue

                    try:
                        result = json.loads(response.body)
                    except (json.JSONDecodeError, TypeError):
                        continue

                    if result.get("parcel_id") != parcel_id:
                        continue

                    agent.result = result
                    return

            except Exception as error:
                agent.error = (
                    f"{type(error).__name__}: {error}"
                )

    async def setup(self):
        self.add_behaviour(self.RequestBehaviour())


async def send_allocation_request(parcel):
    """
    Start a temporary SPADE agent, request allocation, and stop it.

    The running Coordinator and Courier agents must remain active.
    """
    unique_name = f"ui-{uuid.uuid4().hex[:12]}"

    agent = AllocationRequestAgent(
        f"{unique_name}@localhost",
        XMPP_PASSWORD,
        parcel,
    )

    try:
        await agent.start(auto_register=True)

        deadline = (
            asyncio.get_running_loop().time()
            + RESPONSE_TIMEOUT_SECONDS
            + 5
        )

        while (
            agent.result is None
            and agent.error is None
            and asyncio.get_running_loop().time() < deadline
        ):
            await asyncio.sleep(0.2)

        if agent.error:
            return {
                "success": False,
                "error": agent.error,
                "result": agent.result,
            }

        if agent.result is None:
            return {
                "success": False,
                "error": (
                    "No response received from the Coordinator. "
                    "Check the agent terminals and database before "
                    "retrying."
                ),
                "result": None,
            }

        return {
            "success": True,
            "error": None,
            "result": agent.result,
        }

    except Exception as error:
        return {
            "success": False,
            "error": f"{type(error).__name__}: {error}",
            "result": agent.result,
        }

    finally:
        if agent.is_alive():
            await agent.stop()


def submit_parcel_to_mas(parcel):
    """
    Save the parcel first because the existing Coordinator
    validates that the parcel exists in SQLite.
    """
    existing = get_parcel(parcel["parcel_id"])

    if existing is not None:
        return {
            "success": False,
            "error": "This parcel ID already exists.",
            "result": None,
        }

    save_parcel(parcel)

    try:
        response = asyncio.run(send_allocation_request(parcel))
    except Exception as error:
        return {
            "success": False,
            "error": f"{type(error).__name__}: {error}",
            "result": None,
        }

    result = response.get("result")

    if not response["success"] or result is None:
        # Leave the parcel in the database for investigation.
        # It may have been processed even if the response was lost.
        return response

    status = result.get("status", "UNKNOWN")

    # Keep parcel status synchronized with the Coordinator result.
    if status in {
        "ALLOCATED",
        "UNALLOCATED",
        "ALREADY_ALLOCATED",
        "REJECTED",
    }:
        update_parcel_status(
            parcel["parcel_id"],
            status,
        )

    return response


# ---------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------

with st.sidebar:
    st.markdown("## 📦 Delivery MAS")
    st.caption("Collaborative Last-Mile Operations")
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Register Parcel",
            "Parcel Tracking",
            "Courier Management",
            "Allocation History",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Multi-Agent System")
    st.caption("SPADE • XMPP • SQLite")


# ---------------------------------------------------------
# Load current database records
# ---------------------------------------------------------

parcels, couriers, allocations = load_data()


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

if page == "Dashboard":

    st.markdown(
        '<div class="main-title">Operations Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title">'
        "Monitor parcels, allocation outcomes, and courier capacity."
        "</div>",
        unsafe_allow_html=True,
    )

    total_parcels = len(parcels)

    allocated_ids = {
        str(item.get("parcel_id"))
        for item in allocations
        if item.get("status") == "ALLOCATED"
    }

    allocated_parcels = len(allocated_ids)

    unallocated_parcels = sum(
        1
        for parcel in parcels
        if str(parcel.get("parcel_id")) not in allocated_ids
        and parcel.get("status") not in {
            "REJECTED",
            "CANCELLED",
        }
    )

    total_capacity = sum(
        float(courier.get("capacity_kg", 0))
        for courier in couriers
    )

    remaining_capacity = sum(
        float(courier.get("remaining_capacity_kg", 0))
        for courier in couriers
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Parcels", total_parcels)
    col2.metric("Allocated Parcels", allocated_parcels)
    col3.metric("Pending / Other", unallocated_parcels)
    col4.metric(
        "Available Capacity",
        f"{remaining_capacity:.1f} kg",
        delta=f"Total fleet: {total_capacity:.1f} kg",
        delta_color="off",
    )

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown(
            '<div class="section-heading">Recent Parcels</div>',
            unsafe_allow_html=True,
        )

        if parcels:
            recent = pd.DataFrame(parcels).head(10)

            columns = [
                "parcel_id",
                "pickup_location",
                "delivery_location",
                "weight_kg",
                "priority",
                "status",
            ]

            recent = recent[
                [column for column in columns if column in recent]
            ]

            st.dataframe(
                recent,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No parcels registered yet.")

    with right:
        st.markdown(
            '<div class="section-heading">Courier Capacity</div>',
            unsafe_allow_html=True,
        )

        if couriers:
            for courier in couriers:
                remaining = float(
                    courier.get("remaining_capacity_kg", 0)
                )
                capacity = float(courier.get("capacity_kg", 0))

                ratio = (
                    remaining / capacity
                    if capacity > 0
                    else 0
                )

                st.markdown(
                    f"**{courier['courier_id']}** — "
                    f"{remaining:.1f} / {capacity:.1f} kg"
                )

                st.progress(max(0.0, min(1.0, ratio)))

                st.caption(
                    "Available"
                    if courier.get("available")
                    else "Unavailable"
                )
        else:
            st.info(
                "No couriers are registered. Start the Coordinator "
                "and Courier agents to initialize courier records."
            )

    if st.button("Refresh dashboard"):
        st.rerun()


# ---------------------------------------------------------
# Parcel registration
# ---------------------------------------------------------

elif page == "Register Parcel":

    st.markdown(
        '<div class="main-title">Register a Parcel</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title">'
        "Submit a delivery request to the running multi-agent system."
        "</div>",
        unsafe_allow_html=True,
    )

    with st.form("parcel_registration_form", clear_on_submit=False):

        col1, col2 = st.columns(2)

        with col1:
            sender_name = st.text_input(
                "Sender name *",
                placeholder="Enter sender name",
            )

            recipient_name = st.text_input(
                "Recipient name *",
                placeholder="Enter recipient name",
            )

            pickup_location = st.selectbox(
                "Pickup location *",
                ["Colombo", "Kandy", "Galle", "Jaffna"],
            )

        with col2:
            delivery_location = st.selectbox(
                "Delivery location *",
                ["Kandy", "Colombo", "Galle", "Jaffna"],
                index=0,
            )

            size = st.selectbox(
                "Parcel size",
                ["Small", "Medium", "Large"],
            )

            weight_kg = st.number_input(
                "Weight (kg) *",
                min_value=0.1,
                max_value=100.0,
                value=1.0,
                step=0.5,
            )

        priority = st.select_slider(
            "Priority",
            options=["low", "normal", "high"],
            value="normal",
        )

        st.caption(
            "* Required fields. The parcel is saved before the "
            "Coordinator is contacted."
        )

        submitted = st.form_submit_button(
            "Register & Request Allocation",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        if not sender_name.strip() or not recipient_name.strip():
            st.error("Enter both sender and recipient names.")

        elif pickup_location == delivery_location:
            st.error(
                "Pickup and delivery locations must be different."
            )

        else:
            parcel_id = str(uuid.uuid4())[:8].upper()

            parcel = {
                "parcel_id": parcel_id,
                "sender_name": sender_name.strip(),
                "recipient_name": recipient_name.strip(),
                "pickup_location": pickup_location,
                "delivery_location": delivery_location,
                "size": size.lower(),
                "weight_kg": float(weight_kg),
                "priority": priority,
                "status": "REQUESTED",
            }

            with st.spinner(
                "Registering parcel and contacting the Coordinator..."
            ):
                outcome = submit_parcel_to_mas(parcel)

            if outcome["success"]:
                result = outcome["result"]
                status = result.get("status", "UNKNOWN")

                if status == "ALLOCATED":
                    st.success(
                        f"Parcel {parcel_id} was allocated successfully."
                    )
                    st.write(
                        f"**Assigned courier:** "
                        f"{result.get('courier_id') or 'Not specified'}"
                    )
                    st.write(
                        f"**Details:** {result.get('details', '')}"
                    )

                elif status == "UNALLOCATED":
                    st.warning(
                        f"Parcel {parcel_id} was registered but "
                        "could not be allocated."
                    )
                    st.write(result.get("details", ""))

                elif status == "ALREADY_ALLOCATED":
                    st.warning(
                        "The Coordinator reports that this parcel "
                        "has already been allocated."
                    )

                elif status == "REJECTED":
                    st.error(
                        f"Request rejected: {result.get('details', '')}"
                    )

                else:
                    st.info(
                        f"Coordinator response: {status}. "
                        f"{result.get('details', '')}"
                    )

                st.json(result)

            else:
                st.error(outcome["error"])
                st.warning(
                    "The parcel may already be saved, and the "
                    "Coordinator may have processed the request. "
                    "Check Parcel Tracking and Allocation History "
                    "before submitting another request."
                )

            st.rerun()


# ---------------------------------------------------------
# Parcel tracking
# ---------------------------------------------------------

elif page == "Parcel Tracking":

    st.markdown(
        '<div class="main-title">Parcel Tracking</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title">'
        "Search parcels and inspect their latest allocation records."
        "</div>",
        unsafe_allow_html=True,
    )

    search_id = st.text_input(
        "Search by parcel ID",
        placeholder="Enter a parcel ID",
    )

    parcels, couriers, allocations = load_data()

    filtered_parcels = parcels

    if search_id.strip():
        filtered_parcels = [
            parcel
            for parcel in parcels
            if search_id.strip().lower()
            in str(parcel.get("parcel_id", "")).lower()
        ]

    if filtered_parcels:
        st.dataframe(
            pd.DataFrame(filtered_parcels),
            use_container_width=True,
            hide_index=True,
        )

        selected_id = st.selectbox(
            "Select parcel for details",
            [
                parcel["parcel_id"]
                for parcel in filtered_parcels
            ],
        )

        selected_parcel = get_parcel(selected_id)

        if selected_parcel:
            st.subheader(f"Parcel: {selected_id}")
            st.json(selected_parcel)

            parcel_allocations = [
                allocation
                for allocation in allocations
                if str(allocation.get("parcel_id")) == str(selected_id)
            ]

            st.markdown("#### Allocation records")

            if parcel_allocations:
                st.dataframe(
                    pd.DataFrame(parcel_allocations),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No allocation records found for this parcel.")
    else:
        st.info("No matching parcels found.")

    if st.button("Refresh parcel data"):
        st.rerun()


# ---------------------------------------------------------
# Courier management
# ---------------------------------------------------------

elif page == "Courier Management":

    st.markdown(
        '<div class="main-title">Courier Management</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title">'
        "Review courier availability, service locations, and capacity."
        "</div>",
        unsafe_allow_html=True,
    )

    couriers = get_all_couriers()

    if couriers:
        display_couriers = []

        for courier in couriers:
            display_couriers.append(
                {
                    "Courier ID": courier.get("courier_id"),
                    "JID": courier.get("jid"),
                    "Available": (
                        "Yes" if courier.get("available") else "No"
                    ),
                    "Capacity (kg)": courier.get("capacity_kg"),
                    "Remaining (kg)": courier.get(
                        "remaining_capacity_kg"
                    ),
                    "Delivery locations": ", ".join(
                        courier.get("delivery_locations", [])
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(display_couriers),
            use_container_width=True,
            hide_index=True,
        )

        for courier in couriers:
            with st.expander(
                f"{courier['courier_id']} — capacity details"
            ):
                capacity = float(courier.get("capacity_kg", 0))
                remaining = float(
                    courier.get("remaining_capacity_kg", 0)
                )

                st.write(
                    f"**Remaining capacity:** {remaining:.1f} kg"
                )
                st.write(
                    f"**Used capacity:** {capacity - remaining:.1f} kg"
                )
                st.write(
                    f"**Available:** "
                    f"{'Yes' if courier.get('available') else 'No'}"
                )
                st.write(
                    "**Locations:**",
                    ", ".join(courier.get("delivery_locations", [])),
                )
    else:
        st.info(
            "No couriers found. Start the Coordinator and Courier "
            "agents and verify their database initialization."
        )

    if st.button("Refresh courier data"):
        st.rerun()


# ---------------------------------------------------------
# Allocation history
# ---------------------------------------------------------

elif page == "Allocation History":

    st.markdown(
        '<div class="main-title">Allocation History</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title">'
        "Review persisted allocation attempts and outcomes."
        "</div>",
        unsafe_allow_html=True,
    )

    allocations = get_all_allocations()

    if allocations:
        allocation_df = pd.DataFrame(allocations)

        if "status" in allocation_df.columns:
            statuses = sorted(
                allocation_df["status"]
                .fillna("Unknown")
                .astype(str)
                .unique()
                .tolist()
            )

            selected_statuses = st.multiselect(
                "Filter by allocation status",
                statuses,
                default=statuses,
            )

            allocation_df = allocation_df[
                allocation_df["status"]
                .fillna("Unknown")
                .astype(str)
                .isin(selected_statuses)
            ]

        st.dataframe(
            allocation_df,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = allocation_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download allocation history as CSV",
            data=csv_data,
            file_name="allocation_history.csv",
            mime="text/csv",
        )

    else:
        st.info("No allocation records are available.")

    if st.button("Refresh allocation history"):
        st.rerun()
