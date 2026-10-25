
import asyncio
import uuid

import streamlit as st

from dashboard.mas_client import send_allocation_request
from services.database import save_parcel, update_parcel_status


LOCATIONS = ["Colombo", "Kandy", "Galle", "Jaffna"]

VALID_COORDINATOR_STATUSES = {
    "ALLOCATED",
    "UNALLOCATED",
    "ALREADY_ALLOCATED",
    "REJECTED",
    "PENDING",
    "REQUESTED",
}


def _render_page_styles():
    """Apply styling specific to the parcel registration page."""

    st.markdown(
        """
        <style>
        .register-intro {
            color: #64748B;
            font-size: 14px;
            line-height: 1.7;
            margin-bottom: 18px;
        }

        .register-section-title {
            color: #102440;
            font-size: 17px;
            font-weight: 750;
            margin: 6px 0 3px 0;
        }

        .register-section-description {
            color: #64748B;
            font-size: 12px;
            margin-bottom: 12px;
        }

        .route-preview {
            background: #F0F6FF;
            border: 1px solid #DFE9FC;
            border-radius: 14px;
            padding: 18px;
            margin: 8px 0 18px 0;
        }

        .route-label {
            color: #64748B;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        .route-location {
            color: #102440;
            font-size: 16px;
            font-weight: 700;
            margin-top: 5px;
        }

        .route-arrow {
            color: #245CF5;
            font-size: 25px;
            font-weight: 700;
            text-align: center;
            padding-top: 12px;
        }

        .register-note {
            color: #64748B;
            font-size: 12px;
            line-height: 1.6;
        }

        .result-panel {
            background: #F8FAFC;
            border: 1px solid #E2EAF5;
            border-radius: 14px;
            padding: 18px;
        }

        .result-label {
            color: #64748B;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }

        .result-value {
            color: #102440;
            font-size: 20px;
            font-weight: 800;
            margin-top: 5px;
            overflow-wrap: anywhere;
        }

        [data-testid="stMain"] [data-testid="stForm"] {
            background: #FFFFFF;
            border: 1px solid #E2EAF5;
            border-radius: 16px;
            padding: 22px;
        }

        @media (max-width: 768px) {
            [data-testid="stMain"] [data-testid="stForm"] {
                padding: 14px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _show_allocation_result(
    parcel_id,
    parcel,
    response,
):
    """Display the Coordinator's response without inventing outcomes."""

    result = response.get("result") or {}

    coordinator_status = str(
        result.get("status", "")
    ).upper().strip()

    courier_id = (
        result.get("courier_id")
        or result.get("assigned_courier")
        or result.get("courier")
    )

    st.markdown("---")
    st.markdown("## Registration result")

    result_col1, result_col2 = st.columns(2)

    with result_col1:
        st.markdown(
            f"""
            <div class="result-panel">
                <div class="result-label">Parcel reference</div>
                <div class="result-value">{parcel_id}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with result_col2:
        st.markdown(
            f"""
            <div class="result-panel">
                <div class="result-label">Coordinator status</div>
                <div class="result-value">
                    {coordinator_status or "UNKNOWN"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if coordinator_status == "ALLOCATED":
        st.success("The MAS Coordinator reports that the parcel was allocated.")

        if courier_id:
            st.markdown("### Assigned courier")
            st.info(f"Courier reference: **{courier_id}**")

    elif coordinator_status == "ALREADY_ALLOCATED":
        st.info(
            "The Coordinator reports that this parcel is already allocated. "
            "Check the allocation history for the existing assignment."
        )

    elif coordinator_status == "UNALLOCATED":
        st.warning(
            "The parcel was registered, but a courier was not allocated. "
            "Check courier availability, service areas, and capacity."
        )

    elif coordinator_status == "REJECTED":
        st.error("The Coordinator rejected the allocation request.")

    elif coordinator_status in {"PENDING", "REQUESTED"}:
        st.info(
            "The request has not yet reached a confirmed allocation outcome."
        )

    else:
        st.warning(
            "The response did not contain a recognized allocation status. "
            "Check the Coordinator response details before retrying."
        )

    if result:
        with st.expander("Coordinator response details"):
            st.json(result)

    st.markdown("### Parcel summary")

    summary = [
        {"Field": "Sender", "Value": parcel["sender_name"]},
        {"Field": "Recipient", "Value": parcel["recipient_name"]},
        {"Field": "Pickup location", "Value": parcel["pickup_location"]},
        {"Field": "Delivery location", "Value": parcel["delivery_location"]},
        {"Field": "Weight", "Value": f'{parcel["weight_kg"]:.1f} kg'},
        {"Field": "Size", "Value": parcel["size"].title()},
        {"Field": "Priority", "Value": parcel["priority"].title()},
    ]

    st.dataframe(
        summary,
        hide_index=True,
        use_container_width=True,
    )


def render_register_page():
    """Render the parcel registration and allocation request page."""

    _render_page_styles()

    st.markdown(
        '<div class="page-title">Register a Parcel</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="register-intro">
            Enter the sender, recipient, route and parcel details.
            DeliveryMAS will save the parcel and send an allocation request
            to the Multi-Agent System Coordinator.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Registration saves the parcel to SQLite before contacting "
        "the Coordinator. If the response times out, check the parcel "
        "and allocation records before submitting another request."
    )

    # --------------------------------------------------
    # PARCEL REGISTRATION FORM
    # --------------------------------------------------

    with st.form("parcel_registration_form", clear_on_submit=False):

        st.markdown(
            '<div class="register-section-title">Sender and recipient</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="register-section-description">'
            "Provide the contact names for this shipment."
            "</div>",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            sender_name = st.text_input(
                "Sender name *",
                placeholder="Enter sender's full name",
            )

        with col2:
            recipient_name = st.text_input(
                "Recipient name *",
                placeholder="Enter recipient's full name",
            )

        st.markdown(
            '<div class="register-section-title">Delivery route</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="register-section-description">'
            "Choose different pickup and delivery locations."
            "</div>",
            unsafe_allow_html=True,
        )

        route_col1, route_col2 = st.columns(2)

        with route_col1:
            pickup_location = st.selectbox(
                "Pickup location *",
                LOCATIONS,
                key="register_pickup_location",
            )

        with route_col2:
            delivery_options = [
                location
                for location in LOCATIONS
                if location != pickup_location
            ]

            delivery_location = st.selectbox(
                "Delivery location *",
                delivery_options,
                key="register_delivery_location",
            )

        st.markdown(
            '<div class="register-section-title">Parcel details</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="register-section-description">'
            "Specify the parcel weight, size and delivery priority."
            "</div>",
            unsafe_allow_html=True,
        )

        col3, col4, col5 = st.columns(3)

        with col3:
            weight_kg = st.number_input(
                "Weight (kg) *",
                min_value=0.1,
                max_value=100.0,
                value=1.0,
                step=0.1,
                format="%.1f",
            )

        with col4:
            size = st.selectbox(
                "Parcel size *",
                ["Small", "Medium", "Large"],
            )

        with col5:
            priority = st.selectbox(
                "Priority *",
                ["Normal", "High", "Low"],
            )

        st.caption("* Required fields")

        submitted = st.form_submit_button(
            "Register Parcel & Request Allocation",
            type="primary",
            use_container_width=True,
        )

    # --------------------------------------------------
    # ROUTE PREVIEW
    # --------------------------------------------------

    st.markdown(
        f"""
        <div class="route-preview">
            <div style="
                display: grid;
                grid-template-columns: 1fr 50px 1fr;
                align-items: start;
            ">
                <div>
                    <div class="route-label">Pickup</div>
                    <div class="route-location">{pickup_location}</div>
                </div>
                <div class="route-arrow">→</div>
                <div>
                    <div class="route-label">Delivery</div>
                    <div class="route-location">{delivery_location}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not submitted:
        st.markdown(
            """
            <div class="register-note">
                After submission, the Coordinator will evaluate the request
                using the existing MAS allocation workflow.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    sender_name = sender_name.strip()
    recipient_name = recipient_name.strip()

    if not sender_name or not recipient_name:
        st.error("Enter both the sender's and recipient's names.")
        return

    if pickup_location == delivery_location:
        st.error("Pickup and delivery locations must be different.")
        return

    # --------------------------------------------------
    # CREATE AND SAVE PARCEL
    # --------------------------------------------------

    parcel_id = f"PKG-{uuid.uuid4().hex[:8].upper()}"

    parcel = {
        "parcel_id": parcel_id,
        "sender_name": sender_name,
        "recipient_name": recipient_name,
        "pickup_location": pickup_location,
        "delivery_location": delivery_location,
        "size": size.lower(),
        "weight_kg": float(weight_kg),
        "priority": priority.lower(),
        "status": "REQUESTED",
    }

    try:
        save_parcel(parcel)

    except Exception as exc:
        st.error(f"Could not save the parcel to the database: {exc}")
        return

    # --------------------------------------------------
    # SEND REAL MAS ALLOCATION REQUEST
    # --------------------------------------------------

    with st.spinner(
        "Contacting the MAS Coordinator and waiting for a response..."
    ):
        try:
            response = asyncio.run(
                send_allocation_request(parcel)
            )

        except Exception as exc:
            st.warning(
                "The parcel was saved, but the allocation request "
                "did not return a successful response."
            )
            st.code(parcel_id)
            st.error(str(exc))
            st.caption(
                "Check the Coordinator terminal and database records "
                "before attempting another request."
            )
            return

    if not isinstance(response, dict) or not response.get("success"):
        st.warning(
            "The parcel was saved, but the allocation request "
            "did not complete successfully."
        )
        st.markdown(f"**Parcel reference:** `{parcel_id}`")

        error_message = (
            response.get("error", "No response was received.")
            if isinstance(response, dict)
            else "The MAS client returned an unexpected response."
        )

        st.error(error_message)
        st.caption(
            "Check the Coordinator terminal and parcel status before "
            "retrying. The Coordinator may already have processed "
            "the request."
        )
        return

    # --------------------------------------------------
    # PROCESS COORDINATOR RESPONSE
    # --------------------------------------------------

    result = response.get("result") or {}

    if not isinstance(result, dict):
        st.warning(
            "The request returned successfully, but the Coordinator "
            "response format was unexpected."
        )
        st.code(parcel_id)
        st.write(result)
        return

    coordinator_status = str(
        result.get("status", "")
    ).upper().strip()

    if coordinator_status in VALID_COORDINATOR_STATUSES:
        try:
            update_parcel_status(
                parcel_id,
                coordinator_status,
            )
        except Exception as exc:
            st.warning(
                "The Coordinator responded, but updating the parcel "
                f"status in SQLite failed: {exc}"
            )

    _show_allocation_result(
        parcel_id=parcel_id,
        parcel=parcel,
        response=response,
    )
