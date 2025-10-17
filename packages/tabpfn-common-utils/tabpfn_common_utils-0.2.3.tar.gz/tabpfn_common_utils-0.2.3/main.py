from tabpfn_common_utils.telemetry.core.service import ProductTelemetry
from tabpfn_common_utils.telemetry.core.events import PingEvent, FitEvent, PredictEvent
import os
from tabpfn_common_utils.telemetry.core.state import _state_path, get_property

def clear_state_file():
    """Delete the telemetry state file from disk."""
    state_file = _state_path()
    
    try:
        if os.path.exists(state_file):
            os.remove(state_file)
            print(f"Deleted state file: {state_file}")
        else:
            print(f"State file does not exist: {state_file}")
    except Exception as e:
        print(f"Error deleting state file: {e}")




if __name__ == "__main__":

    # Send out a few PingEvent and FitEvent telemetry events

    # Initialize the telemetry client
    telemetry = ProductTelemetry()

    # Send PingEvent(s)
    ping_event_daily = PingEvent(frequency="daily")
    telemetry.capture(ping_event_daily)

    ping_event_weekly = PingEvent(frequency="weekly")
    telemetry.capture(ping_event_weekly)

    # Send FitEvent(s)
    fit_event_classification = FitEvent(task="classification", num_rows=100)
    telemetry.capture(fit_event_classification)

    fit_event_regression = FitEvent(task="regression", num_rows=50)
    telemetry.capture(fit_event_regression)