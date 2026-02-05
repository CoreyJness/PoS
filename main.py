if __name__ == "__main__":
    # Import the classes from your main POS file
    from POS import EmployeeAuth, Inventory, Product
    from UI import POSUI
    import os
    
    # Check if CSV files exist, if not create them
    if not os.path.exists("employees.csv"):
        import csv
        import hashlib
        employees_data = [
            ['Employee_ID', 'Name', 'PIN_Hash', 'Role'],
            ['0001', 'Developer', hashlib.sha256('0000'.encode()).hexdigest(), 'Admin'],
            ['0002', 'John Doe', hashlib.sha256('1234'.encode()).hexdigest(), 'Cashier'],
            ['0003', 'Jane Smith', hashlib.sha256('5678'.encode()).hexdigest(), 'Manager']
        ]
        with open("employees.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(employees_data)
        print("Created employees.csv")
    
    if not os.path.exists("inventory.csv"):
        import csv
        inventory_data = [
            ['Ingredient', 'Quantity', 'Unit', 'Total_Price'],
            ['Flour', '50', 'lbs', '125.00'],
            ['Sugar', '30', 'lbs', '52.50'],
            ['Eggs', '120', 'whole', '30.00'],
            ['Butter', '20', 'lbs', '80.00'],
            ['Milk', '15', 'gallons', '52.50'],
            ['Vanilla Extract', '5', 'bottles', '40.00'],
            ['Baking Powder', '10', 'lbs', '32.50'],
            ['Salt', '25', 'lbs', '25.00'],
            ['Chocolate Chips', '15', 'lbs', '82.50'],
            ['Cocoa Powder', '8', 'lbs', '48.00']
        ]
        with open("inventory.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(inventory_data)
        print("Created inventory.csv")
    
    # Initialize system
    auth = EmployeeAuth()
    auth.load_employees()
    
    inv = Inventory(auth)
    inv.load_from_csv()
    
    # Start UI
    pos_ui = POSUI(auth, inv)
    
    # Add some sample products
    pos_ui.products["Chocolate Cake"] = Product("Chocolate Cake", {
        'Flour': 2.5,
        'Sugar': 1.5,
        'Eggs': 6,
        'Butter': 0.5,
        'Milk': 0.25
    })
    
    pos_ui.products["Vanilla Cupcakes"] = Product("Vanilla Cupcakes", {
        'Flour': 1.0,
        'Sugar': 0.75,
        'Eggs': 3,
        'Butter': 0.25,
        'Vanilla Extract': 0.1
    })
    
    pos_ui.run()
