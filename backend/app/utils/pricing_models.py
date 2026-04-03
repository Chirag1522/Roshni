"""
Realistic electricity pricing models for ROSHNI.
Based on actual Rajasthan DISCOM tariff structure.
"""

from typing import Dict, Tuple


class RajasthanDomesticTariff:
    """
    Rajasthan domestic electricity tariff (JVVNL/PPDCL based).
    Slab-based rates that increase with consumption.

    Real-world reference: JVVNL FY 2024-25 rates
    """

    # Consumption slabs (units/kWh per month)
    SLAB_1_LIMIT = 100          # 0-100 units
    SLAB_2_LIMIT = 200          # 101-200 units
    # 201+ = Slab 3

    # Energy charges (₹/kWh) - realistic rates
    SLAB_1_RATE = 3.0           # 0-100 units: ₹3/kWh
    SLAB_2_RATE = 5.0           # 101-200 units: ₹5/kWh
    SLAB_3_RATE = 7.95          # 200+ units: ₹7.95/kWh

    # Fixed charges (₹/month) based on sanctioned load
    FIXED_CHARGE_1HP = 120.0     # Up to 1 HP (0.75 kW)
    FIXED_CHARGE_2HP = 180.0     # 1-2 HP (1.5 kW)
    FIXED_CHARGE_3HP = 240.0     # 2-3 HP (2.25 kW)
    FIXED_CHARGE_5HP = 360.0     # 3-5 HP (3.75 kW)
    FIXED_CHARGE_7_5HP = 540.0   # 5-7.5 HP (5.6 kW)

    # Surcharges and taxes
    ELECTRICITY_DUTY_PERCENT = 3.0      # State electricity duty
    SURCHARGE_PERCENT = 1.5              # Infrastructure surcharge
    METER_RENT = 20.0                    # Monthly meter rent

    @staticmethod
    def get_fixed_charge(sanctioned_load_kw: float = 2.0) -> float:
        """Get fixed charge based on sanctioned load."""
        if sanctioned_load_kw <= 0.75:
            return RajasthanDomesticTariff.FIXED_CHARGE_1HP
        elif sanctioned_load_kw <= 1.5:
            return RajasthanDomesticTariff.FIXED_CHARGE_2HP
        elif sanctioned_load_kw <= 2.25:
            return RajasthanDomesticTariff.FIXED_CHARGE_3HP
        elif sanctioned_load_kw <= 3.75:
            return RajasthanDomesticTariff.FIXED_CHARGE_5HP
        else:
            return RajasthanDomesticTariff.FIXED_CHARGE_7_5HP

    @staticmethod
    def calculate_energy_charge(consumption_kwh: float) -> float:
        """
        Calculate energy charge using slab rates.
        Higher consumption = progressively higher rates.
        """
        if consumption_kwh <= RajasthanDomesticTariff.SLAB_1_LIMIT:
            # All in slab 1
            return consumption_kwh * RajasthanDomesticTariff.SLAB_1_RATE
        elif consumption_kwh <= RajasthanDomesticTariff.SLAB_2_LIMIT:
            # Slab 1 + Slab 2
            slab_1_consumption = RajasthanDomesticTariff.SLAB_1_LIMIT
            slab_2_consumption = consumption_kwh - slab_1_consumption
            return (
                slab_1_consumption * RajasthanDomesticTariff.SLAB_1_RATE +
                slab_2_consumption * RajasthanDomesticTariff.SLAB_2_RATE
            )
        else:
            # All three slabs
            slab_1_consumption = RajasthanDomesticTariff.SLAB_1_LIMIT
            slab_2_consumption = (
                RajasthanDomesticTariff.SLAB_2_LIMIT -
                RajasthanDomesticTariff.SLAB_1_LIMIT
            )
            slab_3_consumption = consumption_kwh - RajasthanDomesticTariff.SLAB_2_LIMIT
            return (
                slab_1_consumption * RajasthanDomesticTariff.SLAB_1_RATE +
                slab_2_consumption * RajasthanDomesticTariff.SLAB_2_RATE +
                slab_3_consumption * RajasthanDomesticTariff.SLAB_3_RATE
            )

    @staticmethod
    def calculate_total_bill(
        consumption_kwh: float,
        grid_consumption_kwh: float = None,
        sanctioned_load_kw: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate complete domestic bill with all charges.

        Args:
            consumption_kwh: Total consumption (kWh)
            grid_consumption_kwh: Grid-sourced consumption (for mixed prosumer)
            sanctioned_load_kw: Sanctioned load of connection

        Returns:
            Dictionary with breakdown of all charges
        """
        # Use grid consumption if specified, otherwise use total
        billable_consumption = grid_consumption_kwh if grid_consumption_kwh else consumption_kwh

        # Energy charges
        energy_charge = RajasthanDomesticTariff.calculate_energy_charge(billable_consumption)

        # Fixed charges
        fixed_charge = RajasthanDomesticTariff.get_fixed_charge(sanctioned_load_kw)
        meter_rent = RajasthanDomesticTariff.METER_RENT

        # Subtotal before taxes
        subtotal = energy_charge + fixed_charge + meter_rent

        # Taxes and surcharges
        electricity_duty = subtotal * (RajasthanDomesticTariff.ELECTRICITY_DUTY_PERCENT / 100.0)
        surcharge = subtotal * (RajasthanDomesticTariff.SURCHARGE_PERCENT / 100.0)

        # Total bill
        total_bill = subtotal + electricity_duty + surcharge

        return {
            "energy_charge": round(energy_charge, 2),
            "fixed_charge": round(fixed_charge, 2),
            "meter_rent": round(meter_rent, 2),
            "subtotal": round(subtotal, 2),
            "electricity_duty": round(electricity_duty, 2),
            "surcharge": round(surcharge, 2),
            "total_bill": round(total_bill, 2),
        }


class RajasthanCommercialTariff:
    """
    Rajasthan commercial electricity tariff.
    Higher rates, larger fixed charges, higher dues & surcharges.
    """

    # Consumption slabs
    SLAB_1_LIMIT = 200          # 0-200 units
    SLAB_2_LIMIT = 500          # 201-500 units
    # 500+ = Slab 3

    # Energy rates (₹/kWh) - higher than domestic
    SLAB_1_RATE = 8.0
    SLAB_2_RATE = 11.0
    SLAB_3_RATE = 14.5

    # Fixed charges (₹/month) - based on contracted demand
    FIXED_CHARGE_BASE = 500.0   # Base fixed charge
    FIXED_CHARGE_PER_KW = 150.0 # Per kW of contracted demand

    # Surcharges and taxes
    ELECTRICITY_DUTY_PERCENT = 5.0      # Higher duty for commercial
    SURCHARGE_PERCENT = 2.5              # Higher surcharge
    POWER_FACTOR_PENALTY_PERCENT = 1.0  # If PF < 0.95

    @staticmethod
    def calculate_energy_charge(consumption_kwh: float) -> float:
        """Calculate commercial energy charge using slab rates."""
        if consumption_kwh <= RajasthanCommercialTariff.SLAB_1_LIMIT:
            return consumption_kwh * RajasthanCommercialTariff.SLAB_1_RATE
        elif consumption_kwh <= RajasthanCommercialTariff.SLAB_2_LIMIT:
            slab_1 = RajasthanCommercialTariff.SLAB_1_LIMIT
            slab_2 = consumption_kwh - slab_1
            return (
                slab_1 * RajasthanCommercialTariff.SLAB_1_RATE +
                slab_2 * RajasthanCommercialTariff.SLAB_2_RATE
            )
        else:
            slab_1 = RajasthanCommercialTariff.SLAB_1_LIMIT
            slab_2 = (
                RajasthanCommercialTariff.SLAB_2_LIMIT -
                RajasthanCommercialTariff.SLAB_1_LIMIT
            )
            slab_3 = consumption_kwh - RajasthanCommercialTariff.SLAB_2_LIMIT
            return (
                slab_1 * RajasthanCommercialTariff.SLAB_1_RATE +
                slab_2 * RajasthanCommercialTariff.SLAB_2_RATE +
                slab_3 * RajasthanCommercialTariff.SLAB_3_RATE
            )

    @staticmethod
    def calculate_total_bill(
        consumption_kwh: float,
        contracted_demand_kw: float = 5.0,
        power_factor: float = 0.95
    ) -> Dict[str, float]:
        """
        Calculate complete commercial bill.

        Args:
            consumption_kwh: Monthly consumption
            contracted_demand_kw: Contracted demand in kW
            power_factor: Power factor (0-1), normal is 0.95
        """
        # Energy charges
        energy_charge = RajasthanCommercialTariff.calculate_energy_charge(consumption_kwh)

        # Fixed charges
        fixed_charge = (
            RajasthanCommercialTariff.FIXED_CHARGE_BASE +
            (contracted_demand_kw * RajasthanCommercialTariff.FIXED_CHARGE_PER_KW)
        )

        # Subtotal
        subtotal = energy_charge + fixed_charge

        # Taxes and surcharges
        electricity_duty = subtotal * (RajasthanCommercialTariff.ELECTRICITY_DUTY_PERCENT / 100.0)
        surcharge = subtotal * (RajasthanCommercialTariff.SURCHARGE_PERCENT / 100.0)

        # Power factor penalty (if below 0.95)
        pf_penalty = 0.0
        if power_factor < 0.95:
            pf_penalty = subtotal * (RajasthanCommercialTariff.POWER_FACTOR_PENALTY_PERCENT / 100.0)

        # Total
        total_bill = subtotal + electricity_duty + surcharge + pf_penalty

        return {
            "energy_charge": round(energy_charge, 2),
            "fixed_charge": round(fixed_charge, 2),
            "subtotal": round(subtotal, 2),
            "electricity_duty": round(electricity_duty, 2),
            "surcharge": round(surcharge, 2),
            "power_factor_penalty": round(pf_penalty, 2),
            "total_bill": round(total_bill, 2),
        }


class SolarExportRates:
    """
    Rates for solar export to grid (DISCOM buyback rates).
    Based on MNRE guidelines and actual state policies.
    """

    # Residential solar export (rooftop solar to grid)
    RESIDENTIAL_EXPORT_RATE = 6.5  # ₹/kWh - typical for net metering

    # Grid sale rates (commercial solar farms)
    COMMERCIAL_EXPORT_RATE = 5.5   # ₹/kWh - wholesale rate

    # Pool pricing (peer-to-peer renewable energy trading)
    POOL_TRADING_RATE = 9.0  # ₹/kWh - negotiated between prosumer & consumer


class PoolPricingModel:
    """
    Dynamic pool pricing based on supply-demand.
    ROSHNI uses AI-based dynamic pricing.
    """

    # Base rates for ROSHNI pool
    BASE_POOL_PRICE = 9.0           # ₹/kWh base rate
    MIN_POOL_PRICE = 8.0            # Minimum (high supply, low demand)
    MAX_POOL_PRICE = 10.5           # Maximum (low supply, high demand)

    # Price adjustment factors
    DEMAND_TO_SUPPLY_RATIO_MULTIPLIER = 0.8
    SEASONAL_DEMAND_FACTOR = 1.1     # Higher in summer

    @staticmethod
    def calculate_dynamic_price(
        available_supply_kwh: float,
        pending_demand_kwh: float,
        season: str = "monsoon"  # summer, winter, monsoon
    ) -> float:
        """
        Calculate dynamic pool price based on supply-demand ratio.

        Args:
            available_supply_kwh: Total surplus solar available
            pending_demand_kwh: Total demand requests pending
            season: Current season (affects multiplier)

        Returns:
            Recommended pool price (₹/kWh)
        """
        if available_supply_kwh == 0:
            return PoolPricingModel.MAX_POOL_PRICE

        # Demand to supply ratio
        ratio = pending_demand_kwh / available_supply_kwh

        # Seasonal adjustment
        seasonal_factor = 1.0
        if season == "summer":
            seasonal_factor = PoolPricingModel.SEASONAL_DEMAND_FACTOR

        # Calculate price
        price_adjustment = ratio * PoolPricingModel.DEMAND_TO_SUPPLY_RATIO_MULTIPLIER * seasonal_factor
        dynamic_price = PoolPricingModel.BASE_POOL_PRICE + price_adjustment

        # Clamp to min/max
        dynamic_price = max(
            PoolPricingModel.MIN_POOL_PRICE,
            min(dynamic_price, PoolPricingModel.MAX_POOL_PRICE)
        )

        return round(dynamic_price, 2)


# Utility function to calculate bill for any house type
def calculate_house_bill(
    house_type: str,  # "domestic" or "commercial"
    consumption_kwh: float,
    grid_consumption_kwh: float = None,
    **kwargs
) -> Dict[str, float]:
    """
    Calculate house bill based on type and consumption.

    Args:
        house_type: "domestic" or "commercial"
        consumption_kwh: Total consumption
        grid_consumption_kwh: Grid-specific consumption (for prosumer)
        **kwargs: Additional parameters (sanctioned_load_kw, contracted_demand_kw, etc.)

    Returns:
        Bill breakdown dictionary
    """
    if house_type.lower() == "domestic":
        sanctioned_load = kwargs.get("sanctioned_load_kw", 2.0)
        return RajasthanDomesticTariff.calculate_total_bill(
            consumption_kwh,
            grid_consumption_kwh,
            sanctioned_load
        )
    elif house_type.lower() == "commercial":
        contracted_demand = kwargs.get("contracted_demand_kw", 5.0)
        power_factor = kwargs.get("power_factor", 0.95)
        return RajasthanCommercialTariff.calculate_total_bill(
            consumption_kwh,
            contracted_demand,
            power_factor
        )
    else:
        raise ValueError(f"Unknown house type: {house_type}")
