from ai import get_prediction


result = get_prediction(
    "Birth Certificate",
    3
)

print("AI Prediction")
print("----------------")

print("Service:", result["service"])
print("People Ahead:", result["people_ahead"])
print(
    "Predicted Service Time:",
    result["predicted_service_time"],
    "minutes"
)

print(
    "Estimated Waiting Time:",
    result["estimated_waiting_time"],
    "minutes"
)