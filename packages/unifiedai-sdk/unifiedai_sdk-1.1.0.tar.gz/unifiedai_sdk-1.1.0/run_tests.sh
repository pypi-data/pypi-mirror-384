#!/bin/bash
# Run tests with coverage reporting
# Usage: ./run_tests.sh [options]

set -e

echo "🧪 Running UnifiedAI SDK Test Suite..."
echo "========================================"
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    echo ""
fi

# Check if test dependencies are installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing test dependencies..."
    pip install -e ".[dev]"
    echo ""
fi

# Parse arguments
COVERAGE_ONLY=false
HTML_REPORT=false
FAST_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage-only)
            COVERAGE_ONLY=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        --fast)
            FAST_MODE=true
            shift
            ;;
        *)
            # Pass through to pytest
            break
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ "$FAST_MODE" = false ]; then
    # Full coverage report
    PYTEST_CMD="$PYTEST_CMD --cov=src/unifiedai"
    PYTEST_CMD="$PYTEST_CMD --cov-report=term-missing"
    PYTEST_CMD="$PYTEST_CMD --cov-report=html:htmlcov"
    PYTEST_CMD="$PYTEST_CMD --cov-report=xml:coverage.xml"
    PYTEST_CMD="$PYTEST_CMD --cov-fail-under=90"
fi

# Add remaining arguments
PYTEST_CMD="$PYTEST_CMD $@"

# Run tests
echo "📊 Running: $PYTEST_CMD"
echo ""

if $PYTEST_CMD; then
    echo ""
    echo "✅ All tests passed!"
    echo ""
    
    if [ "$FAST_MODE" = false ]; then
        echo "📈 Coverage reports generated:"
        echo "   - Terminal: See above"
        echo "   - HTML:     htmlcov/index.html"
        echo "   - XML:      coverage.xml"
        echo ""
        
        if [ "$HTML_REPORT" = true ]; then
            echo "🌐 Opening HTML coverage report..."
            if command -v open &> /dev/null; then
                open htmlcov/index.html
            elif command -v xdg-open &> /dev/null; then
                xdg-open htmlcov/index.html
            else
                echo "   Open manually: file://$(pwd)/htmlcov/index.html"
            fi
        fi
        
        # Show summary
        echo "📊 Coverage Summary:"
        coverage report --skip-empty --precision=2 | tail -1
    fi
    
    exit 0
else
    echo ""
    echo "❌ Tests failed!"
    echo ""
    echo "💡 Tips:"
    echo "   - Run single test: pytest tests/unit/test_retry.py::test_name"
    echo "   - Show output: pytest -s"
    echo "   - Verbose mode: pytest -vv"
    echo "   - Stop on first failure: pytest -x"
    echo ""
    exit 1
fi

