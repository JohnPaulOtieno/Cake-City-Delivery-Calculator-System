1. Cake Delivery Management System
A Django-based delivery management platform designed for cake shops to efficiently manage orders, calculate dynamic delivery fares, and track shipments across multiple store locations in Nairobi.

2. Overview
This application streamlines the cake delivery workflow by automating fare calculations based on real-world distances, managing multiple store locations, and providing order tracking through a manager dashboard. It integrates with Google Maps for accurate distance calculations and supports SMS notifications for delivery updates.

3. Features
✨ Core Functionality

📦 Create and manage delivery orders with real-time distance calculation
🗺️ Multi-store location management with GPS coordinates
💰 Dynamic fare calculation based on distance (configurable pricing)
📊 Order history and analytics dashboard
🔐 Manager authentication and access control
📱 SMS notifications for customers (via Africa's Talking)
🎫 Receipt generation with QR codes
🛠️ Technical Features

Real road distance calculation via Google Maps API
Fallback geolocation with OpenStreetMap Nominatim
Admin interface for pricing configuration
Order status tracking (Pending → Confirmed → In Transit → Delivered)
Interactive maps and analytics with Plotly
Bootstrap5 responsive UI
Tech Stack
Backend: Django 6.0.5
Database: PostgreSQL
Maps & Geolocation: Google Maps API, Geopy
Notifications: Africa's Talking SMS API
Frontend: Django Templates, Bootstrap5, Crispy Forms
Data Visualization: Plotly
QR Codes: qrcode with Pillow
Project Structure

4. Usage

Managers login and access the dashboard
Create delivery orders by entering customer address and selecting a store
System automatically calculates distance and fare
Generate receipts with QR codes
Track order status in real-time
View analytics and delivery history
Feel free to customize this with your specific project goals, contact info, license, or any additional features!
