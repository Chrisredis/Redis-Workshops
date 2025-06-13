# 🎯 Unified POS System - Clean Demo Interface

## 🚀 **What's New**
A single, clean window that handles everything:
- ✅ Product selection
- ✅ Customer identification  
- ✅ Photo capture with face detection
- ✅ Transaction processing
- ✅ Real-time fraud detection
- ✅ Dashboard integration

**No more switching between terminal and UI!**

## 🏃‍♂️ **Quick Start**

### **Option 1: Simple Launch**
```bash
cd Fraud
python3 start_unified_demo.py
```

### **Option 2: Direct Launch**
```bash
cd Fraud
python3 unified_pos.py
```

## 🎬 **How to Use**

### **1. Setup Transaction**
- Select store (A or B)
- Choose transaction type (Purchase/Return)
- Enter customer ID
- Select product from list

### **2. Capture Photo**
- Click "Start Camera"
- Position face in camera view
- Green rectangles show face detection
- Click "Capture Photo" when ready
- Camera automatically stops after capture

### **3. Process Transaction**
- Click "Process Transaction"
- View confirmation with all details
- Transaction appears in Redis and dashboard

### **4. Monitor Results**
- Click "Open Dashboard" to see real-time view
- Watch transactions appear instantly
- See fraud detection in action

## 🚨 **Demo Scenarios**

### **Legitimate Transaction**
1. Select any product
2. Capture photo with face
3. Process transaction
4. ✅ Shows as verified in dashboard

### **Fraud Simulation**
1. Click "Simulate Fraud Attempt"
2. 🚨 Automatic fraud detection
3. Transaction blocked
4. Alert appears in dashboard

## 🎯 **Key Features**

### **📷 Smart Camera Management**
- Opens only when needed
- Automatic face detection
- Closes after capture
- No multiple camera instances

### **🔄 Real-time Integration**
- Instant Redis storage
- Live dashboard updates
- Cross-store replication
- Fraud pattern detection

### **🎨 Clean Interface**
- Single window design
- Clear status updates
- Visual feedback
- Error handling

## 🛠️ **Requirements**
- Redis containers (ports 6379 & 6380)
- Python packages: `redis opencv-python pillow flask flask-socketio`
- Camera (optional - generates fake photos if unavailable)

## 📊 **What You'll See**

### **Successful Purchase**
```
✅ Transaction TXN_STORE_A_ABC123 processed successfully!
Customer: CHRIS_001
Product: Gaming Laptop
Amount: $2499.99
Photo: ✅ Verified
```

### **Fraud Detection**
```
🚨 FRAUD ATTEMPT DETECTED!

Transaction: TXN_FRAUD_XYZ789
Customer: FRAUDSTER_001
Product: Gaming Laptop
Amount: $2499.99
Fraud Score: 85/100

❌ TRANSACTION BLOCKED
```

## 🎊 **Perfect for Demos**
- Professional single-window interface
- Real face detection with visual feedback
- Instant fraud detection
- Live dashboard integration
- Clean, intuitive workflow

**Just run `python3 start_unified_demo.py` and you're ready to impress! 🎉**
