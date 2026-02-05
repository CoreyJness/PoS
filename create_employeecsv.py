import csv
import hashlib

def create_employees_csv(filename="employees.csv"):
    """Create employee database with PIN codes"""
    employees_data = [
        ['Employee_ID', 'Name', 'PIN_Hash', 'Role'],
        ['0001', 'Developer', hashlib.sha256('0000'.encode()).hexdigest(), 'Admin'],
        ['0002', 'John Doe', hashlib.sha256('1234'.encode()).hexdigest(), 'Cashier'],
        ['0003', 'Jane Smith', hashlib.sha256('5678'.encode()).hexdigest(), 'Manager']
    ]
    
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(employees_data)
    
    print(f"Employees CSV created: {filename}")
    print("Sample PINs: Developer=0000, John Doe=1234, Jane Smith=5678")

# Create the file
create_employees_csv()