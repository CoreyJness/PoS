import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os

KENTUCKY_SALES_TAX = 0.06  # 6% sales tax


class POSUI:
    def __init__(self, auth, inventory):
        self.auth = auth
        self.inventory = inventory
        self.products = {}  # Will store Product objects
        self.cart = []  # Current sale items
        
        self.root = tk.Tk()
        self.root.title("POS System")
        self.root.geometry("1200x800")
        
        # Start with login screen
        self.show_login_screen()
        
    def show_login_screen(self):
        """Display login screen"""
        self.clear_window()
        
        login_frame = tk.Frame(self.root, bg="#2c3e50")
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(login_frame, text="POS System Login", font=("Arial", 24, "bold"), 
                bg="#2c3e50", fg="white").pack(pady=20)
        
        tk.Label(login_frame, text="Enter 4-Digit PIN:", font=("Arial", 14), 
                bg="#2c3e50", fg="white").pack(pady=10)
        
        pin_entry = tk.Entry(login_frame, font=("Arial", 18), show="*", width=10, justify="center")
        pin_entry.pack(pady=10)
        pin_entry.focus()
        
        error_label = tk.Label(login_frame, text="", font=("Arial", 12), 
                              bg="#2c3e50", fg="#e74c3c")
        error_label.pack(pady=5)
        
        def attempt_login():
            pin = pin_entry.get()
            if self.auth.login(pin):
                self.show_main_screen()
            else:
                error_label.config(text="Invalid PIN. Try again.")
                pin_entry.delete(0, tk.END)
        
        tk.Button(login_frame, text="Login", font=("Arial", 14), bg="#27ae60", 
                 fg="white", command=attempt_login, width=15).pack(pady=10)
        
        pin_entry.bind("<Return>", lambda e: attempt_login())
    
    def show_main_screen(self):
        """Display main POS interface"""
        self.clear_window()
        
        # Header
        header = tk.Frame(self.root, bg="#34495e", height=60)
        header.pack(fill="x")
        
        tk.Label(header, text=f"Welcome, {self.auth.get_current_user_name()}", 
                font=("Arial", 16), bg="#34495e", fg="white").pack(side="left", padx=20, pady=10)
        
        tk.Button(header, text="Logout", font=("Arial", 12), bg="#e74c3c", 
                 fg="white", command=self.logout).pack(side="right", padx=20, pady=10)
        
        if self.auth.is_admin():
            tk.Button(header, text="Manage Inventory", font=("Arial", 12), bg="#3498db", 
                     fg="white", command=self.show_inventory_screen).pack(side="right", padx=5, pady=10)
            
            tk.Button(header, text="Manage Products", font=("Arial", 12), bg="#9b59b6", 
                     fg="white", command=self.show_product_management).pack(side="right", padx=5, pady=10)
        
        # Main content area
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)
        
        # Left side - Products
        left_frame = tk.Frame(main_frame, bg="#ecf0f1")
        left_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(left_frame, text="Products", font=("Arial", 18, "bold"), 
                bg="#ecf0f1").pack(pady=10)
        
        # Product grid
        product_scroll = tk.Canvas(left_frame, bg="#ecf0f1")
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=product_scroll.yview)
        product_frame = tk.Frame(product_scroll, bg="#ecf0f1")
        
        product_scroll.create_window((0, 0), window=product_frame, anchor="nw")
        product_scroll.configure(yscrollcommand=scrollbar.set)
        
        product_scroll.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Display products
        self.display_products(product_frame)
        
        product_frame.update_idletasks()
        product_scroll.configure(scrollregion=product_scroll.bbox("all"))
        
        # Right side - Cart and Payment
        right_frame = tk.Frame(main_frame, bg="#bdc3c7", width=400)
        right_frame.pack(side="right", fill="both")
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="Current Sale", font=("Arial", 18, "bold"), 
                bg="#bdc3c7").pack(pady=10)
        
        # Cart display
        cart_frame = tk.Frame(right_frame, bg="white")
        cart_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.cart_text = tk.Text(cart_frame, font=("Arial", 12), state="disabled", 
                                bg="white", relief="flat")
        self.cart_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Total display
        self.total_label = tk.Label(right_frame, text="Subtotal: $0.00\nTax (6%): $0.00\nTotal: $0.00", 
                                    font=("Arial", 14, "bold"), bg="#bdc3c7", justify="left")
        self.total_label.pack(pady=10)
        
        # Payment buttons
        button_frame = tk.Frame(right_frame, bg="#bdc3c7")
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Cash Payment", font=("Arial", 14), bg="#27ae60", 
                 fg="white", command=self.process_cash_payment, width=15).pack(pady=5)
        
        tk.Button(button_frame, text="Card Payment", font=("Arial", 14), bg="#3498db", 
                 fg="white", command=self.process_card_payment, width=15).pack(pady=5)
        
        tk.Button(button_frame, text="Clear Cart", font=("Arial", 14), bg="#e74c3c", 
                 fg="white", command=self.clear_cart, width=15).pack(pady=5)
    
    def display_products(self, parent_frame):
        """Display product buttons in a grid"""
        row = 0
        col = 0
        max_cols = 3
        
        for product_name, product in self.products.items():
            product_btn = tk.Button(parent_frame, text=product_name, font=("Arial", 14), 
                                   bg="#3498db", fg="white", width=15, height=3,
                                   command=lambda p=product: self.add_to_cart(p))
            product_btn.grid(row=row, column=col, padx=10, pady=10)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def add_to_cart(self, product):
        """Add product to cart"""
        try:
            cost = product.calculate_total_cost(self.inventory)
            price = product.calculate_msrp(self.inventory)
            
            self.cart.append({
                'product': product,
                'name': product.name,
                'price': price
            })
            
            self.update_cart_display()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def update_cart_display(self):
        """Update the cart display"""
        self.cart_text.config(state="normal")
        self.cart_text.delete(1.0, tk.END)
        
        for i, item in enumerate(self.cart, 1):
            self.cart_text.insert(tk.END, f"{i}. {item['name']:<20} ${item['price']:.2f}\n")
        
        self.cart_text.config(state="disabled")
        
        # Calculate totals
        subtotal = sum(item['price'] for item in self.cart)
        tax = subtotal * KENTUCKY_SALES_TAX
        total = subtotal + tax
        
        self.total_label.config(text=f"Subtotal: ${subtotal:.2f}\nTax (6%): ${tax:.2f}\nTotal: ${total:.2f}")
    
    def clear_cart(self):
        """Clear all items from cart"""
        self.cart = []
        self.update_cart_display()
    
    def process_cash_payment(self):
        """Process cash payment with change calculation"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "No items in cart")
            return
        
        subtotal = sum(item['price'] for item in self.cart)
        tax = subtotal * KENTUCKY_SALES_TAX
        total = subtotal + tax
        
        # Ask for cash amount
        cash_received = simpledialog.askfloat("Cash Payment", 
                                             f"Total: ${total:.2f}\n\nEnter cash received:",
                                             minvalue=total)
        
        if cash_received is None:
            return
        
        if cash_received < total:
            messagebox.showerror("Insufficient Payment", 
                               f"Need ${total:.2f}, received ${cash_received:.2f}")
            return
        
        change = cash_received - total
        
        # Process sale
        self.complete_sale()
        
        # Show change
        messagebox.showinfo("Payment Complete", 
                          f"Total: ${total:.2f}\nCash Received: ${cash_received:.2f}\n\nCHANGE: ${change:.2f}")
    
    def process_card_payment(self):
        """Process card payment"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "No items in cart")
            return
        
        subtotal = sum(item['price'] for item in self.cart)
        tax = subtotal * KENTUCKY_SALES_TAX
        total = subtotal + tax
        
        if messagebox.askyesno("Card Payment", 
                              f"Total: ${total:.2f}\n\nProcess card payment?"):
            self.complete_sale()
            messagebox.showinfo("Payment Complete", f"Card payment of ${total:.2f} approved!")
    
    def complete_sale(self):
        """Finalize sale and deduct inventory"""
        for item in self.cart:
            try:
                item['product'].sell(self.inventory)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {item['name']}: {e}")
        
        # Save inventory
        self.inventory.save_to_csv()
        
        # Clear cart
        self.clear_cart()
    
    def show_inventory_screen(self):
        """Show inventory management screen"""
        inv_window = tk.Toplevel(self.root)
        inv_window.title("Inventory Management")
        inv_window.geometry("900x600")
        
        # Display current inventory
        tree_frame = tk.Frame(inv_window)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Ingredient", "Quantity", "Unit", "Total Price", "Price/Unit")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        for name, details in self.inventory.ingredients.items():
            tree.insert("", "end", values=(
                name,
                f"{details['quantity']:.1f}",
                details['unit'],
                f"${details['total_price']:.2f}",
                f"${details['price_per_unit']:.2f}"
            ))
        
        tree.pack(fill="both", expand=True)
        
        # Buttons
        btn_frame = tk.Frame(inv_window)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Add from Receipt", font=("Arial", 12), 
                 bg="#27ae60", fg="white", command=lambda: self.add_receipt_dialog(inv_window)).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Add/Update Manually", font=("Arial", 12), 
                 bg="#3498db", fg="white", command=lambda: self.add_ingredient_dialog(inv_window)).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Refresh", font=("Arial", 12), 
                 bg="#95a5a6", fg="white", command=lambda: self.show_inventory_screen()).pack(side="left", padx=5)
    
    def add_receipt_dialog(self, parent):
        """Dialog to add inventory from receipt"""
        dialog = tk.Toplevel(parent)
        dialog.title("Add from Receipt")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="Ingredient Name:", font=("Arial", 12)).pack(pady=5)
        name_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Quantity:", font=("Arial", 12)).pack(pady=5)
        qty_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        qty_entry.pack(pady=5)
        
        tk.Label(dialog, text="Total Price:", font=("Arial", 12)).pack(pady=5)
        price_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        price_entry.pack(pady=5)
        
        def submit():
            try:
                name = name_entry.get()
                qty = float(qty_entry.get())
                price = float(price_entry.get())
                
                self.inventory.update_from_receipt(name, qty, price)
                self.inventory.save_to_csv()
                
                messagebox.showinfo("Success", f"Updated {name} from receipt")
                dialog.destroy()
                self.show_inventory_screen()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(dialog, text="Submit", font=("Arial", 12), bg="#27ae60", 
                 fg="white", command=submit).pack(pady=20)
    
    def add_ingredient_dialog(self, parent):
        """Dialog to add new ingredient"""
        dialog = tk.Toplevel(parent)
        dialog.title("Add New Ingredient")
        dialog.geometry("400x350")
        
        tk.Label(dialog, text="Ingredient Name:", font=("Arial", 12)).pack(pady=5)
        name_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Quantity:", font=("Arial", 12)).pack(pady=5)
        qty_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        qty_entry.pack(pady=5)
        
        tk.Label(dialog, text="Unit (lbs, gallons, etc.):", font=("Arial", 12)).pack(pady=5)
        unit_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        unit_entry.pack(pady=5)
        
        tk.Label(dialog, text="Total Price:", font=("Arial", 12)).pack(pady=5)
        price_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        price_entry.pack(pady=5)
        
        def submit():
            try:
                name = name_entry.get()
                qty = float(qty_entry.get())
                unit = unit_entry.get()
                price = float(price_entry.get())
                
                self.inventory.add_ingredient(name, qty, price, unit)
                self.inventory.save_to_csv()
                
                messagebox.showinfo("Success", f"Added {name}")
                dialog.destroy()
                self.show_inventory_screen()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(dialog, text="Submit", font=("Arial", 12), bg="#27ae60", 
                 fg="white", command=submit).pack(pady=20)
    
    def show_product_management(self):
        """Show product/recipe management screen"""
        prod_window = tk.Toplevel(self.root)
        prod_window.title("Product Management")
        prod_window.geometry("600x400")
        
        tk.Label(prod_window, text="Current Products", font=("Arial", 16, "bold")).pack(pady=10)
        
        # List current products
        listbox = tk.Listbox(prod_window, font=("Arial", 12), height=15)
        listbox.pack(fill="both", expand=True, padx=20, pady=10)
        
        for product_name in self.products.keys():
            listbox.insert(tk.END, product_name)
        
        tk.Button(prod_window, text="Add New Product", font=("Arial", 12), 
                 bg="#27ae60", fg="white", command=self.add_product_dialog).pack(pady=10)
    
    def add_product_dialog(self):
        """Dialog to add new product/recipe"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Product")
        dialog.geometry("500x500")
        
        tk.Label(dialog, text="Product Name:", font=("Arial", 12)).pack(pady=5)
        name_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Recipe (Ingredient: Quantity):", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Recipe entry area
        recipe_frame = tk.Frame(dialog)
        recipe_frame.pack(pady=5)
        
        recipe_entries = []
        
        def add_ingredient_row():
            row_frame = tk.Frame(recipe_frame)
            row_frame.pack(pady=2)
            
            # Dropdown for ingredient
            ingredient_var = tk.StringVar()
            ingredient_dropdown = ttk.Combobox(row_frame, textvariable=ingredient_var, 
                                              values=self.inventory.get_ingredient_names(), 
                                              width=20, font=("Arial", 10))
            ingredient_dropdown.pack(side="left", padx=5)
            
            qty_entry = tk.Entry(row_frame, font=("Arial", 10), width=10)
            qty_entry.pack(side="left", padx=5)
            
            recipe_entries.append((ingredient_var, qty_entry))
        
        # Add first row
        add_ingredient_row()
        
        tk.Button(dialog, text="+ Add Ingredient", font=("Arial", 10), 
                 command=add_ingredient_row).pack(pady=5)
        
        def submit():
            try:
                product_name = name_entry.get()
                if not product_name:
                    raise ValueError("Product name required")
                
                recipe = {}
                for ing_var, qty_entry in recipe_entries:
                    ing = ing_var.get()
                    qty = qty_entry.get()
                    if ing and qty:
                        recipe[ing] = float(qty)
                
                if not recipe:
                    raise ValueError("Recipe must have at least one ingredient")
                
                # Create product
                new_product = Product(product_name, recipe)
                self.products[product_name] = new_product
                
                messagebox.showinfo("Success", f"Added product: {product_name}")
                dialog.destroy()
                self.show_main_screen()  # Refresh to show new product
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(dialog, text="Create Product", font=("Arial", 12), bg="#27ae60", 
                 fg="white", command=submit).pack(pady=20)
    
    def logout(self):
        """Logout current user"""
        self.auth.logout()
        self.show_login_screen()
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def run(self):
        """Start the UI"""
        self.root.mainloop()


