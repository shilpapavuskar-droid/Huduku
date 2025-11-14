erDiagram

    %% ============================
    %% AUTH SERVICE
    %% ============================

    USERS {
        UUID id PK
        string username
        string email
        string password_hash
        boolean is_active
        datetime created_at
    }

    USER_PROFILE {
        UUID id PK
        UUID user_id
        string first_name
        string last_name
        string phone
        UUID avatar_media_id
    }

    USERS ||--|| USER_PROFILE : "has profile"


    %% ============================
    %% LISTING SERVICE
    %% ============================

    CATEGORIES {
        UUID id PK
        string name
        UUID parent_id FK
        string slug
    }

    LISTINGS {
        UUID id PK
        UUID owner_user_id
        UUID category_id
        string title
        text description
        decimal price
        string location
        boolean is_active
        datetime created_at
    }

    LISTING_MEDIA {
        UUID id PK
        UUID listing_id
        UUID media_id
        string type
    }

    REVIEWS {
        UUID id PK
        UUID listing_id
        UUID reviewer_user_id
        int rating
        text comment
        datetime created_at
    }

    FAVORITES {
        UUID id PK
        UUID user_id
        UUID listing_id
    }

    CATEGORIES ||--|{ CATEGORIES : "parent"
    CATEGORIES ||--|{ LISTINGS : "has many"
    LISTINGS ||--|{ LISTING_MEDIA : "media"
    LISTINGS ||--|{ REVIEWS : "reviews"
    LISTINGS ||--|{ FAVORITES : "favorited by"


    %% ============================
    %% PAYMENT SERVICE
    %% ============================

    ORDERS {
        UUID id PK
        UUID user_id
        UUID listing_id
        decimal amount
        string currency
        string status
        datetime created_at
    }

    TRANSACTIONS {
        UUID id PK
        UUID order_id
        string provider
        string payment_token
        decimal amount
        string status
        datetime processed_at
    }

    INVOICES {
        UUID id PK
        UUID order_id
        string invoice_number
        UUID pdf_media_id
    }

    ORDERS ||--|{ TRANSACTIONS : "payments"
    ORDERS ||--|| INVOICES : "invoice"


    %% ============================
    %% MEDIA SERVICE
    %% ============================

    MEDIA_FILES {
        UUID id PK
        UUID owner_user_id
        string file_url
        string file_type
        int file_size
        datetime created_at
    }


    %% ============================
    %% CROSS-SERVICE REFERENCES (DASHED)
    %% ============================

    USERS ||..|| LISTINGS : "owner_user_id (API reference)"
    USERS ||..|| REVIEWS : "reviewer_user_id (API reference)"
    USERS ||..|| FAVORITES : "favorites (API reference)"
    USERS ||..|| ORDERS : "buyer (API reference)"

    LISTINGS ||..|| ORDERS : "listing purchased"
    MEDIA_FILES ||..|| LISTING_MEDIA : "media_id reference"
    MEDIA_FILES ||..|| USER_PROFILE : "avatar_media_id"
    MEDIA_FILES ||..|| INVOICES : "pdf_media_id"
