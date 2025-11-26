import datetime
import os

# Define the grid height
HEIGHT = 7

# Define letters
font = {
    'U': [
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " ### "
    ],
    'S': [
        " ####",
        "#    ",
        "#    ",
        " ### ",
        "    #",
        "    #",
        "#### "
    ],
    'E': [
        "#####",
        "#    ",
        "#    ",
        "#####",
        "#    ",
        "#    ",
        "#####"
    ],
    'A': [
        "  #  ",
        " # # ",
        "#   #",
        "#   #",
        "#####",
        "#   #",
        "#   #"
    ],
    'M': [
        "#   #",
        "## ##",
        "# # #",
        "#   #",
        "#   #",
        "#   #",
        "#   #"
    ],
    'P': [
        "#####",
        "#   #",
        "#   #",
        "#####",
        "#    ",
        "#    ",
        "#    "
    ],
    ' ': [
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     "
    ]
}

message = "USE AMPS"

# Construct the full grid
full_grid_rows = [""] * HEIGHT

for idx, char in enumerate(message):
    letter = font.get(char.upper(), font[' '])
    for r in range(HEIGHT):
        full_grid_rows[r] += letter[r]

    # Add spacing column if not the last letter
    # Use 3 spaces for space character (which is already 5 wide? No wait)
    # In my font ' ' is 5 wide.
    # If char is ' ', we added 5 spaces.
    # The loop adds 1 column separator between letters.
    # If the message has " ", it uses the ' ' font which is 5 spaces.
    # So "USE AMPS": "USE" then " " (5 spaces) then "AMPS".
    # Plus 1 separator. So total separation is 6 columns. That's fine.

    if idx < len(message) - 1:
        for r in range(HEIGHT):
            full_grid_rows[r] += " "

# Print grid to verify
print("Pattern Preview:")
for row in full_grid_rows:
    print(row)

# Convert grid to (col, row) coordinates where we need commits
pixels = []
width = len(full_grid_rows[0])
for c in range(width):
    for r in range(HEIGHT):
        if full_grid_rows[r][c] == '#':
            pixels.append((c, r))

print(f"Width: {width}")
print(f"Total pixels (commits): {len(pixels)}")

# Calculate dates
today = datetime.date.today()

# To ensure the message is correctly aligned, we need to find the Sunday of the current week.
# Python's `weekday()` returns Monday=0, ..., Sunday=6.
# We adjust this so Sunday=0, ..., Saturday=6 to match the graph's layout.
# The `start_sunday` variable determines the first Sunday of the commit sequence,
# while `target_end_sunday` sets the last Sunday, aligning the message correctly.
days_since_sunday = (today.weekday() + 1) % 7
current_sunday = today - datetime.timedelta(days=days_since_sunday)

# Align the last column of the message to the previous week to avoid future dates.
target_end_sunday = current_sunday - datetime.timedelta(weeks=1)
start_sunday = target_end_sunday - datetime.timedelta(weeks=width)
print(f"Start Sunday: {start_sunday}")
print(f"End Week Sunday: {target_end_sunday}")

# Generate bash script lines
script_lines = []
script_lines.append("#!/bin/bash")
# We rely on configured user/email in the environment
# script_lines.append("git config user.name 'Jules'")
# script_lines.append("git config user.email 'jules@example.com'")

count = 0
commits_per_pixel = 50

for c, r in pixels:
    # Calculate date
    commit_date = start_sunday + datetime.timedelta(weeks=c, days=r)

    if commit_date > today:
        print(f"Skipping future date: {commit_date}")
        continue

    for i in range(commits_per_pixel):
        # ISO 8601 format
        # Add random minutes/seconds to avoid collisions if that matters?
        # Git commits with same timestamp are fine, they will be separate commits.
        # But let's vary time slightly to be safe/cleaner.
        # We just use the loop index.
        seconds = count % 60
        minutes = (count // 60) % 60
        hours = 12 + (count // 3600) % 10
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        date_str = commit_date.strftime(f"%Y-%m-%dT{time_str}")

        cmd = f'GIT_AUTHOR_DATE="{date_str}" GIT_COMMITTER_DATE="{date_str}" git commit --allow-empty -m "Pixel {c},{r} - {i+1}/{commits_per_pixel}"'
        script_lines.append(cmd)
        count += 1

with open("make_history.sh", "w") as f:
    f.write("\n".join(script_lines))

print(f"Generated make_history.sh with {count} commits")
