import subprocess
import platform
import time
import csv
import os
import psutil
from datetime import datetime

try:
    from winotify import Notification
except ImportError:
    Notification = None


# =========================================================
# NETWORK TARGETS
# =========================================================

targets = {
    "Home Router": "192.168.1.1",
    "Google DNS": "8.8.8.8",
    "Cloudflare DNS": "1.1.1.1"
}


# =========================================================
# FILE CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_FILE = os.path.join(
    BASE_DIR,
    "network_data.csv"
)

INCIDENT_FILE = os.path.join(
    BASE_DIR,
    "incident_log.csv"
)


# =========================================================
# STATUS MEMORY
# =========================================================

previous_status = {}

active_incidents = {}


# =========================================================
# STATUS PRIORITY
# Used to keep the highest incident severity
# =========================================================

STATUS_PRIORITY = {
    "WARNING": 1,
    "CRITICAL": 2,
    "OFFLINE": 3
}


# =========================================================
# WINDOWS NOTIFICATIONS
# =========================================================

def send_notification(title, message):

    if Notification is None:

        print(
            "Notification skipped: "
            "winotify is not installed."
        )

        return

    try:

        toast = Notification(
            app_id="Network Monitor",
            title=title,
            msg=message,
            duration="short"
        )

        toast.show()

    except Exception as error:

        print(
            f"Notification error: {error}"
        )


# =========================================================
# CREATE NETWORK DATA FILE
# =========================================================

def create_csv_file():

    if not os.path.exists(CSV_FILE):

        with open(
            CSV_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Timestamp",
                "Device",
                "IP Address",
                "Status",
                "Latency (ms)",
                "CPU (%)",
                "RAM (%)"
            ])


# =========================================================
# CREATE INCIDENT FILE
# =========================================================

def create_incident_file():

    if not os.path.exists(INCIDENT_FILE):

        with open(
            INCIDENT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Device",
                "Incident Type",
                "Start Time",
                "Recovery Time",
                "Duration",
                "Status"
            ])


# =========================================================
# SAVE MONITORING DATA
# =========================================================

def save_data(
    timestamp,
    name,
    host,
    status,
    latency,
    cpu="",
    ram=""
):

    with open(
        CSV_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            timestamp,
            name,
            host,
            status,
            latency,
            cpu,
            ram
        ])


# =========================================================
# UPDATE ACTIVE INCIDENT CSV ROW
# =========================================================

