
import streamlit as st


def apply_theme():
    """Apply the shared DeliveryMAS theme."""

    st.markdown(
        """
        <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
        );

        :root {
            --navy: #102440;
            --blue: #245CF5;
            --blue-hover: #1748D8;
            --background: #F5F8FD;
            --surface: #FFFFFF;
            --text: #172744;
            --muted: #64748B;
            --border: #E2EAF5;
        }

        /* ================= GLOBAL ================= */

        html,
        body,
        [class*="css"] {
            font-family: "Inter", sans-serif;
        }

        .stApp {
            background: var(--background);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: rgba(245, 248, 253, 0.96);
        }

        #MainMenu,
        footer,
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        [data-testid="stMain"] .block-container {
            max-width: 1400px;
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text);
        }

        [data-testid="stMain"] h1 {
            font-size: 30px;
            font-weight: 800;
        }

        [data-testid="stMain"] h2 {
            font-size: 24px;
            font-weight: 700;
        }

        [data-testid="stMain"] h3 {
            font-size: 20px;
            font-weight: 700;
        }

        /* ================= SIDEBAR ================= */

        [data-testid="stSidebar"] {
            background: linear-gradient(
                180deg, #0E1D35 0%, #172D4B 100%
            );
            border-right: 1px solid #263A59;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.2rem;
        }

        [data-testid="stSidebar"] hr {
            border-color: #344563;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #B8C5DA;
        }

        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: #8FA3C0 !important;
            font-size: 11px;
        }

        [data-testid="stSidebar"] div.stButton > button {
            background: transparent !important;
            color: #D7E0F0 !important;
            border: 1px solid transparent !important;
            border-radius: 9px;
            text-align: left;
            justify-content: flex-start;
            min-height: 42px;
            padding: 8px 12px;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] div.stButton > button p,
        [data-testid="stSidebar"] div.stButton > button span {
            color: #D7E0F0 !important;
        }

        [data-testid="stSidebar"] div.stButton > button:hover {
            background: rgba(255, 255, 255, 0.09) !important;
            color: #FFFFFF !important;
        }

        [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
            background: var(--blue) !important;
            color: #FFFFFF !important;
            border-color: var(--blue) !important;
        }

        [data-testid="stSidebar"] div.stButton > button[kind="primary"] p,
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] span {
            color: #FFFFFF !important;
        }

        /* ================= MAIN BUTTONS ================= */

        [data-testid="stMain"] div.stButton > button,
        [data-testid="stMain"] div[data-testid="stFormSubmitButton"] button {
            background: var(--blue) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--blue) !important;
            border-radius: 9px;
            font-weight: 600;
            min-height: 40px;
        }

        [data-testid="stMain"] div.stButton > button p,
        [data-testid="stMain"] div[data-testid="stFormSubmitButton"] button p {
            color: #FFFFFF !important;
        }

        [data-testid="stMain"] div.stButton > button:hover,
        [data-testid="stMain"] div[data-testid="stFormSubmitButton"] button:hover {
            background: var(--blue-hover) !important;
            border-color: var(--blue-hover) !important;
        }

        /* ================= HOME ARROW BUTTONS ================= */

        [data-testid="stMain"] [class*="st-key-home_"] button {
            background: #EFF5FF !important;
            background-color: #EFF5FF !important;
            color: #245CF5 !important;
            border: 1px solid #DCE8FF !important;
            border-radius: 10px !important;
            min-height: 42px !important;
            height: 42px !important;
            min-width: 42px !important;
            width: 42px !important;
            padding: 0 !important;
            box-shadow: none !important;
        }

        [data-testid="stMain"] [class*="st-key-home_"] button p,
        [data-testid="stMain"] [class*="st-key-home_"] button span {
            color: #245CF5 !important;
            -webkit-text-fill-color: #245CF5 !important;
        }

        [data-testid="stMain"] [class*="st-key-home_"] button:hover {
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

        /* ================= PAGE HEADINGS ================= */

        .page-title {
            color: var(--text);
            font-size: 30px;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 4px;
        }

        .page-subtitle {
            color: var(--muted);
            font-size: 14px;
            margin-bottom: 16px;
        }

        .section-title {
            color: var(--text);
            font-size: 18px;
            font-weight: 700;
            margin: 8px 0 12px;
        }

        /* ================= HOME PAGE ================= */

        .home-hero {
            background: linear-gradient(
                110deg, #F0F6FF 0%, #FFFFFF 85%
            );
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 28px;
        }

        .home-eyebrow {
            color: var(--blue);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }

        .home-title {
            color: var(--navy);
            font-size: clamp(30px, 3vw, 42px);
            font-weight: 800;
            line-height: 1.18;
        }

        .home-description {
            color: #536782;
            font-size: 15px;
            line-height: 1.7;
        }

        .home-section-title {
            color: var(--navy);
            font-size: 20px;
            font-weight: 700;
        }

        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF;
            border: 1px solid #E5ECF6;
            border-radius: 16px;
            box-shadow: 0 3px 12px rgba(16, 36, 64, 0.025);
        }

        /* ================= KPI CARDS ================= */

        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 16px 18px;
            box-shadow: 0 4px 16px rgba(22, 34, 66, 0.035);
        }

        [data-testid="stMetricLabel"] p {
            color: var(--muted) !important;
            font-size: 12px !important;
            font-weight: 600 !important;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: var(--text) !important;
            font-weight: 800;
        }

        /* ================= FORM LABELS ================= */

        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] span {
            color: #334155 !important;
            font-weight: 600 !important;
        }

        [data-testid="stCaptionContainer"] p {
            color: var(--muted) !important;
        }

        /* ================= TEXT INPUTS ================= */

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea,
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            color: #18243B !important;
            -webkit-text-fill-color: #18243B !important;
            caret-color: var(--blue) !important;
            opacity: 1 !important;
        }

        [data-testid="stTextInput"] [data-baseweb="input"],
        [data-testid="stNumberInput"] [data-baseweb="input"],
        [data-testid="stTextInput"] [data-baseweb="base-input"],
        [data-testid="stNumberInput"] [data-baseweb="base-input"],
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"],
        div[data-baseweb="textarea"] {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 9px !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: #64748B !important;
            -webkit-text-fill-color: #64748B !important;
            opacity: 1 !important;
        }

        [data-testid="stNumberInput"] button {
            background: #F1F5F9 !important;
            color: #334155 !important;
            border-color: #CBD5E1 !important;
        }

        /* ================= SELECT BOXES ================= */

        /*
        Explicitly style the selected control and its immediate
        inner containers. These rules do not alter the sidebar.
        */

        [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"],
        [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            color: #18243B !important;
        }

        [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 9px !important;
            box-shadow: none !important;
            color: #18243B !important;
        }

        [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
        [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div > div {
            background: transparent !important;
            background-color: transparent !important;
            color: #18243B !important;
        }

        [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] *,
        [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] * {
            color: #18243B !important;
            -webkit-text-fill-color: #18243B !important;
        }

        [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] svg,
        [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] svg {
            color: #475569 !important;
            fill: #475569 !important;
        }

        /* Dropdown popup and menu */
        [data-baseweb="popover"],
        [data-baseweb="popover"] > div,
        [data-baseweb="menu"],
        [role="listbox"] {
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            color: #18243B !important;
        }

        [role="option"],
        [role="option"] * {
            background-color: #FFFFFF !important;
            color: #18243B !important;
            -webkit-text-fill-color: #18243B !important;
        }

        [role="option"]:hover,
        [role="option"]:hover * {
            background-color: #EFF4FF !important;
            color: #18243B !important;
            -webkit-text-fill-color: #18243B !important;
        }

        /* ================= RADIO AND CHECKBOX ================= */

        [data-testid="stRadio"] label,
        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label p,
        [data-testid="stCheckbox"] label p {
            color: #334155 !important;
        }

        /* ================= FORMS AND TABLES ================= */

        div[data-testid="stForm"] {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 18px rgba(22, 34, 66, 0.035);
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }

        /* ================= ALERTS ================= */

        [data-testid="stAlert"] {
            border-radius: 10px;
        }

        [data-testid="stAlert"][kind="warning"] {
            background: #FFF7DB !important;
            border: 1px solid #F0D98A !important;
        }

        [data-testid="stAlert"][kind="info"] {
            background: #E8F2FF !important;
            border: 1px solid #B8D5FF !important;
        }

        /* ================= PROGRESS BARS ================= */

        [data-testid="stProgressBar"] > div > div {
            background: var(--blue);
        }

        /* ================= RESPONSIVE ================= */

        @media (max-width: 768px) {
            [data-testid="stMain"] .block-container {
                padding-top: 1rem;
                padding-bottom: 0.75rem;
            }

            .page-title {
                font-size: 25px;
            }

            .home-hero {
                padding: 20px;
            }

            .home-title {
                font-size: 30px;
            }

            div[data-testid="stForm"] {
                padding: 14px;
            }

            [data-testid="stMetric"] {
                padding: 12px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
