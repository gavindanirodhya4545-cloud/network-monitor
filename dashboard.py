from flask import Flask, render_template
import csv
import os
import re


app = Flask(__name__)


# =========================================================
# FILE CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


CSV_FILE = os.path.join(
    BASE_DIR,
    "network_data.csv"
)


INCIDENT_FILE = os.path.join(
    BASE_DIR,
    "incident_log.csv"
)


# =========================================================
# READ CSV
# =========================================================

def read_csv_file(file_path):

    if not os.path.exists(file_path):
        return []


    with open(
        file_path,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        return list(reader)


# =========================================================
# CONVERT DURATION TO SECONDS
# =========================================================

def duration_to_seconds(
    duration_text
):

    if not duration_text:
        return 0


    hours = 0
    minutes = 0
    seconds = 0


    hour_match = re.search(
        r"(\d+)\s*hr",
        duration_text
    )


    minute_match = re.search(
        r"(\d+)\s*min",
        duration_text
    )


    second_match = re.search(
        r"(\d+)\s*sec",
        duration_text
    )


    if hour_match:

        hours = int(
            hour_match.group(1)
        )


    if minute_match:

        minutes = int(
            minute_match.group(1)
        )


    if second_match:

        seconds = int(
            second_match.group(1)
        )


    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


# =========================================================
# FORMAT TOTAL DOWNTIME
# =========================================================

def format_duration(
    total_seconds
):

    hours = total_seconds // 3600


    minutes = (
        total_seconds % 3600
    ) // 60


    seconds = total_seconds % 60


    if hours > 0:

        return (
            f"{hours} hr "
            f"{minutes} min "
            f"{seconds} sec"
        )


    return (
        f"{minutes} min "
        f"{seconds} sec"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def dashboard():


    # =====================================================
    # NETWORK DATA
    # =====================================================

    rows = read_csv_file(
        CSV_FILE
    )


    latest_devices = {}


    for row in rows:

        latest_devices[
            row["Device"]
        ] = row


    # =====================================================
    # DEVICE SUMMARY
    # =====================================================

    normal_count = 0

    warning_count = 0

    critical_count = 0

    offline_count = 0


    latency_values = []


    for device, data in (
        latest_devices.items()
    ):

        status = data["Status"]


        if status == "NORMAL":

            normal_count += 1


        elif status == "WARNING":

            warning_count += 1


        elif status == "CRITICAL":

            critical_count += 1


        elif status == "OFFLINE":

            offline_count += 1


        latency = data.get(
            "Latency (ms)",
            ""
        )


        try:

            if latency not in [
                "",
                "N/A"
            ]:

                latency_values.append(
                    float(latency)
                )

        except ValueError:

            pass


    # =====================================================
    # AVERAGE LATENCY
    # =====================================================

    if latency_values:

        average_latency = round(
            sum(latency_values)
            / len(latency_values),
            2
        )

    else:

        average_latency = 0


    # =====================================================
    # CURRENT ALERTS
    # =====================================================

    current_alerts = []


    for device, data in (
        latest_devices.items()
    ):

        if data["Status"] != "NORMAL":

            current_alerts.append(
                data
            )


    # =====================================================
    # INCIDENT DATA
    # =====================================================

    incidents = read_csv_file(
        INCIDENT_FILE
    )


    total_incidents = len(
        incidents
    )


    active_incidents = [
        incident
        for incident in incidents

        if (
            incident.get(
                "Status"
            ) == "ACTIVE"
        )
    ]


    recovered_incidents = [
        incident
        for incident in incidents

        if (
            incident.get(
                "Status"
            ) == "RECOVERED"
        )
    ]


    active_incident_count = len(
        active_incidents
    )


    recovered_incident_count = len(
        recovered_incidents
    )


    # =====================================================
    # TOTAL DOWNTIME
    # =====================================================

    total_downtime_seconds = 0


    for incident in recovered_incidents:

        total_downtime_seconds += (
            duration_to_seconds(
                incident.get(
                    "Duration",
                    ""
                )
            )
        )


    total_downtime = (
        format_duration(
            total_downtime_seconds
        )
    )


    # =====================================================
    # INCIDENT HISTORY
    # newest first
    # =====================================================

    incident_history = list(
        reversed(incidents[-20:])
    )


    # =====================================================
    # LATENCY GRAPH
    # =====================================================

    network_devices = {}


    for row in rows:

        device = row["Device"]


        if device == "Local PC":
            continue


        latency = row.get(
            "Latency (ms)",
            ""
        )


        try:

            latency = float(
                latency
            )

        except (
            ValueError,
            TypeError
        ):

            continue


        if device not in network_devices:

            network_devices[
                device
            ] = []


        network_devices[
            device
        ].append(
            latency
        )


    # Keep last 20 samples
    for device in network_devices:

        network_devices[
            device
        ] = (
            network_devices[
                device
            ][-20:]
        )


    max_samples = 0


    for values in (
        network_devices.values()
    ):

        if len(values) > max_samples:

            max_samples = len(values)


    chart_labels = [
        f"Sample {i + 1}"
        for i in range(
            max_samples
        )
    ]


    chart_datasets = []


    for device, values in (
        network_devices.items()
    ):

        padding = (
            max_samples
            - len(values)
        )


        padded_values = (
            [None] * padding
            + values
        )


        chart_datasets.append({
            "label": device,
            "data": padded_values
        })


    # =====================================================
    # SEND TO HTML
    # =====================================================

    return render_template(

        "dashboard.html",

        devices=latest_devices,

        normal_count=normal_count,

        warning_count=warning_count,

        critical_count=critical_count,

        offline_count=offline_count,

        average_latency=average_latency,

        current_alerts=current_alerts,

        total_incidents=total_incidents,

        active_incident_count=(
            active_incident_count
        ),

        recovered_incident_count=(
            recovered_incident_count
        ),

        total_downtime=total_downtime,

        incident_history=incident_history,

        chart_labels=chart_labels,

        chart_datasets=chart_datasets
    )


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )