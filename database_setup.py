import sqlite3

def setup_database():
    conn = sqlite3.connect('barcodes1.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (Id INTEGER PRIMARY KEY AUTOINCREMENT, Product TEXT, 
              Owner TEXT, Category TEXT, Serial_no TEXT DEFAULT 'None', 
              barcode TEXT, Tag TEXT, details TEXT, timestamp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS product_movement
                 (Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ProductId INTEGER,
                  status TEXT,
                  Timestamp TEXT,
                  FOREIGN KEY (ProductId) REFERENCES products(Id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (Id INTEGER PRIMARY KEY AUTOINCREMENT, Email TEXT, Name TEXT, Password TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (Id INTEGER PRIMARY KEY AUTOINCREMENT,
                  Name TEXT,
                  Reg_no TEXT UNIQUE,
                  gender TEXT,
                  Department TEXT,
                  Program TEXT,
                  Card TEXT)''')

    # Insert sample data into the user table
    c.execute("INSERT OR IGNORE INTO users (Email, Name, Password) VALUES (?, ?, ?)",
              ('admin@gmail.com', 'Kamana jean', 'admin123'))

    conn.commit()
    conn.close()
    print("Database and tables created successfully. Sample user data inserted.")

if __name__ == "__main__":
    setup_database()
