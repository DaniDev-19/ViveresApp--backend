from fastapi import APIRouter
from app.api.v1.endpoints import (
    rates,
    sales,
    reports,
    purchases,
    upload,
    auth,
    web_orders,
    audit,
    products,
    providers,
    notifications,
    customers,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(rates.router, prefix="/rates", tags=["rates"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
api_router.include_router(web_orders.router, prefix="/web_orders", tags=["web_orders"])
api_router.include_router(upload.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(web_orders.router, prefix="/web-orders", tags=["web-orders"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