def update_incident_row(
    name,
    start_time_text,
    updates
):

    if not os.path.exists(INCIDENT_FILE):
        return

    with open(
        INCIDENT_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        rows = list(reader)

        fieldnames = reader.fieldnames


    if not fieldnames:
        return


    updated = False


    # Search from newest incident backwards
    for row in reversed(rows):

        if (
            row["Device"] == name
            and row["Start Time"] == start_time_text
            and row["Status"] == "ACTIVE"
        ):

            for key, value in updates.items():

                row[key] = value

            updated = True

            break


    if updated:

        with open(
            INCIDENT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()

            writer.writerows(rows)


# =========================================================
# START INCIDENT
# =========================================================

def start_incident(
    name,
    status
):

    if name in active_incidents:
        return


    start_time = datetime.now()

    start_time_text = start_time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    active_incidents[name] = {
        "status": status,
        "start_time": start_time
    }


    # Save incident immediately as ACTIVE
    with open(
        INCIDENT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            name,
            status,
            start_time_text,
            "",
            "",
            "ACTIVE"
        ])


    print(
        f"INCIDENT STARTED | "
        f"{name} | "
        f"{status} | "
        f"{start_time_text}"
    )


# =========================================================
# UPDATE INCIDENT SEVERITY
# =========================================================

def update_incident_severity(
    name,
    new_status
):

    if name not in active_incidents:
        return


    current_status = (
        active_incidents[name]["status"]
    )


    current_priority = STATUS_PRIORITY.get(
        current_status,
        0
    )

    new_priority = STATUS_PRIORITY.get(
        new_status,
        0
    )


    # Only upgrade incident severity
    if new_priority > current_priority:

        active_incidents[name][
            "status"
        ] = new_status


        start_time_text = (
            active_incidents[name]
            ["start_time"]
            .strftime("%Y-%m-%d %H:%M:%S")
        )


        update_incident_row(
            name,
            start_time_text,
            {
                "Incident Type": new_status
            }
        )


# =========================================================
# CLOSE INCIDENT
# =========================================================

def close_incident(name):

    if name not in active_incidents:
        return


    incident = active_incidents[name]

    start_time = incident["start_time"]

    recovery_time = datetime.now()


    duration = (
        recovery_time - start_time
    )


    total_seconds = int(
        duration.total_seconds()
    )


    hours = total_seconds // 3600

    minutes = (
        total_seconds % 3600
    ) // 60

    seconds = total_seconds % 60


    if hours > 0:

        duration_text = (
            f"{hours} hr "
            f"{minutes} min "
            f"{seconds} sec"
        )

    else:

        duration_text = (
            f"{minutes} min "
            f"{seconds} sec"
        )


    start_time_text = start_time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    recovery_time_text = (
        recovery_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


    update_incident_row(
        name,
        start_time_text,
        {
            "Incident Type":
                incident["status"],

            "Recovery Time":
                recovery_time_text,

            "Duration":
                duration_text,

            "Status":
                "RECOVERED"
        }
    )


    print(
        f"INCIDENT RECOVERED | "
        f"{name} | "
        f"Duration: {duration_text}"
    )


    del active_incidents[name]


# =========================================================
# SMART STATUS CHANGE MANAGEMENT
# =========================================================

def handle_status_change(
    name,
    new_status,
    message
):

    old_status = previous_status.get(name)


    # No status change
    if old_status == new_status:
        return


    # =====================================================
    # PROBLEM STATUS
    # =====================================================

    if new_status in [
        "WARNING",
        "CRITICAL",
        "OFFLINE"
    ]:


        send_notification(
            f"{name} Alert",
            message
        )


        if name not in active_incidents:

            start_incident(
                name,
                new_status
            )

        else:

            update_incident_severity(
                name,
                new_status
            )


        print(
            f"ALERT | "
            f"{name} | "
            f"{old_status} -> {new_status}"
        )


    # =====================================================
    # RECOVERY
    # =====================================================

    elif (
        new_status == "NORMAL"
        and old_status in [
            "WARNING",
            "CRITICAL",
            "OFFLINE"
        ]
    ):


        send_notification(
            f"{name} Recovered",
            f"{name} has returned "
            f"to NORMAL status."
        )


        close_incident(name)


        print(
            f"RECOVERY | "
            f"{name} | "
            f"{old_status} -> NORMAL"
        )


    # Remember current status
    previous_status[name] = new_status


# =========================================================
# NETWORK MONITORING
# =========================================================

def check_connection(
    name,
    host
):


    # =====================================================
    # PING COMMAND
    # =====================================================

    if platform.system() == "Windows":

        command = [
            "ping",
            "-n",
            "1",
            "-w",
            "1000",
            host
        ]

    else:

        command = [
            "ping",
            "-c",
            "1",
            "-W",
            "1",
            host
        ]


    # =====================================================
    # LATENCY
    # =====================================================

    start_time = time.time()


    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


    end_time = time.time()


    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # =====================================================
    # DEVICE ONLINE
    # =====================================================

    if result.returncode == 0:


        latency = (
            end_time - start_time
        ) * 1000


        # NORMAL
        if latency < 100:

            status = "NORMAL"


            handle_status_change(
                name,
                status,
                f"{name} is operating normally."
            )


        # WARNING
        elif latency <= 200:

            status = "WARNING"


            handle_status_change(
                name,
                status,
                f"{name} latency is high: "
                f"{latency:.2f} ms"
            )


        # CRITICAL
        else:

            status = "CRITICAL"


            handle_status_change(
                name,
                status,
                f"{name} latency is critical: "
                f"{latency:.2f} ms"
            )


        print(
            f"{status} | "
            f"{name} | "
            f"{host} | "
            f"{latency:.2f} ms"
        )


        save_data(
            timestamp,
            name,
            host,
            status,
            round(latency, 2)
        )


    # =====================================================
    # DEVICE OFFLINE
    # =====================================================

    else:

        status = "OFFLINE"


        handle_status_change(
            name,
            status,
            f"{name} ({host}) is OFFLINE"
        )


        print(
            f"CRITICAL | "
            f"{name} | "
            f"{host} | "
            f"OFFLINE"
        )


        save_data(
            timestamp,
            name,
            host,
            status,
            "N/A"
        )


# =========================================================
# LOCAL PC MONITORING
# =========================================================

def check_local_system():


    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    cpu = psutil.cpu_percent(
        interval=1
    )


    ram = psutil.virtual_memory().percent


    # =====================================================
    # CRITICAL
    # =====================================================

    if cpu > 90 or ram > 90:

        status = "CRITICAL"


        handle_status_change(
            "Local PC",
            status,
            f"CPU: {cpu}% | "
            f"RAM: {ram}%"
        )


    # =====================================================
    # WARNING
    # =====================================================

    elif cpu > 75 or ram > 75:

        status = "WARNING"


        handle_status_change(
            "Local PC",
            status,
            f"CPU: {cpu}% | "
            f"RAM: {ram}%"
        )


    # =====================================================
    # NORMAL
    # =====================================================

    else:

        status = "NORMAL"


        handle_status_change(
            "Local PC",
            status,
            "Local PC is operating normally."
        )


    print(
        f"{status} | "
        f"Local PC | "
        f"CPU: {cpu}% | "
        f"RAM: {ram}%"
    )


    save_data(
        timestamp,
        "Local PC",
        "localhost",
        status,
        "",
        cpu,
        ram
    )


# =========================================================
# INITIALIZE FILES
# =========================================================

create_csv_file()

create_incident_file()


# =========================================================
# START MONITORING
# =========================================================

try:

    while True:


        print(
            "\n"
            "========== NETWORK MONITOR =========="
        )


        # Monitor network targets
        for name, host in targets.items():

            check_connection(
                name,
                host
            )


        # Monitor local PC
        check_local_system()


        print(
            "======================================"
        )


        time.sleep(5)


# =========================================================
# STOP PROGRAM
# =========================================================

except KeyboardInterrupt:

    print(
        "\n"
        "Network Monitoring stopped."
    )