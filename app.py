import streamlit as st
import pandas as pd
from datetime import datetime
import time
import math
from database import connect_db, create_table

# Initialize DB
create_table()

st.set_page_config(page_title="Smart Parking System", layout="wide")
st.title("🚗 Smart Parking Management System")

conn = connect_db()
cursor = conn.cursor()

TOTAL_SLOTS = 50

menu = ["Entry", "Exit", "Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

# =========================
# 🚘 ENTRY
# =========================
if choice == "Entry":
    st.subheader("Vehicle Entry Registration")

    # 1. Vehicle Number (Row 1)
    vehicle_number = st.text_input("🚗 Enter Vehicle Number", placeholder="e.g. MH12AB1234").upper().strip()

    # 2. Vehicle Type (Row 2)
    vehicle_type = st.selectbox("🚘 Select Vehicle Type", ["Bike", "Car", "Truck"])

    # 3. Mode Selection (Row 3)
    mode = st.radio("🛠️ Slot Assignment Mode", ["Auto", "Manual"], horizontal=True)

    # Database check for availability
    cursor.execute("SELECT slot_number FROM parking WHERE exit_time IS NULL")
    occupied = [row[0] for row in cursor.fetchall()]
    available_slots = sorted([i for i in range(1, TOTAL_SLOTS + 1) if i not in occupied])

    slot = None

    # 4. Slot Selection (Row 4)
    if mode == "Auto":
        if available_slots:
            slot = available_slots[0]
            st.info(f"✅ System has reserved **Slot {slot}** for this vehicle.")
        else:
            st.error("❌ Parking Full! No slots available.")
    else:
        if available_slots:
            slot = st.selectbox("📍 Choose an Available Slot", available_slots)
        else:
            st.error("❌ Parking Full! No slots available.")

    st.markdown("---") # Visual separator

    # 5. Submit Button (Row 5)
    if st.button("📥 Confirm & Park Vehicle", use_container_width=True):
        if not vehicle_number:
            st.warning("⚠️ Please enter a vehicle number.")
        elif not slot:
            st.error("🚫 Cannot park: No slot selected or parking is full.")
        else:
            # Duplicate check
            cursor.execute("SELECT id FROM parking WHERE vehicle_number=? AND exit_time IS NULL", (vehicle_number,))
            if cursor.fetchone():
                st.error(f"⚠️ Vehicle **{vehicle_number}** is already parked in the lot!")
            else:
                entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO parking (vehicle_number, slot_number, entry_time, vehicle_type)
                    VALUES (?, ?, ?, ?)
                """, (vehicle_number, slot, entry_time, vehicle_type))
                conn.commit()
                
                st.success(f"✅ Success! Vehicle **{vehicle_number}** parked at **Slot {slot}**.")
                time.sleep(1.5) 
                st.rerun()


# =========================
# 🚗 EXIT 
# =========================
elif choice == "Exit":
    st.subheader("Vehicle Exit & Billing")
    
    # Fetch active vehicles
    cursor.execute("SELECT id, vehicle_number, slot_number, entry_time, vehicle_type FROM parking WHERE exit_time IS NULL")
    data = cursor.fetchall()
    
    if data:
        # 1. Create DataFrame and SORT BY SLOT (Ascending)
        df = pd.DataFrame(data, columns=["ID", "Vehicle", "Slot", "Entry", "Type"])
        df = df.sort_values(by="Slot", ascending=True)
        
        # 2. Dropdown display
        df["Display"] = "Slot " + df["Slot"].astype(str) + " - " + df["Vehicle"]
        selected_display = st.selectbox("Select Vehicle to Checkout", df["Display"])
        
        # 3. Get row data
        selected_row = df[df["Display"] == selected_display].iloc[0]
        vehicle_id = int(selected_row["ID"])
        vehicle_number = selected_row["Vehicle"]
        slot_number = selected_row["Slot"]
        entry_time_str = selected_row["Entry"]
        v_type = selected_row["Type"]

        if st.button("Complete Exit & Generate Bill", use_container_width=True):
            exit_time_dt = datetime.now()
            exit_time_str = exit_time_dt.strftime("%Y-%m-%d %H:%M:%S")
            entry_time_dt = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
            
            # Time & Fee Calculation
            duration_total_hrs = (exit_time_dt - entry_time_dt).total_seconds() / 3600
            hours = int(duration_total_hrs)
            minutes = int((duration_total_hrs * 60) % 60)
            
            rates = {"Bike": 10, "Car": 20, "Truck": 30}
            rate = rates.get(v_type, 20)
            fee = max(10, round(duration_total_hrs * rate, 2))

            # Update Database
            cursor.execute("UPDATE parking SET exit_time=?, fee=? WHERE id=?", 
                         (exit_time_str, fee, vehicle_id))
            conn.commit()

            # --- Visual Receipt ---
            st.success(f"✅ Vehicle {vehicle_number} exited successfully!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📋 Details")
                st.write(f"**Vehicle:** {vehicle_number}")
                st.write(f"**Type:** {v_type}")
                st.write(f"**Slot:** {slot_number}")
            
            with col2:
                st.markdown("### 🕒 Timing")
                st.write(f"**Duration:** {hours}h {minutes}m")
                st.write(f"**Rate:** ₹{rate}/hr")
                st.write(f"**Entry:** {entry_time_str}")

            st.divider()
            
            # SUBTLE FEE DISPLAY (Ash Grey & Charcoal)
            st.markdown(f"""
                <div style="text-align: center; border: 1px solid #d1d5db; padding: 15px; border-radius: 8px; background-color: #f3f4f6;">
                    <h5 style="margin: 0; color: #4b5563; font-weight: 500; font-size: 14px; letter-spacing: 0.5px;">TOTAL AMOUNT DUE</h5>
                    <h2 style="margin: 5px 0 0 0; color: #111827; font-size: 32px; font-weight: 600;">₹{fee}</h2>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("") # Spacer
            if st.button("Finish & Clear"):
                st.rerun()
            
    else:
        st.info("ℹ️ No vehicles are currently parked.")



# =========================
# 📊 DASHBOARD
# =========================
elif choice == "Dashboard":
    st.subheader("Parking Dashboard")

    cursor.execute("SELECT * FROM parking")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["ID","Vehicle","Slot","Entry","Exit","Fee","Type"])

    # 1. Metrics
    cursor.execute("SELECT COUNT(*) FROM parking WHERE exit_time IS NULL")
    occupied_count = cursor.fetchone()[0]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Occupied Slots", occupied_count)
    m2.metric("Available Slots", TOTAL_SLOTS - occupied_count)
    m3.metric("Total Revenue", f"₹{round(df['Fee'].sum(), 2)}")

    # 2. Visual Slot Map (Grid)
    st.subheader("🅿️ Real-time Slot Status")
    cursor.execute("SELECT slot_number FROM parking WHERE exit_time IS NULL")
    occupied_slots = [row[0] for row in cursor.fetchall()]
    
    cols = st.columns(10)
    for i in range(1, TOTAL_SLOTS + 1):
        with cols[(i-1) % 10]:
            if i in occupied_slots:
                st.markdown(f"<div style='background-color:#ff4b4b; color:white; padding:5px; text-align:center; border-radius:5px; margin-bottom:5px;'>🔴 {i}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background-color:#28a745; color:white; padding:5px; text-align:center; border-radius:5px; margin-bottom:5px;'>🟢 {i}</div>", unsafe_allow_html=True)

    # 3. Data Table
    st.subheader("📝 Activity Log")
    status_filter = st.radio("Show:", ["All", "Active", "Exited"], horizontal=True)
    
    df_view = df[["Vehicle","Slot","Entry","Exit","Fee","Type"]].copy()
    if status_filter == "Active":
        df_view = df_view[df_view["Exit"].isna()]
    elif status_filter == "Exited":
        df_view = df_view[df_view["Exit"].notna()]
        
    st.dataframe(df_view, use_container_width=True)

conn.close()
