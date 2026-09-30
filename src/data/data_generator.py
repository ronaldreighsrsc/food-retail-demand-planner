"""
Realistic Ground Truth Data Generator for KIOS-FLOW Retail Food Demand Planner.
Simulates +50 stores in Chile, transoceanic imports from USA, daily sales, CD batches, and pipeline orders.
"""
import os
import random
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
from src.data.db_manager import DatabaseManager


class FoodRetailDataGenerator:
    """Generates synthetic operational and analytical data for food retail demand planning."""

    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
        self.as_of_date = date(2026, 9, 30)

    def generate_products(self) -> pd.DataFrame:
        products = [
            # Snacks & Salados
            {
                "sku": "FOD-SNK-CHTS-226", "product_name": "Cheetos Flamin' Hot Crunchy USA 226g",
                "category": "Snacks & Salados", "sub_category": "Chips & Extruidos", "brand": "Frito-Lay",
                "cogs_clp": 2200.0, "retail_price_clp": 4490.0, "shelf_life_total_days": 270,
                "min_shelf_life_acceptance_days": 150, "units_per_case": 24, "cases_per_pallet": 36,
                "volume_m3_per_case": 0.045, "weight_kg_per_case": 6.2, "moq_units": 1728,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 8.0, "abc_category": "A"
            },
            {
                "sku": "FOD-SNK-CHTS-JAL", "product_name": "Cheetos Crunchy Cheddar Jalapeño 226g",
                "category": "Snacks & Salados", "sub_category": "Chips & Extruidos", "brand": "Frito-Lay",
                "cogs_clp": 2250.0, "retail_price_clp": 4490.0, "shelf_life_total_days": 270,
                "min_shelf_life_acceptance_days": 150, "units_per_case": 24, "cases_per_pallet": 36,
                "volume_m3_per_case": 0.045, "weight_kg_per_case": 6.2, "moq_units": 1728,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.0, "abc_category": "A"
            },
            {
                "sku": "FOD-SNK-DOR-CLR", "product_name": "Doritos Cool Ranch Flavored Tortilla Chips 262g",
                "category": "Snacks & Salados", "sub_category": "Tortillas & Nachos", "brand": "Frito-Lay",
                "cogs_clp": 2400.0, "retail_price_clp": 4690.0, "shelf_life_total_days": 240,
                "min_shelf_life_acceptance_days": 140, "units_per_case": 20, "cases_per_pallet": 32,
                "volume_m3_per_case": 0.050, "weight_kg_per_case": 6.0, "moq_units": 1280,
                "supplier_lead_time_days": 55.0, "lead_time_std_days": 7.5, "abc_category": "A"
            },
            {
                "sku": "FOD-SNK-TAK-FUE", "product_name": "Takis Fuego Hot Chili Pepper & Lime 280g",
                "category": "Snacks & Salados", "sub_category": "Tortillas & Nachos", "brand": "Barcel USA",
                "cogs_clp": 2100.0, "retail_price_clp": 4290.0, "shelf_life_total_days": 300,
                "min_shelf_life_acceptance_days": 160, "units_per_case": 20, "cases_per_pallet": 40,
                "volume_m3_per_case": 0.040, "weight_kg_per_case": 6.5, "moq_units": 1600,
                "supplier_lead_time_days": 50.0, "lead_time_std_days": 6.0, "abc_category": "A"
            },
            {
                "sku": "FOD-SNK-PRG-SRC", "product_name": "Pringles Sour Cream & Onion USA 158g",
                "category": "Snacks & Salados", "sub_category": "Papas & Latas", "brand": "Kellogg's",
                "cogs_clp": 1650.0, "retail_price_clp": 3290.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 14, "cases_per_pallet": 56,
                "volume_m3_per_case": 0.028, "weight_kg_per_case": 3.2, "moq_units": 1568,
                "supplier_lead_time_days": 65.0, "lead_time_std_days": 9.0, "abc_category": "A"
            },
            {
                "sku": "FOD-SNK-PRG-PIZ", "product_name": "Pringles Pizza Flavored Potato Crisps 158g",
                "category": "Snacks & Salados", "sub_category": "Papas & Latas", "brand": "Kellogg's",
                "cogs_clp": 1650.0, "retail_price_clp": 3290.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 14, "cases_per_pallet": 56,
                "volume_m3_per_case": 0.028, "weight_kg_per_case": 3.2, "moq_units": 784,
                "supplier_lead_time_days": 65.0, "lead_time_std_days": 9.0, "abc_category": "B"
            },
            {
                "sku": "FOD-SNK-SNY-HNY", "product_name": "Snyder's of Hanover Honey Mustard & Onion Pretzel Pieces 240g",
                "category": "Snacks & Salados", "sub_category": "Pretzels", "brand": "Campbell Snacks",
                "cogs_clp": 1950.0, "retail_price_clp": 3890.0, "shelf_life_total_days": 300,
                "min_shelf_life_acceptance_days": 160, "units_per_case": 16, "cases_per_pallet": 48,
                "volume_m3_per_case": 0.035, "weight_kg_per_case": 4.5, "moq_units": 768,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 8.0, "abc_category": "B"
            },
            {
                "sku": "FOD-SNK-CMB-PIZ", "product_name": "Combos Pizzeria Pretzel Baked Snacks 178g",
                "category": "Snacks & Salados", "sub_category": "Pretzels & Bites", "brand": "Mars Wrigley",
                "cogs_clp": 1800.0, "retail_price_clp": 3490.0, "shelf_life_total_days": 300,
                "min_shelf_life_acceptance_days": 160, "units_per_case": 18, "cases_per_pallet": 45,
                "volume_m3_per_case": 0.032, "weight_kg_per_case": 3.8, "moq_units": 810,
                "supplier_lead_time_days": 55.0, "lead_time_std_days": 7.0, "abc_category": "B"
            },

            # Bebidas & Energéticas
            {
                "sku": "FOD-BEV-DRPEP-355", "product_name": "Dr Pepper Cherry Soda Lata 355ml",
                "category": "Bebidas & Energéticas", "sub_category": "Gaseosas Importadas", "brand": "Keurig Dr Pepper",
                "cogs_clp": 950.0, "retail_price_clp": 1990.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 24, "cases_per_pallet": 72,
                "volume_m3_per_case": 0.022, "weight_kg_per_case": 9.5, "moq_units": 3456,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.5, "abc_category": "A"
            },
            {
                "sku": "FOD-BEV-DRP-REG", "product_name": "Dr Pepper Original 23 Flavors Lata 355ml",
                "category": "Bebidas & Energéticas", "sub_category": "Gaseosas Importadas", "brand": "Keurig Dr Pepper",
                "cogs_clp": 920.0, "retail_price_clp": 1890.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 24, "cases_per_pallet": 72,
                "volume_m3_per_case": 0.022, "weight_kg_per_case": 9.5, "moq_units": 3456,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.5, "abc_category": "A"
            },
            {
                "sku": "FOD-BEV-MNST-PCH", "product_name": "Monster Energy Ultra Peachy Keen 473ml",
                "category": "Bebidas & Energéticas", "sub_category": "Bebidas Energéticas", "brand": "Monster Energy",
                "cogs_clp": 1450.0, "retail_price_clp": 2790.0, "shelf_life_total_days": 720,
                "min_shelf_life_acceptance_days": 365, "units_per_case": 24, "cases_per_pallet": 60,
                "volume_m3_per_case": 0.026, "weight_kg_per_case": 12.8, "moq_units": 2880,
                "supplier_lead_time_days": 55.0, "lead_time_std_days": 6.5, "abc_category": "A"
            },
            {
                "sku": "FOD-BEV-MNST-AUS", "product_name": "Monster Energy Aussie Style Lemonade 473ml",
                "category": "Bebidas & Energéticas", "sub_category": "Bebidas Energéticas", "brand": "Monster Energy",
                "cogs_clp": 1450.0, "retail_price_clp": 2790.0, "shelf_life_total_days": 720,
                "min_shelf_life_acceptance_days": 365, "units_per_case": 24, "cases_per_pallet": 60,
                "volume_m3_per_case": 0.026, "weight_kg_per_case": 12.8, "moq_units": 2880,
                "supplier_lead_time_days": 55.0, "lead_time_std_days": 6.5, "abc_category": "A"
            },
            {
                "sku": "FOD-BEV-MTN-DEW", "product_name": "Mountain Dew Real Sugar Citrus Soda 355ml",
                "category": "Bebidas & Energéticas", "sub_category": "Gaseosas Importadas", "brand": "PepsiCo USA",
                "cogs_clp": 980.0, "retail_price_clp": 1990.0, "shelf_life_total_days": 270,
                "min_shelf_life_acceptance_days": 140, "units_per_case": 24, "cases_per_pallet": 72,
                "volume_m3_per_case": 0.022, "weight_kg_per_case": 9.5, "moq_units": 1728,
                "supplier_lead_time_days": 62.0, "lead_time_std_days": 8.0, "abc_category": "B"
            },
            {
                "sku": "FOD-BEV-AW-ROOT", "product_name": "A&W Root Beer Aged Vanilla Lata 355ml",
                "category": "Bebidas & Energéticas", "sub_category": "Gaseosas Importadas", "brand": "Keurig Dr Pepper",
                "cogs_clp": 950.0, "retail_price_clp": 1890.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 24, "cases_per_pallet": 72,
                "volume_m3_per_case": 0.022, "weight_kg_per_case": 9.5, "moq_units": 1728,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.0, "abc_category": "B"
            },
            {
                "sku": "FOD-BEV-ARZ-GRN", "product_name": "AriZona Green Tea with Ginseng & Honey 680ml",
                "category": "Bebidas & Energéticas", "sub_category": "Té & Jugos Fríos", "brand": "AriZona Beverages",
                "cogs_clp": 1200.0, "retail_price_clp": 2490.0, "shelf_life_total_days": 540,
                "min_shelf_life_acceptance_days": 270, "units_per_case": 24, "cases_per_pallet": 50,
                "volume_m3_per_case": 0.038, "weight_kg_per_case": 17.5, "moq_units": 2400,
                "supplier_lead_time_days": 58.0, "lead_time_std_days": 8.0, "abc_category": "A"
            },
            {
                "sku": "FOD-BEV-SNP-PCH", "product_name": "Snapple Peach Tea Real Brewed 473ml",
                "category": "Bebidas & Energéticas", "sub_category": "Té & Jugos Fríos", "brand": "Keurig Dr Pepper",
                "cogs_clp": 1350.0, "retail_price_clp": 2690.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 12, "cases_per_pallet": 64,
                "volume_m3_per_case": 0.025, "weight_kg_per_case": 7.2, "moq_units": 768,
                "supplier_lead_time_days": 65.0, "lead_time_std_days": 8.5, "abc_category": "C"
            },

            # Chocolates & Dulces
            {
                "sku": "FOD-SNK-REESE-42G", "product_name": "Reese's Peanut Butter Cups 2-Pack 42g",
                "category": "Chocolates & Dulces", "sub_category": "Chocolates & Manteca Maní", "brand": "The Hershey Company",
                "cogs_clp": 780.0, "retail_price_clp": 1690.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 36, "cases_per_pallet": 80,
                "volume_m3_per_case": 0.015, "weight_kg_per_case": 1.8, "moq_units": 2880,
                "supplier_lead_time_days": 50.0, "lead_time_std_days": 6.0, "abc_category": "A"
            },
            {
                "sku": "FOD-CHO-REESE-WHT", "product_name": "Reese's White Chocolate Peanut Butter Cups 42g",
                "category": "Chocolates & Dulces", "sub_category": "Chocolates & Manteca Maní", "brand": "The Hershey Company",
                "cogs_clp": 820.0, "retail_price_clp": 1790.0, "shelf_life_total_days": 300,
                "min_shelf_life_acceptance_days": 160, "units_per_case": 36, "cases_per_pallet": 80,
                "volume_m3_per_case": 0.015, "weight_kg_per_case": 1.8, "moq_units": 1440,
                "supplier_lead_time_days": 52.0, "lead_time_std_days": 6.5, "abc_category": "B"
            },
            {
                "sku": "FOD-CHO-HERSH-CKC", "product_name": "Hershey's Cookies 'n' Creme Candy Bar 43g",
                "category": "Chocolates & Dulces", "sub_category": "Barras Chocolate", "brand": "The Hershey Company",
                "cogs_clp": 750.0, "retail_price_clp": 1590.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 36, "cases_per_pallet": 80,
                "volume_m3_per_case": 0.014, "weight_kg_per_case": 1.8, "moq_units": 2880,
                "supplier_lead_time_days": 50.0, "lead_time_std_days": 6.0, "abc_category": "A"
            },
            {
                "sku": "FOD-CHO-MM-PNT", "product_name": "M&M's Peanut Butter Chocolate Candies 46g",
                "category": "Chocolates & Dulces", "sub_category": "Chocolates Confitados", "brand": "Mars Wrigley",
                "cogs_clp": 850.0, "retail_price_clp": 1790.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 24, "cases_per_pallet": 90,
                "volume_m3_per_case": 0.012, "weight_kg_per_case": 1.4, "moq_units": 2160,
                "supplier_lead_time_days": 55.0, "lead_time_std_days": 7.0, "abc_category": "A"
            },
            {
                "sku": "FOD-CND-SOUR-99G", "product_name": "Sour Patch Kids Theater Box 99g",
                "category": "Chocolates & Dulces", "sub_category": "Gomitas & Ácidos", "brand": "Mondelēz International",
                "cogs_clp": 1150.0, "retail_price_clp": 2490.0, "shelf_life_total_days": 450,
                "min_shelf_life_acceptance_days": 240, "units_per_case": 12, "cases_per_pallet": 100,
                "volume_m3_per_case": 0.015, "weight_kg_per_case": 1.4, "moq_units": 1200,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.5, "abc_category": "A"
            },
            {
                "sku": "FOD-CND-SWD-FSH", "product_name": "Swedish Fish Red Theater Box Candy 99g",
                "category": "Chocolates & Dulces", "sub_category": "Gomitas & Ácidos", "brand": "Mondelēz International",
                "cogs_clp": 1100.0, "retail_price_clp": 2390.0, "shelf_life_total_days": 450,
                "min_shelf_life_acceptance_days": 240, "units_per_case": 12, "cases_per_pallet": 100,
                "volume_m3_per_case": 0.015, "weight_kg_per_case": 1.4, "moq_units": 600,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.5, "abc_category": "C"
            },
            {
                "sku": "FOD-CND-NRD-ROP", "product_name": "Nerds Rope Very Berry Candy 26g",
                "category": "Chocolates & Dulces", "sub_category": "Caramelos Blandos", "brand": "Ferrara Candy Co",
                "cogs_clp": 620.0, "retail_price_clp": 1390.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 24, "cases_per_pallet": 120,
                "volume_m3_per_case": 0.010, "weight_kg_per_case": 0.8, "moq_units": 1440,
                "supplier_lead_time_days": 58.0, "lead_time_std_days": 7.0, "abc_category": "B"
            },
            {
                "sku": "FOD-BK-POPT-STR", "product_name": "Pop-Tarts Frosted Strawberry Toaster Pastries 8pk 384g",
                "category": "Chocolates & Dulces", "sub_category": "Pastelería & Galletas", "brand": "Kellanova",
                "cogs_clp": 2700.0, "retail_price_clp": 5490.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 12, "cases_per_pallet": 48,
                "volume_m3_per_case": 0.038, "weight_kg_per_case": 5.2, "moq_units": 1152,
                "supplier_lead_time_days": 65.0, "lead_time_std_days": 8.0, "abc_category": "A"
            },
            {
                "sku": "FOD-BK-POPT-BRN", "product_name": "Pop-Tarts Frosted Brown Sugar Cinnamon 8pk 384g",
                "category": "Chocolates & Dulces", "sub_category": "Pastelería & Galletas", "brand": "Kellanova",
                "cogs_clp": 2700.0, "retail_price_clp": 5490.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 12, "cases_per_pallet": 48,
                "volume_m3_per_case": 0.038, "weight_kg_per_case": 5.2, "moq_units": 576,
                "supplier_lead_time_days": 65.0, "lead_time_std_days": 8.0, "abc_category": "B"
            },
            {
                "sku": "FOD-CND-TWZ-STR", "product_name": "Twizzlers Strawberry Twists Chewy Candy 198g",
                "category": "Chocolates & Dulces", "sub_category": "Regaliz & Chewy", "brand": "The Hershey Company",
                "cogs_clp": 1300.0, "retail_price_clp": 2690.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 12, "cases_per_pallet": 60,
                "volume_m3_per_case": 0.022, "weight_kg_per_case": 2.7, "moq_units": 720,
                "supplier_lead_time_days": 54.0, "lead_time_std_days": 6.5, "abc_category": "C"
            },

            # Despensa & Salsas
            {
                "sku": "FOD-GRO-KRAFT-206", "product_name": "Kraft Macaroni & Cheese Original Dinner 206g",
                "category": "Despensa & Salsas", "sub_category": "Pastas Preparadas", "brand": "The Kraft Heinz Company",
                "cogs_clp": 1420.0, "retail_price_clp": 2990.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 24, "cases_per_pallet": 64,
                "volume_m3_per_case": 0.024, "weight_kg_per_case": 5.6, "moq_units": 1536,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.0, "abc_category": "A"
            },
            {
                "sku": "FOD-GRO-KRAFT-DLX", "product_name": "Kraft Deluxe Four Cheese Macaroni & Cheese 397g",
                "category": "Despensa & Salsas", "sub_category": "Pastas Preparadas", "brand": "The Kraft Heinz Company",
                "cogs_clp": 2650.0, "retail_price_clp": 5290.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 12, "cases_per_pallet": 50,
                "volume_m3_per_case": 0.030, "weight_kg_per_case": 5.4, "moq_units": 600,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.0, "abc_category": "B"
            },
            {
                "sku": "FOD-SAU-FRK-HOT", "product_name": "Frank's RedHot Original Cayenne Pepper Sauce 354ml",
                "category": "Despensa & Salsas", "sub_category": "Salsas Picantes", "brand": "McCormick & Co",
                "cogs_clp": 2150.0, "retail_price_clp": 4390.0, "shelf_life_total_days": 720,
                "min_shelf_life_acceptance_days": 365, "units_per_case": 12, "cases_per_pallet": 70,
                "volume_m3_per_case": 0.020, "weight_kg_per_case": 6.8, "moq_units": 840,
                "supplier_lead_time_days": 68.0, "lead_time_std_days": 8.5, "abc_category": "B"
            },
            {
                "sku": "FOD-SAU-SBR-BBQ", "product_name": "Sweet Baby Ray's Honey Barbecue Sauce 510g",
                "category": "Despensa & Salsas", "sub_category": "Salsas BBQ", "brand": "Sweet Baby Ray's",
                "cogs_clp": 2300.0, "retail_price_clp": 4690.0, "shelf_life_total_days": 540,
                "min_shelf_life_acceptance_days": 270, "units_per_case": 12, "cases_per_pallet": 60,
                "volume_m3_per_case": 0.022, "weight_kg_per_case": 7.2, "moq_units": 1440,
                "supplier_lead_time_days": 62.0, "lead_time_std_days": 7.5, "abc_category": "A"
            },
            {
                "sku": "FOD-SAU-HDN-RNC", "product_name": "Hidden Valley The Original Ranch Dressing 473ml",
                "category": "Despensa & Salsas", "sub_category": "Aderezos", "brand": "The Clorox Company",
                "cogs_clp": 2500.0, "retail_price_clp": 4990.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 12, "cases_per_pallet": 60,
                "volume_m3_per_case": 0.022, "weight_kg_per_case": 6.9, "moq_units": 720,
                "supplier_lead_time_days": 65.0, "lead_time_std_days": 8.0, "abc_category": "B"
            },
            {
                "sku": "FOD-SAU-HNZ-MST", "product_name": "Heinz Yellow Mustard Squeeze Bottle USA 396g",
                "category": "Despensa & Salsas", "sub_category": "Mostazas & Condimentos", "brand": "The Kraft Heinz Company",
                "cogs_clp": 1400.0, "retail_price_clp": 2890.0, "shelf_life_total_days": 540,
                "min_shelf_life_acceptance_days": 270, "units_per_case": 16, "cases_per_pallet": 65,
                "volume_m3_per_case": 0.020, "weight_kg_per_case": 7.0, "moq_units": 1040,
                "supplier_lead_time_days": 58.0, "lead_time_std_days": 7.0, "abc_category": "C"
            },
            {
                "sku": "FOD-SPR-SKP-PNT", "product_name": "Skippy Creamy Peanut Butter USA 462g",
                "category": "Despensa & Salsas", "sub_category": "Untables & Cremas", "brand": "Hormel Foods",
                "cogs_clp": 2850.0, "retail_price_clp": 5790.0, "shelf_life_total_days": 365,
                "min_shelf_life_acceptance_days": 180, "units_per_case": 12, "cases_per_pallet": 60,
                "volume_m3_per_case": 0.021, "weight_kg_per_case": 6.4, "moq_units": 720,
                "supplier_lead_time_days": 64.0, "lead_time_std_days": 8.0, "abc_category": "B"
            },
            {
                "sku": "FOD-SOU-CMP-TOM", "product_name": "Campbell's Condensed Tomato Soup 305g",
                "category": "Despensa & Salsas", "sub_category": "Sopas & Enlatados", "brand": "Campbell Soup Co",
                "cogs_clp": 1250.0, "retail_price_clp": 2490.0, "shelf_life_total_days": 720,
                "min_shelf_life_acceptance_days": 365, "units_per_case": 24, "cases_per_pallet": 70,
                "volume_m3_per_case": 0.022, "weight_kg_per_case": 8.9, "moq_units": 840,
                "supplier_lead_time_days": 60.0, "lead_time_std_days": 7.0, "abc_category": "C"
            }
        ]
        return pd.DataFrame(products)

    def generate_stores(self) -> pd.DataFrame:
        stores = [
            # Santiago Metro & Premium
            {"store_id": "STR-01", "store_name": "Providencia Los Leones", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2022-03-15", "sales_area_m2": 140.0, "shelf_capacity_units": 4500, "transit_days_from_cd": 1},
            {"store_id": "STR-02", "store_name": "Providencia Pedro de Valdivia", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2022-05-10", "sales_area_m2": 120.0, "shelf_capacity_units": 3800, "transit_days_from_cd": 1},
            {"store_id": "STR-03", "store_name": "Providencia Manuel Montt", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2022-07-20", "sales_area_m2": 130.0, "shelf_capacity_units": 4000, "transit_days_from_cd": 1},
            {"store_id": "STR-04", "store_name": "Las Condes Escuela Militar", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2022-04-12", "sales_area_m2": 150.0, "shelf_capacity_units": 4800, "transit_days_from_cd": 1},
            {"store_id": "STR-05", "store_name": "Las Condes El Golf", "city": "Santiago", "region_id": "RM", "cluster_id": "Residencial Premium", "opening_date": "2022-06-01", "sales_area_m2": 160.0, "shelf_capacity_units": 5000, "transit_days_from_cd": 1},
            {"store_id": "STR-06", "store_name": "Las Condes Parque Arauco", "city": "Santiago", "region_id": "RM", "cluster_id": "Regional Mall", "opening_date": "2022-08-15", "sales_area_m2": 180.0, "shelf_capacity_units": 5500, "transit_days_from_cd": 1},
            {"store_id": "STR-07", "store_name": "Las Condes Alto Las Condes", "city": "Santiago", "region_id": "RM", "cluster_id": "Regional Mall", "opening_date": "2022-09-10", "sales_area_m2": 175.0, "shelf_capacity_units": 5300, "transit_days_from_cd": 1},
            {"store_id": "STR-08", "store_name": "Vitacura Alonso de Córdova", "city": "Santiago", "region_id": "RM", "cluster_id": "Residencial Premium", "opening_date": "2022-10-05", "sales_area_m2": 190.0, "shelf_capacity_units": 5800, "transit_days_from_cd": 1},
            {"store_id": "STR-09", "store_name": "Vitacura Lo Curro", "city": "Santiago", "region_id": "RM", "cluster_id": "Residencial Premium", "opening_date": "2023-01-18", "sales_area_m2": 160.0, "shelf_capacity_units": 4900, "transit_days_from_cd": 1},
            {"store_id": "STR-10", "store_name": "Lo Barnechea La Dehesa Portal", "city": "Santiago", "region_id": "RM", "cluster_id": "Regional Mall", "opening_date": "2023-02-20", "sales_area_m2": 185.0, "shelf_capacity_units": 5600, "transit_days_from_cd": 1},
            {"store_id": "STR-11", "store_name": "Santiago Centro Paseo Ahumada", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-03-15", "sales_area_m2": 140.0, "shelf_capacity_units": 4600, "transit_days_from_cd": 1},
            {"store_id": "STR-12", "store_name": "Santiago Centro Huérfanos", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-04-10", "sales_area_m2": 135.0, "shelf_capacity_units": 4400, "transit_days_from_cd": 1},
            {"store_id": "STR-13", "store_name": "Santiago Centro Universidad Católica", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-05-22", "sales_area_m2": 125.0, "shelf_capacity_units": 4100, "transit_days_from_cd": 1},
            {"store_id": "STR-14", "store_name": "Ñuñoa Plaza Egaña Mall", "city": "Santiago", "region_id": "RM", "cluster_id": "Regional Mall", "opening_date": "2023-06-15", "sales_area_m2": 170.0, "shelf_capacity_units": 5200, "transit_days_from_cd": 1},
            {"store_id": "STR-15", "store_name": "Ñuñoa Irarrázaval", "city": "Santiago", "region_id": "RM", "cluster_id": "Residencial Premium", "opening_date": "2023-07-08", "sales_area_m2": 130.0, "shelf_capacity_units": 4200, "transit_days_from_cd": 1},
            {"store_id": "STR-16", "store_name": "La Florida Mall Plaza Vespucio", "city": "Santiago", "region_id": "RM", "cluster_id": "Regional Mall", "opening_date": "2023-08-14", "sales_area_m2": 165.0, "shelf_capacity_units": 5100, "transit_days_from_cd": 1},
            {"store_id": "STR-17", "store_name": "La Florida Vicuña Mackenna", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-09-02", "sales_area_m2": 115.0, "shelf_capacity_units": 3700, "transit_days_from_cd": 1},
            {"store_id": "STR-18", "store_name": "Maipú Mall Arauco Maipú", "city": "Santiago", "region_id": "RM", "cluster_id": "Regional Mall", "opening_date": "2023-10-10", "sales_area_m2": 175.0, "shelf_capacity_units": 5300, "transit_days_from_cd": 1},
            {"store_id": "STR-19", "store_name": "Maipú Pajaritos", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-11-15", "sales_area_m2": 120.0, "shelf_capacity_units": 3900, "transit_days_from_cd": 1},
            {"store_id": "STR-20", "store_name": "San Miguel Gran Avenida", "city": "Santiago", "region_id": "RM", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-12-05", "sales_area_m2": 125.0, "shelf_capacity_units": 4000, "transit_days_from_cd": 1},
            {"store_id": "STR-21", "store_name": "Peñalolén Consistorial", "city": "Santiago", "region_id": "RM", "cluster_id": "Residencial Premium", "opening_date": "2024-01-20", "sales_area_m2": 145.0, "shelf_capacity_units": 4400, "transit_days_from_cd": 1},
            {"store_id": "STR-22", "store_name": "La Reina Príncipe de Gales", "city": "Santiago", "region_id": "RM", "cluster_id": "Residencial Premium", "opening_date": "2024-02-18", "sales_area_m2": 140.0, "shelf_capacity_units": 4300, "transit_days_from_cd": 1},

            # V Región Valparaíso / Viña
            {"store_id": "STR-23", "store_name": "Viña del Mar Mall Marina", "city": "Viña del Mar", "region_id": "V", "cluster_id": "Regional Mall", "opening_date": "2022-11-12", "sales_area_m2": 180.0, "shelf_capacity_units": 5500, "transit_days_from_cd": 2},
            {"store_id": "STR-24", "store_name": "Viña del Mar 1 Norte", "city": "Viña del Mar", "region_id": "V", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-02-10", "sales_area_m2": 130.0, "shelf_capacity_units": 4100, "transit_days_from_cd": 2},
            {"store_id": "STR-25", "store_name": "Valparaíso Plaza Victoria", "city": "Valparaíso", "region_id": "V", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-04-05", "sales_area_m2": 120.0, "shelf_capacity_units": 3800, "transit_days_from_cd": 2},
            {"store_id": "STR-26", "store_name": "Concón Bosques de Montemar", "city": "Concón", "region_id": "V", "cluster_id": "Residencial Premium", "opening_date": "2023-08-20", "sales_area_m2": 150.0, "shelf_capacity_units": 4600, "transit_days_from_cd": 2},
            {"store_id": "STR-27", "store_name": "Quilpué Centro Mall", "city": "Quilpué", "region_id": "V", "cluster_id": "Regional Mall", "opening_date": "2024-01-10", "sales_area_m2": 140.0, "shelf_capacity_units": 4200, "transit_days_from_cd": 2},

            # VIII Región Biobío / Concepción
            {"store_id": "STR-28", "store_name": "Concepción Mall Plaza El Trébol", "city": "Talcahuano", "region_id": "VIII", "cluster_id": "Regional Mall", "opening_date": "2022-12-01", "sales_area_m2": 190.0, "shelf_capacity_units": 5800, "transit_days_from_cd": 2},
            {"store_id": "STR-29", "store_name": "Concepción Barros Arana", "city": "Concepción", "region_id": "VIII", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-03-25", "sales_area_m2": 135.0, "shelf_capacity_units": 4200, "transit_days_from_cd": 2},
            {"store_id": "STR-30", "store_name": "San Pedro de la Paz Andalué", "city": "San Pedro de la Paz", "region_id": "VIII", "cluster_id": "Residencial Premium", "opening_date": "2023-09-18", "sales_area_m2": 145.0, "shelf_capacity_units": 4400, "transit_days_from_cd": 2},
            {"store_id": "STR-31", "store_name": "Chillán Mall Arauco Chillán", "city": "Chillán", "region_id": "XVI", "cluster_id": "Regional Mall", "opening_date": "2024-03-12", "sales_area_m2": 150.0, "shelf_capacity_units": 4500, "transit_days_from_cd": 2},
            {"store_id": "STR-32", "store_name": "Los Ángeles Mall Plaza", "city": "Los Ángeles", "region_id": "VIII", "cluster_id": "Regional Mall", "opening_date": "2024-04-15", "sales_area_m2": 140.0, "shelf_capacity_units": 4300, "transit_days_from_cd": 2},

            # Norte Grande y Chico
            {"store_id": "STR-33", "store_name": "Antofagasta Mall Plaza", "city": "Antofagasta", "region_id": "II", "cluster_id": "Regional Mall", "opening_date": "2023-01-25", "sales_area_m2": 175.0, "shelf_capacity_units": 5200, "transit_days_from_cd": 3},
            {"store_id": "STR-34", "store_name": "Antofagasta Paseo Prat", "city": "Antofagasta", "region_id": "II", "cluster_id": "Alto Tráfico Metro", "opening_date": "2023-06-10", "sales_area_m2": 125.0, "shelf_capacity_units": 3900, "transit_days_from_cd": 3},
            {"store_id": "STR-35", "store_name": "Calama Mall Plaza Calama", "city": "Calama", "region_id": "II", "cluster_id": "Regional Mall", "opening_date": "2023-11-20", "sales_area_m2": 150.0, "shelf_capacity_units": 4500, "transit_days_from_cd": 3},
            {"store_id": "STR-36", "store_name": "Iquique Mall Plaza Iquique", "city": "Iquique", "region_id": "I", "cluster_id": "Regional Mall", "opening_date": "2024-02-05", "sales_area_m2": 160.0, "shelf_capacity_units": 4800, "transit_days_from_cd": 4},
            {"store_id": "STR-37", "store_name": "Arica Centro 21 de Mayo", "city": "Arica", "region_id": "XV", "cluster_id": "Alto Tráfico Metro", "opening_date": "2024-05-10", "sales_area_m2": 120.0, "shelf_capacity_units": 3700, "transit_days_from_cd": 4},
            {"store_id": "STR-38", "store_name": "La Serena Mall Plaza La Serena", "city": "La Serena", "region_id": "IV", "cluster_id": "Regional Mall", "opening_date": "2023-05-18", "sales_area_m2": 170.0, "shelf_capacity_units": 5100, "transit_days_from_cd": 2},
            {"store_id": "STR-39", "store_name": "Coquimbo Vivo Mall", "city": "Coquimbo", "region_id": "IV", "cluster_id": "Regional Mall", "opening_date": "2023-10-22", "sales_area_m2": 155.0, "shelf_capacity_units": 4700, "transit_days_from_cd": 2},
            {"store_id": "STR-40", "store_name": "Copiapó Mall Plaza Copiapó", "city": "Copiapó", "region_id": "III", "cluster_id": "Regional Mall", "opening_date": "2024-03-30", "sales_area_m2": 145.0, "shelf_capacity_units": 4400, "transit_days_from_cd": 3},

            # Centro Sur y Zona Austral
            {"store_id": "STR-41", "store_name": "Rancagua Mall Vivo Divo", "city": "Rancagua", "region_id": "VI", "cluster_id": "Regional Mall", "opening_date": "2023-07-12", "sales_area_m2": 150.0, "shelf_capacity_units": 4500, "transit_days_from_cd": 1},
            {"store_id": "STR-42", "store_name": "Curicó Mall Valle Curicó", "city": "Curicó", "region_id": "VII", "cluster_id": "Regional Mall", "opening_date": "2023-11-05", "sales_area_m2": 135.0, "shelf_capacity_units": 4100, "transit_days_from_cd": 2},
            {"store_id": "STR-43", "store_name": "Talca Mall Plaza Maule", "city": "Talca", "region_id": "VII", "cluster_id": "Regional Mall", "opening_date": "2024-01-15", "sales_area_m2": 160.0, "shelf_capacity_units": 4800, "transit_days_from_cd": 2},
            {"store_id": "STR-44", "store_name": "Temuco Portal Temuco", "city": "Temuco", "region_id": "IX", "cluster_id": "Regional Mall", "opening_date": "2023-09-30", "sales_area_m2": 175.0, "shelf_capacity_units": 5300, "transit_days_from_cd": 2},
            {"store_id": "STR-45", "store_name": "Valdivia Mall Plaza Valdivia", "city": "Valdivia", "region_id": "XIV", "cluster_id": "Regional Mall", "opening_date": "2024-02-28", "sales_area_m2": 150.0, "shelf_capacity_units": 4600, "transit_days_from_cd": 3},
            {"store_id": "STR-46", "store_name": "Puerto Montt Mall Costanera", "city": "Puerto Montt", "region_id": "X", "cluster_id": "Regional Mall", "opening_date": "2024-04-01", "sales_area_m2": 165.0, "shelf_capacity_units": 5000, "transit_days_from_cd": 3},

            # Tiendas Nuevas (< 26 semanas desde apertura) para verificar curva de Ramp-Up
            {"store_id": "STR-47", "store_name": "Puerto Varas Walker Martínez", "city": "Puerto Varas", "region_id": "X", "cluster_id": "Tienda Nueva", "opening_date": "2026-05-15", "sales_area_m2": 130.0, "shelf_capacity_units": 4000, "transit_days_from_cd": 3},
            {"store_id": "STR-48", "store_name": "Osorno Mall Portal Osorno", "city": "Osorno", "region_id": "X", "cluster_id": "Tienda Nueva", "opening_date": "2026-06-01", "sales_area_m2": 140.0, "shelf_capacity_units": 4200, "transit_days_from_cd": 3},
            {"store_id": "STR-49", "store_name": "Chicureo Mall Vivo Piedra Roja", "city": "Colina", "region_id": "RM", "cluster_id": "Tienda Nueva", "opening_date": "2026-06-20", "sales_area_m2": 160.0, "shelf_capacity_units": 4900, "transit_days_from_cd": 1},
            {"store_id": "STR-50", "store_name": "Santiago Centro Barrio Lastarria", "city": "Santiago", "region_id": "RM", "cluster_id": "Tienda Nueva", "opening_date": "2026-07-10", "sales_area_m2": 110.0, "shelf_capacity_units": 3500, "transit_days_from_cd": 1},
            {"store_id": "STR-51", "store_name": "Punta Arenas Mall Espacio Urbano", "city": "Punta Arenas", "region_id": "XII", "cluster_id": "Tienda Nueva", "opening_date": "2026-08-01", "sales_area_m2": 170.0, "shelf_capacity_units": 5100, "transit_days_from_cd": 4},
            {"store_id": "STR-52", "store_name": "Reñaca Sector 5 Avenida Borgoño", "city": "Viña del Mar", "region_id": "V", "cluster_id": "Tienda Nueva", "opening_date": "2026-08-20", "sales_area_m2": 125.0, "shelf_capacity_units": 3800, "transit_days_from_cd": 2},
        ]
        return pd.DataFrame(stores)

    def generate_sales_history(self, df_products: pd.DataFrame, df_stores: pd.DataFrame, weeks: int = 52) -> pd.DataFrame:
        """
        Generates 52 weeks of transactional daily sales per store and SKU.
        Incorporate seasonality, promos, ramp-up for new stores, and stockout censoring.
        """
        end_date = self.as_of_date
        start_date = end_date - timedelta(days=weeks * 7)

        cluster_volume_mult = {
            "Alto Tráfico Metro": 1.35,
            "Regional Mall": 1.25,
            "Residencial Premium": 1.05,
            "Tienda Nueva": 0.85
        }

        abc_base_units_day = {
            "A": (12.0, 3.0),
            "B": (4.5, 1.2),
            "C": (1.2, 0.4)
        }

        # Day of week multiplier (Sun=0 to Sat=6)
        # Retail peak on Friday, Saturday, Sunday
        dow_mult = [1.3, 0.85, 0.9, 0.95, 1.1, 1.45, 1.55]

        sales_records = []
        product_rows = df_products.to_dict("records")
        store_rows = df_stores.to_dict("records")

        # Precalculate dates
        num_days = (end_date - start_date).days
        date_list = [start_date + timedelta(days=i) for i in range(num_days)]

        for p in product_rows:
            sku = p["sku"]
            abc = p["abc_category"]
            price = p["retail_price_clp"]
            mean_base, std_base = abc_base_units_day[abc]

            # Assign 2 random promotional campaigns for this SKU during the year
            promo_weeks = set(random.sample(range(1, weeks - 2), 3))

            for s in store_rows:
                store_id = s["store_id"]
                cluster = s["cluster_id"]
                open_date = datetime.strptime(s["opening_date"], "%Y-%m-%d").date()
                store_mult = cluster_volume_mult.get(cluster, 1.0) * (s["sales_area_m2"] / 150.0)

                for day_idx, cur_date in enumerate(date_list):
                    # If store was not open yet, no sales
                    if cur_date < open_date:
                        continue

                    # Ramp-up factor for newly opened stores
                    weeks_since_open = max(0.0, (cur_date - open_date).days / 7.0)
                    ramp_up = 1.0 if weeks_since_open >= 26.0 else float(1.0 - np.exp(-weeks_since_open / 8.0))

                    # Seasonality: higher in summer (Dec-Feb) and winter snacks (July)
                    month = cur_date.month
                    if p["category"] == "Bebidas & Energéticas":
                        month_seasonality = 1.35 if month in [12, 1, 2] else (0.85 if month in [6, 7] else 1.0)
                    elif p["category"] == "Chocolates & Dulces":
                        month_seasonality = 1.30 if month in [6, 7, 8, 10] else 0.95
                    else:
                        month_seasonality = 1.0 + 0.1 * np.sin(cur_date.timetuple().tm_yday / 365.0 * 2 * np.pi)

                    dow_factor = dow_mult[cur_date.weekday()]

                    cur_week = (cur_date - start_date).days // 7
                    is_promo = 1 if cur_week in promo_weeks else 0
                    discount_pct = 0.20 if is_promo else 0.0
                    promo_lift = 1.0 + (1.8 * discount_pct) if is_promo else 1.0

                    expected_units = mean_base * store_mult * dow_factor * month_seasonality * promo_lift * ramp_up
                    # Stochastic variation
                    units_demanded = max(0, int(np.random.normal(expected_units, max(0.5, std_base))))

                    # Stockout censoring: ~3.5% chance of stockout on high volume days
                    stockout_flag = 1 if (np.random.rand() < 0.035 and units_demanded > 0) else 0
                    if stockout_flag:
                        # Observed sale is truncated
                        units_sold = int(units_demanded * np.random.uniform(0.0, 0.4))
                    else:
                        units_sold = units_demanded

                    effective_price = price * (1.0 - discount_pct)
                    revenue = units_sold * effective_price

                    sales_records.append({
                        "date": cur_date.strftime("%Y-%m-%d"),
                        "store_id": store_id,
                        "sku": sku,
                        "units_sold": units_sold,
                        "revenue_clp": round(revenue, 0),
                        "is_promo": is_promo,
                        "discount_pct": discount_pct,
                        "stockout_flag": stockout_flag
                    })

        return pd.DataFrame(sales_records)

    def generate_inventory_cd(self, df_products: pd.DataFrame) -> pd.DataFrame:
        """
        Generates CD central batches with realistic expiry dates for FEFO and biological waste evaluation.
        """
        batches = []
        batch_counter = 1001

        for _, p in df_products.iterrows():
            sku = p["sku"]
            shelf_life = p["shelf_life_total_days"]
            cogs = p["cogs_clp"]
            units_pallet = p["units_per_case"] * p["cases_per_pallet"]

            # Batch 1: Healthy fresh batch (arrived recently, 70-85% shelf life remaining)
            fresh_remaining = int(shelf_life * random.uniform(0.65, 0.85))
            batches.append({
                "batch_id": f"BTC-{batch_counter}",
                "sku": sku,
                "units_on_hand": int(units_pallet * random.randint(2, 5)),
                "units_reserved": int(units_pallet * 0.2),
                "units_available": int(units_pallet * random.randint(2, 5) * 0.8),
                "reception_date": (self.as_of_date - timedelta(days=shelf_life - fresh_remaining)).strftime("%Y-%m-%d"),
                "expiry_date": (self.as_of_date + timedelta(days=fresh_remaining)).strftime("%Y-%m-%d"),
                "pallet_location_id": f"RACK-A{batch_counter % 20:02d}-{batch_counter % 5}"
            })
            batch_counter += 1

            # Batch 2: Intermediate batch (alert tier ~60 to 90 days remaining)
            if p["abc_category"] in ["A", "B"]:
                mid_remaining = random.randint(55, 88)
                batches.append({
                    "batch_id": f"BTC-{batch_counter}",
                    "sku": sku,
                    "units_on_hand": int(units_pallet * random.randint(1, 3)),
                    "units_reserved": 0,
                    "units_available": int(units_pallet * random.randint(1, 3)),
                    "reception_date": (self.as_of_date - timedelta(days=shelf_life - mid_remaining)).strftime("%Y-%m-%d"),
                    "expiry_date": (self.as_of_date + timedelta(days=mid_remaining)).strftime("%Y-%m-%d"),
                    "pallet_location_id": f"RACK-B{batch_counter % 20:02d}-{batch_counter % 5}"
                })
                batch_counter += 1

            # Batch 3: Critical Expiry Risk for specific SKUs to validate FEFO monitor (25 to 45 days remaining, excess inventory)
            if sku in ["FOD-SNK-CMB-PIZ", "FOD-BEV-SNP-PCH", "FOD-CND-SWD-FSH", "FOD-SAU-HNZ-MST", "FOD-BK-POPT-BRN"]:
                short_remaining = random.randint(22, 38)
                batches.append({
                    "batch_id": f"BTC-{batch_counter}-CRIT",
                    "sku": sku,
                    "units_on_hand": int(units_pallet * 3),  # High stock with very little time remaining
                    "units_reserved": 0,
                    "units_available": int(units_pallet * 3),
                    "reception_date": (self.as_of_date - timedelta(days=shelf_life - short_remaining)).strftime("%Y-%m-%d"),
                    "expiry_date": (self.as_of_date + timedelta(days=short_remaining)).strftime("%Y-%m-%d"),
                    "pallet_location_id": f"RACK-C{batch_counter % 20:02d}-{batch_counter % 5}"
                })
                batch_counter += 1

        return pd.DataFrame(batches)

    def generate_store_inventory(self, df_products: pd.DataFrame, df_stores: pd.DataFrame) -> pd.DataFrame:
        """Generates store current on-hand stock."""
        records = []
        for _, s in df_stores.iterrows():
            store_id = s["store_id"]
            cluster = s["cluster_id"]
            stock_base = 35 if cluster == "Alto Tráfico Metro" else (25 if cluster == "Regional Mall" else 15)

            for _, p in df_products.iterrows():
                sku = p["sku"]
                abc = p["abc_category"]
                mult = 2.0 if abc == "A" else (1.0 if abc == "B" else 0.4)
                units = max(0, int(np.random.normal(stock_base * mult, stock_base * mult * 0.3)))
                records.append({
                    "store_id": store_id,
                    "sku": sku,
                    "units_on_hand": units,
                    "last_updated": self.as_of_date.strftime("%Y-%m-%d")
                })
        return pd.DataFrame(records)

    def generate_purchase_orders_pipeline(self, df_products: pd.DataFrame) -> pd.DataFrame:
        """
        Generates realistic USA import purchase orders in transit / customs / Miami.
        """
        orders = []
        po_num = 2026101

        pipeline_skus = [
            ("FOD-SNK-CHTS-226", 3456, "En Tránsito Marítimo", 18),
            ("FOD-BEV-DRPEP-355", 6912, "En Tránsito Marítimo", 25),
            ("FOD-SNK-TAK-FUE", 3200, "Inspección SAG Aduana", 6),
            ("FOD-BEV-MNST-PCH", 2880, "En Puerto Miami", 42),
            ("FOD-SNK-REESE-42G", 5760, "En Tránsito Marítimo", 14),
            ("FOD-SNK-PRG-SRC", 3136, "Inspección SAG Aduana", 4),
            ("FOD-GRO-KRAFT-206", 3072, "Emitida", 58),
            ("FOD-SAU-SBR-BBQ", 1440, "En Puerto Miami", 38),
            ("FOD-BEV-ARZ-GRN", 4800, "En Tránsito Marítimo", 22),
            ("FOD-BK-POPT-STR", 2304, "Inspección SAG Aduana", 5),
            ("FOD-CND-SOUR-99G", 2400, "En Puerto Miami", 40),
            ("FOD-CHO-MM-PNT", 4320, "En Tránsito Marítimo", 19),
        ]

        for sku, units, status, eta_days in pipeline_skus:
            order_date = self.as_of_date - timedelta(days=int(60 - eta_days))
            eta_date = self.as_of_date + timedelta(days=eta_days)
            orders.append({
                "po_number": f"PO-USA-{po_num}",
                "sku": sku,
                "order_date": order_date.strftime("%Y-%m-%d"),
                "units_ordered": units,
                "status": status,
                "estimated_arrival_date": eta_date.strftime("%Y-%m-%d")
            })
            po_num += 1

        return pd.DataFrame(orders)


def seed_database():
    """Generates all synthetic datasets and loads them into SQLite WAL database."""
    print("Iniciando generación de datos de terreno KIOS-FLOW...")
    gen = FoodRetailDataGenerator(seed=42)
    db = DatabaseManager()

    # 1. Products
    df_products = gen.generate_products()
    with db.get_connection() as conn:
        df_products.to_sql("dim_products", conn, if_exists="replace", index=False)
    print(f"-> dim_products: {len(df_products)} SKUs insertados.")

    # 2. Stores
    df_stores = gen.generate_stores()
    with db.get_connection() as conn:
        df_stores.to_sql("dim_stores", conn, if_exists="replace", index=False)
    print(f"-> dim_stores: {len(df_stores)} Tiendas insertadas.")

    # 3. CD Inventory (Batches)
    df_batches = gen.generate_inventory_cd(df_products)
    with db.get_connection() as conn:
        df_batches.to_sql("fct_inventory_cd", conn, if_exists="replace", index=False)
    print(f"-> fct_inventory_cd: {len(df_batches)} Lotes en CD insertados.")

    # 4. Store Inventory
    df_store_inv = gen.generate_store_inventory(df_products, df_stores)
    with db.get_connection() as conn:
        df_store_inv.to_sql("fct_inventory_store", conn, if_exists="replace", index=False)
    print(f"-> fct_inventory_store: {len(df_store_inv)} Registros de stock en tienda insertados.")

    # 5. Purchase Orders Pipeline
    df_pos = gen.generate_purchase_orders_pipeline(df_products)
    with db.get_connection() as conn:
        df_pos.to_sql("fct_purchase_orders_pipeline", conn, if_exists="replace", index=False)
    print(f"-> fct_purchase_orders_pipeline: {len(df_pos)} Órdenes en tránsito insertadas.")

    # 6. Sales Daily (52 weeks)
    print("-> Generando historial transaccional diario a nivel SKU-Tienda...")
    df_sales = gen.generate_sales_history(df_products, df_stores, weeks=52)
    with db.get_connection() as conn:
        df_sales.to_sql("fct_sales_daily", conn, if_exists="replace", index=False)
    print(f"-> fct_sales_daily: {len(df_sales):,} Transacciones diarias insertadas.")

    # Export Parquet copies for fast read access
    data_dir = os.path.dirname(db.db_path)
    df_products.to_parquet(os.path.join(data_dir, "dim_products.parquet"), index=False)
    df_stores.to_parquet(os.path.join(data_dir, "dim_stores.parquet"), index=False)
    df_batches.to_parquet(os.path.join(data_dir, "fct_inventory_cd.parquet"), index=False)
    df_store_inv.to_parquet(os.path.join(data_dir, "fct_inventory_store.parquet"), index=False)
    df_pos.to_parquet(os.path.join(data_dir, "fct_purchase_orders_pipeline.parquet"), index=False)
    df_sales.to_parquet(os.path.join(data_dir, "fct_sales_daily.parquet"), index=False)
    print("-> Archivos Parquet exportados con éxito.")
    print("Inicialización de Base de Datos completada.")


if __name__ == "__main__":
    seed_database()
