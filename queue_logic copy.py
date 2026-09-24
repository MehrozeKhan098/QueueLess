# QueueLess - Backend & Queue Logic
# Member 2 - Backend / Queue Logic

from data import (
    get_queue,
    get_patient_queue,
    get_service_queue as get_snowflake_service_queue,
    get_services,
    add_patient_to_snowflake,
    get_latest_patient_id,
    add_queue_entry,
    cancel_queue_token,
    generate_unique_token,
    serve_queue_token
)


class QueueManager:

    def __init__(self):
        self.queue = []
        self.current_serving = None

    # ========================================================
    # SNOWFLAKE DATA
    # ========================================================

    def get_live_queue(self):
        return get_queue()

    def get_patient_from_snowflake(self, token):
        return get_patient_queue(token)

    def get_live_service_queue(self, service_id):
        return get_snowflake_service_queue(service_id)

    def get_available_services(self):
        return get_services()

    # ========================================================
    # TOKEN GENERATION
    # ========================================================

    def generate_token(self, service_code="A"):
        return generate_unique_token(service_code)

    # ========================================================
    # ADD PATIENT
    # ========================================================

    def add_citizen(
        self,
        name,
        age,
        gender,
        phone,
        service
    ):
        # Find selected service
        services = get_services()

        service_row = services[
            services["SERVICE_NAME"] == service
        ]

        if service_row.empty:
            raise ValueError(
                "Selected service was not found."
            )

        service_id = int(
            service_row.iloc[0]["SERVICE_ID"]
        )

        service_code = str(
            service_row.iloc[0]["SERVICE_CODE"]
        )

        average_time = float(
            service_row.iloc[0]["AVG_SERVICE_TIME"]
        )

        # Save patient in Snowflake
        add_patient_to_snowflake(
            name,
            age,
            gender,
            phone
        )

        # Get newly created patient ID
        patient_id = get_latest_patient_id()

        if patient_id is None:
            raise ValueError(
                "Could not find newly created patient."
            )

        # Generate unique token
        token = self.generate_token(
            service_code
        )

        # Get current active queue
        current_queue = get_snowflake_service_queue(
            service_id
        )

        if current_queue.empty:
            queue_position = 1
            people_ahead = 0
        else:
            active_queue = current_queue[
                current_queue["STATUS"]
                .fillna("")
                .str.upper()
                .isin(["WAITING", "SERVING"])
            ]

            queue_position = len(active_queue) + 1

            people_ahead = len(
                active_queue[
                    active_queue["STATUS"]
                    .fillna("")
                    .str.upper()
                    == "WAITING"
                ]
            )

        # Calculate estimated wait time
        estimated_wait_time = (
            people_ahead * average_time
        )

        # Select doctor
        doctor_map = {
            "A": "Dr. Ahmed",
            "B": "Dr. Khan",
            "C": "Dr. Ali",
            "D": "Dr. Fatima",
            "E": "Dr. Sara"
        }

        doctor_name = doctor_map.get(
            service_code,
            "Doctor"
        )

        # Save queue entry in Snowflake
        add_queue_entry(
            patient_id,
            service_id,
            token,
            queue_position,
            "Waiting",
            estimated_wait_time,
            doctor_name
        )

        # Create patient information
        citizen = {
            "patient_id": patient_id,
            "token": token,
            "name": name,
            "service": service,
            "status": "Waiting",
            "queue_position": queue_position,
            "people_ahead": people_ahead,
            "estimated_wait_time": estimated_wait_time,
            "doctor_name": doctor_name
        }

        # Local cache only
        self.queue.append(citizen)

        return citizen

    # ========================================================
    # LOCAL QUEUE
    # ========================================================

    def get_queue(self):
        return self.queue

    # ========================================================
    # FIND PATIENT
    # ========================================================

    def find_citizen(self, token):
        token = token.strip().upper()

        for citizen in self.queue:
            if citizen["token"].upper() == token:
                return citizen

        return None

    # ========================================================
    # TOKEN STATUS
    # ========================================================

    def get_status(self, token):
        patient = get_patient_queue(
            token.strip().upper()
        )

        if patient is None or patient.empty:
            return "TOKEN NOT FOUND"

        status = str(
            patient.iloc[0]["STATUS"]
        ).upper()

        return status

    # ========================================================
    # PEOPLE AHEAD
    # ========================================================

    def people_ahead(self, token):
        token = token.strip().upper()

        patient = get_patient_queue(token)

        if patient is None or patient.empty:
            return -1

        patient_row = patient.iloc[0]

        status = str(
            patient_row["STATUS"]
        ).upper()

        if status in ["SERVING", "SERVED", "CANCELLED"]:
            return 0

        service_id = int(
            patient_row["SERVICE_ID"]
        )

        queue_position = int(
            patient_row["QUEUE_POSITION"]
        )

        service_queue = get_snowflake_service_queue(
            service_id
        )

        if service_queue.empty:
            return 0

        waiting_patients = service_queue[
            service_queue["STATUS"]
            .fillna("")
            .str.upper()
            == "WAITING"
        ]

        waiting_patients = waiting_patients[
            waiting_patients["QUEUE_POSITION"]
            < queue_position
        ]

        return len(waiting_patients)

    # ========================================================
    # ESTIMATED WAIT TIME
    # ========================================================

    def estimated_wait_time(
        self,
        token,
        average_service_time
    ):
        people = self.people_ahead(token)

        if people == -1:
            return -1

        return people * average_service_time

    # ========================================================
    # QUEUE POSITION
    # ========================================================

    def get_position(self, token):
        token = token.strip().upper()

        patient = get_patient_queue(token)

        if patient is None or patient.empty:
            return -1

        status = str(
            patient.iloc[0]["STATUS"]
        ).upper()

        if status in ["SERVING", "SERVED", "CANCELLED"]:
            return 0

        people = self.people_ahead(token)

        if people == -1:
            return -1

        return people + 1

    # ========================================================
    # SERVE NEXT PATIENT
    # ========================================================

    def serve_next(self):
        live_queue = get_queue()

        if live_queue.empty:
            self.current_serving = None
            return None

        # Check if someone is already being served
        serving = live_queue[
            live_queue["STATUS"]
            .fillna("")
            .str.upper()
            == "SERVING"
        ]

        if not serving.empty:
            current_patient = serving.iloc[0]

            self.current_serving = {
                "token": current_patient["TOKEN_NUMBER"],
                "name": current_patient["PATIENT_NAME"],
                "status": "SERVING"
            }

            return None

        # Find waiting patients
        waiting = live_queue[
            live_queue["STATUS"]
            .fillna("")
            .str.upper()
            == "WAITING"
        ]

        if waiting.empty:
            self.current_serving = None
            return None

        # Sort by queue position
        waiting = waiting.sort_values(
            by="QUEUE_POSITION"
        )

        next_patient = waiting.iloc[0]

        token = str(
            next_patient["TOKEN_NUMBER"]
        ).strip().upper()

        # Update Snowflake
        success = serve_queue_token(token)

        if not success:
            return None

        self.current_serving = {
            "token": token,
            "name": next_patient["PATIENT_NAME"],
            "status": "SERVING"
        }

        return self.current_serving

    # ========================================================
    # CURRENTLY SERVING
    # ========================================================

    def get_current_serving(self):
        live_queue = get_queue()

        if live_queue.empty:
            self.current_serving = None
            return None

        serving = live_queue[
            live_queue["STATUS"]
            .fillna("")
            .str.upper()
            == "SERVING"
        ]

        if serving.empty:
            self.current_serving = None
            return None

        current_patient = serving.iloc[0]

        self.current_serving = {
            "token": current_patient["TOKEN_NUMBER"],
            "name": current_patient["PATIENT_NAME"],
            "status": "SERVING"
        }

        return self.current_serving

    # ========================================================
    # CANCEL QUEUE TOKEN
    # ========================================================

    def cancel_token(self, token):
        token = token.strip().upper()

        patient = get_patient_queue(token)

        if patient is None or patient.empty:
            return False

        status = str(
            patient.iloc[0]["STATUS"]
        ).upper()

        # Do not allow a served or currently serving
        # patient to be cancelled
        if status in ["SERVED", "SERVING"]:
            return False

        # Delete token from active Snowflake queue
        success = cancel_queue_token(token)

        if not success:
            return False

        # Remove token from local cache
        self.queue = [
            citizen
            for citizen in self.queue
            if citizen["token"].upper() != token
        ]

        return True

    # ========================================================
    # LOCAL SERVICE QUEUE
    # ========================================================

    def get_service_queue(self, service):
        service_queue = []

        for citizen in self.queue:
            if (
                citizen["service"] == service
                and citizen["status"].upper() == "WAITING"
            ):
                service_queue.append(citizen)

        return service_queue