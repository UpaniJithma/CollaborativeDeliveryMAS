
import streamlit as st

from dashboard.styles import apply_theme
from dashboard.data_service import initialize_data_service

from dashboard.pages.dashboard_page import render_dashboard
from dashboard.pages.register_page import render_register_page
from dashboard.pages.tracking_page import render_tracking_page
from dashboard.pages.courier_page import render_courier_page
from dashboard.pages.allocation_page import render_allocation_page

# Existing backend explanation page


# New parcel and courier records page
from dashboard.pages.parcel_allocation_records_page import (
    render_parcel_allocation_records_page,
)

# Experiment pages are temporarily disabled.
# from dashboard.pages.simulation_page import render_simulation_page
# from dashboard.pages.experiment_setup_page import render_experiment_setup


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="DeliveryMAS",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)


# ==================================================
# AUTHENTICATION
# ==================================================

# Keep your existing authentication logic here if configured.
# Do not remove your existing authentication implementation.


# ==================================================
# APPLY SHARED THEME
# ==================================================

apply_theme()

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        .stApp {
            background: #F5F8FD;
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0 18px 0;
        }

        .sidebar-brand-icon {
            background: #245CF5;
            color: white;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 23px;
        }

        .sidebar-brand-name {
            color: #FFFFFF;
            font-size: 23px;
            font-weight: 800;
            letter-spacing: -0.6px;
        }

        .sidebar-brand-caption {
            color: #A8B8D0;
            font-size: 10px;
            letter-spacing: 1px;
        }

        .sidebar-section {
            color: #8FA3C0;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1.2px;
            padding: 12px 0 5px 3px;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }

        [data-testid="stSidebar"] div.stButton > button {
            min-height: 42px;
            border-radius: 9px;
            justify-content: flex-start;
            text-align: left;
            padding-left: 13px;
            font-weight: 500;
        }

        [data-testid="stMain"] .block-container {
            padding-top: 1.6rem;
            padding-bottom: 1.5rem;
        }

        div[role="radiogroup"] {
            gap: 0.35rem;
        }

        div[role="radiogroup"] label {
            padding: 0.35rem 0.5rem;
            border-radius: 8px;
        }

        div[role="radiogroup"] label:hover {
            background: #F0F4FF;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# INITIALIZE DATABASE
# ==================================================

try:
    initialize_data_service()
except Exception as exc:
    st.error(f"Database initialization failed: {exc}")
    st.stop()


# ==================================================
# NAVIGATION CONFIGURATION
# ==================================================

NAVIGATION = [
    {
        "section": "WORKSPACE",
        "pages": [
            ("Home", "🏠", "Dashboard"),
            ("Register Parcel", "📦", "Parcel Requests"),
            # ("Parcel Tracking", "🔎", "Parcel Tracking"),
            ("Courier Management", "🚚", "Courier Management"),
            # ("Allocation History", "📋", "Allocation History"),

            # New page: parcel and courier allocation records
            (
                "Parcel & Courier Records",
                "📦",
                "Parcel & Courier Records",
            ),

            # Existing backend explanation page
            # (
            #     "Allocation Decision & Backend",
            #     "🧠",
            #     "Backend Process",
            # ),
        ],
    },

    # Experiment pages remain temporarily disabled.
    # {
    #     "section": "MULTI-AGENT SYSTEM",
    #     "pages": [
    #         ("Experiment Setup", "🧪", "Experiment Setup"),
    #         ("Live Agent Monitoring", "🤖", "Live Agent Monitoring"),
    #         ("Experiment Results", "📈", "Experiment Results"),
    #     ],
    # },
]


# ==================================================
# VALIDATE NAVIGATION
# ==================================================

ALL_PAGES = [
    page_key
    for section in NAVIGATION
    for _, _, page_key in section["pages"]
]

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Dashboard"

if st.session_state["active_page"] not in ALL_PAGES:
    st.session_state["active_page"] = "Dashboard"


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">📦</div>
            <div>
                <div class="sidebar-brand-name">DeliveryMAS</div>
                <div class="sidebar-brand-caption">
                    DELIVERY PLATFORM
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    for section in NAVIGATION:

        st.markdown(
            f'<div class="sidebar-section">'
            f'{section["section"]}</div>',
            unsafe_allow_html=True,
        )

        for label, icon, page_key in section["pages"]:

            is_active = (
                st.session_state["active_page"] == page_key
            )

            if st.button(
                f"{icon}   {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                if st.session_state["active_page"] != page_key:
                    st.session_state["active_page"] = page_key
                    st.rerun()

    st.markdown("---")
    st.caption("SYSTEM ARCHITECTURE")
    st.caption("SPADE · XMPP · SQLite")


# ==================================================
# PAGE ROUTING
# ==================================================

active_page = st.session_state["active_page"]

if active_page == "Dashboard":
    render_dashboard()

elif active_page == "Parcel Requests":
    render_register_page()

elif active_page == "Parcel Tracking":
    render_tracking_page()

elif active_page == "Courier Management":
    render_courier_page()

elif active_page == "Allocation History":
    # Keep the existing allocation-history behaviour.
    render_tracking_page()

elif active_page == "Parcel & Courier Records":
    # Display parcel details and courier allocation records
    # using the separate page module.
    render_parcel_allocation_records_page()

elif active_page == "Backend Process":
    render_backend_process_page()

# Experiment pages remain temporarily disabled.
# elif active_page == "Experiment Setup":
#     render_experiment_setup()
#
# elif active_page == "Live Agent Monitoring":
#     render_simulation_page()
#
# elif active_page == "Experiment Results":
#     render_allocation_page()

else:
    st.error(f"Unknown page selected: {active_page}")
