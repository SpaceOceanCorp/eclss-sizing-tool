"""Tests for ContaminantEstimator (BVAD Table 4-3)."""

import pytest
from eclss.contaminants import ContaminantEstimator
from eclss.constants import TRACE_CONTAMINANTS


class TestContaminantGeneration:
    def test_seventeen_contaminants(self):
        est = ContaminantEstimator(crew_count=1, cabin_volume_m3=25.0)
        rates = est.total_generation_rates()
        assert len(rates) == 17

    def test_metabolic_scales_with_crew(self):
        est2 = ContaminantEstimator(crew_count=2, cabin_volume_m3=25.0)
        est4 = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0)
        r2 = est2.metabolic_generation_rates()
        r4 = est4.metabolic_generation_rates()
        for name in r2:
            assert r4[name] == pytest.approx(r2[name] * 2)

    def test_metabolic_rates_nonnegative(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0)
        rates = est.metabolic_generation_rates()
        assert all(v >= 0 for v in rates.values())

    def test_equipment_only_contaminants(self):
        """Trimethylsilanol and Hexamethylcyclotrisiloxane have 0 metabolic."""
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0)
        rates = est.metabolic_generation_rates()
        assert rates["Trimethylsilanol"] == 0.0
        assert rates["Hexamethylcyclotrisiloxane"] == 0.0


class TestEquipmentGeneration:
    def test_zero_equipment_mass(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0, equipment_mass_kg=0.0)
        equip = est.equipment_generation_rates()
        assert all(v == 0.0 for v in equip.values())

    def test_equipment_scales_with_mass(self):
        est1 = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0, equipment_mass_kg=100.0)
        est2 = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0, equipment_mass_kg=200.0)
        r1 = est1.equipment_generation_rates()
        r2 = est2.equipment_generation_rates()
        for name in r1:
            assert r2[name] == pytest.approx(r1[name] * 2)

    def test_total_equals_metabolic_plus_equipment(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0, equipment_mass_kg=500.0)
        total = est.total_generation_rates()
        metab = est.metabolic_generation_rates()
        equip = est.equipment_generation_rates()
        for name in total:
            assert total[name] == pytest.approx(metab[name] + equip[name])

    def test_equipment_contributes_to_smac(self):
        """Equipment mass should increase accumulation in SMAC check."""
        est_no_equip = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0)
        est_with_equip = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0,
                                               equipment_mass_kg=5000.0)
        r_no = est_no_equip.check_smac_limits()
        r_with = est_with_equip.check_smac_limits()
        for no, wi in zip(r_no, r_with):
            assert wi["accumulation_mg_m3"] >= no["accumulation_mg_m3"]


class TestSMACLimits:
    def test_smac_check_structure(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0)
        results = est.check_smac_limits()
        assert len(results) == 17
        for r in results:
            assert "name" in r
            assert "generation_mg_day" in r
            assert "metabolic_mg_day" in r
            assert "equipment_mg_day" in r
            assert "accumulation_mg_m3" in r
            assert "smac_mg_m3" in r
            assert "exceeds_smac" in r
            assert "removal_rate_required_mg_day" in r

    def test_large_volume_reduces_exceedance(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=20000.0)
        results = est.check_smac_limits()
        for r in results:
            assert r["exceeds_smac"] is False

    def test_tiny_volume_exceeds_smac(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=0.1)
        results = est.check_smac_limits()
        assert any(r["exceeds_smac"] for r in results)

    def test_removal_rate_zero_when_under_smac(self):
        est = ContaminantEstimator(crew_count=1, cabin_volume_m3=100000.0)
        results = est.check_smac_limits()
        for r in results:
            assert r["removal_rate_required_mg_day"] == pytest.approx(0.0)

    def test_ammonia_value_corrected(self):
        """Verify Ammonia generation is 50 mg/CM-d, not 0.5."""
        assert TRACE_CONTAMINANTS["Ammonia"]["metabolic_mg_per_cm_day"] == 50.0
        assert TRACE_CONTAMINANTS["Ammonia"]["smac_180d_mg_m3"] == 2.0

    def test_hydrogen_value_corrected(self):
        assert TRACE_CONTAMINANTS["Hydrogen"]["metabolic_mg_per_cm_day"] == 42.0

    def test_methane_value_corrected(self):
        assert TRACE_CONTAMINANTS["Methane"]["metabolic_mg_per_cm_day"] == 329.0


class TestContaminantValidation:
    def test_zero_crew_raises(self):
        with pytest.raises(ValueError, match="crew_count"):
            ContaminantEstimator(crew_count=0, cabin_volume_m3=25.0)

    def test_negative_volume_raises(self):
        with pytest.raises(ValueError, match="cabin_volume_m3"):
            ContaminantEstimator(crew_count=4, cabin_volume_m3=-1.0)

    def test_negative_equipment_raises(self):
        with pytest.raises(ValueError, match="equipment_mass_kg"):
            ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0, equipment_mass_kg=-1.0)


class TestCustomContaminants:
    def test_custom_contaminant_added(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0,
            custom_contaminants={"Siloxane-D5": {
                "metabolic_mg_per_cm_day": 0.0,
                "equipment_mg_per_kg_day": 0.01,
                "smac_180d_mg_m3": 5.0,
            }})
        rates = est.total_generation_rates()
        assert "Siloxane-D5" in rates
        assert len(rates) == 18  # 17 BVAD + 1 custom

    def test_add_contaminant_method(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0)
        est.add_contaminant("NewGas", metabolic_mg_per_cm_day=1.0,
                           equipment_mg_per_kg_day=0.001, smac_180d_mg_m3=10.0)
        rates = est.total_generation_rates()
        assert "NewGas" in rates
        assert rates["NewGas"] == pytest.approx(4.0)  # 1.0 * 4 crew

    def test_override_existing_contaminant(self):
        est = ContaminantEstimator(crew_count=4, cabin_volume_m3=25.0,
            custom_contaminants={"Ammonia": {
                "metabolic_mg_per_cm_day": 30.0,  # override from 50
                "equipment_mg_per_kg_day": 0.0,
                "smac_180d_mg_m3": 2.0,
            }})
        rates = est.metabolic_generation_rates()
        assert rates["Ammonia"] == pytest.approx(120.0)  # 30 * 4
