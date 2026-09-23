# QueueLess - Backend & Queue Logic
# Member 2

from data import (
    get_queue,
    get_patient_queue,
    get_service_queue as get_snowflake_service_queue,
    get_services,
    add_patient_to_snowflake,
    get_latest_patient_id,
    get_service_id,
    add_queue_entry,
    cancel_queue_token
)


class QueueManager:

    def __init__(self):
        self.queue = []
        self.next_token_number = 1
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

        token = f"{service_code}-{self.next_token_number:03d}"

        self.next_token_number += 1

        return token

    # ========================================================
    # ADD CITIZEN / PATIENT
    # ========================================================

    def add_citizen(
        self,
        name,
        age,
        gender,
        phone,
        service
    ):

        # ----------------------------------------------------
        # 1. Find service ID and service code
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 2. Save patient in Snowflake
        # ----------------------------------------------------

        add_patient_to_snowflake(
            name,
            age,
            gender,
            phone
        )

        # ----------------------------------------------------
        # 3. Get newly created patient ID
        # ----------------------------------------------------

        patient_id = get_latest_patient_id()

        if patient_id is None:
            raise ValueError(
                "Could not find newly created patient."
            )

        # ----------------------------------------------------
        # 4. Generate token
        # ----------------------------------------------------

        token = self.generate_token(
            service_code
        )

        # ----------------------------------------------------
        # 5. Find current queue position
        # ----------------------------------------------------

        current_queue = get_snowflake_service_queue(
            service_id
        )

        queue_position = len(current_queue) + 1

        # ----------------------------------------------------
        # 6. Calculate people ahead
        # ----------------------------------------------------

        people_ahead = len(
            current_queue[
                current_queue["STATUS"].str.upper() == "WAITING"
            ]
        )

        # ----------------------------------------------------
        # 7. Get average service time
        # ----------------------------------------------------

        average_time = float(
            service_row.iloc[0]["AVG_SERVICE_TIME"]
        )

        estimated_wait_time = (
            people_ahead * average_time
        )

        # ----------------------------------------------------
        # 8. Select doctor
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # 9. Save queue entry in Snowflake
        # ----------------------------------------------------

        add_queue_entry(
            patient_id,
            service_id,
            token,
            queue_position,
            "Waiting",
            estimated_wait_time,
            doctor_name
        )

        # ----------------------------------------------------
        # 10. Return patient information
        # ----------------------------------------------------

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

        self.queue.append(
            citizen
        )

        return citizen

    # ========================================================
    # LOCAL QUEUE
    # ========================================================

    def get_queue(self):
        return self.queue

    # ========================================================
    # FIND CITIZEN
    # ========================================================

    def find_citizen(self, token):

        for citizen in self.queue:

            if citizen["token"] == token:

                return citizen

        return None

    # ========================================================
    # TOKEN STATUS
    # ========================================================

    def get_status(self, token):

        citizen = self.find_citizen(token)

        if citizen is None:

            return "TOKEN NOT FOUND"

        return citizen["status"]

    # ========================================================
    # PEOPLE AHEAD
    # ========================================================

    def people_ahead(self, token):

        count = 0

        for citizen in self.queue:

            if citizen["token"] == token:

                return count

            if citizen["status"] == "Waiting":

                count += 1

        return -1

    # ========================================================
    # ESTIMATED WAIT
    # ========================================================

    def estimated_wait_time(
        self,
        token,
        average_service_time
    ):

        people = self.people_ahead(
            token
        )

        if people == -1:

            return -1

        return people * average_service_time

    # ========================================================
    # QUEUE POSITION
    # ========================================================

    def get_position(self, token):

        people = self.people_ahead(
            token
        )

        if people == -1:

            return -1

        return people + 1

    # ========================================================
    # SERVE NEXT
    # ========================================================

    def serve_next(self):

        if self.current_serving is not None:

            self.current_serving["status"] = "SERVED"

        for citizen in self.queue:

            if citizen["status"] == "Waiting":

                citizen["status"] = "SERVING"

                self.current_serving = citizen

                return citizen

        self.current_serving = None

        return None

    # ========================================================
    # CURRENTLY SERVING
    # ========================================================

    def get_current_serving(self):

        return self.current_serving

    # ========================================================
    # CANCEL QUEUE
    # ========================================================

    def cancel_token(self, token):

        token = token.strip().upper()

        success = cancel_queue_token(token)

        if success:

            citizen = self.find_citizen(token)

            if citizen is not None:
                citizen["status"] = "CANCELLED"

            return True

        return False

    # ========================================================
    # LOCAL SERVICE QUEUE
    # ========================================================

    def get_service_queue(self, service):

        service_queue = []

        for citizen in self.queue:

            if (
                citizen["service"] == service
                and citizen["status"] == "Waiting"
            ):

                service_queue.append(
                    citizen
                )

        return service_queue