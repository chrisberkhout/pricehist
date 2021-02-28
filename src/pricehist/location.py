"""Send greetings."""

def greet(tz):
    """Greet a location."""
    friendly_time = "now"
    location = tz.split("/")[-1].replace("_"," ")
    return f"Hello, {location}! The time is {friendly_time}."
