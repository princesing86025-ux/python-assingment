# College Attendance Analyzer

This project reads attendance data from a CSV file, calculates student attendance percentages, finds students below the minimum required threshold, and displays basic charts for analysis.

## Features
- Reads CSV attendance records
- Validates attendance data
- Calculates percentage for each student
- Lists students below the required attendance threshold
- Shows subject-wise attendance averages
- Saves bar and pie charts to the `charts` folder

## Run the project

1. Create and activate a virtual environment.
2. Install the dependencies:
   `pip install -r requirements.txt`
3. Start the program:
   `python main.py --file attendance.csv`

## Example CSV format

```csv
Name,Subject,Classes_Held,Classes_Attended
Aman,Python,40,36
Riya,Python,40,28
Karan,Python,40,30
```
