
import streamlit as st
import plotly.graph_objects as go

from dashboard.data_service import (
    fetch_parcels,
    fetch_couriers,
    fetch_allocations,
    get_courier_capacity,
)


def _field(record, *keys, default="—"):
    """Safely retrieve a value from a database record."""
    if not hasattr(record, "get"):
        return default

    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return value

    return default


def _normalise_status(record):
    """Return a record's status in uppercase."""
    return str(_field(record, "status", default="UNKNOWN")).upper()


def _build_network(couriers, allocations):
    """Build an interactive network of the MAS components."""

    fig = go.Figure()

    # Core system components.
    nodes = [
        {
            "id": "UI",
            "label": "Streamlit UI",
            "x": 0.07,
            "y": 0.59,
            "color": "#4263EB",
            "description": "User interface and parcel registration",
        },
        {
            "id": "XMPP",
            "label": "XMPP Server",
            "x": 0.36,
            "y": 0.88,
            "color": "#8B5CF6",
            "description": "Message transport between SPADE agents",
        },
        {
            "id": "COORD",
            "label": "Coordinator Agent",
            "x": 0.51,
            "y": 0.57,
            "color": "#7C3AED",
            "description": "Receives allocation requests and selects suitable couriers",
        },
        {
            "id": "DB",
            "label": "SQLite Database",
            "x": 0.93,
            "y": 0.59,
            "color": "#0F766E",
            "description": "Persistent parcel, courier, and allocation records",
        },
    ]

    # Add registered courier agents dynamically.
    courier_nodes = []
    display_couriers = couriers[:6]
    count = len(display_couriers)

    for index, courier in enumerate(display_couriers):
        courier_id = str(
            _field(
                courier,
                "courier_id",
                "id",
                "jid",
                default=f"Courier {index + 1}",
            )
        )

        if count == 1:
            x = 0.51
        else:
            x = 0.15 + index * (0.72 / (count - 1))

        courier_nodes.append(
            {
                "id": courier_id,
                "label": f"Courier Agent\n{courier_id}",
                "x": x,
                "y": 0.23,
                "color": "#16A34A",
                "description": "Courier agent and available delivery capacity",
            }
        )

    nodes.extend(courier_nodes)

    # Logical communication and database paths.
    edges = [
        ("UI", "XMPP", "Allocation request"),
        ("XMPP", "COORD", "Request to Coordinator"),
        ("COORD", "XMPP", "Allocation response"),
        ("XMPP", "UI", "Response to UI"),
        ("COORD", "DB", "Persist allocation"),
        ("DB", "UI", "Read parcel status"),
    ]

    for node in courier_nodes:
        edges.append(
            ("COORD", node["id"], "Courier allocation")
        )

    node_lookup = {node["id"]: node for node in nodes}
    annotations = []

    for source, target, label in edges:
        start = node_lookup.get(source)
        end = node_lookup.get(target)

        if not start or not end:
            continue

        dx = end["x"] - start["x"]
        dy = end["y"] - start["y"]
        length = max((dx * dx + dy * dy) ** 0.5, 0.001)

        # Shorten edges so arrowheads do not overlap node markers.
        offset = 0.065

        x_start = start["x"] + dx / length * offset
        y_start = start["y"] + dy / length * offset
        x_end = end["x"] - dx / length * offset
        y_end = end["y"] - dy / length * offset

        # Highlight coordinator-to-courier paths when an allocation
        # record exists for that courier.
        is_allocation = source == "COORD"

        has_record = any(
            str(
                _field(
                    allocation,
                    "courier_id",
                    "assigned_courier",
                    default="",
                )
            ) == target
            and _normalise_status(allocation) == "ALLOCATED"
            for allocation in allocations
        )

        line_color = (
            "#16A34A"
            if is_allocation and has_record
            else "#94A3B8"
        )

        fig.add_trace(
            go.Scatter(
                x=[x_start, x_end],
                y=[y_start, y_end],
                mode="lines",
                line=dict(
                    color=line_color,
                    width=2.5 if is_allocation and has_record else 1.8,
                ),
                hovertemplate=(
                    f"<b>{source} → {target}</b><br>"
                    f"{label}<extra></extra>"
                ),
                showlegend=False,
            )
        )

        annotations.append(
            {
                "x": x_end,
                "y": y_end,
                "ax": x_start,
                "ay": y_start,
                "xref": "x",
                "yref": "y",
                "axref": "x",
                "ayref": "y",
                "text": "",
                "showarrow": True,
                "arrowhead": 2,
                "arrowsize": 1.1,
                "arrowwidth": 2,
                "arrowcolor": line_color,
            }
        )

    # Draw component nodes above the communication paths.
    fig.add_trace(
        go.Scatter(
            x=[node["x"] for node in nodes],
            y=[node["y"] for node in nodes],
            mode="markers+text",
            text=[node["label"] for node in nodes],
            textposition="bottom center",
            textfont=dict(size=11, color="#18243B"),
            marker=dict(
                size=[
                    42 if node["id"] in {"UI", "COORD", "DB", "XMPP"}
                    else 32
                    for node in nodes
                ],
                color=[node["color"] for node in nodes],
                line=dict(color="#FFFFFF", width=2),
                symbol="circle",
            ),
            customdata=[
                [node["id"], node["description"]]
                for node in nodes
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    fig.update_layout(
        height=680,
        margin=dict(l=30, r=30, t=35, b=85),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        xaxis=dict(
            range=(-0.08, 1.08),
            visible=False,
            fixedrange=True,
        ),
        yaxis=dict(
            range=(0.02, 1.05),
            visible=False,
            fixedrange=True,
        ),
        annotations=annotations,
        hovermode="closest",
        showlegend=False,
    )

    return fig


def render_simulation_page():
    """Render the interactive agent network simulation page."""

    st.markdown(
        '<div class="page-title">Agent Network Simulation</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-subtitle">'
        "Explore agent communication paths, courier capacity, "
        "and parcel allocation activity."
        "</div>",
        unsafe_allow_html=True,
    )

    @st.fragment(run_every="3s")
    def live_simulation():
        try:
            parcels = fetch_parcels() or []
            couriers = fetch_couriers() or []
            allocations = fetch_allocations() or []

        except Exception as exc:
            st.error(f"Unable to load simulation data: {exc}")
            return

        # Summary metrics.
        statuses = [_normalise_status(parcel) for parcel in parcels]

        allocated_count = sum(
            status == "ALLOCATED" for status in statuses
        )

        pending_count = sum(
            status in {"PENDING", "REQUESTED", "REGISTERED"}
            for status in statuses
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total parcels", len(parcels))
        col2.metric("Allocated parcels", allocated_count)
        col3.metric("Pending parcels", pending_count)
        col4.metric("Courier agents", len(couriers))

        st.caption(
            "Data refreshes every 3 seconds. Green links indicate a "
            "courier associated with a successful allocation record. "
            "The diagram shows logical communication paths, not live "
            "XMPP packet capture."
        )

        # Network diagram.
        st.markdown("### System communication network")

        fig = _build_network(couriers, allocations)

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": True,
                "scrollZoom": False,
            },
        )

        st.caption(
            "Hover over a component or connection to inspect its role. "
            "Up to six courier agents are shown in the network diagram."
        )

        # Courier capacity.
        st.markdown("### Courier capacity")

        if not couriers:
            st.info("No courier records are currently available.")

        else:
            for courier in couriers:
                courier_id = _field(
                    courier,
                    "courier_id",
                    "id",
                    "jid",
                    default="Unknown",
                )

                try:
                    capacity = get_courier_capacity(courier) or {}
                except Exception:
                    capacity = {}

                total = float(capacity.get("capacity", 0) or 0)
                remaining = float(capacity.get("remaining", 0) or 0)
                used = float(capacity.get("used", 0) or 0)
                utilisation = float(
                    capacity.get("utilisation_percent", 0) or 0
                )

                with st.container(border=True):
                    left, right = st.columns([3, 1])

                    with left:
                        st.markdown(
                            f"**Courier Agent: {courier_id}**"
                        )

                        st.progress(
                            min(max(utilisation / 100, 0), 1),
                            text=(
                                "Capacity utilisation: "
                                f"{utilisation:.1f}%"
                            ),
                        )

                    with right:
                        st.metric(
                            "Remaining capacity",
                            f"{remaining:.1f} kg",
                        )

                    st.caption(
                        f"Used: {used:.1f} kg · "
                        f"Total: {total:.1f} kg"
                    )

        # Recent allocation records.
        st.markdown("### Recent allocation events")

        if not allocations:
            st.info("No allocation records are available yet.")

        else:
            rows = []

            for allocation in reversed(allocations[-10:]):
                rows.append(
                    {
                        "Allocation ID": _field(
                            allocation, "allocation_id", "id"
                        ),
                        "Parcel ID": _field(
                            allocation, "parcel_id"
                        ),
                        "Courier": _field(
                            allocation,
                            "courier_id",
                            "assigned_courier",
                        ),
                        "Status": _normalise_status(allocation),
                        "Timestamp": _field(
                            allocation,
                            "allocated_at",
                            "created_at",
                            "timestamp",
                        ),
                    }
                )

            st.dataframe(
                rows,
                hide_index=True,
                use_container_width=True,
            )

    live_simulation()
