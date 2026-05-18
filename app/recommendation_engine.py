# calculates recommendation scores
# ranks the hospitals
# chooses the best facilities

def calculate_score(
        facility,
        user_lat,
        user_lon,
):
    distance = haversine(
        user_lat,
        user_lon,
        facility["latitude"],
        facility["longitude"]
    )

    distance_score = max(0, 100 - distance)

    