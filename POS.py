import csv
import hashlib
import datetime
import json
import os

class Inventory:
    def __init__(self, auth_system):
        self.ingredients = {}
        self.auth = auth_system
        
    def _require_login(self):
        """Check if user is logged in before allowing actions"""
        if not self.auth.is_logged_in():
            raise PermissionError("You must be logged in to perform this action")
        return self.auth.get_current_user_name()
    
    def load_from_csv(self, filename="inventory.csv"):
        """Load inventory from CSV file"""
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row['Ingredient']
                quantity = float(row['Quantity'])
                total_price = float(row['Total_Price'])
                
                # Calculate price per unit automatically
                price_per_unit = total_price / quantity if quantity > 0 else 0
                
                self.ingredients[name] = {
                    'quantity': quantity,
                    'total_price': total_price,
                    'price_per_unit': price_per_unit,
                    'unit': row['Unit']
                }
        print(f"Loaded {len(self.ingredients)} ingredients from {filename}")
    
    def save_to_csv(self, filename="inventory.csv"):
        """Save current inventory to CSV file"""
        with open(filename, 'w', newline='') as file:
            fieldnames = ['Ingredient', 'Quantity', 'Unit', 'Total_Price']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for name, details in self.ingredients.items():
                writer.writerow({
                    'Ingredient': name,
                    'Quantity': details['quantity'],
                    'Unit': details['unit'],
                    'Total_Price': f"{details['total_price']:.2f}"
                })
        print(f"Saved inventory to {filename}")
    
    def get_ingredient_names(self):
        """Return list of ingredient names for dropdowns"""
        return sorted(list(self.ingredients.keys()))
    
    def add_ingredient(self, name, quantity, total_price, unit):
        """Add or update ingredient - workers just enter quantity and total price"""
        employee_name = self._require_login()
        
        price_per_unit = total_price / quantity if quantity > 0 else 0
        
        self.ingredients[name] = {
            'quantity': quantity,
            'total_price': total_price,
            'price_per_unit': price_per_unit,
            'unit': unit
        }
        
        self.log_transaction(
            action="ADD_INGREDIENT",
            employee=employee_name,
            details=f"{name}: {quantity} {unit} for ${total_price:.2f}"
        )
        print(f"Added {name}: {quantity} {unit} for ${total_price:.2f} (${price_per_unit:.2f} per {unit})")
        
    def update_quantity(self, name, new_quantity):
        """Update quantity - recalculates price per unit"""
        employee_name = self._require_login()
        
        if name in self.ingredients:
            old_quantity = self.ingredients[name]['quantity']
            self.ingredients[name]['quantity'] = new_quantity
            
            # Recalculate price per unit with new quantity
            if new_quantity > 0:
                self.ingredients[name]['price_per_unit'] = self.ingredients[name]['total_price'] / new_quantity
            else:
                self.ingredients[name]['price_per_unit'] = 0
            
            self.log_transaction(
                action="UPDATE_QUANTITY",
                employee=employee_name,
                details=f"{name}: {old_quantity} → {new_quantity} {self.ingredients[name]['unit']}"
            )
            print(f"Updated {name}: {new_quantity} {self.ingredients[name]['unit']}")
        else:
            print(f"Ingredient '{name}' not found")
    
    def update_from_receipt(self, name, quantity, total_price, receipt_image_path=None):
        """Update ingredient from a new receipt/purchase"""
        employee_name = self._require_login()
        
        if name in self.ingredients:
            old_quantity = self.ingredients[name]['quantity']
            # Add new quantity and price to existing
            self.ingredients[name]['quantity'] += quantity
            self.ingredients[name]['total_price'] += total_price
            # Recalculate average price per unit
            self.ingredients[name]['price_per_unit'] = self.ingredients[name]['total_price'] / self.ingredients[name]['quantity']
            
            details = f"{name}: +{quantity} {self.ingredients[name]['unit']} for ${total_price:.2f} (total now: {self.ingredients[name]['quantity']})"
            if receipt_image_path:
                details += f" | Receipt: {receipt_image_path}"
            
            self.log_transaction(
                action="RECEIPT_UPDATE",
                employee=employee_name,
                details=details
            )
            print(f"Updated {name} from receipt: +{quantity} {self.ingredients[name]['unit']} for ${total_price:.2f}")
        else:
            # New ingredient - need to get unit
            self.add_ingredient(name, quantity, total_price, "units")
    
    def deduct_ingredients(self, ingredient_usage, employee_name):
        """Deduct ingredients from inventory (called when product is sold)"""
        # First check if all ingredients are available
        for ingredient, qty_needed in ingredient_usage.items():
            if ingredient not in self.ingredients:
                raise ValueError(f"Ingredient '{ingredient}' not found in inventory")
            if self.ingredients[ingredient]['quantity'] < qty_needed:
                raise ValueError(f"Not enough {ingredient} in stock. Need {qty_needed}, have {self.ingredients[ingredient]['quantity']}")
        
        # Deduct all ingredients
        for ingredient, qty_needed in ingredient_usage.items():
            old_qty = self.ingredients[ingredient]['quantity']
            self.ingredients[ingredient]['quantity'] -= qty_needed
            
            # Recalculate total_price proportionally
            if old_qty > 0:
                self.ingredients[ingredient]['total_price'] = (self.ingredients[ingredient]['quantity'] / old_qty) * self.ingredients[ingredient]['total_price']
            
            self.log_transaction(
                action="DEDUCT_INGREDIENT",
                employee=employee_name,
                details=f"{ingredient}: -{qty_needed} {self.ingredients[ingredient]['unit']} (remaining: {self.ingredients[ingredient]['quantity']})"
            )
    
    def log_transaction(self, action, employee, details):
        """Log all inventory transactions with timestamp and employee"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('transaction_log.txt', 'a') as log:
            log.write(f"{timestamp} | {employee:<15} | {action:<20} | {details}\n")
    
    def display_inventory(self):
        """Display current inventory"""
        print("\n=== Current Inventory ===")
        print(f"{'Ingredient':<20} {'Quantity':<10} {'Unit':<10} {'Total $':<12} {'$/Unit':<10}")
        print("-" * 65)
        for name, details in self.ingredients.items():
            print(f"{name:<20} {details['quantity']:<10.1f} {details['unit']:<10} ${details['total_price']:<11.2f} ${details['price_per_unit']:<9.2f}")
        print()
    
    def generate_inventory_report(self):
        """Generate inventory report data"""
        report = []
        total_value = 0
        
        for name, details in sorted(self.ingredients.items()):
            item_value = details['total_price']
            total_value += item_value
            
            report.append({
                'ingredient': name,
                'quantity': details['quantity'],
                'unit': details['unit'],
                'price_per_unit': details['price_per_unit'],
                'total_price': item_value
            })
        
        return report, total_value


class Product:
    def __init__(self, name, recipe):
        self.name = name
        self.recipe = recipe
        
    def calculate_total_cost(self, inventory):
        """Calculate cost based on current ingredient prices in inventory"""
        total = 0
        for ingredient, qty_needed in self.recipe.items():
            if ingredient in inventory.ingredients:
                unit_price = inventory.ingredients[ingredient]['price_per_unit']
                total += unit_price * qty_needed
            else:
                raise ValueError(f"Ingredient '{ingredient}' not found in inventory")
        return total
        
    def calculate_msrp(self, inventory, markup=3.0):
        """Calculate selling price with markup"""
        cost = self.calculate_total_cost(inventory)
        return cost * markup
    
    def sell(self, inventory):
        """Record a sale - deducts ingredients from inventory"""
        employee_name = inventory._require_login()
        
        try:
            inventory.deduct_ingredients(self.recipe, employee_name)
            
            # Log the sale
            cost = self.calculate_total_cost(inventory)
            price = self.calculate_msrp(inventory)
            inventory.log_transaction(
                action="PRODUCT_SOLD",
                employee=employee_name,
                details=f"{self.name} sold for ${price:.2f} (cost: ${cost:.2f})"
            )
            
            print(f"✓ Sold {self.name} for ${price:.2f}")
            return price
        except ValueError as e:
            print(f"✗ Cannot sell {self.name}: {e}")
            return None      


class DailySales:
    """Track daily sales and cash register"""
    def __init__(self):
        self.sales_file = "daily_sales.json"
        self.load_sales()
    
    def load_sales(self):
        """Load sales data from file"""
        if os.path.exists(self.sales_file):
            with open(self.sales_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {}
    
    def save_sales(self):
        """Save sales data to file"""
        with open(self.sales_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_today_key(self):
        """Get today's date as key"""
        return datetime.date.today().strftime("%Y-%m-%d")
    
    def initialize_day(self):
        """Initialize today's sales data"""
        today = self.get_today_key()
        if today not in self.data:
            self.data[today] = {
                'total_sales': 0.0,
                'total_cash': 0.0,
                'total_card': 0.0,
                'transaction_count': 0,
                'transactions': []
            }
            self.save_sales()
    
    def record_sale(self, amount, payment_type, employee, items):
        """Record a sale transaction"""
        self.initialize_day()
        today = self.get_today_key()
        
        self.data[today]['total_sales'] += amount
        self.data[today]['transaction_count'] += 1
        
        if payment_type == 'cash':
            self.data[today]['total_cash'] += amount
        elif payment_type == 'card':
            self.data[today]['total_card'] += amount
        
        # Record transaction details
        transaction = {
            'time': datetime.datetime.now().strftime("%H:%M:%S"),
            'amount': amount,
            'payment_type': payment_type,
            'employee': employee,
            'items': items
        }
        self.data[today]['transactions'].append(transaction)
        
        self.save_sales()
    
    def get_today_totals(self):
        """Get today's sales totals"""
        self.initialize_day()
        today = self.get_today_key()
        return self.data[today]
    
    def get_end_of_day_report(self):
        """Generate end of day report"""
        today = self.get_today_key()
        if today in self.data:
            return self.data[today]
        return None


