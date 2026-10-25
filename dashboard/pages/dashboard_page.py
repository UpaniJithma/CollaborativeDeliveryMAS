
import streamlit as st


def render_dashboard():
    """Render the DeliveryMAS home page."""

    # --------------------------------------------------
    # PAGE STYLING
    # --------------------------------------------------
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 1.5rem;
            max-width: 1400px;
        }

        .home-hero {
            background: linear-gradient(
                110deg, #F4F8FF 0%, #FFFFFF 75%
            );
            border: 1px solid #E7EEF9;
            border-radius: 22px;
            padding: 32px 34px;
            min-height: 220px;
            box-sizing: border-box;
        }

        .home-eyebrow {
            color: #4263EB;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }

        .home-title {
            color: #102440;
            font-size: clamp(30px, 3.5vw, 42px);
            font-weight: 750;
            line-height: 1.15;
            margin: 0 0 12px 0;
        }

        .home-description {
            color: #536782;
            font-size: 15px;
            line-height: 1.7;
            margin: 0;
            max-width: 540px;
        }

        .home-illustration {
            text-align: center;
            background: #EFF5FF;
            border: 1px solid #E7EEF9;
            border-radius: 22px;
            padding: 32px 14px;
            min-height: 220px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .home-illustration-icons {
            font-size: 58px;
            line-height: 1.5;
            margin-bottom: 10px;
        }

        .home-illustration-caption {
            color: #3158A8;
            font-weight: 650;
            font-size: 13px;
        }

        .home-section-title {
            color: #102440;
            font-size: 20px;
            font-weight: 750;
            margin: 8px 0 16px 0;
        }

        /* Navigation tile borders */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #E5ECF6;
            border-radius: 16px;
        }

        /* General button styling */
        div.stButton > button {
            min-height: 44px;
            border-radius: 10px;
            font-weight: 600;
            transition:
                background-color 0.2s ease,
                border-color 0.2s ease,
                color 0.2s ease;
        }

        /*
        Home arrow buttons:
        The widget keys in dashboard_page.py begin with "home_".
        Use the widget wrapper to override the global main-button CSS.
        */
        [data-testid="stMain"] [class*="st-key-home_"] button,
        [data-testid="stMain"] [class*="st-key-home_"] button[kind] {
            background: #EEF3FF !important;
            background-color: #EEF3FF !important;
            color: #245CF5 !important;
            border: 1px solid #DCE6FF !important;
            border-radius: 10px !important;
            width: 42px !important;
            min-width: 42px !important;
            max-width: 42px !important;
            height: 42px !important;
            min-height: 42px !important;
            padding: 0 !important;
            box-shadow: none !important;
        }

        [data-testid="stMain"] [class*="st-key-home_"] button p,
        [data-testid="stMain"] [class*="st-key-home_"] button span {
            color: #245CF5 !important;
            -webkit-text-fill-color: #245CF5 !important;
        }

        [data-testid="stMain"] [class*="st-key-home_"] button:hover,
        [data-testid="stMain"] [class*="st-key-home_"] button[kind]:hover {
            background: #245CF5 !important;
            background-color: #245CF5 !important;
            color: #FFFFFF !important;
            border-color: #245CF5 !important;
        }

        [data-testid="stMain"] [class*="st-key-home_"] button:hover p,
        [data-testid="stMain"] [class*="st-key-home_"] button:hover span {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }

        [data-testid="stMain"] [class*="st-key-home_"] button:focus {
            outline: none !important;
            box-shadow: 0 0 0 2px rgba(36, 92, 245, 0.18) !important;
        }

        @media (max-width: 768px) {
            .home-hero {
                padding: 24px 20px;
                min-height: auto;
            }

            .home-illustration {
                min-height: 160px;
                padding: 20px 12px;
            }

            .home-illustration-icons {
                font-size: 44px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # WELCOME SECTION
    # --------------------------------------------------
    hero_left, hero_right = st.columns(
        [1.6, 1],
        vertical_alignment="center",
    )

    with hero_left:
        st.markdown(
            """
            <div class="home-hero">
                <div class="home-eyebrow">
                    Collaborative Delivery Platform
                </div>
                <div class="home-title">
                    Welcome to<br>DeliveryMAS
                </div>
                <p class="home-description">
                    A collaborative multi-agent system for efficient
                    and reliable parcel delivery allocation.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with hero_right:
        st.markdown(
            """
            <div class="home-illustration">
                <div class="home-illustration-icons">
                    📦 🚚
                </div>
                <div class="home-illustration-caption">
                    Smart delivery. Collaborative agents.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------
    # NAVIGATION SECTION
    # --------------------------------------------------
    st.markdown(
        """
        <div class="home-section-title">
            What would you like to do?
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Format: title, description, icon, destination page
    tiles = [
        (
            "Register Parcel",
            "Submit a parcel and find a suitable courier.",
            "📦",
            "Parcel Requests",
        ),
        # (
        #     "Parcel Tracking",
        #     "Check parcel status and allocation details.",
        #     "🔎",
        #     "Parcel Tracking",
        # ),
        (
            "Courier Management",
            "Add, edit and manage courier agents.",
            "🚚",
            "Courier Management",
        ),
        (
         "Parcel & Courier Records",
          "Allocate parcels to suitable couriers.",
          "🎯",
            "Parcel & Courier Records",
        ),
        
        # (
        #     "Experiment Workspace",
        #     "Configure and run delivery experiments.",
        #     "🧪",
        #     "Experiment Setup",
        # ),
        # (
        #     "Live Agent Monitoring",
        #     "Inspect agent activity and messages.",
        #     "🤖",
        #     "Live Agent Monitoring",
        # ),
    ]

    # Two navigation tiles per row
    for row_start in range(0, len(tiles), 2):
        columns = st.columns(2, gap="large")

        for column, tile in zip(
            columns,
            tiles[row_start:row_start + 2],
        ):
            title, description, icon, destination = tile

            with column:
                with st.container(border=True):
                    icon_col, text_col, action_col = st.columns(
                        [0.8, 3.2, 0.5],
                        vertical_alignment="center",
                    )

                    # Tile icon
                    with icon_col:
                        st.markdown(
                            f"""
                            <div style="
                                background: #EAF1FF;
                                width: 54px;
                                height: 54px;
                                border-radius: 14px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 27px;
                            ">
                                {icon}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Tile title and description
                    with text_col:
                        st.markdown(f"**{title}**")
                        st.caption(description)

                    # Navigation button
                    with action_col:
                        if st.button(
                            "›",
                            key=f"home_{destination}_{title}",
                            help=f"Open {title}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            st.session_state["active_page"] = destination
                            st.rerun()
