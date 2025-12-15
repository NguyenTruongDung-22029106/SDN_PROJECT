#!/bin/bash
# Installation script for SDN-ML-Blockchain project
# Ubuntu 20.04/22.04

set -e

echo "======================================"
echo "SDN-ML-Blockchain Installation Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[*]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run as root"
    exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update

# Install basic dependencies
print_status "Installing basic dependencies..."
sudo apt install -y \
    git \
    curl \
    wget \
    vim \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    software-properties-common

# Install Mininet
print_status "Installing Mininet..."
if ! command -v mn &> /dev/null; then
    sudo apt install -y mininet
    print_status "Mininet installed successfully"
else
    print_warning "Mininet already installed"
fi

# Install Open vSwitch
print_status "Installing Open vSwitch..."
sudo apt install -y openvswitch-switch openvswitch-common

# Install Ryu Controller
print_status "Installing Ryu SDN Controller..."
sudo pip3 install ryu

# Install Python ML libraries
print_status "Installing Python ML libraries..."
sudo pip3 install \
    numpy \
    pandas \
    scikit-learn \
    joblib \
    matplotlib \
    seaborn

# Install Flask for gateway server
print_status "Installing Flask and dependencies..."
sudo pip3 install \
    flask \
    flask-cors \
    requests

# Install attack tools
print_status "Installing attack simulation tools..."
sudo apt install -y hping3 iperf3

# Install Docker (for Hyperledger Fabric)
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_status "Docker installed. You may need to log out and back in."
else
    print_warning "Docker already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    print_warning "Docker Compose already installed"
fi

# Install Go (for Hyperledger Fabric chaincode)
print_status "Installing Go..."
if ! command -v go &> /dev/null; then
    wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
    rm go1.21.0.linux-amd64.tar.gz
    
    # Add to PATH
    echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.bashrc
    export PATH=$PATH:/usr/local/go/bin
    
    print_status "Go installed successfully"
else
    print_warning "Go already installed"
fi

# Install Node.js and npm (optional, for JavaScript chaincode)
print_status "Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
else
    print_warning "Node.js already installed"
fi

# Download Hyperledger Fabric samples and binaries
print_status "Downloading Hyperledger Fabric..."
if [ ! -d "fabric-samples" ]; then
    curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.0 1.5.5
    print_status "Hyperledger Fabric downloaded"
else
    print_warning "Fabric samples already exist"
fi

# Set up Python virtual environment (optional but recommended)
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt 2>/dev/null || print_warning "requirements.txt not found, skipping"
else
    print_warning "Virtual environment already exists"
fi

# Make scripts executable
print_status "Making scripts executable..."
chmod +x scripts/*.sh
chmod +x topology/*.py

# Verify installations
print_status "Verifying installations..."
echo ""
echo "Mininet version:"
mn --version || print_error "Mininet not found"
echo ""
echo "Ryu version:"
ryu-manager --version || print_error "Ryu not found"
echo ""
echo "Docker version:"
docker --version || print_error "Docker not found"
echo ""
echo "Go version:"
go version || print_error "Go not found"
echo ""
echo "Node version:"
node --version || print_error "Node not found"

echo ""
echo "======================================"
print_status "Installation completed!"
echo "======================================"
echo ""
print_warning "Important next steps:"
echo "1. Log out and back in to apply Docker group changes"
echo "2. Run 'source ~/.bashrc' to update PATH"
echo "3. Activate virtual environment: source venv/bin/activate"
echo "4. Read README.md for usage instructions"
echo ""
