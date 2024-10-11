import sqlite3

def display_barcodes():
    conn = sqlite3.connect('barcodes1.db')
    c = conn.cursor()
    
    c.execute("SELECT Id, Product, Owner, Category, barcode, Tag, timestamp FROM products ORDER BY timestamp DESC")
    rows = c.fetchall()
    
    if not rows:
        print("No products found in the database.")
    else:
        print("ID\tProduct\t\tOwner\t\tCategory\tBarcode\t\tTag\t\tTimestamp")
        print("-" * 120)
        for row in rows:
            id, product, owner, category, barcode, tag, timestamp = row
            print(f"{id}\t{product[:15]:<15}\t{owner[:15]:<15}\t{category[:10]:<10}\t{barcode:<15}\t{tag:<15}\t{timestamp}")

    
    conn.close()

if __name__ == "__main__":
    display_barcodes()
