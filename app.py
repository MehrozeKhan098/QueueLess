import streamlit as st

from queue_logic import QueueManager
from ai import get_prediction, get_queue_status


st.set_page_config(
    page_title="QueueLess",
    page_icon="🏥",
    layout="wide"
)


st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


queue_manager = QueueManager()


# ========================================================
# HEADER
# ========================================================

st.title("🏥 QueueLess")

st.caption(
    "Smart Hospital Queue Management System"
)


# ========================================================
# SIDEBAR
# ========================================================

st.sidebar.title("QueueLess")


page = st.sidebar.radio(
    "Menu",
    [
        "🎫 Get Digital Token",
        "🔎 Check Token",
        "🚪 Leave Queue",
        "👨‍⚕️ Staff Dashboard"
    ]
)


# ========================================================
# GET DIGITAL TOKEN
# ========================================================

if page == "🎫 Get Digital Token":

    st.header("Get Digital Token")

    st.write(
        "Enter patient details and select the required service."
    )

    try:

        services = (
            queue_manager
            .get_available_services()
        )

        if services.empty:

            st.warning(
                "No services available."
            )

            st.stop()

        service_names = (
            services["SERVICE_NAME"]
            .tolist()
        )

    except Exception as error:

        st.error(
            "Could not load services from Snowflake."
        )

        st.code(
            str(error)
        )

        st.stop()


    col1, col2 = st.columns(2)


    with col1:

        name = st.text_input(
            "Patient Name",
            placeholder="Enter patient name"
        )

        age = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=20
        )

        gender = st.selectbox(
            "Gender",
            [
                "Male",
                "Female",
                "Other"
            ]
        )


    with col2:

        phone = st.text_input(
            "Phone Number",
            placeholder="Enter phone number"
        )

        service = st.selectbox(
            "Select Service",
            service_names
        )


    st.write("")


    if st.button(
        "🎫 Generate Digital Token",
        type="primary",
        use_container_width=True
    ):

        if not name.strip():

            st.warning(
                "Please enter patient name."
            )

        elif not phone.strip():

            st.warning(
                "Please enter phone number."
            )

        else:

            try:

                with st.spinner(
                    "Creating your digital token..."
                ):

                    patient = (
                        queue_manager
                        .add_citizen(
                            name,
                            age,
                            gender,
                            phone,
                            service
                        )
                    )


                st.success(
                    "Token created successfully!"
                )


                token = patient[
                    "token"
                ]


                people_ahead = patient[
                    "people_ahead"
                ]


                prediction = get_prediction(
                    service,
                    people_ahead
                )


                waiting_time = prediction[
                    "estimated_waiting_time"
                ]


                status = get_queue_status(
                    people_ahead,
                    waiting_time
                )


                st.divider()


                st.subheader(
                    "🎫 Your Token"
                )


                token_col1, token_col2 = (
                    st.columns(2)
                )


                with token_col1:

                    st.metric(
                        "Token Number",
                        token
                    )


                with token_col2:

                    st.metric(
                        "Service",
                        service
                    )


                st.divider()


                st.subheader(
                    "⏱️ Queue Information"
                )


                q1, q2, q3 = (
                    st.columns(3)
                )


                with q1:

                    st.metric(
                        "People Ahead",
                        people_ahead
                    )


                with q2:

                    st.metric(
                        "Estimated Wait",
                        f"{waiting_time} min"
                    )


                with q3:

                    st.write(
                        "**Status**"
                    )

                    st.success(
                        status
                    )


                st.info(
                    f"Please remember your token: {token}"
                )


            except Exception as error:

                st.error(
                    "Could not generate token."
                )

                st.code(
                    str(error)
                )


# ========================================================
# CHECK TOKEN
# ========================================================

elif page == "🔎 Check Token":

    st.header(
        "Check Your Token"
    )

    st.write(
        "Enter your token number to check your queue status."
    )


    token = st.text_input(
        "Token Number",
        placeholder="Example: A-023"
    )


    if st.button(
        "🔎 Check Status",
        type="primary",
        use_container_width=True
    ):

        if not token.strip():

            st.warning(
                "Please enter your token number."
            )

        else:

            token = (
                token
                .strip()
                .upper()
            )


            try:

                result = (
                    queue_manager
                    .get_patient_from_snowflake(
                        token
                    )
                )


                if result.empty:

                    st.error(
                        "Token not found."
                    )

                else:

                    row = result.iloc[0]


                    patient_name = row[
                        "PATIENT_NAME"
                    ]


                    service_name = row[
                        "SERVICE_NAME"
                    ]


                    position = int(
                        row["QUEUE_POSITION"]
                    )


                    current_status = row[
                        "STATUS"
                    ]


                    people_ahead = max(
                        position - 1,
                        0
                    )


                    prediction = (
                        get_prediction(
                            service_name,
                            people_ahead
                        )
                    )


                    waiting_time = (
                        prediction[
                            "estimated_waiting_time"
                        ]
                    )


                    queue_status = (
                        get_queue_status(
                            people_ahead,
                            waiting_time
                        )
                    )


                    st.success(
                        f"Token {token} found!"
                    )


                    st.subheader(
                        f"Hello, {patient_name} 👋"
                    )


                    c1, c2, c3 = (
                        st.columns(3)
                    )


                    with c1:

                        st.metric(
                            "Token",
                            token
                        )


                    with c2:

                        st.metric(
                            "People Ahead",
                            people_ahead
                        )


                    with c3:

                        st.metric(
                            "Estimated Wait",
                            f"{waiting_time} min"
                        )


                    st.divider()


                    st.write(
                        "**Service:**",
                        service_name
                    )


                    st.write(
                        "**Queue Position:**",
                        position
                    )


                    st.write(
                        "**Current Status:**",
                        current_status
                    )


                    st.success(
                        queue_status
                    )


            except Exception as error:

                st.error(
                    "Unable to check this token."
                )

                st.code(
                    str(error)
                )


