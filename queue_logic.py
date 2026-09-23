# QueueLess - Backend & Queue Logic
# Member 2


class QueueManager:

    def __init__(self):
        self.queue = []
        self.next_token_number = 1
        self.current_serving = None

    # Generate a digital token
    def generate_token(self):
        token = f"A{self.next_token_number:03d}"
        self.next_token_number += 1
        return token

    # Add a citizen to the queue
    def add_citizen(self, name, service):
        token = self.generate_token()

        citizen = {
            "token": token,
            "name": name,
            "service": service,
            "status": "WAITING"
        }

        self.queue.append(citizen)

        return citizen

    # Get the complete queue
    def get_queue(self):
        return self.queue

    # Find a citizen using token
    def find_citizen(self, token):
        for citizen in self.queue:
            if citizen["token"] == token:
                return citizen

        return None

    # Get token status
    def get_status(self, token):
        citizen = self.find_citizen(token)

        if citizen is None:
            return "TOKEN NOT FOUND"

        return citizen["status"]

    # Calculate people ahead
    def people_ahead(self, token):
        count = 0

        for citizen in self.queue:

            if citizen["token"] == token:
                return count

            if citizen["status"] == "WAITING":
                count += 1

        return -1

    # Calculate estimated waiting time
    def estimated_wait_time(self, token, average_service_time):
        people = self.people_ahead(token)

        if people == -1:
            return -1

        return people * average_service_time

    # Get queue position
    def get_position(self, token):
        people = self.people_ahead(token)

        if people == -1:
            return -1

        return people + 1

    # Serve the next citizen
    def serve_next(self):

        # Finish the currently serving citizen
        if self.current_serving is not None:
            self.current_serving["status"] = "SERVED"

        # Find the next waiting citizen
        for citizen in self.queue:

            if citizen["status"] == "WAITING":

                citizen["status"] = "SERVING"
                self.current_serving = citizen

                return citizen

        self.current_serving = None

        return None

    # Get the citizen currently being served
    def get_current_serving(self):
        return self.current_serving

    # Cancel / leave the queue
    def cancel_token(self, token):
        citizen = self.find_citizen(token)

        if citizen is None:
            return False

        if citizen["status"] != "WAITING":
            return False

        citizen["status"] = "CANCELLED"

        return True

    # Get waiting citizens for a particular service
    def get_service_queue(self, service):
        service_queue = []

        for citizen in self.queue:

            if (
                citizen["service"] == service
                and citizen["status"] == "WAITING"
            ):
                service_queue.append(citizen)

        return service_queue