"""
Mock data layer.

Everything in this file stands in for a real database (Postgres, etc).
Keeping it isolated here means swapping in real models/queries later
only touches this file and the route handlers that call it — templates
and JS never need to change.
"""
from datetime import datetime, timedelta

# ---------------------------------------------------------------------
# Landing page content
# ---------------------------------------------------------------------

STATS = [
    {"value": "2.4M+", "label": "Rides completed"},
    {"value": "18", "label": "Cities across Africa"},
    {"value": "94k", "label": "Active drivers"},
    {"value": "4.9/5", "label": "Average rating"},
]

FEATURES = [
    {
        "icon": "zap",
        "title": "Matched in seconds",
        "text": "Our dispatch engine finds the closest available driver so you're rarely waiting more than a few minutes.",
    },
    {
        "icon": "shield-check",
        "title": "Verified drivers, every trip",
        "text": "Background checks, vehicle inspections and live ID verification before anyone gets behind the wheel.",
    },
    {
        "icon": "map-pin",
        "title": "Live tracking, start to finish",
        "text": "Share your trip with anyone. Watch the route update in real time, down to the minute.",
    },
    {
        "icon": "wallet",
        "title": "Pay your way",
        "text": "Mobile money, card, or Fumbi Wallet — top up once and ride across every city we serve.",
    },
    {
        "icon": "package",
        "title": "Send it, don't drive it",
        "text": "Same-day delivery for documents, food and parcels, tracked exactly like a ride.",
    },
    {
        "icon": "headset",
        "title": "Support that answers",
        "text": "A real human, in under two minutes, whenever a trip doesn't go to plan.",
    },
]

WHY_US = [
    {
        "title": "Built for African roads",
        "text": "Routing tuned for the streets that international apps get wrong — unnamed roads, informal addresses, landmark-based navigation.",
    },
    {
        "title": "Fair pricing, shown upfront",
        "text": "You see the full fare before you book. No surge you can't see coming.",
    },
    {
        "title": "Drivers earn more",
        "text": "Lower commission than the industry standard, so the people driving you keep more of every fare.",
    },
]

TESTIMONIALS = [
    {
        "quote": "I schedule my airport rides three days out now. It's never once been late.",
        "name": "Amaka O.",
        "role": "Lagos",
    },
    {
        "quote": "Sent a parcel across town before lunch — it was signed for before I'd finished my coffee.",
        "name": "Kwabena T.",
        "role": "Accra",
    },
    {
        "quote": "Driving full-time on Fumbi paid off my taxi in eleven months.",
        "name": "Grace N.",
        "role": "Driver, Nairobi",
    },
]

FAQS = [
    {
        "q": "How do I pay for a ride?",
        "a": "Add mobile money, a debit or credit card, or top up your Fumbi Wallet. You choose the payment method before every trip, and receipts are emailed automatically.",
    },
    {
        "q": "What cities does Fumbi operate in?",
        "a": "We're live in 18 cities across West and East Africa, with new cities added roughly every quarter. Open the app to see live coverage for your area.",
    },
    {
        "q": "How are drivers verified?",
        "a": "Every driver passes a government ID check, a criminal background check, and a vehicle inspection before their first trip — then re-verifies every six months.",
    },
    {
        "q": "Can I schedule a ride in advance?",
        "a": "Yes. Booking ride can be scheduled up to 14 days ahead from the booking screen — useful for flights, interviews, or anything you can't be late for.",
    },
    {
        "q": "What if I leave something in the car?",
        "a": "Open your trip in Booking History and tap 'Report lost item' — we connect you directly with your driver's last known contact route.",
    },
    {
        "q": "How does delivery pricing work?",
        "a": "Delivery fares are based on distance and parcel size, shown in full before you confirm. There are no hidden weight surcharges.",
    },
]

# ---------------------------------------------------------------------
# Dashboard / account data
# ---------------------------------------------------------------------

CURRENT_USER = {
    "name": "Tariro Moyo",
    "email": "tariro.moyo@example.com",
    "phone": "+263 77 123 4567",
    "city": "Harare",
    "rating": 4.9,
    "member_since": "March 2023",
    "avatar_initials": "TM",
}

