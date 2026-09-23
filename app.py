```python
import streamlit as st

from queue_logic import QueueManager
from ai import get_prediction, get_queue_status


# Create QueueLess queue manager
if "queue_manager" not in st.session_state:
    st.session_state.queue_manager = QueueManager()

queue = st.session_state.queue_manager


# Page configuration
st.set_page_config(
    page_title="QueueLess",
    page_icon="🏛️",
    layout="wide"
)


# =========================================================
# HEADER
# =========================================================

st.title("🏛️ QueueLess")

st.subheader(
    "Smart Government Office Queue Management System"
)

st.write(
    "Get a digital token, track your position, "
    "and avoid unnecessary waiting."
)

st.divider()


# =========================================================
# GET DIGITAL TOKEN
# =========================================================

st.header("🎫 Get Digital Token")

name = st.text_input(
    "Enter your name",
    placeholder="Enter your name"
)

service = st.selectbox(
    "Select Government Service",
    [
        "Birth Certificate",
        "Income Certificate",
        "Caste Certificate",
        "Residence Certificate",
        "Document Registration"
    ]
)


if st.button("🎫 Get Token"):

    if name.strip() == "":
        st.warning("Please enter your name.")

    else:

        # Add citizen to queue
        citizen = queue.add_citizen(
            name.strip(),
            service
        )

        token = citizen["token"]

        # Calculate people ahead
        people_ahead = queue.people_ahead(
            token
        )

        # Get AI prediction
        prediction = get_prediction(
            service,
            people_ahead
        )

        waiting_time = prediction[
            "estimated_waiting_time"
        ]

        queue_status = get_queue_status(
            people_ahead,
            waiting_time
        )

        # Show token
        st.success(
            f"🎟️ Your Digital Token: {token}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "People Ahead",
                people_ahead
            )

        with col2:
            st.metric(
                "Service Time",
                f"{prediction['predicted_service_time']} min"
            )

        with col3:
            st.metric(
                "Estimated Wait",
                f"{waiting_time} min"
            )

        st.info(
            f"📊 Queue Status: {queue_status}"
        )


st.divider()


# =========================================================
# CHECK TOKEN
# =========================================================

st.header("🔎 Check Token")

token_input = st.text_input(
    "Enter your token",
    placeholder="Example: A001"
)


if st.button("🔎 Check Token"):

    token_input = token_input.strip().upper()

    if token_input == "":
        st.warning("Please enter your token.")

    else:

        citizen = queue.find_citizen(
            token_input
        )

        if citizen is None:

            st.error("❌ Token not found.")

        else:

            st.success("✅ Token found!")

            st.write(
                f"**Token:** {citizen['token']}"
            )

            st.write(
                f"**Name:** {citizen['name']}"
            )

            st.write(
                f"**Service:** {citizen['service']}"
            )

            st.write(
                f"**Status:** {citizen['status']}"
            )

            # Waiting citizen
            if citizen["status"] == "WAITING":

                people_ahead = queue.people_ahead(
                    token_input
                )

                prediction = get_prediction(
                    citizen["service"],
                    people_ahead
                )

                waiting_time = prediction[
                    "estimated_waiting_time"
                ]

                queue_status = get_queue_status(
                    people_ahead,
                    waiting_time
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Position",
                        queue.get_position(
                            token_input
                        )
                    )

                with col2:
                    st.metric(
                        "People Ahead",
                        people_ahead
                    )

                with col3:
                    st.metric(
                        "Estimated Wait",
                        f"{waiting_time} min"
                    )

                st.info(
                    f"📊 {queue_status}"
                )

            # Citizen currently being served
            elif citizen["status"] == "SERVING":

                st.success(
                    "🟢 It is your turn! "
                    "Please proceed to the counter."
                )

            # Citizen already served
            elif citizen["status"] == "SERVED":

                st.success(
                    "✅ Your service has been completed."
                )

            # Citizen cancelled
            elif citizen["status"] == "CANCELLED":

                st.warning(
                    "❌ This token has been cancelled."
                )


st.divider()


# =========================================================
# LEAVE QUEUE
# =========================================================

st.header("❌ Leave Queue")

cancel_token = st.text_input(
    "Enter token to leave the queue",
    placeholder="Example: A001"
)


if st.button("❌ Leave Queue"):

    cancel_token = cancel_token.strip().upper()

    if cancel_token == "":
        st.warning("Please enter your token.")

    else:

        result = queue.cancel_token(
            cancel_token
        )

        if result:

            st.success(
                "✅ You have successfully left the queue."
            )

        else:

            st.error(
                "Unable to leave the queue. "
                "Check your token or status."
            )


st.divider()


# =========================================================
# STAFF DASHBOARD
# =========================================================

st.header("👨‍💼 Staff Dashboard")

current = queue.get_current_serving()


if current:

    st.info(
        f"🟢 Currently Serving: "
        f"{current['token']} - {current['name']}"
    )

else:

    st.info(
        "Nobody is currently being served."
    )


if st.button("➡️ Serve Next Citizen"):

    served = queue.serve_next()

    if served:

        st.success(
            f"🟢 Now Serving: "
            f"{served['token']} - {served['name']}"
        )

        st.rerun()

    else:

        st.warning(
            "No citizens are currently waiting."
        )


st.divider()


# =========================================================
# CURRENT QUEUE
# =========================================================

st.header("📋 Current Queue")

all_citizens = queue.get_queue()


if len(all_citizens) == 0:

    st.info("Queue is currently empty.")

else:

    for citizen in all_citizens:

        if citizen["status"] == "WAITING":

            people_ahead = queue.people_ahead(
                citizen["token"]
            )

            prediction = get_prediction(
                citizen["service"],
                people_ahead
            )

            waiting_time = prediction[
                "estimated_waiting_time"
            ]

            st.write(
                f"🎫 {citizen['token']} | "
                f"{citizen['name']} | "
                f"{citizen['service']} | "
                f"🟡 WAITING | "
                f"People Ahead: {people_ahead} | "
                f"Wait: {waiting_time} min"
            )

        elif citizen["status"] == "SERVING":

            st.write(
                f"🎫 {citizen['token']} | "
                f"{citizen['name']} | "
                f"{citizen['service']} | "
                f"🟢 SERVING"
            )

        elif citizen["status"] == "SERVED":

            st.write(
                f"🎫 {citizen['token']} | "
                f"{citizen['name']} | "
                f"{citizen['service']} | "
                f"✅ SERVED"
            )

        elif citizen["status"] == "CANCELLED":

            st.write(
                f"🎫 {citizen['token']} | "
                f"{citizen['name']} | "
                f"{citizen['service']} | "
                f"❌ CANCELLED"
            )
```
