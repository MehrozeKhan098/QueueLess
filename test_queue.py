from queue_logic import QueueManager


# Create QueueLess queue
queue = QueueManager()


# Add citizens
queue.add_citizen("Rahul", "Birth Certificate")
queue.add_citizen("Priya", "Registration")
queue.add_citizen("Aman", "Document Verification")


# Show queue
print("========== QUEUE ==========")

for citizen in queue.get_queue():
    print(citizen)


# Check token
print("\n========== TOKEN INFO ==========")

token = "A002"

print("Status:", queue.get_status(token))
print("Position:", queue.get_position(token))
print("People ahead:", queue.people_ahead(token))

print(
    "Estimated wait:",
    queue.estimated_wait_time(token, 5),
    "minutes"
)


# Serve next
print("\n========== SERVE NEXT ==========")

served = queue.serve_next()

print("Now serving:", served)


# Check current serving
print("\n========== CURRENT SERVING ==========")

print(queue.get_current_serving())