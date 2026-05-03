"""
Seed script — loads 20 sample products into Elasticsearch.
Run from project root: python scripts/seed_products.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch import Elasticsearch
from app.services.es_service import get_es_client, setup_indices, index_products

SAMPLE_PRODUCTS = [
    {
        "id": "1",
        "name": "Sony WH-1000XM5 Wireless Headphones",
        "description": "Industry-leading noise cancelling with Auto NC Optimizer. Crystal clear hands-free calling, up to 30-hour battery life.",
        "price": 24999,
        "category": "Electronics",
        "brand": "Sony",
        "rating": 4.7,
        "stock": 15,
        "tags": ["headphones", "wireless", "noise-cancelling", "bluetooth"]
    },
    {
        "id": "2",
        "name": "Apple AirPods Pro (2nd Generation)",
        "description": "Active Noise Cancellation, Adaptive Transparency, Personalized Spatial Audio with dynamic head tracking.",
        "price": 19999,
        "category": "Electronics",
        "brand": "Apple",
        "rating": 4.6,
        "stock": 40,
        "tags": ["earbuds", "wireless", "noise-cancelling", "apple"]
    },
    {
        "id": "3",
        "name": "Nike Air Max 270",
        "description": "Lightweight running shoe featuring Nike's biggest Air unit yet for all-day comfort and bold style.",
        "price": 8999,
        "category": "Footwear",
        "brand": "Nike",
        "rating": 4.4,
        "stock": 50,
        "tags": ["shoes", "running", "air-max", "sports"]
    },
    {
        "id": "4",
        "name": "Adidas Ultraboost 22",
        "description": "Our most responsive running shoe. Energy-returning Boost midsole, Primeknit+ upper for sock-like fit.",
        "price": 12999,
        "category": "Footwear",
        "brand": "Adidas",
        "rating": 4.5,
        "stock": 30,
        "tags": ["shoes", "running", "boost", "sports"]
    },
    {
        "id": "5",
        "name": "Samsung Galaxy Tab S9",
        "description": "11-inch Dynamic AMOLED 2X display, Snapdragon 8 Gen 2, IP68 water resistance, S Pen included.",
        "price": 52999,
        "category": "Tablets",
        "brand": "Samsung",
        "rating": 4.5,
        "stock": 20,
        "tags": ["tablet", "android", "amoled", "s-pen"]
    },
    {
        "id": "6",
        "name": "Apple iPad Air (M2)",
        "description": "Powerful M2 chip, 11-inch Liquid Retina display, USB-C, Apple Pencil Pro support, all-day battery.",
        "price": 59900,
        "category": "Tablets",
        "brand": "Apple",
        "rating": 4.8,
        "stock": 25,
        "tags": ["tablet", "ipad", "m2", "apple"]
    },
    {
        "id": "7",
        "name": "Levi's 501 Original Jeans",
        "description": "The iconic straight-leg, button-fly jeans. Made with 100% cotton denim in a classic dark wash.",
        "price": 4999,
        "category": "Clothing",
        "brand": "Levi's",
        "rating": 4.3,
        "stock": 120,
        "tags": ["jeans", "denim", "casual", "cotton"]
    },
    {
        "id": "8",
        "name": "Kindle Paperwhite (16 GB)",
        "description": "Waterproof, glare-free 6.8-inch display, 300 ppi, weeks of battery life, adjustable warm light.",
        "price": 12999,
        "category": "Electronics",
        "brand": "Amazon",
        "rating": 4.6,
        "stock": 60,
        "tags": ["ebook", "reader", "kindle", "waterproof"]
    },
    {
        "id": "9",
        "name": "Logitech MX Master 3S Mouse",
        "description": "8K DPI sensor works on any surface including glass. MagSpeed electromagnetic scroll wheel, USB-C charging.",
        "price": 8799,
        "category": "Accessories",
        "brand": "Logitech",
        "rating": 4.8,
        "stock": 35,
        "tags": ["mouse", "wireless", "ergonomic", "productivity"]
    },
    {
        "id": "10",
        "name": "Keychron K2 Pro Mechanical Keyboard",
        "description": "75% layout, hot-swappable, Bluetooth 5.1, compatible with Mac and Windows. RGB backlight.",
        "price": 9499,
        "category": "Accessories",
        "brand": "Keychron",
        "rating": 4.6,
        "stock": 28,
        "tags": ["keyboard", "mechanical", "wireless", "rgb"]
    },
    {
        "id": "11",
        "name": "OnePlus 12 5G",
        "description": "Snapdragon 8 Gen 3, 50MP Hasselblad triple camera, 100W SUPERVOOC charging, 6.82\" AMOLED display.",
        "price": 64999,
        "category": "Smartphones",
        "brand": "OnePlus",
        "rating": 4.4,
        "stock": 45,
        "tags": ["smartphone", "5g", "android", "oneplus"]
    },
    {
        "id": "12",
        "name": "Samsung Galaxy S24 Ultra",
        "description": "200MP camera, built-in S Pen, 6.8-inch QHD+ display, titanium frame, AI features.",
        "price": 129999,
        "category": "Smartphones",
        "brand": "Samsung",
        "rating": 4.7,
        "stock": 20,
        "tags": ["smartphone", "android", "camera", "s-pen"]
    },
    {
        "id": "13",
        "name": "boAt Airdopes 141 TWS",
        "description": "42H total playback, BEAST Mode low latency, ENx technology for clear calls, IPX4 water resistant.",
        "price": 999,
        "category": "Electronics",
        "brand": "boAt",
        "rating": 4.1,
        "stock": 200,
        "tags": ["earbuds", "tws", "bluetooth", "budget"]
    },
    {
        "id": "14",
        "name": "Puma Softride Running Shoes",
        "description": "Softride midsole for maximum cushioning. Breathable mesh upper, rubber outsole for grip.",
        "price": 3499,
        "category": "Footwear",
        "brand": "Puma",
        "rating": 4.0,
        "stock": 80,
        "tags": ["shoes", "running", "cushioning", "sports"]
    },
    {
        "id": "15",
        "name": "Lenovo IdeaPad Slim 5 Laptop",
        "description": "Intel Core i7 13th Gen, 16GB RAM, 512GB SSD, 15.6\" FHD IPS display, backlit keyboard.",
        "price": 72990,
        "category": "Laptops",
        "brand": "Lenovo",
        "rating": 4.3,
        "stock": 18,
        "tags": ["laptop", "intel", "i7", "ssd"]
    },
    {
        "id": "16",
        "name": "Apple MacBook Air M3",
        "description": "M3 chip, 13.6-inch Liquid Retina display, 18-hour battery life, fanless design, 8GB RAM.",
        "price": 114900,
        "category": "Laptops",
        "brand": "Apple",
        "rating": 4.9,
        "stock": 12,
        "tags": ["laptop", "macbook", "m3", "apple"]
    },
    {
        "id": "17",
        "name": "Fitbit Charge 6",
        "description": "Built-in GPS, heart rate monitoring, ECG app, sleep tracking, 7-day battery, Google Maps integration.",
        "price": 14999,
        "category": "Wearables",
        "brand": "Fitbit",
        "rating": 4.2,
        "stock": 55,
        "tags": ["fitness", "tracker", "gps", "health"]
    },
    {
        "id": "18",
        "name": "JBL Charge 5 Bluetooth Speaker",
        "description": "20 hours of playtime, IP67 waterproof and dustproof, PartyBoost, USB-C charging.",
        "price": 11999,
        "category": "Electronics",
        "brand": "JBL",
        "rating": 4.5,
        "stock": 42,
        "tags": ["speaker", "bluetooth", "waterproof", "portable"]
    },
    {
        "id": "19",
        "name": "Canon EOS R50 Mirrorless Camera",
        "description": "24.2MP APS-C sensor, 4K video, Dual Pixel CMOS AF II, compact and lightweight body.",
        "price": 74995,
        "category": "Cameras",
        "brand": "Canon",
        "rating": 4.5,
        "stock": 10,
        "tags": ["camera", "mirrorless", "4k", "photography"]
    },
    {
        "id": "20",
        "name": "IKEA MARKUS Ergonomic Chair",
        "description": "Adjustable lumbar support, breathable mesh back, seat height adjustment. Suitable for up to 10 hours of use.",
        "price": 22995,
        "category": "Furniture",
        "brand": "IKEA",
        "rating": 4.3,
        "stock": 8,
        "tags": ["chair", "ergonomic", "office", "mesh"]
    }
]


def main():
    print("Connecting to Elasticsearch...")
    es = get_es_client()

    if not es.ping():
        print("❌ Cannot connect to Elasticsearch. Is it running?")
        print("   Start it with: docker compose up -d")
        sys.exit(1)

    print("✅ Connected.")
    setup_indices(es)

    print(f"Indexing {len(SAMPLE_PRODUCTS)} products...")
    success, failed = index_products(es, SAMPLE_PRODUCTS)

    print(f"\n✅ Done! Indexed {success} products, {failed} failed.")
    print("\nTry searching:")
    print('  curl -X POST http://localhost:8000/api/products/search \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"query": "wireless headphones", "category": "Electronics"}\'')


if __name__ == "__main__":
    main()