WALLET = {
    "balance": 184.50,
    "currency": "USD",
    "pending": 12.00,
}

WALLET_TRANSACTIONS = [
    {"date": "Jul 5", "label": "Ride — Borrowdale to CBD", "type": "debit", "amount": 6.50},
    {"date": "Jul 4", "label": "Wallet top-up — Mobile Money", "type": "credit", "amount": 50.00},
    {"date": "Jul 2", "label": "Delivery — Parcel to Avondale", "type": "debit", "amount": 4.20},
    {"date": "Jun 29", "label": "Ride — Airport transfer", "type": "debit", "amount": 18.00},
    {"date": "Jun 26", "label": "Referral bonus", "type": "credit", "amount": 5.00},
    {"date": "Jun 24", "label": "Wallet top-up — Visa •••• 4471", "type": "credit", "amount": 40.00},
]

BOOKINGS = [
    {
        "id": "FMB-88213",
        "type": "ride",
        "date": "Jul 5, 2026",
        "time": "08:12 AM",
        "from_": "Borrowdale, Harare",
        "to": "CBD, Harare",
        "driver": "Tendai M.",
        "fare": 6.50,
        "status": "completed",
    },
    {
        "id": "FMB-88190",
        "type": "delivery",
        "date": "Jul 2, 2026",
        "time": "01:45 PM",
        "from_": "Newlands, Harare",
        "to": "Avondale, Harare",
        "driver": "Rudo C.",
        "fare": 4.20,
        "status": "completed",
    },
    {
        "id": "FMB-88104",
        "type": "ride",
        "date": "Jun 29, 2026",
        "time": "05:30 AM",
        "from_": "Greendale, Harare",
        "to": "R.G. Mugabe Int'l Airport",
        "driver": "Farai K.",
        "fare": 18.00,
        "status": "completed",
    },
    {
        "id": "FMB-88099",
        "type": "ride",
        "date": "Jun 27, 2026",
        "time": "07:02 PM",
        "from_": "CBD, Harare",
        "to": "Belgravia, Harare",
        "driver": "—",
        "fare": 0.00,
        "status": "cancelled",
    },
    {
        "id": "FMB-88041",
        "type": "delivery",
        "date": "Jun 24, 2026",
        "time": "11:20 AM",
        "from_": "Eastlea, Harare",
        "to": "Mount Pleasant, Harare",
        "driver": "Blessing N.",
        "fare": 5.10,
        "status": "completed",
    },
]

NOTIFICATIONS = [
    {
        "icon": "car",
        "title": "Your driver is arriving",
        "text": "Tendai M. is 2 minutes away in a white Toyota Axio, plate AEX 4471.",
        "time": "2m ago",
        "unread": True,
    },
    {
        "icon": "receipt",
        "title": "Receipt ready",
        "text": "Your receipt for trip FMB-88213 has been added to Booking History.",
        "time": "3h ago",
        "unread": True,
    },
    {
        "icon": "gift",
        "title": "You earned a referral bonus",
        "text": "$5.00 was added to your Fumbi Wallet after Kwame's first ride.",
        "time": "1d ago",
        "unread": False,
    },
    {
        "icon": "alert-triangle",
        "title": "Scheduled maintenance",
        "text": "Wallet top-ups may be briefly unavailable tonight between 11PM–12AM CAT.",
        "time": "2d ago",
        "unread": False,
    },
    {
        "icon": "star",
        "title": "Rate your last trip",
        "text": "How was your ride with Farai K. on Jun 29? Your feedback helps other riders.",
        "time": "5d ago",
        "unread": False,
    },
]

DASHBOARD_SUMMARY = {
    "total_trips": 132,
    "total_spent": 1284.60,
    "co2_saved_kg": 46,
    "avg_rating_given": 4.8,
}

RECENT_ACTIVITY_CHART = [12, 18, 9, 22, 14, 26, 19]  # last 7 days, trip count proxy
