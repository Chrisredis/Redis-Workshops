#!/usr/bin/env python3
"""
Unified POS System with Photo Capture
A clean, single-window interface for the fraud detection demo that handles:
1. Product selection
2. Customer identification  
3. Photo capture with face detection
4. Transaction processing
5. Real-time fraud detection
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import cv2
import numpy as np
import redis
import json
import time
import uuid
import base64
import threading
from datetime import datetime
from PIL import Image, ImageTk
import os

class UnifiedPOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Redis Fraud Detection - Unified POS System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Redis connections
        self.redis_store_a = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.redis_store_b = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Camera
        self.camera = None
        self.camera_active = False
        self.captured_photo = None
        self.photo_base64 = None
        
        # Products catalog
        self.products = {
            "LAPTOP_001": {"name": "Gaming Laptop", "price": 2499.99, "category": "Electronics"},
            "WATCH_001": {"name": "Luxury Watch", "price": 1299.99, "category": "Accessories"},
            "PHONE_001": {"name": "Smartphone", "price": 899.99, "category": "Electronics"},
            "JACKET_001": {"name": "Leather Jacket", "price": 299.99, "category": "Clothing"},
            "SHOES_001": {"name": "Running Shoes", "price": 159.99, "category": "Footwear"},
            "TABLET_001": {"name": "Tablet Pro", "price": 799.99, "category": "Electronics"},
            "HEADPHONES_001": {"name": "Wireless Headphones", "price": 249.99, "category": "Electronics"},
            "JEANS_001": {"name": "Designer Jeans", "price": 189.99, "category": "Clothing"}
        }
        
        # Current transaction data
        self.current_customer = ""
        self.current_store = "STORE_A"
        self.selected_product = None
        self.transaction_type = "PURCHASE"
        
        self.setup_ui()
        self.check_redis_connection()
        
    def setup_ui(self):
        """Create the unified interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Left panel - Transaction details
        self.setup_transaction_panel(main_frame)
        
        # Right panel - Camera and photo
        self.setup_camera_panel(main_frame)
        
        # Bottom panel - Actions
        self.setup_action_panel(main_frame)
        
        # Status bar
        self.setup_status_bar(main_frame)
        
    def setup_transaction_panel(self, parent):
        """Setup the transaction details panel"""
        # Transaction frame
        txn_frame = ttk.LabelFrame(parent, text="Transaction Details", padding="10")
        txn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Store selection
        ttk.Label(txn_frame, text="Store:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.store_var = tk.StringVar(value="STORE_A")
        store_combo = ttk.Combobox(txn_frame, textvariable=self.store_var, 
                                  values=["STORE_A", "STORE_B"], state="readonly", width=15)
        store_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        store_combo.bind('<<ComboboxSelected>>', self.on_store_change)
        
        # Transaction type
        ttk.Label(txn_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="PURCHASE")
        type_combo = ttk.Combobox(txn_frame, textvariable=self.type_var,
                                 values=["PURCHASE", "RETURN"], state="readonly", width=15)
        type_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Customer ID
        ttk.Label(txn_frame, text="Customer:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.customer_var = tk.StringVar(value="CHRIS_001")
        customer_entry = ttk.Entry(txn_frame, textvariable=self.customer_var, width=20)
        customer_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Product selection
        ttk.Label(txn_frame, text="Product:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        # Product listbox with scrollbar
        product_frame = ttk.Frame(txn_frame)
        product_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.product_listbox = tk.Listbox(product_frame, height=8, width=40)
        scrollbar = ttk.Scrollbar(product_frame, orient=tk.VERTICAL, command=self.product_listbox.yview)
        self.product_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.product_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Populate products
        for sku, product in self.products.items():
            display_text = f"{product['name']} - ${product['price']:.2f}"
            self.product_listbox.insert(tk.END, display_text)
        
        self.product_listbox.bind('<<ListboxSelect>>', self.on_product_select)
        
        # Selected product display
        self.selected_label = ttk.Label(txn_frame, text="No product selected", 
                                       foreground="gray")
        self.selected_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)
        
    def setup_camera_panel(self, parent):
        """Setup the camera and photo panel"""
        # Camera frame
        camera_frame = ttk.LabelFrame(parent, text="Photo Verification", padding="10")
        camera_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Camera display
        self.camera_label = ttk.Label(camera_frame, text="Camera Preview", 
                                     background="black", foreground="white")
        self.camera_label.grid(row=0, column=0, columnspan=2, pady=10, padx=10)
        
        # Camera controls
        controls_frame = ttk.Frame(camera_frame)
        controls_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_camera_btn = ttk.Button(controls_frame, text="Start Camera", 
                                          command=self.start_camera)
        self.start_camera_btn.grid(row=0, column=0, padx=5)
        
        self.capture_btn = ttk.Button(controls_frame, text="Capture Photo", 
                                     command=self.capture_photo, state="disabled")
        self.capture_btn.grid(row=0, column=1, padx=5)
        
        self.stop_camera_btn = ttk.Button(controls_frame, text="Stop Camera", 
                                         command=self.stop_camera, state="disabled")
        self.stop_camera_btn.grid(row=0, column=2, padx=5)
        
        # Photo status
        self.photo_status = ttk.Label(camera_frame, text="No photo captured", 
                                     foreground="gray")
        self.photo_status.grid(row=2, column=0, columnspan=2, pady=5)
        
    def setup_action_panel(self, parent):
        """Setup the action buttons panel"""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=1, column=0, columnspan=2, pady=20)
        
        # Process transaction button
        self.process_btn = ttk.Button(action_frame, text="Process Transaction", 
                                     command=self.process_transaction, 
                                     style="Accent.TButton")
        self.process_btn.grid(row=0, column=0, padx=10)
        
        # Generate fraud attempt button
        fraud_btn = ttk.Button(action_frame, text="Simulate Fraud Attempt", 
                              command=self.simulate_fraud)
        fraud_btn.grid(row=0, column=1, padx=10)
        
        # Open dashboard button
        dashboard_btn = ttk.Button(action_frame, text="Open Dashboard", 
                                  command=self.open_dashboard)
        dashboard_btn.grid(row=0, column=2, padx=10)
        
        # Clear/Reset button
        clear_btn = ttk.Button(action_frame, text="Clear/Reset", 
                              command=self.clear_transaction)
        clear_btn.grid(row=0, column=3, padx=10)
        
    def setup_status_bar(self, parent):
        """Setup the status bar"""
        self.status_var = tk.StringVar(value="Ready - Select product and capture photo to begin")
        status_bar = ttk.Label(parent, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

    def check_redis_connection(self):
        """Check Redis connection and update status"""
        try:
            self.redis_store_a.ping()
            self.redis_store_b.ping()
            self.update_status("✅ Connected to Redis stores")
        except Exception as e:
            self.update_status(f"❌ Redis connection error: {e}")
            messagebox.showerror("Redis Error",
                               "Cannot connect to Redis stores. Please ensure Redis containers are running.")

    def update_status(self, message):
        """Update the status bar"""
        self.status_var.set(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        self.root.update_idletasks()

    def on_store_change(self, event=None):
        """Handle store selection change"""
        self.current_store = self.store_var.get()
        self.update_status(f"Store changed to {self.current_store}")

    def on_product_select(self, event=None):
        """Handle product selection"""
        selection = self.product_listbox.curselection()
        if selection:
            index = selection[0]
            product_skus = list(self.products.keys())
            self.selected_product = product_skus[index]
            product = self.products[self.selected_product]

            self.selected_label.config(
                text=f"Selected: {product['name']} - ${product['price']:.2f}",
                foreground="blue"
            )
            self.update_status(f"Product selected: {product['name']}")

    def start_camera(self):
        """Start the camera feed"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Camera not available")

            self.camera_active = True
            self.start_camera_btn.config(state="disabled")
            self.capture_btn.config(state="normal")
            self.stop_camera_btn.config(state="normal")

            self.update_status("📷 Camera started")
            self.update_camera_feed()

        except Exception as e:
            self.update_status(f"❌ Camera error: {e}")
            messagebox.showerror("Camera Error", f"Cannot start camera: {e}")

    def update_camera_feed(self):
        """Update the camera feed display"""
        if self.camera_active and self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Resize frame for display
                frame = cv2.resize(frame, (400, 300))

                # Add face detection
                frame_with_faces = self.detect_faces(frame)

                # Convert to RGB for tkinter
                frame_rgb = cv2.cvtColor(frame_with_faces, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)

                # Update label
                self.camera_label.config(image=photo, text="")
                self.camera_label.image = photo  # Keep a reference

            # Schedule next update
            self.root.after(30, self.update_camera_feed)

    def detect_faces(self, frame):
        """Detect faces in the frame and draw rectangles"""
        try:
            # Load face cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Face Detected", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Add face count
            cv2.putText(frame, f"Faces: {len(faces)}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            return frame

        except Exception as e:
            # If face detection fails, return original frame
            cv2.putText(frame, "Face detection unavailable", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            return frame

    def capture_photo(self):
        """Capture a photo from the camera"""
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Resize for storage
                self.captured_photo = cv2.resize(frame, (320, 240))

                # Convert to base64
                _, buffer = cv2.imencode('.jpg', self.captured_photo)
                self.photo_base64 = base64.b64encode(buffer).decode('utf-8')

                # Update status
                self.photo_status.config(text="✅ Photo captured successfully", foreground="green")
                self.update_status("📸 Photo captured and ready for transaction")

                # Save photo file for reference
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"customer_photo_{timestamp}.jpg"
                cv2.imwrite(filename, self.captured_photo)

                # Stop camera after capture
                self.stop_camera()

            else:
                self.update_status("❌ Failed to capture photo")
        else:
            self.update_status("❌ Camera not available")

    def stop_camera(self):
        """Stop the camera feed"""
        self.camera_active = False
        if self.camera:
            self.camera.release()
            self.camera = None

        # Reset camera display
        self.camera_label.config(image="", text="Camera Preview\n(Stopped)",
                                background="black", foreground="white")

        # Update buttons
        self.start_camera_btn.config(state="normal")
        self.capture_btn.config(state="disabled")
        self.stop_camera_btn.config(state="disabled")

        self.update_status("📷 Camera stopped")

    def process_transaction(self):
        """Process the current transaction"""
        # Validate inputs
        if not self.selected_product:
            messagebox.showerror("Error", "Please select a product")
            return

        customer_id = self.customer_var.get().strip()
        if not customer_id:
            messagebox.showerror("Error", "Please enter a customer ID")
            return

        transaction_type = self.type_var.get()
        store_id = self.store_var.get()

        # Check for photo if it's a purchase
        if transaction_type == "PURCHASE" and not self.photo_base64:
            result = messagebox.askyesno("No Photo",
                                       "No photo captured. Process without photo verification?\n"
                                       "(This may trigger fraud detection)")
            if not result:
                return

        try:
            # Create transaction
            transaction_id = f"TXN_{store_id}_{uuid.uuid4().hex[:8].upper()}"
            product = self.products[self.selected_product]

            transaction_data = {
                "transaction_id": transaction_id,
                "store_id": store_id,
                "customer_id": customer_id,
                "product_sku": self.selected_product,
                "product_name": product["name"],
                "price": product["price"],
                "transaction_type": transaction_type,
                "timestamp": datetime.now().isoformat(),
                "has_photo": bool(self.photo_base64),
                "is_fraudulent": False
            }

            # Get Redis client for the store
            redis_client = self.redis_store_a if store_id == "STORE_A" else self.redis_store_b

            # Store transaction
            redis_client.set(f"transaction:{transaction_id}", json.dumps(transaction_data))

            # Store photo if available
            if self.photo_base64:
                redis_client.set(f"photo:{transaction_id}", self.photo_base64)

            # Add to transaction stream
            redis_client.xadd("transaction_stream", {
                "transaction_id": transaction_id,
                "store_id": store_id,
                "customer_id": customer_id,
                "amount": product["price"],
                "type": transaction_type,
                "has_photo": "true" if self.photo_base64 else "false"
            })

            # Show success message
            messagebox.showinfo("Success",
                              f"Transaction {transaction_id} processed successfully!\n"
                              f"Customer: {customer_id}\n"
                              f"Product: {product['name']}\n"
                              f"Amount: ${product['price']:.2f}\n"
                              f"Photo: {'✅ Verified' if self.photo_base64 else '❌ Missing'}")

            self.update_status(f"✅ Transaction {transaction_id} processed")

            # Clear the transaction
            self.clear_transaction()

        except Exception as e:
            self.update_status(f"❌ Transaction failed: {e}")
            messagebox.showerror("Transaction Error", f"Failed to process transaction: {e}")

    def simulate_fraud(self):
        """Simulate a fraudulent transaction attempt"""
        try:
            # Create fraudulent transaction (return without photo)
            transaction_id = f"TXN_FRAUD_{uuid.uuid4().hex[:8].upper()}"

            # Use high-value product
            fraud_product_sku = "LAPTOP_001"  # Gaming Laptop
            product = self.products[fraud_product_sku]

            transaction_data = {
                "transaction_id": transaction_id,
                "store_id": "STORE_B",  # Fraud typically at different store
                "customer_id": "FRAUDSTER_001",
                "product_sku": fraud_product_sku,
                "product_name": product["name"],
                "price": product["price"],
                "transaction_type": "RETURN",
                "timestamp": datetime.now().isoformat(),
                "has_photo": False,
                "is_fraudulent": True,
                "fraud_indicators": ["no_photo", "high_value_return", "suspicious_customer"]
            }

            # Store in Redis Store B
            self.redis_store_b.set(f"transaction:{transaction_id}", json.dumps(transaction_data))

            # Add fraud alert
            fraud_alert = {
                "alert_id": f"FRAUD_{uuid.uuid4().hex[:8].upper()}",
                "transaction_id": transaction_id,
                "fraud_score": 85,
                "risk_level": "HIGH",
                "indicators": ["Missing photo verification", "High-value return", "Known fraudster"],
                "timestamp": datetime.now().isoformat(),
                "action_taken": "TRANSACTION_BLOCKED"
            }

            self.redis_store_b.set(f"fraud_alert:{transaction_id}", json.dumps(fraud_alert))

            # Add to transaction stream
            self.redis_store_b.xadd("transaction_stream", {
                "transaction_id": transaction_id,
                "store_id": "STORE_B",
                "customer_id": "FRAUDSTER_001",
                "amount": product["price"],
                "type": "RETURN",
                "has_photo": "false",
                "fraud_detected": "true"
            })

            messagebox.showwarning("Fraud Detected",
                                 f"🚨 FRAUD ATTEMPT DETECTED!\n\n"
                                 f"Transaction: {transaction_id}\n"
                                 f"Customer: FRAUDSTER_001\n"
                                 f"Product: {product['name']}\n"
                                 f"Amount: ${product['price']:.2f}\n"
                                 f"Fraud Score: 85/100\n\n"
                                 f"❌ TRANSACTION BLOCKED")

            self.update_status(f"🚨 Fraud detected and blocked: {transaction_id}")

        except Exception as e:
            self.update_status(f"❌ Fraud simulation failed: {e}")
            messagebox.showerror("Error", f"Failed to simulate fraud: {e}")

    def open_dashboard(self):
        """Open the fraud detection dashboard"""
        import webbrowser
        import subprocess
        import threading

        def start_dashboard():
            try:
                # Start the dashboard in a separate process
                subprocess.Popen(["python3", "fraud_dashboard.py"],
                               cwd=os.path.dirname(os.path.abspath(__file__)))
                time.sleep(2)  # Give it time to start
                webbrowser.open("http://localhost:8080")
            except Exception as e:
                self.update_status(f"❌ Failed to open dashboard: {e}")

        # Start in background thread
        threading.Thread(target=start_dashboard, daemon=True).start()
        self.update_status("🌐 Opening fraud detection dashboard...")

    def clear_transaction(self):
        """Clear/reset the current transaction"""
        # Reset selections
        self.product_listbox.selection_clear(0, tk.END)
        self.selected_product = None
        self.selected_label.config(text="No product selected", foreground="gray")

        # Reset photo
        self.captured_photo = None
        self.photo_base64 = None
        self.photo_status.config(text="No photo captured", foreground="gray")

        # Stop camera if running
        if self.camera_active:
            self.stop_camera()

        # Reset customer (optional)
        # self.customer_var.set("CHRIS_001")

        self.update_status("🔄 Transaction cleared - Ready for new transaction")

    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Handle application closing"""
        if self.camera_active:
            self.stop_camera()
        self.root.destroy()

if __name__ == "__main__":
    # Create and run the unified POS system
    app = UnifiedPOS()
    app.run()
