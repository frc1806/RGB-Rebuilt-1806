#!/bin/bash
# Diagnostic script to check RGB-Rebuilt-1806 installation

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "RGB-Rebuilt-1806 Installation Check"
echo "=========================================="
echo ""

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Check venv exists
echo "1. Checking virtual environment..."
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found${NC}"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "  Run: python3 -m venv venv"
    exit 1
fi

# Check Python version
echo ""
echo "2. Checking Python version..."
PYTHON_VERSION=$(venv/bin/python3 --version)
echo "  $PYTHON_VERSION"

# Check pip
echo ""
echo "3. Checking pip..."
venv/bin/python3 -m pip --version

# Check pyntcore
echo ""
echo "4. Checking pyntcore (Network Tables)..."
if venv/bin/python3 -c "import ntcore; print(f'✓ ntcore imported successfully')" 2>/dev/null; then
    NTCORE_VERSION=$(venv/bin/python3 -c "import ntcore; print(ntcore.__version__)" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ pyntcore installed (version: $NTCORE_VERSION)${NC}"
else
    echo -e "${RED}✗ pyntcore not working${NC}"
    echo "  Trying to import..."
    venv/bin/python3 -c "import ntcore" 2>&1 || true
    echo ""
    echo "  Fix: source venv/bin/activate && pip install pyntcore"
fi

# Check spidev
echo ""
echo "5. Checking spidev (LED control)..."
if venv/bin/python3 -c "import spidev; print('✓ spidev imported successfully')" 2>/dev/null; then
    echo -e "${GREEN}✓ spidev installed${NC}"
else
    echo -e "${RED}✗ spidev not working${NC}"
    echo "  Fix: source venv/bin/activate && pip install spidev"
fi

# Check PyYAML
echo ""
echo "6. Checking PyYAML (configuration)..."
if venv/bin/python3 -c "import yaml; print('✓ PyYAML imported successfully')" 2>/dev/null; then
    echo -e "${GREEN}✓ PyYAML installed${NC}"
else
    echo -e "${RED}✗ PyYAML not working${NC}"
    echo "  Fix: source venv/bin/activate && pip install PyYAML"
fi

# Check package installation
echo ""
echo "7. Checking rgb_reefscape package..."
if venv/bin/python3 -c "import rgb_reefscape; print('✓ rgb_reefscape imported successfully')" 2>/dev/null; then
    echo -e "${GREEN}✓ rgb_reefscape package installed${NC}"
else
    echo -e "${RED}✗ rgb_reefscape package not installed${NC}"
    echo "  Fix: source venv/bin/activate && pip install -e ."
fi

# Check SPI device
echo ""
echo "8. Checking SPI device..."
if [ -e "/dev/spidev0.0" ]; then
    echo -e "${GREEN}✓ /dev/spidev0.0 exists${NC}"
    ls -l /dev/spidev0.0
else
    echo -e "${YELLOW}⚠ /dev/spidev0.0 not found${NC}"
    echo "  SPI may not be enabled. Run: sudo raspi-config or orangepi-config"
fi

# Summary
echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "To run the application:"
echo "  source venv/bin/activate"
echo "  python3 -m rgb_reefscape.main"
echo ""
echo "Or directly with venv python:"
echo "  venv/bin/python3 -m rgb_reefscape.main"
echo ""
