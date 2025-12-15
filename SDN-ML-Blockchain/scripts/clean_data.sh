#!/bin/bash
# Clean runtime data files

DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/data"

echo "==================================="
echo "Cleaning Runtime Data Files"
echo "==================================="

if [ ! -d "$DATA_DIR" ]; then
    echo "❌ Data directory not found: $DATA_DIR"
    exit 1
fi

cd "$DATA_DIR"

# Count files before cleaning
FILE_COUNT=$(ls -1 *.csv 2>/dev/null | wc -l)

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "✓ No CSV files to clean"
    exit 0
fi

echo "Found $FILE_COUNT CSV file(s):"
ls -lh *.csv 2>/dev/null

read -p "Do you want to delete all CSV files? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f *.csv
    echo "✓ Deleted all CSV files"
    
    # Ensure .gitkeep exists
    if [ ! -f .gitkeep ]; then
        echo "# Data directory for runtime CSV files" > .gitkeep
        echo "✓ Created .gitkeep"
    fi
    
    echo "✓ Data directory cleaned"
else
    echo "Cancelled"
fi

echo "==================================="
