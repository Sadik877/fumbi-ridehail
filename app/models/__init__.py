"""
Import every model here so that:
  1. `from app.models import User, Wallet, ...` works from anywhere
  2. Flask-Migrate / db.create_all() sees the full metadata graph
"""
from app.models.user import User, UserRole
from app.models.profiles import (
    PassengerProfile,
    FavoriteDriver,
    DriverProfile,
    VehicleType,
    Vehicle,
    BusinessProfile,
)
from app.models.booking import (
    RideBooking,
    DeliveryBooking,
    Trip,
    BookingStatus,
    ParcelSize,
)
from app.models.wallet import (
    Wallet,
    Transaction,
    TransactionType,
    TransactionProvider,
    TransactionStatus,
)
from app.models.misc import (
    Notification,
    Rating,
    Review,
    PromoCode,
    DiscountType,
    SupportTicket,
    TicketStatus,
    SavedLocation,
    EmergencyContact,
)

__all__ = [
    "User", "UserRole",
    "PassengerProfile", "FavoriteDriver", "DriverProfile", "VehicleType", "Vehicle", "BusinessProfile",
    "RideBooking", "DeliveryBooking", "Trip", "BookingStatus", "ParcelSize",
    "Wallet", "Transaction", "TransactionType", "TransactionProvider", "TransactionStatus",
    "Notification", "Rating", "Review", "PromoCode", "DiscountType",
    "SupportTicket", "TicketStatus", "SavedLocation", "EmergencyContact",
]
