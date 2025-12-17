from ninja import NinjaAPI

from inventory.module4 import router as router4


api =NinjaAPI(
    title="HUDUKU API",
    description="API endpoints for managing categories, listings, media, reviews, and favorites in the Huduku marketplace.",
    version="1.0.0",
)

api.add_router("v1/",router4)