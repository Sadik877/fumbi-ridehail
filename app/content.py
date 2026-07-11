"""
Marketing/editorial content for the public site. This is copywriting, not
application data — unlike the old mock_data.py, nothing here stands in for
a database record. Live numbers (driver counts, completed trips, etc.) are
computed from the database in routes/main.py.
"""

FEATURES = [
    {"icon": "zap", "title": "Matched in seconds", "text": "Our dispatch engine finds the closest available driver so you're rarely waiting more than a few minutes."},
    {"icon": "shield-check", "title": "Verified drivers, every trip", "text": "Background checks, vehicle inspections and live ID verification before anyone gets behind the wheel."},
    {"icon": "map-pin", "title": "Live tracking, start to finish", "text": "Share your trip with anyone. Watch the route update in real time on OpenStreetMap."},
    {"icon": "wallet", "title": "Pay your way", "text": "Mobile money, card via Flutterwave or Paystack, cash, or MoveX Wallet."},
    {"icon": "package", "title": "Send it, don't drive it", "text": "Same-day delivery for documents, food and parcels, tracked exactly like a ride."},
    {"icon": "headset", "title": "Support that answers", "text": "A real human, in under two minutes, whenever a trip doesn't go to plan."},
]

WHY_US = [
    {"title": "Built for African roads", "text": "Routing tuned for the streets international apps get wrong — unnamed roads, informal addresses, landmark-based navigation."},
    {"title": "Fair pricing, shown upfront", "text": "You see the full fare before you book. No surge you can't see coming."},
    {"title": "Drivers earn more", "text": "Lower commission than the industry standard, so the people driving you keep more of every fare."},
]

FAQS = [
    {"q": "How do I pay for a ride?", "a": "Add mobile money, a debit or credit card via Flutterwave or Paystack, or top up your MoveX Wallet. You choose the payment method before every trip, and receipts are emailed automatically."},
    {"q": "What cities does MoveX operate in?", "a": "We're expanding across Nigeria and West Africa, with new cities added regularly. Open the app to see live coverage for your area."},
    {"q": "How are drivers verified?", "a": "Every driver passes a government ID check, a criminal background check, and a vehicle inspection before their first trip — then re-verifies periodically."},
    {"q": "Can I schedule a ride in advance?", "a": "Yes. Rides can be scheduled ahead of time from the booking screen — useful for flights, interviews, or anything you can't be late for."},
    {"q": "What if I leave something in the car?", "a": "Open your trip in Booking History and tap 'Report lost item' — we connect you directly with your driver's last known contact route."},
    {"q": "How does delivery pricing work?", "a": "Delivery fares are based on distance and parcel size, shown in full before you confirm. There are no hidden weight surcharges."},
    {"q": "Can businesses send multiple deliveries at once?", "a": "Yes — the Business dashboard supports bulk delivery requests, invoicing, and monthly reporting for teams that ship regularly."},
    {"q": "What happens if I need emergency help during a trip?", "a": "Every trip screen has an SOS button that alerts your saved emergency contacts and shares your live location."},
]
