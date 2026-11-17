from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REQUIRED_COLUMNS = ["Name", "Subject", "Classes_Held", "Classes_Attended"]
DEFAULT_THRESHOLD = 75.0


def read_csv(file_path: str | Path | pd.DataFrame) -> pd.DataFrame:
    """Read the attendance CSV and validate its columns."""
    if isinstance(file_path, pd.DataFrame):
        data = file_path.copy()
    else:
        csv_path = Path(file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        data = pd.read_csv(csv_path)

    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(
            f"The file is missing required columns: {', '.join(missing)}"
        )
    return data


def calculate_student_percentages(records: pd.DataFrame) -> List[Tuple[str, float]]:
    """Return each student's overall attendance percentage in file order."""
    if records.empty:
        return []

    results: List[Tuple[str, float]] = []
    seen: set[str] = set()

    for _, row in records.iterrows():
        name = str(row["Name"]).strip()
        if name in seen:
            continue
        seen.add(name)

        student_rows = records[records["Name"] == name]
        total_held = int(student_rows["Classes_Held"].sum())
        total_attended = int(student_rows["Classes_Attended"].sum())
        percentage = (total_attended / total_held) * 100 if total_held else 0.0
        results.append((name, percentage))

    return results


def calculate_subject_averages(records: pd.DataFrame) -> List[Tuple[str, float]]:
    """Return subject-wise average attendance percentages."""
    if records.empty:
        return []

    subject_summary: Dict[str, Dict[str, int]] = {}

    for _, row in records.iterrows():
        subject = str(row["Subject"]).strip()
        held = int(row["Classes_Held"])
        attended = int(row["Classes_Attended"])

        if subject not in subject_summary:
            subject_summary[subject] = {"held": 0, "attended": 0}

        subject_summary[subject]["held"] += held
        subject_summary[subject]["attended"] += attended

    results: List[Tuple[str, float]] = []
    for subject, values in subject_summary.items():
        held = values["held"]
        attended = values["attended"]
        percentage = (attended / held) * 100 if held else 0.0
        results.append((subject, percentage))

    return results


def validate_and_clean(file_path: str | Path | pd.DataFrame) -> pd.DataFrame:
    """Read the CSV, skip invalid rows, and return clean data."""
    data = read_csv(file_path)
    cleaned_rows: List[dict] = []

    for row_number, row in enumerate(data.to_dict(orient="records"), start=1):
        try:
            name = str(row.get("Name", "")).strip()
            subject = str(row.get("Subject", "")).strip()
            held_raw = row.get("Classes_Held")
            attended_raw = row.get("Classes_Attended")

            if pd.isna(held_raw) or pd.isna(attended_raw):
                raise ValueError("missing value")

            held = int(held_raw)
            attended = int(attended_raw)

            if not name or not subject:
                raise ValueError("empty required data")
            if held < 0 or attended < 0:
                raise ValueError("negative attendance value")
            if attended > held:
                print(
                    f"Row {row_number} invalid: attended ({attended}) cannot exceed held ({held}). Row skipped."
                )
                continue

            cleaned_rows.append(
                {
                    "Name": name,
                    "Subject": subject,
                    "Classes_Held": held,
                    "Classes_Attended": attended,
                }
            )
        except ValueError:
            print(f"Row {row_number} invalid. Row skipped.")

    return pd.DataFrame(cleaned_rows, columns=REQUIRED_COLUMNS)


def display_student_percentages(records: pd.DataFrame) -> None:
    """Display student attendance percentages in a single summary line."""
    if records.empty:
        print("No valid attendance data available.")
        return

    student_data = calculate_student_percentages(records)
    summary = " | ".join(f"{name}: {percentage:.2f}%" for name, percentage in student_data)
    print(summary)

    save_chart(student_data, title="Student Attendance Percentages", chart_type="bar")


def display_shortage_list(records: pd.DataFrame, threshold: float = DEFAULT_THRESHOLD) -> None:
    """Show students below the minimum attendance requirement."""
    if records.empty:
        print("No valid attendance data available.")
        return

    student_data = calculate_student_percentages(records)
    below_threshold = [(name, percentage) for name, percentage in student_data if percentage < threshold]
    eligible = [(name, percentage) for name, percentage in student_data if percentage >= threshold]

    if not below_threshold:
        if len(eligible) == 1:
            name, percentage = eligible[0]
            print(f"No student below {threshold:.0f}%. {name} ({percentage:.2f}%) is eligible.")
        else:
            names = " | ".join(f"{name} ({percentage:.2f}%)" for name, percentage in eligible)
            print(f"No student below {threshold:.0f}%. {names} are eligible.")
    else:
        names = " | ".join(f"{name} ({percentage:.2f}%)" for name, percentage in below_threshold)
        print(f"Students below {threshold:.0f}%: {names}")


def display_subject_averages(records: pd.DataFrame) -> None:
    """Display average attendance percentage per subject in one line."""
    if records.empty:
        print("No valid attendance data available.")
        return

    subject_data = calculate_subject_averages(records)
    summary = " | ".join(f"{subject}: {percentage:.2f}%" for subject, percentage in subject_data)
    print(summary)

    save_chart(subject_data, title="Subject-wise Attendance Average", chart_type="bar")
    save_chart(subject_data, title="Subject-wise Attendance Distribution", chart_type="pie")


def save_chart(data: Iterable[Tuple[str, float]], title: str, chart_type: str) -> None:
    """Save a chart image to the charts folder."""
    folder = Path("charts")
    folder.mkdir(exist_ok=True)

    items = list(data)
    if not items:
        return

    labels = [item[0] for item in items]
    values = [item[1] for item in items]

    fig, ax = plt.subplots(figsize=(8, 5))

    if chart_type == "bar":
        ax.bar(labels, values, color=["#5DA5DA", "#60BD68", "#F17CB0", "#FAA43A", "#B276B2"])
        ax.set_ylabel("Attendance (%)")
        ax.set_title(title)
        ax.set_ylim(0, 100)
        for tick in ax.get_xticklabels():
            tick.set_rotation(20)
        for container in ax.containers:
            ax.bar_label(container, fmt="%.2f", padding=3)
    elif chart_type == "pie":
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title(title)

    file_name = f"{title.lower().replace(' ', '_')}.png"
    fig.tight_layout()
    fig.savefig(folder / file_name)
    plt.close(fig)


def run_menu(file_path: str | Path, threshold: float = DEFAULT_THRESHOLD) -> None:
    """Show the interactive menu and handle user requests."""
    records = validate_and_clean(file_path)

    while True:
        print("\nAttendance Analyzer Menu")
        print("1. Student Percentage")
        print("2. Shortage List")
        print("3. Subject-wise Average")
        print("4. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            display_student_percentages(records)
        elif choice == "2":
            display_shortage_list(records, threshold)
        elif choice == "3":
            display_subject_averages(records)
        elif choice == "4":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please select 1, 2, 3 or 4.")


def print_full_report(file_path: str | Path, threshold: float = DEFAULT_THRESHOLD) -> None:
    """Generate the full assignment-style console report in one run."""
    records = validate_and_clean(file_path)
    if records.empty:
        print("No valid attendance data available.")
        return

    print("Student attendance percentages:")
    display_student_percentages(records)
    print("\nEligibility check:")
    display_shortage_list(records, threshold)
    print("\nSubject-wise average attendance:")
    display_subject_averages(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="College Attendance Analyzer")
    parser.add_argument("csv_file", nargs="?", default="attendance.csv", help="Path to the CSV file")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Minimum attendance percentage required (default: 75)",
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="Run the interactive menu instead of the direct assignment report.",
    )
    args = parser.parse_args()

    if args.menu:
        run_menu(args.csv_file, threshold=args.threshold)
    else:
        print_full_report(args.csv_file, threshold=args.threshold)


if __name__ == "__main__":
    main()
