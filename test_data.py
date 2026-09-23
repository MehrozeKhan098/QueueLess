from queue_logic import QueueManager


queue = QueueManager()

print("========== LIVE QUEUE ==========")

live_queue = queue.get_live_queue()

print(live_queue)

print("\nTotal records:", len(live_queue))


print("\n========== SERVICES ==========")

services = queue.get_available_services()

print(services)

print("\nTotal services:", len(services))


print("\n========== PATIENT TOKEN ==========")

patient = queue.get_patient_from_snowflake("A-023")

print(patient)