# ========================================================
# LEAVE QUEUE
# ========================================================

elif page == "🚪 Leave Queue":

    st.header(
        "Leave Queue"
    )

    st.write(
        "Enter your token if you want to leave the queue."
    )


    token = st.text_input(
        "Token Number",
        placeholder="Example: A-023"
    )


    if st.button(
        "🚪 Leave Queue",
        type="primary",
        use_container_width=True
    ):

        if not token.strip():

            st.warning(
                "Please enter your token."
            )

        else:

            token = (
                token
                .strip()
                .upper()
            )


            try:

                success = (
                    queue_manager
                    .cancel_token(
                        token
                    )
                )


                if success:

                    st.success(
                        f"Token {token} has been cancelled."
                    )

                    st.rerun()

                else:

                    st.warning(
                        "Token could not be cancelled. "
                        "It may not exist or may already be serving."
                    )


            except Exception as error:

                st.error(
                    "Could not cancel the token."
                )

                st.code(
                    str(error)
                )


# ========================================================
# STAFF DASHBOARD
# ========================================================

elif page == "👨‍⚕️ Staff Dashboard":

    st.header(
        "👨‍⚕️ Staff Dashboard"
    )

    st.write(
        "Monitor and manage the hospital queue."
    )


    # ====================================================
    # SERVE NEXT BUTTON
    # ====================================================

    if st.button(
        "▶️ Serve Next Patient",
        type="primary",
        use_container_width=True
    ):

        try:

            patient = (
                queue_manager
                .serve_next()
            )


            if patient is None:

                st.warning(
                    "No waiting patients in the queue."
                )

            else:

                st.success(
                    f"Now serving {patient['token']} — "
                    f"{patient['name']}"
                )

                st.rerun()


        except Exception as error:

            st.error(
                "Could not serve the next patient."
            )

            st.code(
                str(error)
            )


    st.divider()


    # ====================================================
    # LIVE QUEUE
    # ====================================================

    try:

        live_queue = (
            queue_manager
            .get_live_queue()
        )


        if live_queue.empty:

            st.info(
                "No patients currently in the queue."
            )


        else:

            total_patients = len(
                live_queue
            )


            waiting_patients = len(
                live_queue[
                    live_queue["STATUS"]
                    .str.upper()
                    == "WAITING"
                ]
            )


            serving_patients = len(
                live_queue[
                    live_queue["STATUS"]
                    .str.upper()
                    == "SERVING"
                ]
            )


            served_patients = len(
                live_queue[
                    live_queue["STATUS"]
                    .str.upper()
                    == "SERVED"
                ]
            )


            cancelled_patients = len(
                live_queue[
                    live_queue["STATUS"]
                    .str.upper()
                    == "CANCELLED"
                ]
            )


            c1, c2, c3, c4, c5 = (
                st.columns(5)
            )


            with c1:

                st.metric(
                    "Total Patients",
                    total_patients
                )


            with c2:

                st.metric(
                    "Waiting",
                    waiting_patients
                )


            with c3:

                st.metric(
                    "Serving",
                    serving_patients
                )


            with c4:

                st.metric(
                    "Served",
                    served_patients
                )


            with c5:

                st.metric(
                    "Cancelled",
                    cancelled_patients
                )


            st.divider()


            # ============================================
            # LIVE QUEUE TABLE
            # ============================================

            st.subheader(
                "📋 Live Queue"
            )


            display_columns = [

                "QUEUE_ID",

                "TOKEN_NUMBER",

                "PATIENT_NAME",

                "SERVICE_NAME",

                "QUEUE_POSITION",

                "STATUS",

                "ESTIMATED_WAIT_TIME",

                "DOCTOR_NAME"
            ]


            available_columns = [

                column

                for column in display_columns

                if column in live_queue.columns
            ]


            st.dataframe(

                live_queue[
                    available_columns
                ],

                use_container_width=True,

                hide_index=True
            )


            st.divider()


            # ============================================
            # FILTER
            # ============================================

            st.subheader(
                "🔍 Filter by Service"
            )


            service_list = sorted(

                live_queue[
                    "SERVICE_NAME"
                ]
                .dropna()
                .unique()
                .tolist()
            )


            selected_service = (
                st.selectbox(
                    "Service",
                    [
                        "All Services"
                    ] + service_list
                )
            )


            if (
                selected_service
                != "All Services"
            ):

                filtered_queue = (
                    live_queue[
                        live_queue[
                            "SERVICE_NAME"
                        ]
                        == selected_service
                    ]
                )


                st.dataframe(

                    filtered_queue[
                        available_columns
                    ],

                    use_container_width=True,

                    hide_index=True
                )


            st.divider()


            # ============================================
            # WAITING CHART
            # ============================================

            st.subheader(
                "📊 Waiting Patients by Service"
            )


            waiting_data = (
                live_queue[
                    live_queue["STATUS"]
                    .str.upper()
                    == "WAITING"
                ]
            )


            if not waiting_data.empty:

                service_counts = (

                    waiting_data
                    .groupby(
                        "SERVICE_NAME"
                    )
                    .size()
                )


                st.bar_chart(
                    service_counts
                )


            else:

                st.info(
                    "No patients are currently waiting."
                )


    except Exception as error:

        st.error(
            "Unable to load live queue from Snowflake."
        )

        st.code(
            str(error)
        )


# ========================================================
# FOOTER
# ========================================================

st.divider()


st.caption(
    "QueueLess • Smart Hospital Queue Management System"
)