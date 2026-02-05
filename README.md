# 🥪 PoS Deli Inventory System

This project is a Python-based Point of Sale (PoS) system made for a small deli.

The system is built around inventory-first logic, where products are defined by recipes and pricing is derived directly from ingredient costs.

## What It Does

- Manages deli inventory at the ingredient level
- Builds products from recipes that pull directly from inventory
- Automatically calculates product pricing using a standard **300% markup** on total ingredient cost
- Updates inventory as items are produced or sold
- Provides a simple graphical interface for daily use

## Design Approach

The application is structured using OOP principles to reflect how a real deli operates:

- Inventory tracks ingredients and quantities
- Recipes define how ingredients are combined
- Products derive their cost and price from recipes
- UI logic is separated from business logic to support future expansion

The frontend is implemented with **Tkinter**. Claude was used to assist with initial UI scaffolding, which was then adapted to fit the operational needs of the deli.

## Why This Project

This system was intentionally designed as a real-world application rather than a demo or coding exercise. The goal was to build something that:

- Models real operational constraints
- Can be extended without major refactoring
- Is usable by non-technical users
- Demonstrates applied software design, not just syntax

## Tech Stack

- Python
- Tkinter

## Current Status

This project is actively being developed. While the core inventory and pricing logic is in place, upcoming improvements include:

- Enhanced UI
- Sales tracking and reporting
- Additional safeguards around inventory validation

## Running the Project

```bash
git clone https://github.com/CoreyJness/PoS.git
cd PoS
python main.py
```



(Entry point and structure may evolve as the project moves closer to deployment.)

##Note for Reviewers

This project demonstrates applied Python OOP, domain modeling, and iterative system design with an emphasis on real-world usability.
