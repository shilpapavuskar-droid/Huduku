from ninja import NinjaAPI

from users.module4 import router


api =NinjaAPI(
    title="HUDUKU API",
    description="API endpoints for managing User and user profile in Huduku marketplace.",
    version="1.0.0",
)

api.add_router("v1/",router)

