from statistics import mean

from service_data import SERVICE_TIMES


def predict_service_time(service):

    times = SERVICE_TIMES.get(service)

    if not times:
        return 5.0

    predicted_time = mean(times)

    return round(predicted_time, 1)


def predict_waiting_time(service, people_ahead):

    service_time = predict_service_time(service)

    waiting_time = people_ahead * service_time

    return round(waiting_time, 1)


def get_prediction(service, people_ahead):

    predicted_service_time = predict_service_time(
        service
    )

    estimated_waiting_time = predict_waiting_time(
        service,
        people_ahead
    )

    return {
        "service": service,
        "people_ahead": people_ahead,
        "predicted_service_time": predicted_service_time,
        "estimated_waiting_time": estimated_waiting_time
    }


def get_queue_status(people_ahead, waiting_time):

    if people_ahead == 0:
        return "🟢 Your turn"

    if waiting_time <= 15:
        return "🟢 Low waiting time"

    if waiting_time <= 30:
        return "🟡 Moderate waiting time"

    if waiting_time <= 60:
        return "🟠 High waiting time"

    return "🔴 Very busy"