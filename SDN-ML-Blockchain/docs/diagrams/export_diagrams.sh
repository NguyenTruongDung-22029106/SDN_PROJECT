#!/bin/bash

# Script to export all Mermaid diagrams to PNG/SVG
# Requires: @mermaid-js/mermaid-cli
# Install: npm install -g @mermaid-js/mermaid-cli

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Mermaid Diagram Export Tool                               ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if mmdc is installed
if ! command -v mmdc &> /dev/null; then
    echo "❌ Error: Mermaid CLI (mmdc) is not installed."
    echo ""
    echo "To install, run:"
    echo "  npm install -g @mermaid-js/mermaid-cli"
    echo ""
    echo "Or use Docker:"
    echo "  docker pull minlag/mermaid-cli"
    exit 1
fi

echo "✓ Mermaid CLI found: $(which mmdc)"
echo ""

# Create output directories
mkdir -p png svg pdf
echo "✓ Created output directories: png/, svg/, pdf/"
echo ""

# Count total files
TOTAL_FILES=$(ls -1 *.mmd 2>/dev/null | wc -l)

if [ "$TOTAL_FILES" -eq 0 ]; then
    echo "❌ No .mmd files found in current directory"
    exit 1
fi

echo "Found $TOTAL_FILES diagram files to export"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Export format selection
FORMAT="${1:-png}"  # Default to PNG if no argument provided

case "$FORMAT" in
    png|PNG)
        FORMAT="png"
        ;;
    svg|SVG)
        FORMAT="svg"
        ;;
    pdf|PDF)
        FORMAT="pdf"
        ;;
    all|ALL)
        FORMAT="all"
        ;;
    *)
        echo "❌ Invalid format: $FORMAT"
        echo "Usage: $0 [png|svg|pdf|all]"
        exit 1
        ;;
esac

# Export function
export_diagram() {
    local input_file="$1"
    local output_format="$2"
    local basename="${input_file%.mmd}"
    local output_file="${output_format}/${basename}.${output_format}"
    
    echo -n "  Exporting ${input_file} → ${output_file}... "
    
    if mmdc -i "$input_file" -o "$output_file" -b transparent 2>/dev/null; then
        echo "✓"
        return 0
    else
        echo "✗ (failed)"
        return 1
    fi
}

# Export all diagrams
SUCCESS=0
FAILED=0

if [ "$FORMAT" = "all" ]; then
    echo "Exporting to PNG, SVG, and PDF formats..."
    echo ""
    
    for file in *.mmd; do
        echo "Processing: $file"
        
        for fmt in png svg pdf; do
            if export_diagram "$file" "$fmt"; then
                ((SUCCESS++))
            else
                ((FAILED++))
            fi
        done
        
        echo ""
    done
else
    echo "Exporting to $FORMAT format..."
    echo ""
    
    for file in *.mmd; do
        if export_diagram "$file" "$FORMAT"; then
            ((SUCCESS++))
        else
            ((FAILED++))
        fi
    done
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Export Summary:"
echo "  ✓ Success: $SUCCESS"
echo "  ✗ Failed:  $FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo "🎉 All diagrams exported successfully!"
else
    echo "⚠️  Some diagrams failed to export. Check the errors above."
fi

echo ""
echo "Output locations:"
if [ "$FORMAT" = "all" ]; then
    echo "  - PNG files: $SCRIPT_DIR/png/"
    echo "  - SVG files: $SCRIPT_DIR/svg/"
    echo "  - PDF files: $SCRIPT_DIR/pdf/"
else
    echo "  - ${FORMAT^^} files: $SCRIPT_DIR/$FORMAT/"
fi

echo ""
echo "Done!"