class EmployeeAuth:
    def __init__(self):
        self.employees = {}
        self.current_user = None
        
    def load_employees(self, filename="employees.csv"):
        """Load employee data from CSV"""
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                emp_id = row['Employee_ID']
                self.employees[emp_id] = {
                    'name': row['Name'],
                    'pin_hash': row['PIN_Hash'],
                    'role': row['Role']
                }
        print(f"Loaded {len(self.employees)} employees")
    
    def hash_pin(self, pin):
        """Hash a PIN for secure storage/comparison"""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def login(self, pin):
        """Authenticate employee with 4-digit PIN"""
        if len(pin) != 4 or not pin.isdigit():
            print("❌ Invalid PIN format. Must be 4 digits.")
            return False
        
        pin_hash = self.hash_pin(pin)
        
        # Search for matching PIN
        for emp_id, details in self.employees.items():
            if details['pin_hash'] == pin_hash:
                self.current_user = {
                    'id': emp_id,
                    'name': details['name'],
                    'role': details['role']
                }
                print(f"✓ Welcome, {details['name']} ({details['role']})")
                self.log_login()
                return True
        
        print("❌ Invalid PIN. Access denied.")
        return False
    
    def logout(self):
        """Log out current user"""
        if self.current_user:
            print(f"Logged out: {self.current_user['name']}")
            self.log_logout()
            self.current_user = None
        else:
            print("No user currently logged in")
    
    def is_logged_in(self):
        """Check if someone is logged in"""
        return self.current_user is not None
    
    def get_current_user_name(self):
        """Get name of current logged-in user"""
        if self.current_user:
            return self.current_user['name']
        return "Unknown"
    
    def get_current_user_role(self):
        """Get role of current logged-in user"""
        if self.current_user:
            return self.current_user['role']
        return None
    
    def is_admin(self):
        """Check if current user is admin"""
        return self.current_user and self.current_user['role'] == 'Admin'
    
    def is_manager_or_admin(self):
        """Check if current user is manager or admin"""
        return self.current_user and self.current_user['role'] in ['Admin', 'Manager']
    
    def log_login(self):
        """Log employee login"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('employee_log.txt', 'a') as log:
            log.write(f"{timestamp} | LOGIN  | {self.current_user['name']} ({self.current_user['id']})\n")
    
    def log_logout(self):
        """Log employee logout"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('employee_log.txt', 'a') as log:
            log.write(f"{timestamp} | LOGOUT | {self.current_user['name']} ({self.current_user['id']})\n")
    
    def add_employee(self, name, pin, role="Cashier"):
        """Add new employee (admin only)"""
        if not self.is_admin():
            print("❌ Only admins can add employees")
            return False
        
        if len(pin) != 4 or not pin.isdigit():
            print("❌ PIN must be 4 digits")
            return False
        
        # Generate new employee ID
        emp_ids = [int(emp_id) for emp_id in self.employees.keys()]
        new_id = f"{max(emp_ids) + 1:04d}"
        
        self.employees[new_id] = {
            'name': name,
            'pin_hash': self.hash_pin(pin),
            'role': role
        }
        
        # Save to CSV
        self.save_employees()
        print(f"✓ Added employee: {name} (ID: {new_id}, PIN: {pin})")
        return True
    
    def save_employees(self, filename="employees.csv"):
        """Save employees back to CSV"""
        with open(filename, 'w', newline='') as file:
            fieldnames = ['Employee_ID', 'Name', 'PIN_Hash', 'Role']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for emp_id, details in self.employees.items():
                writer.writerow({
                    'Employee_ID': emp_id,
                    'Name': details['name'],
                    'PIN_Hash': details['pin_hash'],
                    'Role': details['role']
                })
    def __init__(self):
        self.employees = {}
        self.current_user = None
        
    def load_employees(self, filename="employees.csv"):
        """Load employee data from CSV"""
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                emp_id = row['Employee_ID']
                self.employees[emp_id] = {
                    'name': row['Name'],
                    'pin_hash': row['PIN_Hash'],
                    'role': row['Role']
                }
        print(f"Loaded {len(self.employees)} employees")
    
    def hash_pin(self, pin):
        """Hash a PIN for secure storage/comparison"""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def login(self, pin):
        """Authenticate employee with 4-digit PIN"""
        if len(pin) != 4 or not pin.isdigit():
            print("❌ Invalid PIN format. Must be 4 digits.")
            return False
        
        pin_hash = self.hash_pin(pin)
        
        # Search for matching PIN
        for emp_id, details in self.employees.items():
            if details['pin_hash'] == pin_hash:
                self.current_user = {
                    'id': emp_id,
                    'name': details['name'],
                    'role': details['role']
                }
                print(f"✓ Welcome, {details['name']} ({details['role']})")
                self.log_login()
                return True
        
        print("❌ Invalid PIN. Access denied.")
        return False
    
    def logout(self):
        """Log out current user"""
        if self.current_user:
            print(f"Logged out: {self.current_user['name']}")
            self.log_logout()
            self.current_user = None
        else:
            print("No user currently logged in")
    
    def is_logged_in(self):
        """Check if someone is logged in"""
        return self.current_user is not None
    
    def get_current_user_name(self):
        """Get name of current logged-in user"""
        if self.current_user:
            return self.current_user['name']
        return "Unknown"
    
    def is_admin(self):
        """Check if current user is admin"""
        return self.current_user and self.current_user['role'] == 'Admin'
    
    def log_login(self):
        """Log employee login"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('employee_log.txt', 'a') as log:
            log.write(f"{timestamp} | LOGIN  | {self.current_user['name']} ({self.current_user['id']})\n")
    
    def log_logout(self):
        """Log employee logout"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('employee_log.txt', 'a') as log:
            log.write(f"{timestamp} | LOGOUT | {self.current_user['name']} ({self.current_user['id']})\n")
    
    def add_employee(self, name, pin, role="Cashier"):
        """Add new employee (admin only)"""
        if not self.is_admin():
            print("❌ Only admins can add employees")
            return False
        
        if len(pin) != 4 or not pin.isdigit():
            print("❌ PIN must be 4 digits")
            return False
        
        # Generate new employee ID
        emp_ids = [int(emp_id) for emp_id in self.employees.keys()]
        new_id = f"{max(emp_ids) + 1:04d}"
        
        self.employees[new_id] = {
            'name': name,
            'pin_hash': self.hash_pin(pin),
            'role': role
        }
        
        # Save to CSV
        self.save_employees()
        print(f"✓ Added employee: {name} (ID: {new_id}, PIN: {pin})")
        return True
    
    def save_employees(self, filename="employees.csv"):
        """Save employees back to CSV"""
        with open(filename, 'w', newline='') as file:
            fieldnames = ['Employee_ID', 'Name', 'PIN_Hash', 'Role']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for emp_id, details in self.employees.items():
                writer.writerow({
                    'Employee_ID': emp_id,
                    'Name': details['name'],
                    'PIN_Hash': details['pin_hash'],
                    'Role': details['role']
                })