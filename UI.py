import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
import os
import shutil
from datetime import datetime

KENTUCKY_SALES_TAX = 0.06  # 6% sales tax


class POSUI:
    def __init__(self, auth, inventory, daily_sales):
        self.auth = auth
        self.inventory = inventory
        self.daily_sales = daily_sales
        self.products = {}  # Will store Product objects
        self.recipes = {}  # Store recipes separately for management
        self.cart = []  # Current sale items
        
        self.root = tk.Tk()
        self.root.title("POS System")
        self.root.geometry("1200x800")
        
        # Create receipts directory if it doesn't exist
        if not os.path.exists("receipts"):
            os.makedirs("receipts")
        
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
        
        # Admin/Manager buttons
        if self.auth.is_manager_or_admin():
            tk.Button(header, text="End of Day Report", font=("Arial", 12), bg="#e67e22", 
                     fg="white", command=self.show_end_of_day_report).pack(side="right", padx=5, pady=10)
            
            tk.Button(header, text="Inventory Report", font=("Arial", 12), bg="#16a085", 
                     fg="white", command=self.show_inventory_report).pack(side="right", padx=5, pady=10)
            
            tk.Button(header, text="Manage Inventory", font=("Arial", 12), bg="#3498db", 
                     fg="white", command=self.show_inventory_screen).pack(side="right", padx=5, pady=10)
            
            tk.Button(header, text="Manage Recipes", font=("Arial", 12), bg="#9b59b6", 
                     fg="white", command=self.show_recipe_management).pack(side="right", padx=5, pady=10)
        
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
        """Process cash payment"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to cart first")
            return
        
        subtotal = sum(item['price'] for item in self.cart)
        tax = subtotal * KENTUCKY_SALES_TAX
        total = subtotal + tax
        
        # Ask for cash amount
        cash_received = simpledialog.askfloat("Cash Payment", 
                                             f"Total: ${total:.2f}\nEnter cash received:")
        
        if cash_received is None:
            return
        
        if cash_received < total:
            messagebox.showerror("Insufficient Funds", 
                               f"Need ${total:.2f}, received ${cash_received:.2f}")
            return
        
        change = cash_received - total
        
        # Process sale
        self.complete_sale(total, 'cash')
        
        messagebox.showinfo("Payment Complete", 
                          f"Total: ${total:.2f}\nCash: ${cash_received:.2f}\nChange: ${change:.2f}")
    
    def process_card_payment(self):
        """Process card payment"""
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Please add items to cart first")
            return
        
        subtotal = sum(item['price'] for item in self.cart)
        tax = subtotal * KENTUCKY_SALES_TAX
        total = subtotal + tax
        
        # Simulate card processing
        response = messagebox.askyesno("Card Payment", 
                                      f"Total: ${total:.2f}\nProcess card payment?")
        
        if response:
            self.complete_sale(total, 'card')
            messagebox.showinfo("Payment Complete", f"Card payment of ${total:.2f} processed")
    
    def complete_sale(self, total, payment_type):
        """Complete the sale and update inventory"""
        try:
            # Deduct ingredients from inventory for each product
            for item in self.cart:
                item['product'].sell(self.inventory)
            
            # Save inventory
            self.inventory.save_to_csv()
            
            # Record sale in daily sales
            items_sold = [item['name'] for item in self.cart]
            self.daily_sales.record_sale(total, payment_type, 
                                        self.auth.get_current_user_name(), 
                                        items_sold)
            
            # Clear cart
            self.clear_cart()
            
        except Exception as e:
            messagebox.showerror("Error", f"Sale failed: {str(e)}")
    
    def show_inventory_screen(self):
        """Display inventory management screen"""
        inv_window = tk.Toplevel(self.root)
        inv_window.title("Inventory Management")
        inv_window.geometry("900x600")
        
        tk.Label(inv_window, text="Current Inventory", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Inventory table
        tree_frame = tk.Frame(inv_window)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = ("Ingredient", "Quantity", "Unit", "Price/Unit", "Total Price")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                           yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        for name, details in sorted(self.inventory.ingredients.items()):
            tree.insert("", "end", values=(
                name,
                f"{details['quantity']:.1f}",
                details['unit'],
                f"${details['price_per_unit']:.2f}",
                f"${details['total_price']:.2f}"
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
        """Dialog to add inventory from receipt with image upload"""
        dialog = tk.Toplevel(parent)
        dialog.title("Add from Receipt")
        dialog.geometry("500x500")
        
        # Receipt image upload
        receipt_image_path = tk.StringVar()
        
        tk.Label(dialog, text="Upload Receipt Image (Optional):", font=("Arial", 12, "bold")).pack(pady=10)
        
        image_frame = tk.Frame(dialog)
        image_frame.pack(pady=5)
        
        image_label = tk.Label(image_frame, text="No image selected", bg="#ecf0f1", 
                              width=40, height=3, relief="sunken")
        image_label.pack()
        
        def upload_receipt_image():
            filename = filedialog.askopenfilename(
                title="Select Receipt Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"), ("All files", "*.*")]
            )
            if filename:
                # Copy to receipts folder with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = os.path.splitext(filename)[1]
                new_filename = f"receipt_{timestamp}{ext}"
                new_path = os.path.join("receipts", new_filename)
                shutil.copy(filename, new_path)
                receipt_image_path.set(new_path)
                image_label.config(text=f"✓ {new_filename}")
        
        tk.Button(image_frame, text="Upload Receipt Image", font=("Arial", 10), 
                 bg="#3498db", fg="white", command=upload_receipt_image).pack(pady=5)
        
        # Ingredient details
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
                
                img_path = receipt_image_path.get() if receipt_image_path.get() else None
                
                self.inventory.update_from_receipt(name, qty, price, img_path)
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
    
    def show_recipe_management(self):
        """Show recipe management screen"""
        recipe_window = tk.Toplevel(self.root)
        recipe_window.title("Recipe Management")
        recipe_window.geometry("700x500")
        
        tk.Label(recipe_window, text="Recipe Management", font=("Arial", 16, "bold")).pack(pady=10)
        
        # List current recipes/products
        list_frame = tk.Frame(recipe_window)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        recipe_listbox = tk.Listbox(list_frame, font=("Arial", 12), height=15, 
                                    yscrollcommand=scrollbar.set)
        scrollbar.config(command=recipe_listbox.yview)
        recipe_listbox.pack(fill="both", expand=True)
        
        for product_name, product in self.products.items():
            ingredients_str = ", ".join([f"{ing}: {qty}" for ing, qty in product.recipe.items()])
            recipe_listbox.insert(tk.END, f"{product_name} - [{ingredients_str}]")
        
        # Buttons
        btn_frame = tk.Frame(recipe_window)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Add New Recipe", font=("Arial", 12), 
                 bg="#27ae60", fg="white", command=self.add_recipe_dialog).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Refresh", font=("Arial", 12), 
                 bg="#95a5a6", fg="white", command=lambda: self.show_recipe_management()).pack(side="left", padx=5)
    
    def add_recipe_dialog(self):
        """Dialog to add new recipe with dynamic ingredient rows"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Recipe")
        dialog.geometry("600x600")
        
        # Scrollable frame for recipe entries
        canvas = tk.Canvas(dialog)
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Recipe name
        tk.Label(scrollable_frame, text="Recipe Name:", font=("Arial", 12, "bold")).pack(pady=10)
        name_entry = tk.Entry(scrollable_frame, font=("Arial", 12), width=30)
        name_entry.pack(pady=5)
        
        tk.Label(scrollable_frame, text="Ingredients:", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Container for ingredient rows
        ingredients_container = tk.Frame(scrollable_frame)
        ingredients_container.pack(pady=5, fill="both", expand=True)
        
        # Header
        header_frame = tk.Frame(ingredients_container)
        header_frame.pack(pady=5)
        tk.Label(header_frame, text="Ingredient", font=("Arial", 10, "bold"), width=20).pack(side="left", padx=5)
        tk.Label(header_frame, text="Quantity", font=("Arial", 10, "bold"), width=15).pack(side="left", padx=5)
        tk.Label(header_frame, text="", width=8).pack(side="left")  # Space for delete button
        
        recipe_entries = []
        
        def add_ingredient_row():
            row_frame = tk.Frame(ingredients_container, relief="raised", borderwidth=1)
            row_frame.pack(pady=3, fill="x", padx=10)
            
            # Dropdown for ingredient from inventory
            ingredient_var = tk.StringVar()
            ingredient_dropdown = ttk.Combobox(row_frame, textvariable=ingredient_var, 
                                              values=self.inventory.get_ingredient_names(), 
                                              width=20, font=("Arial", 10), state="readonly")
            ingredient_dropdown.pack(side="left", padx=5, pady=5)
            
            # Quantity entry
            qty_entry = tk.Entry(row_frame, font=("Arial", 10), width=15)
            qty_entry.pack(side="left", padx=5, pady=5)
            
            # Delete button for this row
            def delete_row():
                row_frame.destroy()
                recipe_entries.remove((ingredient_var, qty_entry, row_frame))
            
            delete_btn = tk.Button(row_frame, text="Remove", font=("Arial", 9), 
                                   bg="#e74c3c", fg="white", command=delete_row, width=8)
            delete_btn.pack(side="left", padx=5, pady=5)
            
            recipe_entries.append((ingredient_var, qty_entry, row_frame))
        
        # Add initial row
        add_ingredient_row()
        
        # Add ingredient button
        tk.Button(scrollable_frame, text="+ Add Ingredient", font=("Arial", 11), 
                 bg="#3498db", fg="white", command=add_ingredient_row).pack(pady=10)
        
        def submit():
            try:
                product_name = name_entry.get().strip()
                if not product_name:
                    raise ValueError("Recipe name is required")
                
                recipe = {}
                for ing_var, qty_entry, _ in recipe_entries:
                    ing = ing_var.get()
                    qty_str = qty_entry.get().strip()
                    if ing and qty_str:
                        try:
                            recipe[ing] = float(qty_str)
                        except ValueError:
                            raise ValueError(f"Invalid quantity for {ing}: {qty_str}")
                
                if not recipe:
                    raise ValueError("Recipe must have at least one ingredient")
                
                # Import Product class
                from POS import Product
                
                # Create product
                new_product = Product(product_name, recipe)
                self.products[product_name] = new_product
                self.recipes[product_name] = recipe
                
                messagebox.showinfo("Success", f"Added recipe: {product_name}")
                dialog.destroy()
                self.show_main_screen()  # Refresh to show new product
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(scrollable_frame, text="Create Recipe", font=("Arial", 12), 
                 bg="#27ae60", fg="white", command=submit, width=20).pack(pady=20)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_end_of_day_report(self):
        """Display end of day report"""
        report_window = tk.Toplevel(self.root)
        report_window.title("End of Day Report")
        report_window.geometry("700x600")
        
        tk.Label(report_window, text="End of Day Report", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Get today's data
        today_data = self.daily_sales.get_end_of_day_report()
        
        if not today_data:
            tk.Label(report_window, text="No sales data for today", 
                    font=("Arial", 14)).pack(pady=20)
            return
        
        # Summary frame
        summary_frame = tk.Frame(report_window, relief="raised", borderwidth=2)
        summary_frame.pack(fill="x", padx=20, pady=10)
        
        today_date = datetime.now().strftime("%B %d, %Y")
        tk.Label(summary_frame, text=f"Date: {today_date}", 
                font=("Arial", 12, "bold")).pack(pady=5)
        
        tk.Label(summary_frame, text=f"Total Transactions: {today_data['transaction_count']}", 
                font=("Arial", 12)).pack(pady=5)
        
        tk.Label(summary_frame, text=f"Total Sales: ${today_data['total_sales']:.2f}", 
                font=("Arial", 14, "bold"), fg="#27ae60").pack(pady=5)
        
        tk.Label(summary_frame, text=f"Cash: ${today_data['total_cash']:.2f}", 
                font=("Arial", 12)).pack(pady=2)
        
        tk.Label(summary_frame, text=f"Card: ${today_data['total_card']:.2f}", 
                font=("Arial", 12)).pack(pady=2)
        
        tk.Label(summary_frame, text=f"Register Total (Cash): ${today_data['total_cash']:.2f}", 
                font=("Arial", 13, "bold"), fg="#2980b9").pack(pady=10)
        
        # Transactions list
        tk.Label(report_window, text="Transactions:", font=("Arial", 12, "bold")).pack(pady=10)
        
        trans_frame = tk.Frame(report_window)
        trans_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        scrollbar = tk.Scrollbar(trans_frame)
        scrollbar.pack(side="right", fill="y")
        
        trans_text = tk.Text(trans_frame, font=("Courier", 10), yscrollcommand=scrollbar.set)
        scrollbar.config(command=trans_text.yview)
        trans_text.pack(fill="both", expand=True)
        
        trans_text.insert("1.0", f"{'Time':<10} {'Type':<8} {'Amount':<12} {'Employee':<15} {'Items'}\n")
        trans_text.insert("end", "-" * 80 + "\n")
        
        for trans in today_data['transactions']:
            items_str = ", ".join(trans['items'])
            trans_text.insert("end", 
                f"{trans['time']:<10} {trans['payment_type']:<8} "
                f"${trans['amount']:<11.2f} {trans['employee']:<15} {items_str}\n")
        
        trans_text.config(state="disabled")
        
        # Export button
        def export_report():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"eod_report_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(f"END OF DAY REPORT\n")
                f.write(f"Date: {today_date}\n")
                f.write(f"=" * 80 + "\n\n")
                f.write(f"Total Transactions: {today_data['transaction_count']}\n")
                f.write(f"Total Sales: ${today_data['total_sales']:.2f}\n")
                f.write(f"Cash: ${today_data['total_cash']:.2f}\n")
                f.write(f"Card: ${today_data['total_card']:.2f}\n")
                f.write(f"Register Total: ${today_data['total_cash']:.2f}\n")
                f.write(f"\n" + "=" * 80 + "\n\n")
                f.write(trans_text.get("1.0", "end"))
            
            messagebox.showinfo("Report Exported", f"Report saved to {filename}")
        
        tk.Button(report_window, text="Export Report", font=("Arial", 12), 
                 bg="#3498db", fg="white", command=export_report).pack(pady=10)
    
    def show_inventory_report(self):
        """Display inventory report"""
        report_window = tk.Toplevel(self.root)
        report_window.title("Inventory Report")
        report_window.geometry("800x600")
        
        tk.Label(report_window, text="Inventory Report", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Get inventory data
        report_data, total_value = self.inventory.generate_inventory_report()
        
        # Summary
        summary_frame = tk.Frame(report_window, relief="raised", borderwidth=2)
        summary_frame.pack(fill="x", padx=20, pady=10)
        
        today_date = datetime.now().strftime("%B %d, %Y")
        tk.Label(summary_frame, text=f"Date: {today_date}", 
                font=("Arial", 12, "bold")).pack(pady=5)
        
        tk.Label(summary_frame, text=f"Total Inventory Items: {len(report_data)}", 
                font=("Arial", 12)).pack(pady=5)
        
        tk.Label(summary_frame, text=f"Total Inventory Value: ${total_value:.2f}", 
                font=("Arial", 14, "bold"), fg="#27ae60").pack(pady=5)
        
        # Inventory table
        tree_frame = tk.Frame(report_window)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = ("Ingredient", "Quantity", "Unit", "Price/Unit", "Total Value")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                           yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        for item in report_data:
            tree.insert("", "end", values=(
                item['ingredient'],
                f"{item['quantity']:.1f}",
                item['unit'],
                f"${item['price_per_unit']:.2f}",
                f"${item['total_price']:.2f}"
            ))
        
        tree.pack(fill="both", expand=True)
        
        # Export button
        def export_report():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inventory_report_{timestamp}.csv"
            
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Ingredient', 'Quantity', 'Unit', 'Price/Unit', 'Total Value'])
                for item in report_data:
                    writer.writerow([
                        item['ingredient'],
                        f"{item['quantity']:.1f}",
                        item['unit'],
                        f"{item['price_per_unit']:.2f}",
                        f"{item['total_price']:.2f}"
                    ])
                writer.writerow([])
                writer.writerow(['Total Inventory Value', f"${total_value:.2f}"])
            
            messagebox.showinfo("Report Exported", f"Report saved to {filename}")
        
        tk.Button(report_window, text="Export to CSV", font=("Arial", 12), 
                 bg="#3498db", fg="white", command=export_report).pack(pady=10)
    
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

