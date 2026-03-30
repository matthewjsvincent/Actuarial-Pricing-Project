import tkinter as tk
import pandas as pd
from utils.logger import logger
from utils.export import export_quotes_to_csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.dates import calculate_vehicle_age, get_current_year
from simulation.customer_generator import generate_customers_and_policies_to_target
from analytics.portfolio import forecast_current_portfolio
from simulation.annual_outcomes import simulate_annual_claims_for_current_portfolio
from simulation.retraining_data import build_retraining_datasets
from utils.paths import user_data_dir
from simulation.year_end import roll_forward_one_year
from tkinter import ttk, messagebox
import threading
from persistence.database import get_all_policies_raw
from pricing.premium_calculator import calculate_expected_loss, calculate_final_premium

from utils.analytics import get_quotes_dataframe, get_portfolio_summary, get_average_premium_by_customer, \
    get_average_final_premium_by_customer

from pricing.premium_calculator import calculate_premium
from persistence.database import (
    create_customer,
    get_all_customers,
    search_customers,
    delete_customer,
    update_customer,

    create_policy,
    get_all_policies,
    get_policy_by_id,
    search_policies,
    delete_policy,
    update_policy,

    create_quote,
    get_all_quotes,
    search_quotes,
    delete_quote,
)


class PricingApp:
    def __init__(self, root, model_bundle, freq_data):
        self.root = root
        self.model_bundle = model_bundle
        self.freq_data = freq_data
        self.year_end_df = None

        self.selected_customer_id = None
        self.selected_policy_id = None

        self.root.title("Actuarial Pricing Application")
        self.root.geometry("1300x800")

        self.last_result = None
        self.last_policy_id = None

        self.customer_search_var = tk.StringVar()
        self.policy_search_var = tk.StringVar()
        self.quote_search_var = tk.StringVar()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.customers_tab = ttk.Frame(self.notebook)
        self.policies_tab = ttk.Frame(self.notebook)
        self.quotes_tab = ttk.Frame(self.notebook)
        self.analytics_tab = ttk.Frame(self.notebook)
        self.portfolio_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.customers_tab, text="Customers")
        self.notebook.add(self.policies_tab, text="Policies")
        self.notebook.add(self.quotes_tab, text="Quotes")
        self.notebook.add(self.analytics_tab, text="Analytics")
        self.notebook.add(self.portfolio_tab, text="Portfolio Engine")
        self.notebook.add(self.logs_tab, text="Logs")

        self._build_customers_tab()
        self._build_policies_tab()
        self._build_quotes_tab()
        self._build_analytics_tab()
        self._build_portfolio_tab()
        self._build_logs_tab()

        self.status_var = tk.StringVar(value="Ready")

        self.is_busy = False

        status_frame = ttk.Frame(self.root)
        status_frame.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_label_var = tk.StringVar(value="")

        status_bar = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w"
        )
        status_bar.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.progress_label = ttk.Label(
            status_frame,
            textvariable=self.progress_label_var,
            width=8,
            anchor="e"
        )
        self.progress_label.pack(side="right", padx=(4, 8))

        self.progress = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            mode="determinate",
            length=220,
            maximum=100
        )
        self.progress.pack(side="right", padx=(4, 0), pady=2)

        self.refresh_all()

        self.set_status("Application ready")

    # -----------------------------
    # Customers tab
    # -----------------------------
    def _build_customers_tab(self):
        form = ttk.LabelFrame(self.customers_tab, text="Create Customer")
        form.pack(fill="x", padx=10, pady=10)

        self.customer_name_var = tk.StringVar()
        self.customer_email_var = tk.StringVar()
        self.customer_phone_var = tk.StringVar()

        ttk.Label(form, text="Full Name").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(form, textvariable=self.customer_name_var, width=30).grid(row=0, column=1, padx=8, pady=6)

        ttk.Label(form, text="Email").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(form, textvariable=self.customer_email_var, width=30).grid(row=1, column=1, padx=8, pady=6)

        ttk.Label(form, text="Phone").grid(row=2, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(form, textvariable=self.customer_phone_var, width=30).grid(row=2, column=1, padx=8, pady=6)

        ttk.Button(form, text="Save Customer", command=self.save_customer).grid(
            row=0, column=2, padx=15, pady=6, sticky="w"
        )
        ttk.Button(form, text="Refresh Customers", command=self.refresh_customers).grid(
            row=1, column=2, padx=15, pady=6, sticky="w"
        )

        search_frame = ttk.LabelFrame(self.customers_tab, text="Search Customers")
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Search").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(search_frame, textvariable=self.customer_search_var, width=40).grid(
            row=0, column=1, padx=8, pady=6, sticky="w"
        )

        ttk.Button(search_frame, text="Search", command=self.search_customers_action).grid(
            row=0, column=2, padx=8, pady=6
        )
        ttk.Button(search_frame, text="Clear", command=self.clear_customer_search).grid(
            row=0, column=3, padx=8, pady=6
        )
        ttk.Button(search_frame, text="Delete Selected", command=self.delete_selected_customer).grid(
            row=0, column=4, padx=8, pady=6
        )

        ttk.Button(form, text="Update Customer", command=self.update_customer_action).grid(
            row=2, column=2, padx=15, pady=6, sticky="w"
        )

        table_frame = ttk.LabelFrame(self.customers_tab, text="Customer List")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        customer_columns = ("id", "full_name", "email", "phone", "created_at")
        self.customer_tree = ttk.Treeview(table_frame, columns=customer_columns, show="headings")

        self.customer_tree.bind("<<TreeviewSelect>>", self.on_customer_select)



        for col in customer_columns:
            self.customer_tree.heading(col, text=col)
            self.customer_tree.column(col, width=180, anchor="center")

        customer_vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.customer_tree.yview)
        customer_hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.customer_tree.xview)

        self.customer_tree.configure(yscrollcommand=customer_vsb.set, xscrollcommand=customer_hsb.set)

        self.customer_tree.grid(row=0, column=0, sticky="nsew")
        customer_vsb.grid(row=0, column=1, sticky="ns")
        customer_hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def save_customer(self):
        full_name = self.customer_name_var.get().strip()
        email = self.customer_email_var.get().strip()
        phone = self.customer_phone_var.get().strip()

        if not full_name:
            messagebox.showerror("Validation Error", "Full Name is required.")
            return

        try:
            create_customer(full_name, email, phone)
            messagebox.showinfo("Saved", "Customer saved successfully.")
            self.set_status("Customer saved")

            self.customer_name_var.set("")
            self.customer_email_var.set("")
            self.customer_phone_var.set("")

            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc))

    def refresh_customers(self):
        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)

        for row in get_all_customers():
            self.customer_tree.insert("", "end", values=row)

        self._reload_customer_dropdowns()
        self.set_status("Customers refreshed")

    def search_customers_action(self):
        search_text = self.customer_search_var.get().strip()

        for item in self.customer_tree.get_children():
            self.customer_tree.delete(item)

        rows = search_customers(search_text) if search_text else get_all_customers()

        for row in rows:
            self.customer_tree.insert("", "end", values=row)

        self.set_status("Customer search completed")

    def clear_customer_search(self):
        self.customer_search_var.set("")
        self.refresh_customers()
        self.set_status("Customer search cleared")

    def delete_selected_customer(self):
        selected = self.customer_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a customer to delete.")
            return

        values = self.customer_tree.item(selected[0], "values")
        customer_id = int(values[0])
        customer_name = values[1]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete customer '{customer_name}'?\n\nThis will also delete related policies and quotes."
        )

        if not confirm:
            return

        try:
            delete_customer(customer_id)
            self.refresh_all()
            self.set_status(f"Customer deleted: {customer_name}")
        except Exception as exc:
            messagebox.showerror("Delete Error", str(exc))

    def on_customer_select(self, event):
        selected = self.customer_tree.selection()
        if not selected:
            return

        values = self.customer_tree.item(selected[0], "values")

        self.selected_customer_id = int(values[0])

        self.customer_name_var.set(values[1])
        self.customer_email_var.set(values[2])
        self.customer_phone_var.set(values[3])

        self.set_status(f"Customer selected: {values[1]}")

    def update_customer_action(self):
        if self.selected_customer_id is None:
            messagebox.showwarning("No Selection", "Select a customer first.")
            return

        try:
            update_customer(
                customer_id=self.selected_customer_id,
                full_name=self.customer_name_var.get(),
                email=self.customer_email_var.get(),
                phone=self.customer_phone_var.get(),
            )

            self.refresh_all()
            self.set_status("Customer updated")

        except Exception as exc:
            messagebox.showerror("Update Error", str(exc))

    # -----------------------------
    # Policies tab
    # -----------------------------
    def _build_policies_tab(self):
        form = ttk.LabelFrame(self.policies_tab, text="Create Policy")
        form.pack(fill="x", padx=10, pady=10)

        self.policy_customer_var = tk.StringVar()
        self.policy_name_var = tk.StringVar()

        self.policy_exposure_var = tk.StringVar(value="1")
        self.policy_vehicle_year_var = tk.StringVar(value="2020")
        self.policy_pricing_year_var = tk.StringVar(value=str(get_current_year()))
        self.policy_driv_age_var = tk.StringVar(value="45")
        self.policy_bonus_malus_var = tk.StringVar(value="80")
        self.policy_density_var = tk.StringVar(value="1000")
        self.policy_no_accident_years_var = tk.StringVar(value="0")
        self.policy_accident_count_recent_var = tk.StringVar(value="0")

        veh_gas_options = sorted(self.freq_data["VehGas"].dropna().astype(str).unique().tolist())
        veh_brand_options = sorted(self.freq_data["VehBrand"].dropna().astype(str).unique().tolist())
        region_options = sorted(self.freq_data["Region"].dropna().astype(str).unique().tolist())
        area_options = sorted(self.freq_data["Area"].dropna().astype(str).unique().tolist())

        self.policy_veh_gas_var = tk.StringVar(value=veh_gas_options[0] if veh_gas_options else "")
        self.policy_veh_brand_var = tk.StringVar(value=veh_brand_options[0] if veh_brand_options else "")
        self.policy_region_var = tk.StringVar(value=region_options[0] if region_options else "")
        self.policy_area_var = tk.StringVar(value=area_options[0] if area_options else "")

        ttk.Label(form, text="Customer").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.policy_customer_combo = ttk.Combobox(form, textvariable=self.policy_customer_var, state="readonly", width=40)
        self.policy_customer_combo.grid(row=0, column=1, padx=8, pady=6, sticky="w")

        ttk.Label(form, text="Policy Name").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(form, textvariable=self.policy_name_var, width=30).grid(row=1, column=1, padx=8, pady=6, sticky="w")

        self._add_entry(form, "Exposure", self.policy_exposure_var, 2)
        self._add_entry(form, "Vehicle Year", self.policy_vehicle_year_var, 3)
        self._add_entry(form, "Pricing Year", self.policy_pricing_year_var, 4)
        self._add_entry(form, "Driver Age", self.policy_driv_age_var, 5)
        self._add_entry(form, "Bonus Malus", self.policy_bonus_malus_var, 6)
        self._add_entry(form, "Density", self.policy_density_var, 7)
        self._add_entry(form, "No Accident Years", self.policy_no_accident_years_var, 8)
        self._add_entry(form, "Recent Accident Count", self.policy_accident_count_recent_var, 9)

        self._add_combo(form, "Fuel Type", self.policy_veh_gas_var, veh_gas_options, 10)
        self._add_combo(form, "Vehicle Brand", self.policy_veh_brand_var, veh_brand_options, 11)
        self._add_combo(form, "Region", self.policy_region_var, region_options, 12)
        self._add_combo(form, "Area", self.policy_area_var, area_options, 13)

        ttk.Button(form, text="Save Policy", command=self.save_policy).grid(
            row=0, column=2, padx=15, pady=6, sticky="w"
        )
        ttk.Button(form, text="Refresh Policies", command=self.refresh_policies).grid(
            row=1, column=2, padx=15, pady=6, sticky="w"
        )
        ttk.Button(form, text="Update Policy", command=self.update_policy_action).grid(
            row=2, column=2, padx=15, pady=6, sticky="w"
        )
        ttk.Button(form, text="Clear Selection", command=self.clear_policy_selection).grid(
            row=3, column=2, padx=15, pady=6, sticky="w"
        )

        search_frame = ttk.LabelFrame(self.policies_tab, text="Search Policies")
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Search").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(search_frame, textvariable=self.policy_search_var, width=40).grid(
            row=0, column=1, padx=8, pady=6, sticky="w"
        )

        ttk.Button(search_frame, text="Search", command=self.search_policies_action).grid(
            row=0, column=2, padx=8, pady=6
        )
        ttk.Button(search_frame, text="Clear", command=self.clear_policy_search).grid(
            row=0, column=3, padx=8, pady=6
        )
        ttk.Button(search_frame, text="Delete Selected", command=self.delete_selected_policy).grid(
            row=0, column=4, padx=8, pady=6
        )


        table_frame = ttk.LabelFrame(self.policies_tab, text="Policy List")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        policy_columns = (
            "id", "customer_id", "customer_name", "policy_name", "exposure",
            "vehicle_year", "pricing_year", "veh_age", "driv_age", "bonus_malus", "density",
            "veh_gas", "veh_brand", "region", "area",
            "no_accident_years", "accident_count_recent", "created_at"
        )

        self.policy_tree = ttk.Treeview(table_frame, columns=policy_columns, show="headings")

        self.policy_tree.bind("<<TreeviewSelect>>", self.on_policy_select)

        for col in policy_columns:
            self.policy_tree.heading(col, text=col)
            self.policy_tree.column(col, width=110, anchor="center")

        policy_vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.policy_tree.yview)
        policy_hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.policy_tree.xview)

        self.policy_tree.configure(yscrollcommand=policy_vsb.set, xscrollcommand=policy_hsb.set)

        self.policy_tree.grid(row=0, column=0, sticky="nsew")
        policy_vsb.grid(row=0, column=1, sticky="ns")
        policy_hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def save_policy(self):
        customer_text = self.policy_customer_var.get().strip()
        policy_name = self.policy_name_var.get().strip()

        if not customer_text:
            messagebox.showerror("Validation Error", "Select a customer.")
            return

        if not policy_name:
            messagebox.showerror("Validation Error", "Policy Name is required.")
            return

        try:
            customer_id = int(customer_text.split(" - ", 1)[0])

            exposure = float(self.policy_exposure_var.get())
            vehicle_year = int(self.policy_vehicle_year_var.get())
            pricing_year = int(self.policy_pricing_year_var.get())
            policy_year = int(self.policy_pricing_year_var.get())
            veh_age = calculate_vehicle_age(vehicle_year, pricing_year)
            driv_age = float(self.policy_driv_age_var.get())
            bonus_malus = float(self.policy_bonus_malus_var.get())
            density = float(self.policy_density_var.get())
            veh_gas = float(self.policy_veh_gas_var.get())
            veh_brand = float(self.policy_veh_brand_var.get())
            region = float(self.policy_region_var.get())
            area = float(self.policy_area_var.get())
            no_accident_years = int(self.policy_no_accident_years_var.get())
            accident_count_recent = int(self.policy_accident_count_recent_var.get())

            if exposure <= 0:
                raise ValueError("Exposure must be greater than 0.")

            create_policy(
                customer_id=customer_id,
                policy_name=policy_name,
                exposure=exposure,
                vehicle_year=vehicle_year,
                pricing_year=pricing_year,
                policy_year=pricing_year,
                veh_age=veh_age,
                driv_age=driv_age,
                bonus_malus=bonus_malus,
                density=density,
                veh_gas=self.policy_veh_gas_var.get(),
                veh_brand=self.policy_veh_brand_var.get(),
                region=self.policy_region_var.get(),
                area=self.policy_area_var.get(),
                no_accident_years=no_accident_years,
                accident_count_recent=accident_count_recent,
                source_policy_id=None,
            )

            messagebox.showinfo("Saved", "Policy saved successfully.")
            self.policy_name_var.set("")
            self.refresh_all()

        except Exception as exc:
            messagebox.showerror("Save Error", str(exc))

    def refresh_policies(self):
        for item in self.policy_tree.get_children():
            self.policy_tree.delete(item)

        for row in get_all_policies():
            self.policy_tree.insert("", "end", values=row)

        self._reload_policy_dropdowns()
        self.set_status("Policies refreshed")

    def search_policies_action(self):
        search_text = self.policy_search_var.get().strip()

        for item in self.policy_tree.get_children():
            self.policy_tree.delete(item)

        rows = search_policies(search_text) if search_text else get_all_policies()

        for row in rows:
            self.policy_tree.insert("", "end", values=row)

        self.set_status("Policy search completed")

    def clear_policy_search(self):
        self.policy_search_var.set("")
        self.refresh_policies()
        self.set_status("Policy search cleared")

    def delete_selected_policy(self):
        selected = self.policy_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a policy to delete.")
            return

        values = self.policy_tree.item(selected[0], "values")
        policy_id = int(values[0])
        policy_name = values[3]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete policy '{policy_name}'?\n\nThis will also delete related quotes."
        )

        if not confirm:
            return

        try:
            delete_policy(policy_id)
            self.refresh_all()
            self.set_status(f"Policy deleted: {policy_name}")
        except Exception as exc:
            messagebox.showerror("Delete Error", str(exc))

    def on_policy_select(self, event):
        selected = self.policy_tree.selection()
        if not selected:
            return

        values = self.policy_tree.item(selected[0], "values")

        self.selected_policy_id = int(values[0])

        customer_display = f"{values[1]} - {values[2]}"
        self.policy_customer_var.set(customer_display)

        self.policy_name_var.set(values[3])
        self.policy_exposure_var.set(values[4])
        self.policy_vehicle_year_var.set(values[5])
        self.policy_pricing_year_var.set(values[6])
        self.policy_driv_age_var.set(values[8])
        self.policy_bonus_malus_var.set(values[9])
        self.policy_density_var.set(values[10])
        self.policy_veh_gas_var.set(values[11])
        self.policy_veh_brand_var.set(values[12])
        self.policy_region_var.set(values[13])
        self.policy_area_var.set(values[14])
        self.policy_no_accident_years_var.set(values[15])
        self.policy_accident_count_recent_var.set(values[16])

        self.set_status(f"Policy selected: {values[3]}")

    def update_policy_action(self):
        if self.selected_policy_id is None:
            messagebox.showwarning("No Selection", "Select a policy first.")
            return

        try:
            customer_id = int(self.policy_customer_var.get().split(" - ")[0])

            vehicle_year = int(self.policy_vehicle_year_var.get())
            pricing_year = int(self.policy_pricing_year_var.get())
            veh_age = calculate_vehicle_age(vehicle_year, pricing_year)

            update_policy(
                policy_id=self.selected_policy_id,
                customer_id=customer_id,
                policy_name=self.policy_name_var.get(),
                exposure=float(self.policy_exposure_var.get()),
                vehicle_year=vehicle_year,
                pricing_year=pricing_year,
                veh_age=veh_age,
                driv_age=float(self.policy_driv_age_var.get()),
                bonus_malus=float(self.policy_bonus_malus_var.get()),
                density=float(self.policy_density_var.get()),
                veh_gas=self.policy_veh_gas_var.get(),
                veh_brand=self.policy_veh_brand_var.get(),
                region=self.policy_region_var.get(),
                area=self.policy_area_var.get(),
                no_accident_years=int(self.policy_no_accident_years_var.get()),
                accident_count_recent=int(self.policy_accident_count_recent_var.get()),
            )

            self.refresh_all()
            self.set_status("Policy updated")

        except Exception as exc:
            messagebox.showerror("Update Error", str(exc))

    def clear_policy_selection(self):
        self.selected_policy_id = None
        self.policy_name_var.set("")
        self.set_status("Policy selection cleared")

    # -----------------------------
    # Quotes tab
    # -----------------------------
    def _build_quotes_tab(self):
        form = ttk.LabelFrame(self.quotes_tab, text="Quote From Existing Policy")
        form.pack(fill="x", padx=10, pady=10)

        self.quote_policy_var = tk.StringVar()

        ttk.Label(form, text="Policy").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.quote_policy_combo = ttk.Combobox(form, textvariable=self.quote_policy_var, state="readonly", width=60)
        self.quote_policy_combo.grid(row=0, column=1, padx=8, pady=6, sticky="w")

        ttk.Button(form, text="Calculate Premium", command=self.calculate_quote_for_policy).grid(
            row=0, column=2, padx=15, pady=6, sticky="w"
        )
        ttk.Button(form, text="Save Quote", command=self.save_quote).grid(
            row=1, column=2, padx=15, pady=6, sticky="w"
        )
        ttk.Button(form, text="Refresh Quotes", command=self.refresh_quotes).grid(
            row=2, column=2, padx=15, pady=6, sticky="w"
        )
        ttk.Button(form, text="Export to CSV", command=self.export_quotes).grid(
            row=3, column=2, padx=15, pady=6, sticky="w"
        )

        result_frame = ttk.LabelFrame(self.quotes_tab, text="Calculation Results")
        result_frame.pack(fill="x", padx=10, pady=10)

        self.quote_details_label = ttk.Label(result_frame, text="Selected Policy: -")
        self.quote_details_label.pack(anchor="w", padx=10, pady=5)

        self.expected_claims_label = ttk.Label(result_frame, text="Expected Claims: -")
        self.expected_claims_label.pack(anchor="w", padx=10, pady=5)

        self.expected_severity_label = ttk.Label(result_frame, text="Expected Severity: -")
        self.expected_severity_label.pack(anchor="w", padx=10, pady=5)

        self.expected_loss_label = ttk.Label(result_frame, text="Expected Loss: -")
        self.expected_loss_label.pack(anchor="w", padx=10, pady=5)

        self.inflated_loss_label = ttk.Label(result_frame, text="Inflated Loss: -")
        self.inflated_loss_label.pack(anchor="w", padx=10, pady=5)

        self.technical_premium_label = ttk.Label(result_frame, text="Technical Premium: -")
        self.technical_premium_label.pack(anchor="w", padx=10, pady=5)

        self.final_premium_label = ttk.Label(result_frame, text="Final Premium: -")
        self.final_premium_label.pack(anchor="w", padx=10, pady=5)

        search_frame = ttk.LabelFrame(self.quotes_tab, text="Search Quotes")
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Search").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(search_frame, textvariable=self.quote_search_var, width=40).grid(
            row=0, column=1, padx=8, pady=6, sticky="w"
        )

        ttk.Button(search_frame, text="Search", command=self.search_quotes_action).grid(
            row=0, column=2, padx=8, pady=6
        )
        ttk.Button(search_frame, text="Clear", command=self.clear_quote_search).grid(
            row=0, column=3, padx=8, pady=6
        )
        ttk.Button(search_frame, text="Delete Selected", command=self.delete_selected_quote).grid(
            row=0, column=4, padx=8, pady=6
        )

        table_frame = ttk.LabelFrame(self.quotes_tab, text="Quote History")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        quote_columns = (
            "id", "policy_id", "customer_name", "policy_name",
            "expected_claims", "expected_severity", "expected_loss",
            "inflated_loss", "technical_premium", "final_premium", "created_at"
        )

        self.quote_tree = ttk.Treeview(table_frame, columns=quote_columns, show="headings")

        for col in quote_columns:
            self.quote_tree.heading(col, text=col)
            self.quote_tree.column(col, width=130, anchor="center")

        self.quote_tree.pack(fill="both", expand=True)

    def calculate_quote_for_policy(self):
        if not self.model_bundle.is_ready():
            messagebox.showerror("Model Error", "Models are not loaded.")
            return

        policy_text = self.quote_policy_var.get().strip()
        if not policy_text:
            messagebox.showerror("Validation Error", "Select a policy.")
            return

        try:
            policy_id = int(policy_text.split(" - ", 1)[0])
            policy_row = get_policy_by_id(policy_id)

            if policy_row is None:
                messagebox.showerror("Not Found", "Policy could not be found.")
                return

            self.last_policy_id = policy_id

            policy_data = pd.DataFrame({
                "Exposure": [float(policy_row[4])],
                "VehicleYear": [int(policy_row[5])],
                "PricingYear": [int(policy_row[6])],
                "VehAge": [float(policy_row[7])],
                "DrivAge": [float(policy_row[8])],
                "BonusMalus": [float(policy_row[9])],
                "Density": [float(policy_row[10])],
                "VehGas": [str(policy_row[11])],
                "VehBrand": [str(policy_row[12])],
                "Region": [str(policy_row[13])],
                "Area": [str(policy_row[14])],
            })

            result = calculate_premium(
                self.model_bundle.freq_model,
                self.model_bundle.sev_model,
                self.model_bundle.freq_columns,
                self.model_bundle.sev_columns,
                self.model_bundle.freq_category_levels,
                self.model_bundle.sev_category_levels,
                policy_data,
                expense_ratio=0.25,
                profit_margin=0.10,
                annual_inflation_rate=0.03,
                inflation_years=1,
                no_accident_years=int(policy_row[15]),
                accident_count_recent=int(policy_row[16]),
            )

            self.last_result = result

            self.quote_details_label.config(
                text=f"Selected Policy: {policy_row[2]} / {policy_row[3]} / Policy ID {policy_id}"
            )
            self.expected_claims_label.config(
                text=f"Expected Claims: {result['expected_claims']:.6f}"
            )
            self.expected_severity_label.config(
                text=f"Expected Severity: {result['expected_severity']:.2f}"
            )
            self.expected_loss_label.config(
                text=f"Expected Loss: {result['expected_loss']:.2f}"
            )
            self.inflated_loss_label.config(
                text=f"Inflated Loss: {result['inflated_loss']:.2f}"
            )
            self.technical_premium_label.config(
                text=f"Technical Premium: {result['technical_premium']:.2f}"
            )
            self.final_premium_label.config(
                text=f"Final Premium: {result['final_premium']:.2f}"
            )
            self.set_status("Quote calculated")

        except Exception as exc:
            messagebox.showerror("Calculation Error", str(exc))

    def save_quote(self):
        if self.last_result is None or self.last_policy_id is None:
            messagebox.showwarning("Nothing to Save", "Calculate a quote first.")
            return

        try:
            create_quote(
                policy_id=self.last_policy_id,
                expected_claims=self.last_result["expected_claims"],
                expected_severity=self.last_result["expected_severity"],
                expected_loss=self.last_result["expected_loss"],
                inflated_loss=self.last_result["inflated_loss"],
                technical_premium=self.last_result["technical_premium"],
                final_premium=self.last_result["final_premium"],
            )

            messagebox.showinfo("Saved", "Quote saved successfully.")
            self.set_status("Quote saved")
            self.refresh_quotes()
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc))

        self.refresh_analytics()

    def refresh_quotes(self):
        for item in self.quote_tree.get_children():
            self.quote_tree.delete(item)

        for row in get_all_quotes():
            self.quote_tree.insert("", "end", values=row)

        self.set_status("Quotes refreshed")

    def search_quotes_action(self):
        search_text = self.quote_search_var.get().strip()

        for item in self.quote_tree.get_children():
            self.quote_tree.delete(item)

        rows = search_quotes(search_text) if search_text else get_all_quotes()

        for row in rows:
            self.quote_tree.insert("", "end", values=row)

        self.set_status("Quote search completed")

    def clear_quote_search(self):
        self.quote_search_var.set("")
        self.refresh_quotes()
        self.set_status("Quote search cleared")

    def delete_selected_quote(self):
        selected = self.quote_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a quote to delete.")
            return

        values = self.quote_tree.item(selected[0], "values")
        quote_id = int(values[0])

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete quote ID {quote_id}?"
        )

        if not confirm:
            return

        try:
            delete_quote(quote_id)
            self.refresh_quotes()
            self.set_status(f"Quote deleted: {quote_id}")
        except Exception as exc:
            messagebox.showerror("Delete Error", str(exc))

        self.refresh_analytics()

    def export_quotes(self):
        try:
            file_path = export_quotes_to_csv()
            messagebox.showinfo("Export Complete", f"Saved to {file_path}")
            self.set_status("Quotes exported to CSV")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    # -----------------------------
    # Logs tab
    # -----------------------------

    def _build_logs_tab(self):
        frame = ttk.Frame(self.logs_tab)
        frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(frame, state="disabled", wrap="none")
        self.log_text.pack(fill="both", expand=True)

        # Subscribe to logger
        logger.subscribe(self._append_log)

    def _append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # -----------------------------
    # Analytics tab
    # -----------------------------

    def _build_analytics_tab(self):
        summary_frame = ttk.LabelFrame(self.analytics_tab, text="Portfolio Summary")
        summary_frame.pack(fill="x", padx=10, pady=10)

        self.analytics_labels = {
            "count": ttk.Label(summary_frame, text="Total Quotes: -"),
            "total_expected_loss": ttk.Label(summary_frame, text="Total Expected Loss: -"),
            "total_inflated_loss": ttk.Label(summary_frame, text="Total Inflated Loss: -"),
            "total_final_premium": ttk.Label(summary_frame, text="Total Final Premium: -"),
            "avg_final_premium": ttk.Label(summary_frame, text="Average Final Premium: -"),
        }

        for i, label in enumerate(self.analytics_labels.values()):
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

        ttk.Button(
            summary_frame,
            text="Refresh Analytics",
            command=self.refresh_analytics
        ).grid(row=0, column=1, padx=20, pady=5, sticky="nw")

        charts_frame = ttk.LabelFrame(self.analytics_tab, text="Charts")
        charts_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.figure = plt.Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=charts_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

    def refresh_analytics(self):
        summary = get_portfolio_summary()

        self.analytics_labels["count"].config(
            text=f"Total Quotes: {summary['count']}"
        )
        self.analytics_labels["total_expected_loss"].config(
            text=f"Total Expected Loss: {summary['total_expected_loss']:.2f}"
        )
        self.analytics_labels["total_inflated_loss"].config(
            text=f"Total Inflated Loss: {summary['total_inflated_loss']:.2f}"
        )
        self.analytics_labels["total_final_premium"].config(
            text=f"Total Final Premium: {summary['total_final_premium']:.2f}"
        )
        self.analytics_labels["avg_final_premium"].config(
            text=f"Average Final Premium: {summary['avg_final_premium']:.2f}"
        )

        df = get_quotes_dataframe()
        customer_df = get_average_final_premium_by_customer()

        self.figure.clear()

        ax1 = self.figure.add_subplot(311)
        if not df.empty:
            ax1.hist(df["final_premium"].dropna(), bins=15)
            ax1.set_title("Final Premium Distribution")
            ax1.set_xlabel("Final Premium")
            ax1.set_ylabel("Count")
        else:
            ax1.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax1.set_title("Final Premium Distribution")

        ax2 = self.figure.add_subplot(312)
        if not df.empty:
            ax2.hist(df["expected_loss"].dropna(), bins=15)
            ax2.set_title("Expected Loss Distribution")
            ax2.set_xlabel("Expected Loss")
            ax2.set_ylabel("Count")
        else:
            ax2.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax2.set_title("Expected Loss Distribution")

        ax3 = self.figure.add_subplot(313)
        if not customer_df.empty:
            ax3.bar(customer_df["customer_name"], customer_df["final_premium"])
            ax3.set_title("Average Final Premium by Customer")
            ax3.set_xlabel("Customer")
            ax3.set_ylabel("Average Final Premium")
            ax3.tick_params(axis="x", rotation=45)
        else:
            ax3.text(0.5, 0.5, "No data available", ha="center", va="center")
            ax3.set_title("Average Final Premium by Customer")

        self.figure.tight_layout()
        self.canvas.draw()

        self.set_status("Analytics refreshed")

    # -----------------------------
    # Portfolio tab
    # -----------------------------

    def _build_portfolio_tab(self):
        self.portfolio_forecast_df = None
        self.portfolio_claims_df = None
        self.retraining_freq_df = None
        self.retraining_sev_df = None

        gen_frame = ttk.LabelFrame(self.portfolio_tab, text="A. Generate Portfolio into Database")
        gen_frame.pack(fill="x", padx=10, pady=10)

        self.gen_batch_name_var = tk.StringVar(value="Simulated Portfolio Batch")
        self.gen_policy_count_var = tk.StringVar(value="1000")
        self.gen_pricing_year_var = tk.StringVar(value="2026")

        self._add_entry(gen_frame, "Batch Name", self.gen_batch_name_var, 0)
        self._add_entry(gen_frame, "Target Policy Count", self.gen_policy_count_var, 1)
        self._add_entry(gen_frame, "Pricing Year", self.gen_pricing_year_var, 2)

        ttk.Button(
            gen_frame,
            text="Generate Customers + Policies",
            command=self.generate_portfolio_to_database_action
        ).grid(row=0, column=2, padx=20, pady=6, sticky="w")

        forecast_frame = ttk.LabelFrame(self.portfolio_tab, text="B. Forecast Current Portfolio")
        forecast_frame.pack(fill="x", padx=10, pady=10)

        self.forecast_expense_ratio_var = tk.StringVar(value="0.25")
        self.forecast_profit_margin_var = tk.StringVar(value="0.10")
        self.forecast_inflation_rate_var = tk.StringVar(value="0.03")
        self.forecast_inflation_years_var = tk.StringVar(value="1")

        self._add_entry(forecast_frame, "Expense Ratio", self.forecast_expense_ratio_var, 0)
        self._add_entry(forecast_frame, "Profit Margin", self.forecast_profit_margin_var, 1)
        self._add_entry(forecast_frame, "Inflation Rate", self.forecast_inflation_rate_var, 2)
        self._add_entry(forecast_frame, "Inflation Years", self.forecast_inflation_years_var, 3)

        ttk.Button(
            forecast_frame,
            text="Forecast Current Portfolio",
            command=self.forecast_current_portfolio_action
        ).grid(row=0, column=2, padx=20, pady=6, sticky="w")

        annual_frame = ttk.LabelFrame(self.portfolio_tab, text="C. Simulate Annual Claims")
        annual_frame.pack(fill="x", padx=10, pady=10)

        self.simulation_year_var = tk.StringVar(value="2026")
        self._add_entry(annual_frame, "Simulation Year", self.simulation_year_var, 0)

        ttk.Button(
            annual_frame,
            text="Simulate Annual Claims",
            command=self.simulate_annual_claims_action
        ).grid(row=0, column=2, padx=20, pady=6, sticky="w")

        year_end_frame = ttk.LabelFrame(self.portfolio_tab, text="D. Year-End Roll Forward")
        year_end_frame.pack(fill="x", padx=10, pady=10)

        self.roll_forward_year_var = tk.StringVar(value="2026")
        self._add_entry(year_end_frame, "Simulation Year to Roll Forward", self.roll_forward_year_var, 0)

        ttk.Button(
            year_end_frame,
            text="Roll Forward to Next Year",
            command=self.roll_forward_year_end_action
        ).grid(row=0, column=2, padx=20, pady=6, sticky="w")

        retrain_frame = ttk.LabelFrame(self.portfolio_tab, text="E. Build Retraining Datasets")
        retrain_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            retrain_frame,
            text="Build Retraining Datasets",
            command=self.build_retraining_datasets_action
        ).grid(row=0, column=0, padx=20, pady=6, sticky="w")

        ttk.Button(
            retrain_frame,
            text="Export Retraining CSVs",
            command=self.export_retraining_datasets_action
        ).grid(row=0, column=1, padx=20, pady=6, sticky="w")

        ttk.Button(
            retrain_frame,
            text="Retrain Models Now",
            command=self.retrain_models_now_action
        ).grid(row=0, column=2, padx=20, pady=6, sticky="w")

        summary_frame = ttk.LabelFrame(self.portfolio_tab, text="Portfolio Engine Summary")
        summary_frame.pack(fill="x", padx=10, pady=10)

        self.portfolio_engine_labels = {
            "generated": ttk.Label(summary_frame, text="Generated: -"),
            "forecast": ttk.Label(summary_frame, text="Forecast: -"),
            "claims": ttk.Label(summary_frame, text="Annual Claims: -"),
            "roll_forward": ttk.Label(summary_frame, text="Roll Forward: -"),
            "retraining": ttk.Label(summary_frame, text="Retraining Datasets: -"),
        }

        for i, label in enumerate(self.portfolio_engine_labels.values()):
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

    def generate_portfolio_to_database_action(self):
        try:
            batch_name = self.gen_batch_name_var.get().strip()
            n_policies = int(self.gen_policy_count_var.get())
            pricing_year = int(self.gen_pricing_year_var.get())

            self.set_status("Generating customers and policies...")

            result = generate_customers_and_policies_to_target(
                n_policies=n_policies,
                pricing_year=pricing_year,
                batch_name=batch_name or "Simulated Portfolio Batch"
            )

            self.refresh_all()

            self.portfolio_engine_labels["generated"].config(
                text=(
                    f"Generated: batch_id={result['batch_id']}, "
                    f"customers={result['created_customers']}, "
                    f"policies={result['created_policies']}"
                )
            )

            self.set_status("Portfolio generation complete")

        except Exception as exc:
            messagebox.showerror("Generation Error", str(exc))

    def forecast_current_portfolio_action(self):
        try:
            expense_ratio = float(self.forecast_expense_ratio_var.get())
            profit_margin = float(self.forecast_profit_margin_var.get())
            inflation_rate = float(self.forecast_inflation_rate_var.get())
            inflation_years = int(self.forecast_inflation_years_var.get())
        except Exception as exc:
            messagebox.showerror("Input Error", str(exc))
            return

        def worker():
            self.post_status("Loading active portfolio...")
            rows = get_all_policies_raw()

            if not rows:
                raise ValueError("No active policies found in the database.")

            results = []
            total_rows = len(rows)

            self.post_status(f"Loaded {total_rows} active policies")

            for idx, row in enumerate(rows, start=1):
                policy_id = row[0]

                policy_data = pd.DataFrame([{
                    "Exposure": row[3],
                    "VehicleYear": row[4],
                    "PricingYear": row[5],
                    "VehAge": row[7],
                    "DrivAge": row[8],
                    "BonusMalus": row[9],
                    "Density": row[10],
                    "VehGas": row[11],
                    "VehBrand": row[12],
                    "Region": row[13],
                    "Area": row[14],
                }])

                if idx == 1:
                    self.post_status("Calculating expected claims...")
                elif idx == max(2, total_rows // 3):
                    self.post_status("Calculating expected severity...")
                elif idx == max(3, (2 * total_rows) // 3):
                    self.post_status("Calculating premiums...")

                loss_result = calculate_expected_loss(
                    self.model_bundle.freq_model,
                    self.model_bundle.sev_model,
                    self.model_bundle.freq_columns,
                    self.model_bundle.sev_columns,
                    self.model_bundle.freq_category_levels,
                    self.model_bundle.sev_category_levels,
                    policy_data
                )

                premium_result = calculate_final_premium(
                    expected_loss=loss_result["expected_loss"],
                    expense_ratio=expense_ratio,
                    profit_margin=profit_margin,
                    annual_inflation_rate=inflation_rate,
                    inflation_years=inflation_years,
                    no_accident_years=int(row[15]),
                    accident_count_recent=int(row[16]),
                )

                results.append({
                    "policy_id": policy_id,
                    "expected_claims": loss_result["expected_claims"],
                    "expected_severity": loss_result["expected_severity"],
                    "expected_loss": loss_result["expected_loss"],
                    "inflated_loss": premium_result["inflated_loss"],
                    "technical_premium": premium_result["technical_premium"],
                    "final_premium": premium_result["final_premium"],
                })

                if idx % 25 == 0 or idx == total_rows:
                    self.post_status(f"Forecasting policy {idx:,} of {total_rows:,}...")

            self.post_status("Preparing forecast results...")
            df = pd.DataFrame(results)

            if df.empty:
                summary = {
                    "policy_count": 0,
                    "total_expected_loss": 0.0,
                    "total_inflated_loss": 0.0,
                    "total_technical_premium": 0.0,
                    "total_final_premium": 0.0,
                    "avg_final_premium": 0.0,
                }
            else:
                summary = {
                    "policy_count": int(len(df)),
                    "total_expected_loss": float(df["expected_loss"].sum()),
                    "total_inflated_loss": float(df["inflated_loss"].sum()),
                    "total_technical_premium": float(df["technical_premium"].sum()),
                    "total_final_premium": float(df["final_premium"].sum()),
                    "avg_final_premium": float(df["final_premium"].mean()),
                }

            return df, summary

        def on_success(result):
            df, summary = result
            self.portfolio_forecast_df = df

            self.portfolio_engine_labels["forecast"].config(
                text=(
                    f"Forecast: policies={summary['policy_count']}, "
                    f"expected_loss={summary['total_expected_loss']:.2f}, "
                    f"final_premium={summary['total_final_premium']:.2f}, "
                    f"avg_final_premium={summary['avg_final_premium']:.2f}"
                )
            )

            self.set_status("Portfolio forecast complete")

        self.run_background_task(
            "Portfolio forecast",
            worker,
            on_success=on_success
        )

    def simulate_annual_claims_action(self):
        try:
            simulation_year = int(self.simulation_year_var.get())

            self.set_status("Simulating annual claims...")

            df = simulate_annual_claims_for_current_portfolio(
                self.model_bundle.freq_model,
                self.model_bundle.sev_model,
                self.model_bundle.freq_columns,
                self.model_bundle.sev_columns,
                self.model_bundle.freq_category_levels,
                self.model_bundle.sev_category_levels,
                simulation_year=simulation_year
            )

            self.portfolio_claims_df = df

            total_claims = int(df["claim_count"].sum()) if not df.empty else 0
            total_amount = float(df["total_claim_amount"].sum()) if not df.empty else 0.0

            self.portfolio_engine_labels["claims"].config(
                text=(
                    f"Annual Claims: rows={len(df)}, "
                    f"claim_count={total_claims}, "
                    f"claim_amount={total_amount:.2f}"
                )
            )

            self.set_status("Annual claim simulation complete")

        except Exception as exc:
            messagebox.showerror("Simulation Error", str(exc))

    def build_retraining_datasets_action(self):
        try:
            self.set_status("Building retraining datasets...")

            freq_df, sev_df = build_retraining_datasets()

            self.retraining_freq_df = freq_df
            self.retraining_sev_df = sev_df

            total_claims = int(freq_df["ClaimNb"].sum()) if not freq_df.empty else 0

            self.portfolio_engine_labels["retraining"].config(
                text=(
                    f"Retraining Datasets: "
                    f"freq_rows={len(freq_df)}, "
                    f"sev_rows={len(sev_df)}, "
                    f"total_claims={total_claims}"
                )
            )

            self.set_status("Retraining datasets ready")

        except Exception as exc:
            messagebox.showerror("Retraining Error", str(exc))

    def export_retraining_datasets_action(self):
        if self.retraining_freq_df is None or self.retraining_sev_df is None:
            messagebox.showwarning("No Data", "Build retraining datasets first.")
            return

        try:
            freq_path = user_data_dir() / "retraining_freq.csv"
            sev_path = user_data_dir() / "retraining_sev.csv"

            self.retraining_freq_df.to_csv(freq_path, index=False)
            self.retraining_sev_df.to_csv(sev_path, index=False)

            messagebox.showinfo(
                "Export Complete",
                f"Saved:\n{freq_path}\n{sev_path}"
            )
            self.set_status("Retraining datasets exported")

        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def roll_forward_year_end_action(self):
        try:
            simulation_year = int(self.roll_forward_year_var.get())
            next_year = simulation_year + 1

            confirmed = messagebox.askyesno(
                "Confirm Roll Forward",
                (
                    f"This will:\n\n"
                    f"1. Snapshot the current active customers and policies for {simulation_year}\n"
                    f"2. Update the active portfolio in place to {next_year}\n\n"
                    f"This will not append new active policies.\n\n"
                    f"Continue?"
                )
            )

            if not confirmed:
                self.set_status("Roll forward cancelled")
                return

            self.set_status("Rolling portfolio forward to next year...")

            df, summary = roll_forward_one_year(simulation_year=simulation_year)
            self.year_end_df = df

            self.portfolio_engine_labels["roll_forward"].config(
                text=(
                    f"Roll Forward: "
                    f"rolled_policies={summary['rolled_policy_count']}, "
                    f"customer_snapshots={summary['customer_snapshots_created']}, "
                    f"policy_snapshots={summary['policy_snapshots_created']}, "
                    f"updated={summary['updated_policy_count']}"
                )
            )

            self.refresh_all()
            self.set_status("Year-end roll forward complete")

            messagebox.showinfo(
                "Roll Forward Complete",
                (
                    f"Snapshot created for {summary['snapshot_year']}.\n"
                    f"Updated active policies in place for {next_year}.\n\n"
                    f"Policies updated: {summary['updated_policy_count']}"
                )
            )

        except Exception as exc:
            messagebox.showerror("Roll Forward Error", str(exc))

    def retrain_models_now_action(self):
        if self.retraining_freq_df is None or self.retraining_sev_df is None:
            messagebox.showwarning("No Data", "Build retraining datasets first.")
            return

        try:
            self.set_status("Retraining models from simulated history...")

            self.model_bundle.retrain_from_dataframes(
                self.retraining_freq_df,
                self.retraining_sev_df
            )

            self.set_status("Model retraining complete")
            messagebox.showinfo("Retrain Complete", "Models retrained from simulated history.")

        except Exception as exc:
            messagebox.showerror("Retrain Error", str(exc))

    # -----------------------------
    # Shared helpers
    # -----------------------------
    def _add_entry(self, parent, label_text, variable, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=8, pady=6, sticky="w")
        ttk.Entry(parent, textvariable=variable, width=25).grid(row=row, column=1, padx=8, pady=6, sticky="w")

    def _add_combo(self, parent, label_text, variable, values, row):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=8, pady=6, sticky="w")
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=22)
        combo.grid(row=row, column=1, padx=8, pady=6, sticky="w")

    def _reload_customer_dropdowns(self):
        customers = get_all_customers()
        values = [f"{row[0]} - {row[1]}" for row in customers]
        self.policy_customer_combo["values"] = values

        if values and not self.policy_customer_var.get():
            self.policy_customer_var.set(values[0])

    def _reload_policy_dropdowns(self):
        policies = get_all_policies()
        values = [f"{row[0]} - {row[2]} - {row[3]}" for row in policies]
        self.quote_policy_combo["values"] = values

        if values and not self.quote_policy_var.get():
            self.quote_policy_var.set(values[0])

    def refresh_all(self):
        self.refresh_customers()
        self.refresh_policies()
        self.refresh_quotes()
        self.refresh_analytics()

    def set_status(self, message):
        self.status_var.set(message)
        logger.log(message)

    def set_busy(self, message="Working..."):
        self.is_busy = True
        self.status_var.set(message)
        self.progress.start(10)
        self.root.config(cursor="watch")

    def clear_busy(self, message="Ready"):
        self.is_busy = False
        self.progress.stop()
        self.status_var.set(message)
        self.root.config(cursor="")

    def run_background_task(self, task_name, worker, on_success=None):
        if self.is_busy:
            messagebox.showwarning("Busy", "Please wait for the current task to finish.")
            return

        self.set_busy(f"{task_name} in progress...")
        logger.log(f"{task_name} started")

        def task_wrapper():
            try:
                result = worker()
                self.root.after(0, lambda: self._handle_task_success(task_name, result, on_success))
            except Exception as exc:
                self.root.after(0, lambda: self._handle_task_error(task_name, exc))

        threading.Thread(target=task_wrapper, daemon=True).start()

    def _handle_task_success(self, task_name, result, on_success):
        try:
            if on_success:
                on_success(result)
            logger.log(f"{task_name} completed")
            self.clear_busy(f"{task_name} complete")
        except Exception as exc:
            self._handle_task_error(task_name, exc)

    def _handle_task_error(self, task_name, exc):
        logger.log(f"{task_name} failed: {exc}", level="ERROR")
        self.clear_busy(f"{task_name} failed")
        messagebox.showerror(f"{task_name} Error", str(exc))

    def post_status(self, message):
        self.root.after(0, lambda: self.status_var.set(message))
        self.root.after(0, lambda: logger.log(message))

    def set_busy(self, message="Working...", determinate=False):
        self.is_busy = True
        self.status_var.set(message)
        self.root.config(cursor="watch")

        self.progress.stop()
        self.progress_var.set(0.0)
        self.progress_label_var.set("")

        if determinate:
            self.progress.configure(mode="determinate", maximum=100)
        else:
            self.progress.configure(mode="indeterminate")
            self.progress.start(10)

    def clear_busy(self, message="Ready"):
        self.is_busy = False
        self.progress.stop()
        self.progress.configure(mode="determinate", maximum=100)
        self.progress_var.set(0.0)
        self.progress_label_var.set("")
        self.status_var.set(message)
        self.root.config(cursor="")

    def post_status(self, message):
        self.root.after(0, lambda: self.status_var.set(message))
        self.root.after(0, lambda: logger.log(message))

    def post_progress(self, current, total, message=None):
        def _update():
            if total <= 0:
                percent = 0.0
            else:
                percent = (current / total) * 100.0

            self.progress.configure(mode="determinate", maximum=100)
            self.progress_var.set(percent)
            self.progress_label_var.set(f"{percent:.0f}%")

            if message:
                self.status_var.set(message)

        self.root.after(0, _update)
