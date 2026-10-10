from decimal import Decimal
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Product, User
from app.services.auth_service import ensure_admin_user

SAMPLE_PRODUCTS = [
    # Fruits
    {
        "name": "Fresh Shimla Apples (1 kg)",
        "price": Decimal("180.00"),
        "category": "Fruits",
        "stock_quantity": 45,
        "image_url": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&auto=format&fit=crop&q=80",
        "description": "Crisp and juicy handpicked royal delicious apples from the orchards of Shimla."
    },
    {
        "name": "Alphonso Mangoes (1 Dozen)",
        "price": Decimal("650.00"),
        "category": "Fruits",
        "stock_quantity": 25,
        "image_url": "https://images.unsplash.com/photo-1553279768-865429fa0078?w=600&auto=format&fit=crop&q=80",
        "description": "Naturally ripened Ratnagiri Alphonso mangoes, renowned for their heavenly aroma and sweet taste."
    },
    {
        "name": "Robusta Bananas (1 kg)",
        "price": Decimal("48.00"),
        "category": "Fruits",
        "stock_quantity": 80,
        "image_url": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=600&auto=format&fit=crop&q=80",
        "description": "Fresh, nutrient-rich yellow bananas packed with potassium and natural dietary energy."
    },
    {
        "name": "Valencia Sweet Oranges (1 kg)",
        "price": Decimal("120.00"),
        "category": "Fruits",
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1582979512210-99b6a53386f9?w=600&auto=format&fit=crop&q=80",
        "description": "Juicy sweet citrus oranges, perfect for fresh morning breakfast juice."
    },
    {
        "name": "Seedless Green Grapes (500 g)",
        "price": Decimal("95.00"),
        "category": "Fruits",
        "stock_quantity": 40,
        "image_url": "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=600&auto=format&fit=crop&q=80",
        "description": "Sweet and tangy seedless Thompson green grapes fresh from Nashik vineyards."
    },

    # Vegetables
    {
        "name": "Organic Red Tomatoes (1 kg)",
        "price": Decimal("38.00"),
        "category": "Vegetables",
        "stock_quantity": 70,
        "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=80",
        "description": "Firm, plump, vine-ripened organic red tomatoes suitable for curries and fresh salads."
    },
    {
        "name": "Farm Fresh Potatoes (2 kg)",
        "price": Decimal("60.00"),
        "category": "Vegetables",
        "stock_quantity": 95,
        "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=600&auto=format&fit=crop&q=80",
        "description": "Peeled or baked, these high-starch farm fresh potatoes are a household kitchen staple."
    },
    {
        "name": "Crisp Green Capsicum (500 g)",
        "price": Decimal("45.00"),
        "category": "Vegetables",
        "stock_quantity": 35,
        "image_url": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=600&auto=format&fit=crop&q=80",
        "description": "Crunchy bell peppers packed with Vitamin C, ideal for stir-fries and pizza toppings."
    },
    {
        "name": "Hydroponic Baby Spinach (250 g)",
        "price": Decimal("35.00"),
        "category": "Vegetables",
        "stock_quantity": 25,
        "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600&auto=format&fit=crop&q=80",
        "description": "Tender, washed and ready-to-eat baby palak leaves rich in iron and essential folate."
    },
    {
        "name": "Fresh Red Onions (1 kg)",
        "price": Decimal("42.00"),
        "category": "Vegetables",
        "stock_quantity": 85,
        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=600&auto=format&fit=crop&q=80",
        "description": "Pungent and flavorful red onions, essential for everyday Indian culinary curries."
    },

    # Dairy
    {
        "name": "Amul Taaza Homogenised Toned Milk (1 L)",
        "price": Decimal("56.00"),
        "category": "Dairy",
        "stock_quantity": 60,
        "image_url": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=600&auto=format&fit=crop&q=80",
        "description": "Pure pasteurized toned milk enriched with Vitamin A and D for everyday family health."
    },
    {
        "name": "Amul Salted Butter (500 g)",
        "price": Decimal("275.00"),
        "category": "Dairy",
        "stock_quantity": 40,
        "image_url": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=600&auto=format&fit=crop&q=80",
        "description": "The classic creamy salted butter that gives your warm toast and parathas unmatched flavor."
    },
    {
        "name": "Fresh Malai Paneer (200 g)",
        "price": Decimal("90.00"),
        "category": "Dairy",
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
        "description": "Soft and melt-in-mouth cottage cheese blocks, ideal for Shahi Paneer and Matar Paneer."
    },
    {
        "name": "Greek Natural Yogurt (400 g)",
        "price": Decimal("110.00"),
        "category": "Dairy",
        "stock_quantity": 25,
        "image_url": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=600&auto=format&fit=crop&q=80",
        "description": "High-protein, thick and creamy probiotic curd crafted with whole cow milk."
    },
    {
        "name": "Farm Fresh White Eggs (Pack of 12)",
        "price": Decimal("108.00"),
        "category": "Dairy",
        "stock_quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=600&auto=format&fit=crop&q=80",
        "description": "Carefully sorted, graded, and washed poultry eggs rich in high-quality protein."
    },

    # Grains
    {
        "name": "India Gate Basmati Rice Classic (5 kg)",
        "price": Decimal("520.00"),
        "category": "Grains",
        "stock_quantity": 40,
        "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&auto=format&fit=crop&q=80",
        "description": "Aged long-grain aromatic basmati rice that cooks into slender, fluffy, and separate grains."
    },
    {
        "name": "Aashirvaad Shudh Chakki Atta (5 kg)",
        "price": Decimal("245.00"),
        "category": "Grains",
        "stock_quantity": 55,
        "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&auto=format&fit=crop&q=80",
        "description": "100% pure whole wheat flour processed with traditional chakki stone grinding for soft rotis."
    },
    {
        "name": "Tata Sampann Unpolished Toor Dal (1 kg)",
        "price": Decimal("165.00"),
        "category": "Grains",
        "stock_quantity": 45,
        "image_url": "https://images.unsplash.com/photo-1585994192701-f1a505c817ea?w=600&auto=format&fit=crop&q=80",
        "description": "Natural unpolished pigeon peas that retain their natural wholesome goodness and protein."
    },
    {
        "name": "Quaker Rolled Oats (1 kg)",
        "price": Decimal("190.00"),
        "category": "Grains",
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1614961908593-3560f78d30e3?w=600&auto=format&fit=crop&q=80",
        "description": "100% whole grain rolled oats with beta-glucan soluble fiber that helps support heart health."
    },
    {
        "name": "Organic Royal Quinoa (500 g)",
        "price": Decimal("230.00"),
        "category": "Grains",
        "stock_quantity": 20,
        "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&auto=format&fit=crop&q=80",
        "description": "Gluten-free supergrain rich in complete plant protein and dietary minerals."
    },

    # Snacks
    {
        "name": "Lay's Classic Salted Potato Chips (115 g)",
        "price": Decimal("40.00"),
        "category": "Snacks",
        "stock_quantity": 60,
        "image_url": "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=600&auto=format&fit=crop&q=80",
        "description": "Thinly sliced golden potatoes fried to crisp perfection and seasoned with sea salt."
    },
    {
        "name": "Haldiram's Nagpur Bhujia Sev (400 g)",
        "price": Decimal("130.00"),
        "category": "Snacks",
        "stock_quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
        "description": "Crunchy, spicy moth-bean and chickpea savory noodles flavored with authentic Indian spices."
    },
    {
        "name": "Britannia Good Day Cashew Cookies (200 g)",
        "price": Decimal("45.00"),
        "category": "Snacks",
        "stock_quantity": 65,
        "image_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=600&auto=format&fit=crop&q=80",
        "description": "Rich butter cookies studded with crunchy cashew nut bites for tea-time indulgence."
    },
    {
        "name": "California Roasted Salted Almonds (200 g)",
        "price": Decimal("280.00"),
        "category": "Snacks",
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1508061257970-57e34f0f7201?w=600&auto=format&fit=crop&q=80",
        "description": "Premium slow-roasted California almonds with a light hint of Himalayan pink salt."
    },
    {
        "name": "Amul Dark Chocolate 75% Cocoa (150 g)",
        "price": Decimal("110.00"),
        "category": "Snacks",
        "stock_quantity": 35,
        "image_url": "https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=600&auto=format&fit=crop&q=80",
        "description": "Exquisite dark chocolate crafted with single-origin Ghanaian cocoa beans."
    },

    # Beverages
    {
        "name": "Brooke Bond Red Label Tea (500 g)",
        "price": Decimal("260.00"),
        "category": "Beverages",
        "stock_quantity": 55,
        "image_url": "https://images.unsplash.com/photo-1594631252845-29fc4cc8cde9?w=600&auto=format&fit=crop&q=80",
        "description": "Rich, amber-colored Assam CTC tea leaves with unmatched flavor and refreshing warmth."
    },
    {
        "name": "Nescafe Classic Instant Coffee (100 g)",
        "price": Decimal("240.00"),
        "category": "Beverages",
        "stock_quantity": 40,
        "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop&q=80",
        "description": "100% pure Robusta coffee beans roasted and granulated for an invigorating quick brew."
    },
    {
        "name": "Tropicana 100% Orange Juice (1 L)",
        "price": Decimal("145.00"),
        "category": "Beverages",
        "stock_quantity": 30,
        "image_url": "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=600&auto=format&fit=crop&q=80",
        "description": "No added sugar, pure and natural fruit juice packed with natural Vitamin C."
    },
    {
        "name": "Raw Pressery Tender Coconut Water (200 ml)",
        "price": Decimal("55.00"),
        "category": "Beverages",
        "stock_quantity": 45,
        "image_url": "https://images.unsplash.com/photo-1544253103-34e8f7ec29a9?w=600&auto=format&fit=crop&q=80",
        "description": "Naturally isotonic tender coconut water without preservatives or artificial sugar."
    },

    # Household Essentials
    {
        "name": "Surf Excel Matic Top Load Detergent (1 kg)",
        "price": Decimal("230.00"),
        "category": "Household Essentials",
        "stock_quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1585421514738-01798e348b17?w=600&auto=format&fit=crop&q=80",
        "description": "Powerful machine-wash powder formulated to remove tough stains in a single cycle."
    },
    {
        "name": "Vim Dishwash Liquid Gel Lemon (750 ml)",
        "price": Decimal("155.00"),
        "category": "Household Essentials",
        "stock_quantity": 45,
        "image_url": "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?w=600&auto=format&fit=crop&q=80",
        "description": "Concentrated lemon gel with grease-cutting enzymes that cleans a sink full of vessels with one spoon."
    },
    {
        "name": "Dettol Liquid Handwash Refill (750 ml)",
        "price": Decimal("115.00"),
        "category": "Household Essentials",
        "stock_quantity": 60,
        "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&auto=format&fit=crop&q=80",
        "description": "Original germ-defense handwash soap refill with 99.9% antibacterial protection."
    },
    {
        "name": "Origami 3-Ply Soft Kitchen Towels (Pack of 2)",
        "price": Decimal("140.00"),
        "category": "Household Essentials",
        "stock_quantity": 35,
        "image_url": "https://images.unsplash.com/photo-1584556812952-905ffd0c611a?w=600&auto=format&fit=crop&q=80",
        "description": "Ultra-absorbent virgin fiber paper towels designed for wiping spills and oily snacks."
    }
]


def seed_database(db: Session) -> None:
    """
    Seeds initial admin user and grocery inventory idempotently.
    Avoids duplicate entries if called multiple times.
    """
    # 1. Ensure admin user exists
    ensure_admin_user(db)

    # 2. Seed products idempotently by product name
    added_count = 0
    for item_data in SAMPLE_PRODUCTS:
        existing = db.query(Product).filter(Product.name == item_data["name"]).first()
        if not existing:
            prod = Product(
                name=item_data["name"],
                price=item_data["price"],
                category=item_data["category"],
                stock_quantity=item_data["stock_quantity"],
                image_url=item_data["image_url"],
                description=item_data["description"]
            )
            db.add(prod)
            added_count += 1

    if added_count > 0:
        db.commit()
        print(f"Successfully seeded {added_count} new grocery products.")
    else:
        print("Database already contains sample products. No duplicate insertion.")


def main():
    """CLI runner for database initialization and seeding."""
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized.")

    db = SessionLocal()
    try:
        seed_database(db)
        print("Seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
