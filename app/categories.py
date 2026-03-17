# Full 3-level category hierarchy: Macro -> Sub -> [Micro]
# Exactly as provided by the business team.

CATEGORIES = {
    "Technology": {
        "Main devices": ["General", "Smartphones", "Tablets", "Laptops", "Desktop Computers"],
        "Accessories": [
            "General", "Headphones", "Smartwatches", "Chargers", "Power Banks",
            "Cables", "Keyboards", "Mouse", "Webcams", "Digital pen", "Printers",
            "Remote controller", "Other",
        ],
        "TV & Home electronics": [
            "General", "Televisions", "Projectors", "Audio Systems",
            "Streaming Devices", "Wi-Fi Routers",
        ],
        "Gaming": [
            "General", "Consoles", "Gaming Laptops", "Handheld Gaming Devices",
            "Controllers", "VR Headsets", "Other",
        ],
        "Imaging & Video": [
            "General", "Camera", "Lenses", "Camera accessories", "Drones", "Gimbals",
        ],
        "Personal Electronics": [
            "General", "Hair Dryers", "Electric Toothbrushes", "Electric Razors",
            "Air Purifiers", "Humidifiers", "Smart Thermostats", "Other",
        ],
        "AI & Software Services": [
            "General", "Chatbots", "Virtual Assistants", "Office Productivity Software",
            "Image/Video Editing Software", "Cloud Storage Services", "Security Software",
            "CRM Platforms", "Other softwares",
        ],
        "Other": ["-"],
    },
    "Food": {
        "Restaurants, Bars & Pubs": [
            "General", "Pizzas", "Burgers", "Sandwiches", "Pasta dishes",
            "International cuisine", "Breakfast items", "Pastries", "Coffee",
            "Drinks", "Desserts",
        ],
        "Groceries": [
            "General", "Fresh produce", "Dairy", "Eggs", "Meat", "Poultry",
            "Seafood", "Packaged foods", "Snacks", "Beverages",
        ],
        "Food Delivery Platforms": [
            "General", "Restaurant Meal Delivery", "Grocery & Fresh Produce Delivery",
            "Meal Kits", "Dessert & Baked Goods Delivery",
        ],
        "Direct Producers": [
            "General", "Fresh produce", "Dairy", "Eggs", "Meat", "Poultry",
            "Seafood", "Packaged foods", "Snacks", "Coffee & hot beverages",
            "Drinks", "Desserts",
        ],
    },
    "Fashion": {
        "Clothes & Shoes": [
            "General", "Footwear", "Lower-Body Wear", "Upper-Body Wear",
            "One-Piece & Dresses", "Active & Sportswear", "Underwear & socks",
        ],
        "Accessories": [
            "General", "Bags", "Wallets", "Belts", "Straps", "Headwear",
            "Eyewear", "Jewelry", "Watches", "Handwear", "Headwear & scarf",
            "Ties", "Hair Accessories",
        ],
        "Other": ["-"],
    },
    "House": {
        "Furniture": [
            "General", "Chairs", "Tables", "Sofas", "Beds", "Wardrobes",
            "Dressers", "Nightstands", "Cabinets", "Shelves", "Benches", "Decores",
        ],
        "Kitchen Products": [
            "General", "Microwaves", "Refrigerators", "Ovens", "Stoves", "Dishes",
            "Pots", "Pans", "Cutlery", "Blenders", "Coffee machines",
        ],
        "Appliances": [
            "General", "Washing machines", "Dryers", "Dishwashers",
            "Vacuum cleaners", "Air conditioners", "Heaters",
        ],
        "Hygiene & Cleaning": [
            "General", "Mops", "Brooms", "Brushes", "Sponges", "Detergents",
            "Bleaches", "Disinfectants", "Cleaning cloths",
        ],
        "Green Life": [
            "General", "Flowers", "Potted plants", "Indoor plants", "Planters",
            "Gardening tools", "Seeds",
        ],
    },
    "Media": {
        "Books Subscription": [
            "General", "E-book platforms", "Digital libraries", "Audiobook platforms",
        ],
        "Media Subscriptions": ["General", "Movies", "Music", "Streaming"],
        "Telecommunication": ["General", "Telephone", "Simcart", "Satellite"],
        "Other": ["-"],
    },
    "Health": {
        "Beauty & hygiene": [
            "General", "Deodorants", "Perfumes", "Skincare products", "Makeup",
            "Shampoos & soaps", "Oral",
        ],
        "Sports & Activity": [
            "General", "Gyms", "Fitness centers", "Sport classes",
            "Personal training sessions", "Group workouts",
        ],
        "Health Products": [
            "General", "Medicines", "Supplements", "Medical devices",
        ],
        "Spa & Relax": ["General", "Spa facilities", "Wellness treatments"],
        "Athletic accessories": [
            "General", "Hiking equipment", "Camping gear", "Backpacks", "Tents",
            "Sleeping bags", "Fitness accessories", "Yoga mats",
        ],
    },
    "Travel": {
        "Accommodation": [
            "General", "Hotels", "Hostels", "Short-term rental",
        ],
        "Transportation": [
            "General", "Buses", "Trains", "Flights", "Ferries", "Car rentals",
        ],
        "Package Delivery": [
            "General", "Parcel shipping", "Express courier services",
            "Standard mail delivery", "International logistics",
        ],
        "Multi-Purpose Platforms & Tours": ["General"],
    },
    "Finance, Bureaucracy & Paperwork": {
        "Banking": ["General"],
        "Insurance": [
            "General", "Life", "Health", "Travel", "Vehicle", "Property", "Product",
        ],
        "Scholarship & Funding": ["General", "Scholarships", "Research"],
        "Accounting": ["General", "Tax preparation", "Financial reporting"],
        "Legal & Bureaucratic Services": [
            "General", "Legal consultation", "Immigration advisory",
            "Public administration helpdesks",
        ],
        "Multi-Purpose": ["General"],
    },
    "Market Places": {
        "Fashion": ["General"],
        "Electronics & Gadgets": ["General"],
        "Hobby / Collectibles": ["General", "Toys & Games", "Musical instruments"],
        "Other": ["-"],
    },
    "Education": {
        "Universities": [
            "General", "Public", "Private", "Technical", "Art", "High-school",
        ],
        "Online Platforms": ["General", "Language", "Scientific", "Public Knowledge"],
        "Institutions": ["General", "Language", "Scientific", "Public Knowledge"],
        "Educational Products": [
            "General", "E-book readers", "Textbooks", "Educational Instruments",
        ],
        "Scientific & Educational Events & Offers": [
            "General", "Internships", "Research programs", "Hackathons",
            "Workshops", "Conferences", "Summer schools",
        ],
    },
    "Culture": {
        "Cinema & Movies": ["General", "Tickets", "Subscriptions"],
        "Theater & Shows": [
            "General", "Theater performances", "Stand-up comedy shows",
            "Talks and conferences", "Live stage events",
        ],
        "Live Concerts": [
            "General", "Music concerts", "Artist tours", "Live music festivals",
        ],
        "Entertainment & Events": [
            "General", "Fashion shows", "Cultural festivals", "Exhibitions",
            "Public entertainment events",
        ],
        "Museums & Galleries": [
            "General", "Museums", "Art galleries", "Historical sites",
            "Monuments", "Cultural landmarks",
        ],
    },
}

# Macro categories only (for brand-level categorization)
MACRO_CATEGORIES = list(CATEGORIES.keys())

# Helper functions
def get_sub_categories(macro: str) -> list[str]:
    return list(CATEGORIES.get(macro, {}).keys())

def get_micro_categories(macro: str, sub: str) -> list[str]:
    return CATEGORIES.get(macro, {}).get(sub, [])
