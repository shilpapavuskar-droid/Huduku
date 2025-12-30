from django.db import transaction
from .models import Category

# flat description, using parent_slug instead of numeric IDs
DEFAULT_CATEGORIES = [
    {"name": "Electronics", "slug": "electronics", "parent_slug": None},
    {"name": "Automobiles", "slug": "automobiles", "parent_slug": None},
    {"name": "Furniture", "slug": "furniture", "parent_slug": None},
    {"name": "Cars", "slug": "cars", "parent_slug": "automobiles"},
    {"name": "Bikes", "slug": "bikes", "parent_slug": "automobiles"},
    {"name": "Real Estate", "slug": "real-estate", "parent_slug": None},
]


def bootstrap_categories():
    """Create default categories in two passes so parents exist before children."""
    with transaction.atomic():
        # first pass: create all categories without parents
        for data in DEFAULT_CATEGORIES:
            if data["parent_slug"] is None:
                Category.objects.get_or_create(
                    slug=data["slug"],
                    defaults={"name": data["name"], "parent": None},
                )

        # second pass: assign parents for children
        for data in DEFAULT_CATEGORIES:
            if data["parent_slug"] is not None:
                parent = Category.objects.filter(slug=data["parent_slug"]).first()
                if not parent:
                    continue  # parent not found; skip safely
                Category.objects.get_or_create(
                    slug=data["slug"],
                    defaults={"name": data["name"], "parent": parent},
                )