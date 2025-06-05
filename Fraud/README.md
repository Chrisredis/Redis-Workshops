# Redis Active-Active Fraud Detection Demo

This demo simulates a real-world fraud scenario using Redis Active-Active replication to detect fraudulent return attempts across multiple store locations.

## Scenario Overview

**The Setup**: A customer purchases a shirt at Store A, with both the transaction and their photo stored in Redis. Using Active-Active replication, this data syncs to Store B. Later, the customer attempts to return the item legitimately at Store A (with photo verification), while simultaneously a fraudster tries to return the same item at Store B using a hacked POS system without photo verification.

**The Detection**: Our system identifies the fraudulent attempt by comparing legitimate returns (with photos) against suspicious returns (without photos) in real-time.

## Architecture

```
[Store A - POS + Camera] → [Redis A] ←→ [Active-Active Sync] ←→ [Redis B] ← [Store B - Hacked POS]
                              ↓                                              ↓
                    [Legitimate Return]                           [Fraudulent Return]
                              ↓                                              ↓
                                    [Web Dashboard - Side by Side View]
                                              ↓
                                        [Fraud Detection]
```

## Key Features

- **Photo-Verified Transactions**: Camera integration for customer verification
- **Redis Active-Active Replication**: Real-time data sync between locations
- **Simultaneous Transaction Detection**: Identify concurrent return attempts
- **Visual Fraud Dashboard**: Side-by-side comparison of legitimate vs fraudulent attempts
- **Real-time Alerting**: Immediate fraud detection and notification

## Components

### 1. POS Transaction Simulator
- Simulates purchase transactions with photo capture
- Stores transaction data and customer photos in Redis
- Generates realistic transaction metadata

### 2. Active-Active Redis Setup
- Two Redis instances with bidirectional replication
- Automatic conflict resolution
- Real-time data synchronization

### 3. Return Processing System
- Legitimate return processing with photo verification
- Fraudulent return simulation without photos
- Transaction conflict detection

### 4. Fraud Detection Engine
- Real-time comparison of return attempts
- Photo verification analysis
- Risk scoring and alerting

### 5. Web Dashboard
- Live view of transactions across both locations
- Side-by-side fraud comparison
- Real-time alerts and notifications

## Prerequisites

- Redis Enterprise (for Active-Active) or Redis Stack
- Python 3.8+
- Webcam or camera for photo simulation
- Web browser for dashboard

## Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run the complete demo setup
python run_demo.py
```

This will:
- Check and install dependencies
- Start Redis containers
- Launch the fraud detection dashboard
- Provide an interactive menu for running scenarios

### Option 2: Manual Setup

1. **Setup Redis Active-Active**:
   ```bash
   # Start two Redis instances
   docker run -d --name redis-store-a -p 6379:6379 redis/redis-stack:latest
   docker run -d --name redis-store-b -p 6380:6379 redis/redis-stack:latest
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Components Separately**:
   ```bash
   python fraud_dashboard.py  # Terminal 1 - Web Dashboard
   python pos_simulator.py   # Terminal 2 - Store A (Legitimate)
   python hacked_pos.py      # Terminal 3 - Store B (Fraudulent)
   ```

4. **Open Dashboard**: Navigate to `http://localhost:8080`

## Demo Scenarios

### Scenario 1: Complete Fraud Detection
1. **Purchase**: Customer buys shirt at Store A with photo verification
2. **Sync**: Transaction automatically replicates to Store B via Active-Active
3. **Legitimate Return**: Customer returns item at Store A with photo verification
4. **Fraud Attempt**: Hacker simultaneously tries to return same item at Store B without photo
5. **Detection**: Dashboard shows both attempts side-by-side and flags the fraud

### Scenario 2: Interactive Testing
- Use the POS simulator to create various purchase transactions
- Use the hacked POS to attempt fraudulent returns
- Monitor real-time fraud detection on the dashboard

## Key Features Demonstrated

- **Photo Verification**: Legitimate transactions include customer photos
- **Active-Active Replication**: Data syncs between Redis instances in real-time
- **Fraud Detection**: System identifies returns without proper photo verification
- **Real-time Dashboard**: Live monitoring of transactions across both locations
- **Simultaneous Transaction Detection**: Identifies concurrent return attempts on same item
