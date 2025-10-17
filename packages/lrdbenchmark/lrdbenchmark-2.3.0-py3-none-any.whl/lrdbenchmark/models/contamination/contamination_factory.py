#!/usr/bin/env python3
"""
Advanced Contamination Factory for Realistic Data Confounding

This module provides a sophisticated contamination factory that creates realistic
confounding profiles based on real-world scenarios encountered in time series analysis.
It goes beyond simple noise addition to simulate complex, realistic data artifacts.

Real-world scenarios include:
1. Financial time series (market crashes, volatility clustering, regime changes)
2. Physiological signals (sensor drift, motion artifacts, equipment failures)
3. Environmental data (seasonal effects, extreme events, measurement drift)
4. Network traffic (bursts, congestion, equipment failures)
5. Industrial sensors (calibration drift, sensor aging, environmental interference)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import signal, stats
import random


class ConfoundingScenario(Enum):
    """Real-world confounding scenarios."""
    
    # Financial scenarios
    FINANCIAL_CRASH = "financial_crash"
    FINANCIAL_VOLATILITY_CLUSTERING = "financial_volatility_clustering"
    FINANCIAL_REGIME_CHANGE = "financial_regime_change"
    
    # Physiological scenarios
    PHYSIOLOGICAL_SENSOR_DRIFT = "physiological_sensor_drift"
    PHYSIOLOGICAL_MOTION_ARTIFACTS = "physiological_motion_artifacts"
    PHYSIOLOGICAL_EQUIPMENT_FAILURE = "physiological_equipment_failure"
    
    # Environmental scenarios
    ENVIRONMENTAL_SEASONAL = "environmental_seasonal"
    ENVIRONMENTAL_EXTREME_EVENTS = "environmental_extreme_events"
    ENVIRONMENTAL_MEASUREMENT_DRIFT = "environmental_measurement_drift"
    
    # Network scenarios
    NETWORK_BURSTS = "network_bursts"
    NETWORK_CONGESTION = "network_congestion"
    NETWORK_EQUIPMENT_FAILURE = "network_equipment_failure"
    
    # Industrial scenarios
    INDUSTRIAL_CALIBRATION_DRIFT = "industrial_calibration_drift"
    INDUSTRIAL_SENSOR_AGING = "industrial_sensor_aging"
    INDUSTRIAL_ENVIRONMENTAL_INTERFERENCE = "industrial_environmental_interference"
    
    # EEG scenarios
    EEG_OCULAR_ARTIFACTS = "eeg_ocular_artifacts"
    EEG_MUSCLE_ARTIFACTS = "eeg_muscle_artifacts"
    EEG_CARDIAC_ARTIFACTS = "eeg_cardiac_artifacts"
    EEG_ELECTRODE_POPPING = "eeg_electrode_popping"
    EEG_ELECTRODE_DRIFT = "eeg_electrode_drift"
    EEG_60HZ_NOISE = "eeg_60hz_noise"
    EEG_SWEAT_ARTIFACTS = "eeg_sweat_artifacts"
    EEG_MOVEMENT_ARTIFACTS = "eeg_movement_artifacts"
    
    # Mixed realistic scenarios
    MIXED_REALISTIC_LIGHT = "mixed_realistic_light"
    MIXED_REALISTIC_MODERATE = "mixed_realistic_moderate"
    MIXED_REALISTIC_SEVERE = "mixed_realistic_severe"


@dataclass
class ConfoundingProfile:
    """Configuration for a specific confounding profile."""
    
    scenario: ConfoundingScenario
    intensity: float  # 0.0 to 1.0
    parameters: Dict[str, float]
    description: str
    
    def __hash__(self):
        return hash((self.scenario, self.intensity, tuple(sorted(self.parameters.items())), self.description))


class ContaminationFactory:
    """
    Advanced contamination factory that creates realistic confounding profiles.
    
    This factory generates complex, realistic data artifacts that mimic real-world
    scenarios encountered in time series analysis across various domains.
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        """
        Initialize the contamination factory.
        
        Parameters
        ----------
        random_seed : int, optional
            Random seed for reproducible results
        """
        if random_seed is not None:
            np.random.seed(random_seed)
            random.seed(random_seed)
        
        self.profiles = self._initialize_profiles()
    
    def _initialize_profiles(self) -> Dict[ConfoundingScenario, ConfoundingProfile]:
        """Initialize predefined confounding profiles."""
        profiles = {}
        
        # Financial scenarios
        profiles[ConfoundingScenario.FINANCIAL_CRASH] = ConfoundingProfile(
            scenario=ConfoundingScenario.FINANCIAL_CRASH,
            intensity=0.8,
            parameters={
                "crash_probability": 0.05,
                "crash_magnitude": 3.0,
                "recovery_time": 0.3,
                "volatility_increase": 2.0
            },
            description="Simulates market crashes with increased volatility and gradual recovery"
        )
        
        profiles[ConfoundingScenario.FINANCIAL_VOLATILITY_CLUSTERING] = ConfoundingProfile(
            scenario=ConfoundingScenario.FINANCIAL_VOLATILITY_CLUSTERING,
            intensity=0.6,
            parameters={
                "cluster_duration": 0.2,
                "volatility_multiplier": 1.5,
                "cluster_probability": 0.1
            },
            description="Simulates volatility clustering common in financial time series"
        )
        
        profiles[ConfoundingScenario.FINANCIAL_REGIME_CHANGE] = ConfoundingProfile(
            scenario=ConfoundingScenario.FINANCIAL_REGIME_CHANGE,
            intensity=0.7,
            parameters={
                "regime_change_probability": 0.02,
                "mean_shift": 0.5,
                "volatility_shift": 0.3,
                "transition_smoothness": 0.1
            },
            description="Simulates regime changes in financial markets"
        )
        
        # Physiological scenarios
        profiles[ConfoundingScenario.PHYSIOLOGICAL_SENSOR_DRIFT] = ConfoundingProfile(
            scenario=ConfoundingScenario.PHYSIOLOGICAL_SENSOR_DRIFT,
            intensity=0.4,
            parameters={
                "drift_rate": 0.001,
                "drift_variability": 0.1,
                "calibration_events": 0.05
            },
            description="Simulates gradual sensor drift with occasional recalibration"
        )
        
        profiles[ConfoundingScenario.PHYSIOLOGICAL_MOTION_ARTIFACTS] = ConfoundingProfile(
            scenario=ConfoundingScenario.PHYSIOLOGICAL_MOTION_ARTIFACTS,
            intensity=0.6,
            parameters={
                "motion_probability": 0.1,
                "motion_duration": 0.05,
                "motion_amplitude": 2.0,
                "motion_frequency": 0.3
            },
            description="Simulates motion artifacts in physiological recordings"
        )
        
        profiles[ConfoundingScenario.PHYSIOLOGICAL_EQUIPMENT_FAILURE] = ConfoundingProfile(
            scenario=ConfoundingScenario.PHYSIOLOGICAL_EQUIPMENT_FAILURE,
            intensity=0.8,
            parameters={
                "failure_probability": 0.01,
                "failure_duration": 0.1,
                "failure_magnitude": 5.0,
                "recovery_time": 0.2
            },
            description="Simulates equipment failures with temporary signal loss"
        )
        
        # Environmental scenarios
        profiles[ConfoundingScenario.ENVIRONMENTAL_SEASONAL] = ConfoundingProfile(
            scenario=ConfoundingScenario.ENVIRONMENTAL_SEASONAL,
            intensity=0.5,
            parameters={
                "seasonal_amplitude": 0.3,
                "seasonal_period": 0.25,
                "trend_component": 0.1,
                "noise_level": 0.05
            },
            description="Simulates seasonal effects with trend and noise"
        )
        
        profiles[ConfoundingScenario.ENVIRONMENTAL_EXTREME_EVENTS] = ConfoundingProfile(
            scenario=ConfoundingScenario.ENVIRONMENTAL_EXTREME_EVENTS,
            intensity=0.7,
            parameters={
                "extreme_probability": 0.02,
                "extreme_magnitude": 4.0,
                "extreme_duration": 0.05,
                "recovery_rate": 0.1
            },
            description="Simulates extreme environmental events (storms, etc.)"
        )
        
        profiles[ConfoundingScenario.ENVIRONMENTAL_MEASUREMENT_DRIFT] = ConfoundingProfile(
            scenario=ConfoundingScenario.ENVIRONMENTAL_MEASUREMENT_DRIFT,
            intensity=0.3,
            parameters={
                "drift_rate": 0.0005,
                "temperature_dependence": 0.2,
                "humidity_dependence": 0.1
            },
            description="Simulates measurement drift due to environmental conditions"
        )
        
        # Network scenarios
        profiles[ConfoundingScenario.NETWORK_BURSTS] = ConfoundingProfile(
            scenario=ConfoundingScenario.NETWORK_BURSTS,
            intensity=0.6,
            parameters={
                "burst_probability": 0.05,
                "burst_duration": 0.02,
                "burst_amplitude": 3.0,
                "burst_frequency": 0.1
            },
            description="Simulates network traffic bursts"
        )
        
        profiles[ConfoundingScenario.NETWORK_CONGESTION] = ConfoundingProfile(
            scenario=ConfoundingScenario.NETWORK_CONGESTION,
            intensity=0.5,
            parameters={
                "congestion_probability": 0.1,
                "congestion_duration": 0.15,
                "congestion_severity": 0.5,
                "recovery_time": 0.1
            },
            description="Simulates network congestion effects"
        )
        
        profiles[ConfoundingScenario.NETWORK_EQUIPMENT_FAILURE] = ConfoundingProfile(
            scenario=ConfoundingScenario.NETWORK_EQUIPMENT_FAILURE,
            intensity=0.8,
            parameters={
                "failure_probability": 0.005,
                "failure_duration": 0.2,
                "failure_magnitude": 10.0,
                "recovery_time": 0.3
            },
            description="Simulates network equipment failures"
        )
        
        # Industrial scenarios
        profiles[ConfoundingScenario.INDUSTRIAL_CALIBRATION_DRIFT] = ConfoundingProfile(
            scenario=ConfoundingScenario.INDUSTRIAL_CALIBRATION_DRIFT,
            intensity=0.4,
            parameters={
                "drift_rate": 0.0002,
                "drift_variability": 0.05,
                "calibration_interval": 0.1,
                "calibration_accuracy": 0.02
            },
            description="Simulates industrial sensor calibration drift"
        )
        
        profiles[ConfoundingScenario.INDUSTRIAL_SENSOR_AGING] = ConfoundingProfile(
            scenario=ConfoundingScenario.INDUSTRIAL_SENSOR_AGING,
            intensity=0.3,
            parameters={
                "aging_rate": 0.0001,
                "aging_variability": 0.02,
                "noise_increase": 0.1,
                "sensitivity_decrease": 0.05
            },
            description="Simulates sensor aging effects"
        )
        
        profiles[ConfoundingScenario.INDUSTRIAL_ENVIRONMENTAL_INTERFERENCE] = ConfoundingProfile(
            scenario=ConfoundingScenario.INDUSTRIAL_ENVIRONMENTAL_INTERFERENCE,
            intensity=0.5,
            parameters={
                "interference_frequency": 0.05,
                "interference_amplitude": 0.3,
                "interference_duration": 0.1,
                "interference_probability": 0.2
            },
            description="Simulates environmental interference in industrial sensors"
        )
        
        # EEG scenarios
        profiles[ConfoundingScenario.EEG_OCULAR_ARTIFACTS] = ConfoundingProfile(
            scenario=ConfoundingScenario.EEG_OCULAR_ARTIFACTS,
            intensity=0.7,
            parameters={
                "blink_probability": 0.1,
                "saccade_probability": 0.05,
                "eye_movement_amplitude": 50.0,  # μV
                "blink_duration": 0.3,  # seconds
                "saccade_duration": 0.1,  # seconds
                "frequency_min": 0.5,  # Hz
                "frequency_max": 4.0  # Hz
            },
            description="Simulates ocular artifacts (blinks, saccades) in EEG recordings"
        )
        
        profiles[ConfoundingScenario.EEG_MUSCLE_ARTIFACTS] = ConfoundingProfile(
            scenario=ConfoundingScenario.EEG_MUSCLE_ARTIFACTS,
            intensity=0.6,
            parameters={
                "muscle_activity_probability": 0.15,
                "muscle_amplitude": 100.0,  # μV
                "muscle_duration": 0.5,  # seconds
                "frequency_min": 20.0,  # Hz
                "frequency_max": 100.0,  # Hz
                "burst_probability": 0.3
            },
            description="Simulates muscle artifacts (EMG) in EEG recordings"
        )
        
        profiles[ConfoundingScenario.EEG_CARDIAC_ARTIFACTS] = ConfoundingProfile(
            scenario=ConfoundingScenario.EEG_CARDIAC_ARTIFACTS,
            intensity=0.4,
            parameters={
                "heart_rate": 1.2,  # Hz (72 BPM)
                "ecg_amplitude": 20.0,  # μV
                "qrs_duration": 0.1,  # seconds
                "variability": 0.1,  # heart rate variability
                "conduction_delay": 0.05  # seconds
            },
            description="Simulates cardiac artifacts (ECG) in EEG recordings"
        )
        
        profiles[ConfoundingScenario.EEG_ELECTRODE_POPPING] = ConfoundingProfile(
            scenario=ConfoundingScenario.EEG_ELECTRODE_POPPING,
            intensity=0.8,
            parameters={
                "pop_probability": 0.02,
                "pop_amplitude": 200.0,  # μV
                "pop_duration": 0.01,  # seconds
                "recovery_time": 0.1,  # seconds
                "impedance_threshold": 0.5
            },
            description="Simulates electrode popping artifacts in EEG recordings"
        )
        
        profiles[ConfoundingScenario.EEG_ELECTRODE_DRIFT] = ConfoundingProfile(
            scenario=ConfoundingScenario.EEG_ELECTRODE_DRIFT,
            intensity=0.3,
            parameters={
                "drift_rate": 0.5,  # μV/second
                "drift_variability": 0.1,
                "baseline_shift": 10.0,  # μV
                "impedance_change": 0.2,
                "calibration_drift": 0.05
            },
            description="Simulates electrode drift and impedance changes in EEG recordings"
        )
        
        profiles[ConfoundingScenario.EEG_60HZ_NOISE] = ConfoundingProfile(
            scenario=ConfoundingScenario.EEG_60HZ_NOISE,
            intensity=0.5,
            parameters={
                "line_frequency": 60.0,  # Hz
                "noise_amplitude": 5.0,  # μV
                "harmonic_amplitude": 2.0,  # μV
                "phase_noise": 0.1,
                "frequency_drift": 0.1  # Hz
            },
            description="Simulates 60Hz power line noise and harmonics in EEG recordings"
        )
        
        profiles[ConfoundingScenario.EEG_SWEAT_ARTIFACTS] = ConfoundingProfile(
            scenario=ConfoundingScenario.EEG_SWEAT_ARTIFACTS,
            intensity=0.4,
            parameters={
                "sweat_probability": 0.1,
                "sweat_amplitude": 30.0,  # μV
                "sweat_duration": 2.0,  # seconds
                "impedance_reduction": 0.3,
                "slow_drift": 0.2  # μV/second
            },
            description="Simulates sweat artifacts and impedance changes in EEG recordings"
        )
        
        profiles[ConfoundingScenario.EEG_MOVEMENT_ARTIFACTS] = ConfoundingProfile(
            scenario=ConfoundingScenario.EEG_MOVEMENT_ARTIFACTS,
            intensity=0.6,
            parameters={
                "movement_probability": 0.05,
                "movement_amplitude": 80.0,  # μV
                "movement_duration": 1.0,  # seconds
                "frequency_min": 0.1,  # Hz
                "frequency_max": 10.0,  # Hz
                "acceleration_effect": 0.5
            },
            description="Simulates head/body movement artifacts in EEG recordings"
        )
        
        # Mixed realistic scenarios
        profiles[ConfoundingScenario.MIXED_REALISTIC_LIGHT] = ConfoundingProfile(
            scenario=ConfoundingScenario.MIXED_REALISTIC_LIGHT,
            intensity=0.3,
            parameters={
                "noise_level": 0.05,
                "drift_rate": 0.001,
                "artifact_probability": 0.02,
                "trend_component": 0.02
            },
            description="Light realistic contamination with minimal artifacts"
        )
        
        profiles[ConfoundingScenario.MIXED_REALISTIC_MODERATE] = ConfoundingProfile(
            scenario=ConfoundingScenario.MIXED_REALISTIC_MODERATE,
            intensity=0.5,
            parameters={
                "noise_level": 0.1,
                "drift_rate": 0.002,
                "artifact_probability": 0.05,
                "trend_component": 0.05,
                "seasonal_amplitude": 0.1
            },
            description="Moderate realistic contamination with common artifacts"
        )
        
        profiles[ConfoundingScenario.MIXED_REALISTIC_SEVERE] = ConfoundingProfile(
            scenario=ConfoundingScenario.MIXED_REALISTIC_SEVERE,
            intensity=0.8,
            parameters={
                "noise_level": 0.2,
                "drift_rate": 0.005,
                "artifact_probability": 0.1,
                "trend_component": 0.1,
                "seasonal_amplitude": 0.2,
                "extreme_events": 0.05
            },
            description="Severe realistic contamination with multiple artifacts"
        )
        
        return profiles
    
    def create_confounding_profile(self, 
                                 scenario: ConfoundingScenario,
                                 intensity: Optional[float] = None,
                                 custom_parameters: Optional[Dict[str, float]] = None) -> ConfoundingProfile:
        """
        Create a confounding profile for a specific scenario.
        
        Parameters
        ----------
        scenario : ConfoundingScenario
            The confounding scenario to create
        intensity : float, optional
            Intensity of the confounding (0.0 to 1.0). If None, uses default.
        custom_parameters : dict, optional
            Custom parameters to override defaults
            
        Returns
        -------
        ConfoundingProfile
            The created confounding profile
        """
        if scenario not in self.profiles:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        base_profile = self.profiles[scenario]
        
        # Create a copy with modifications
        profile = ConfoundingProfile(
            scenario=scenario,
            intensity=intensity if intensity is not None else base_profile.intensity,
            parameters=base_profile.parameters.copy(),
            description=base_profile.description
        )
        
        # Apply custom parameters
        if custom_parameters:
            profile.parameters.update(custom_parameters)
        
        # Scale parameters by intensity
        for key, value in profile.parameters.items():
            profile.parameters[key] = value * profile.intensity
        
        return profile
    
    def apply_confounding(self, 
                         data: np.ndarray, 
                         scenario: ConfoundingScenario,
                         intensity: Optional[float] = None) -> Tuple[np.ndarray, str]:
        """
        Apply confounding to data based on a specific scenario.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series data
        scenario : ConfoundingScenario
            Confounding scenario to apply
        intensity : float, optional
            Intensity of confounding (0.0 to 1.0). If None, uses default.
            
        Returns
        -------
        tuple
            (contaminated_data, description)
        """
        # Create profile
        profile = self.create_confounding_profile(scenario, intensity)
        
        contaminated = data.copy()
        n = len(data)
        params = profile.parameters
        
        if profile.scenario == ConfoundingScenario.FINANCIAL_CRASH:
            contaminated = self._apply_financial_crash(contaminated, params)
        elif profile.scenario == ConfoundingScenario.FINANCIAL_VOLATILITY_CLUSTERING:
            contaminated = self._apply_volatility_clustering(contaminated, params)
        elif profile.scenario == ConfoundingScenario.FINANCIAL_REGIME_CHANGE:
            contaminated = self._apply_regime_change(contaminated, params)
        elif profile.scenario == ConfoundingScenario.PHYSIOLOGICAL_SENSOR_DRIFT:
            contaminated = self._apply_sensor_drift(contaminated, params)
        elif profile.scenario == ConfoundingScenario.PHYSIOLOGICAL_MOTION_ARTIFACTS:
            contaminated = self._apply_motion_artifacts(contaminated, params)
        elif profile.scenario == ConfoundingScenario.PHYSIOLOGICAL_EQUIPMENT_FAILURE:
            contaminated = self._apply_equipment_failure(contaminated, params)
        elif profile.scenario == ConfoundingScenario.ENVIRONMENTAL_SEASONAL:
            contaminated = self._apply_seasonal_effects(contaminated, params)
        elif profile.scenario == ConfoundingScenario.ENVIRONMENTAL_EXTREME_EVENTS:
            contaminated = self._apply_extreme_events(contaminated, params)
        elif profile.scenario == ConfoundingScenario.ENVIRONMENTAL_MEASUREMENT_DRIFT:
            contaminated = self._apply_measurement_drift(contaminated, params)
        elif profile.scenario == ConfoundingScenario.NETWORK_BURSTS:
            contaminated = self._apply_network_bursts(contaminated, params)
        elif profile.scenario == ConfoundingScenario.NETWORK_CONGESTION:
            contaminated = self._apply_network_congestion(contaminated, params)
        elif profile.scenario == ConfoundingScenario.NETWORK_EQUIPMENT_FAILURE:
            contaminated = self._apply_network_equipment_failure(contaminated, params)
        elif profile.scenario == ConfoundingScenario.INDUSTRIAL_CALIBRATION_DRIFT:
            contaminated = self._apply_calibration_drift(contaminated, params)
        elif profile.scenario == ConfoundingScenario.INDUSTRIAL_SENSOR_AGING:
            contaminated = self._apply_sensor_aging(contaminated, params)
        elif profile.scenario == ConfoundingScenario.INDUSTRIAL_ENVIRONMENTAL_INTERFERENCE:
            contaminated = self._apply_environmental_interference(contaminated, params)
        elif profile.scenario == ConfoundingScenario.MIXED_REALISTIC_LIGHT:
            contaminated = self._apply_mixed_realistic_light(contaminated, params)
        elif profile.scenario == ConfoundingScenario.MIXED_REALISTIC_MODERATE:
            contaminated = self._apply_mixed_realistic_moderate(contaminated, params)
        elif profile.scenario == ConfoundingScenario.MIXED_REALISTIC_SEVERE:
            contaminated = self._apply_mixed_realistic_severe(contaminated, params)
        elif profile.scenario == ConfoundingScenario.EEG_OCULAR_ARTIFACTS:
            contaminated = self._apply_eeg_ocular_artifacts(contaminated, params)
        elif profile.scenario == ConfoundingScenario.EEG_MUSCLE_ARTIFACTS:
            contaminated = self._apply_eeg_muscle_artifacts(contaminated, params)
        elif profile.scenario == ConfoundingScenario.EEG_CARDIAC_ARTIFACTS:
            contaminated = self._apply_eeg_cardiac_artifacts(contaminated, params)
        elif profile.scenario == ConfoundingScenario.EEG_ELECTRODE_POPPING:
            contaminated = self._apply_eeg_electrode_popping(contaminated, params)
        elif profile.scenario == ConfoundingScenario.EEG_ELECTRODE_DRIFT:
            contaminated = self._apply_eeg_electrode_drift(contaminated, params)
        elif profile.scenario == ConfoundingScenario.EEG_60HZ_NOISE:
            contaminated = self._apply_eeg_60hz_noise(contaminated, params)
        elif profile.scenario == ConfoundingScenario.EEG_SWEAT_ARTIFACTS:
            contaminated = self._apply_eeg_sweat_artifacts(contaminated, params)
        elif profile.scenario == ConfoundingScenario.EEG_MOVEMENT_ARTIFACTS:
            contaminated = self._apply_eeg_movement_artifacts(contaminated, params)
        else:
            warnings.warn(f"Unknown scenario: {profile.scenario}")
        
        return contaminated, profile.description
    
    def _apply_financial_crash(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply financial crash confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate crash events
        crash_mask = np.random.random(n) < params["crash_probability"]
        crash_indices = np.where(crash_mask)[0]
        
        for crash_idx in crash_indices:
            # Apply crash
            crash_magnitude = params["crash_magnitude"] * np.random.choice([-1, 1])
            contaminated[crash_idx] += crash_magnitude
            
            # Apply recovery and increased volatility
            recovery_length = int(params["recovery_time"] * n)
            for i in range(1, min(recovery_length, n - crash_idx)):
                if crash_idx + i < n:
                    # Gradual recovery
                    recovery_factor = 1 - (i / recovery_length)
                    contaminated[crash_idx + i] += crash_magnitude * recovery_factor * 0.1
                    
                    # Increased volatility
                    volatility_noise = np.random.normal(0, params["volatility_increase"] * 0.1)
                    contaminated[crash_idx + i] += volatility_noise
        
        return contaminated
    
    def _apply_volatility_clustering(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply volatility clustering confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate volatility clusters
        cluster_mask = np.random.random(n) < params["cluster_probability"]
        cluster_length = int(params["cluster_duration"] * n)
        
        for i in range(n):
            if cluster_mask[i]:
                # Start a volatility cluster
                for j in range(min(cluster_length, n - i)):
                    if i + j < n:
                        volatility_multiplier = params["volatility_multiplier"]
                        noise = np.random.normal(0, volatility_multiplier * 0.1)
                        contaminated[i + j] += noise
        
        return contaminated
    
    def _apply_regime_change(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply regime change confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate regime changes
        regime_mask = np.random.random(n) < params["regime_change_probability"]
        regime_indices = np.where(regime_mask)[0]
        
        current_regime = 0
        for i in range(n):
            if i in regime_indices:
                current_regime = 1 - current_regime  # Switch regime
            
            # Apply regime effects
            mean_shift = params["mean_shift"] * (2 * current_regime - 1)
            volatility_shift = 1 + params["volatility_shift"] * (2 * current_regime - 1)
            
            contaminated[i] += mean_shift
            contaminated[i] += np.random.normal(0, volatility_shift * 0.1)
        
        return contaminated
    
    def _apply_sensor_drift(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply sensor drift confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate drift
        t = np.arange(n) / n
        drift = params["drift_rate"] * t + np.random.normal(0, params["drift_variability"], n)
        
        # Add calibration events
        calibration_mask = np.random.random(n) < params["calibration_events"]
        for i in range(n):
            if calibration_mask[i]:
                # Reset drift
                drift[i:] -= drift[i]
        
        contaminated += drift
        return contaminated
    
    def _apply_motion_artifacts(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply motion artifacts confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate motion events
        motion_mask = np.random.random(n) < params["motion_probability"]
        motion_length = int(params["motion_duration"] * n)
        
        for i in range(n):
            if motion_mask[i]:
                # Apply motion artifact
                for j in range(min(motion_length, n - i)):
                    if i + j < n:
                        motion_amplitude = params["motion_amplitude"]
                        motion_freq = params["motion_frequency"]
                        motion_signal = motion_amplitude * np.sin(2 * np.pi * motion_freq * j)
                        contaminated[i + j] += motion_signal
        
        return contaminated
    
    def _apply_equipment_failure(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply equipment failure confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate failure events
        failure_mask = np.random.random(n) < params["failure_probability"]
        failure_length = int(params["failure_duration"] * n)
        recovery_length = int(params["recovery_time"] * n)
        
        for i in range(n):
            if failure_mask[i]:
                # Apply failure
                failure_magnitude = params["failure_magnitude"]
                contaminated[i] += failure_magnitude * np.random.choice([-1, 1])
                
                # Apply recovery
                for j in range(1, min(recovery_length, n - i)):
                    if i + j < n:
                        recovery_factor = 1 - (j / recovery_length)
                        contaminated[i + j] += failure_magnitude * recovery_factor * 0.1
        
        return contaminated
    
    def _apply_seasonal_effects(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply seasonal effects confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate seasonal component
        t = np.arange(n) / n
        seasonal = params["seasonal_amplitude"] * np.sin(2 * np.pi * t / params["seasonal_period"])
        seasonal += 0.3 * params["seasonal_amplitude"] * np.sin(4 * np.pi * t / params["seasonal_period"])
        
        # Add trend
        trend = params["trend_component"] * t
        
        # Add noise
        noise = np.random.normal(0, params["noise_level"], n)
        
        contaminated += seasonal + trend + noise
        return contaminated
    
    def _apply_extreme_events(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply extreme events confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate extreme events
        extreme_mask = np.random.random(n) < params["extreme_probability"]
        extreme_length = int(params["extreme_duration"] * n)
        
        for i in range(n):
            if extreme_mask[i]:
                # Apply extreme event
                extreme_magnitude = params["extreme_magnitude"] * np.random.choice([-1, 1])
                for j in range(min(extreme_length, n - i)):
                    if i + j < n:
                        contaminated[i + j] += extreme_magnitude * (1 - j / extreme_length)
        
        return contaminated
    
    def _apply_measurement_drift(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply measurement drift confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate environmental conditions
        temperature = np.random.normal(20, 5, n)  # Temperature variation
        humidity = np.random.normal(50, 10, n)    # Humidity variation
        
        # Apply drift based on environmental conditions
        drift = (params["drift_rate"] * np.arange(n) / n + 
                params["temperature_dependence"] * (temperature - 20) / 100 +
                params["humidity_dependence"] * (humidity - 50) / 100)
        
        contaminated += drift
        return contaminated
    
    def _apply_network_bursts(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply network bursts confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate burst events
        burst_mask = np.random.random(n) < params["burst_probability"]
        burst_length = int(params["burst_duration"] * n)
        
        for i in range(n):
            if burst_mask[i]:
                # Apply burst
                burst_amplitude = params["burst_amplitude"]
                for j in range(min(burst_length, n - i)):
                    if i + j < n:
                        burst_signal = burst_amplitude * np.exp(-j / (burst_length * 0.5))
                        contaminated[i + j] += burst_signal
        
        return contaminated
    
    def _apply_network_congestion(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply network congestion confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate congestion events
        congestion_mask = np.random.random(n) < params["congestion_probability"]
        congestion_length = int(params["congestion_duration"] * n)
        
        for i in range(n):
            if congestion_mask[i]:
                # Apply congestion
                congestion_severity = params["congestion_severity"]
                for j in range(min(congestion_length, n - i)):
                    if i + j < n:
                        # Gradual onset and recovery
                        congestion_factor = np.sin(np.pi * j / congestion_length)
                        contaminated[i + j] += congestion_severity * congestion_factor
        
        return contaminated
    
    def _apply_network_equipment_failure(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply network equipment failure confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate failure events
        failure_mask = np.random.random(n) < params["failure_probability"]
        failure_length = int(params["failure_duration"] * n)
        recovery_length = int(params["recovery_time"] * n)
        
        for i in range(n):
            if failure_mask[i]:
                # Apply failure
                failure_magnitude = params["failure_magnitude"]
                for j in range(min(failure_length, n - i)):
                    if i + j < n:
                        contaminated[i + j] += failure_magnitude
                
                # Apply recovery
                for j in range(failure_length, min(failure_length + recovery_length, n - i)):
                    if i + j < n:
                        recovery_factor = 1 - ((j - failure_length) / recovery_length)
                        contaminated[i + j] += failure_magnitude * recovery_factor
        
        return contaminated
    
    def _apply_calibration_drift(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply calibration drift confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate drift
        t = np.arange(n) / n
        drift = params["drift_rate"] * t + np.random.normal(0, params["drift_variability"], n)
        
        # Add calibration events
        calibration_interval = int(params["calibration_interval"] * n)
        for i in range(0, n, calibration_interval):
            if i < n:
                # Apply calibration correction
                calibration_correction = np.random.normal(0, params["calibration_accuracy"])
                drift[i:] += calibration_correction
        
        contaminated += drift
        return contaminated
    
    def _apply_sensor_aging(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply sensor aging confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate aging effects
        t = np.arange(n) / n
        aging = params["aging_rate"] * t + np.random.normal(0, params["aging_variability"], n)
        
        # Apply noise increase
        noise_increase = params["noise_increase"] * t
        noise = np.random.normal(0, noise_increase, n)
        
        # Apply sensitivity decrease
        sensitivity_factor = 1 - params["sensitivity_decrease"] * t
        
        contaminated = contaminated * sensitivity_factor + aging + noise
        return contaminated
    
    def _apply_environmental_interference(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply environmental interference confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate interference events
        interference_mask = np.random.random(n) < params["interference_probability"]
        interference_length = int(params["interference_duration"] * n)
        
        for i in range(n):
            if interference_mask[i]:
                # Apply interference
                interference_amplitude = params["interference_amplitude"]
                interference_freq = params["interference_frequency"]
                for j in range(min(interference_length, n - i)):
                    if i + j < n:
                        interference_signal = interference_amplitude * np.sin(2 * np.pi * interference_freq * j)
                        contaminated[i + j] += interference_signal
        
        return contaminated
    
    def _apply_mixed_realistic_light(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply light realistic confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Add noise
        noise = np.random.normal(0, params["noise_level"], n)
        contaminated += noise
        
        # Add drift
        drift = params["drift_rate"] * np.arange(n) / n
        contaminated += drift
        
        # Add occasional artifacts
        artifact_mask = np.random.random(n) < params["artifact_probability"]
        contaminated[artifact_mask] += np.random.normal(0, 0.5, np.sum(artifact_mask))
        
        # Add trend
        trend = params["trend_component"] * np.arange(n) / n
        contaminated += trend
        
        return contaminated
    
    def _apply_mixed_realistic_moderate(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply moderate realistic confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Add noise
        noise = np.random.normal(0, params["noise_level"], n)
        contaminated += noise
        
        # Add drift
        drift = params["drift_rate"] * np.arange(n) / n
        contaminated += drift
        
        # Add artifacts
        artifact_mask = np.random.random(n) < params["artifact_probability"]
        contaminated[artifact_mask] += np.random.normal(0, 1.0, np.sum(artifact_mask))
        
        # Add trend
        trend = params["trend_component"] * np.arange(n) / n
        contaminated += trend
        
        # Add seasonal component
        t = np.arange(n) / n
        seasonal = params["seasonal_amplitude"] * np.sin(2 * np.pi * t / 0.25)
        contaminated += seasonal
        
        return contaminated
    
    def _apply_mixed_realistic_severe(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply severe realistic confounding."""
        n = len(data)
        contaminated = data.copy()
        
        # Add noise
        noise = np.random.normal(0, params["noise_level"], n)
        contaminated += noise
        
        # Add drift
        drift = params["drift_rate"] * np.arange(n) / n
        contaminated += drift
        
        # Add artifacts
        artifact_mask = np.random.random(n) < params["artifact_probability"]
        contaminated[artifact_mask] += np.random.normal(0, 2.0, np.sum(artifact_mask))
        
        # Add trend
        trend = params["trend_component"] * np.arange(n) / n
        contaminated += trend
        
        # Add seasonal component
        t = np.arange(n) / n
        seasonal = params["seasonal_amplitude"] * np.sin(2 * np.pi * t / 0.25)
        contaminated += seasonal
        
        # Add extreme events
        extreme_mask = np.random.random(n) < params["extreme_events"]
        contaminated[extreme_mask] += np.random.normal(0, 5.0, np.sum(extreme_mask))
        
        return contaminated
    
    def _apply_eeg_ocular_artifacts(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply EEG ocular artifacts (blinks, saccades)."""
        n = len(data)
        contaminated = data.copy()
        
        # Assume 250 Hz sampling rate for EEG
        sampling_rate = 250.0
        dt = 1.0 / sampling_rate
        
        # Generate blink artifacts
        blink_mask = np.random.random(n) < params["blink_probability"] * dt
        blink_indices = np.where(blink_mask)[0]
        
        for blink_idx in blink_indices:
            blink_duration = int(params["blink_duration"] * sampling_rate)
            blink_amplitude = params["eye_movement_amplitude"] * np.random.choice([-1, 1])
            
            # Create blink artifact (exponential decay)
            for i in range(min(blink_duration, n - blink_idx)):
                if blink_idx + i < n:
                    decay_factor = np.exp(-i / (blink_duration * 0.3))
                    contaminated[blink_idx + i] += blink_amplitude * decay_factor
        
        # Generate saccade artifacts
        saccade_mask = np.random.random(n) < params["saccade_probability"] * dt
        saccade_indices = np.where(saccade_mask)[0]
        
        for saccade_idx in saccade_indices:
            saccade_duration = int(params["saccade_duration"] * sampling_rate)
            saccade_amplitude = params["eye_movement_amplitude"] * 0.3 * np.random.choice([-1, 1])
            
            # Create saccade artifact (sharp transient)
            for i in range(min(saccade_duration, n - saccade_idx)):
                if saccade_idx + i < n:
                    contaminated[saccade_idx + i] += saccade_amplitude * (1 - i / saccade_duration)
        
        return contaminated
    
    def _apply_eeg_muscle_artifacts(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply EEG muscle artifacts (EMG)."""
        n = len(data)
        contaminated = data.copy()
        
        # Assume 250 Hz sampling rate for EEG
        sampling_rate = 250.0
        dt = 1.0 / sampling_rate
        
        # Generate muscle activity
        muscle_mask = np.random.random(n) < params["muscle_activity_probability"] * dt
        muscle_indices = np.where(muscle_mask)[0]
        
        for muscle_idx in muscle_indices:
            muscle_duration = int(params["muscle_duration"] * sampling_rate)
            muscle_amplitude = params["muscle_amplitude"] * np.random.uniform(0.5, 1.5)
            
            # Create muscle artifact (high-frequency noise)
            for i in range(min(muscle_duration, n - muscle_idx)):
                if muscle_idx + i < n:
                    # High-frequency muscle activity
                    freq = np.random.uniform(params["frequency_min"], params["frequency_max"])
                    phase = 2 * np.pi * freq * i / sampling_rate
                    muscle_signal = muscle_amplitude * np.sin(phase) * np.random.uniform(0.5, 1.0)
                    contaminated[muscle_idx + i] += muscle_signal
        
        return contaminated
    
    def _apply_eeg_cardiac_artifacts(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply EEG cardiac artifacts (ECG)."""
        n = len(data)
        contaminated = data.copy()
        
        # Assume 250 Hz sampling rate for EEG
        sampling_rate = 250.0
        dt = 1.0 / sampling_rate
        
        # Generate heart rate variability
        heart_rate = params["heart_rate"] * (1 + np.random.normal(0, params["variability"]))
        heart_period = 1.0 / heart_rate
        
        # Generate R-peaks
        current_time = 0
        while current_time < n * dt:
            # Add R-peak
            r_peak_idx = int(current_time * sampling_rate)
            if r_peak_idx < n:
                r_peak_amplitude = params["ecg_amplitude"] * np.random.uniform(0.8, 1.2)
                contaminated[r_peak_idx] += r_peak_amplitude
                
                # Add QRS complex
                qrs_duration = int(params["qrs_duration"] * sampling_rate)
                for i in range(1, min(qrs_duration, n - r_peak_idx)):
                    if r_peak_idx + i < n:
                        qrs_decay = np.exp(-i / (qrs_duration * 0.3))
                        contaminated[r_peak_idx + i] += r_peak_amplitude * 0.3 * qrs_decay
            
            # Next heartbeat with variability
            current_time += heart_period * (1 + np.random.normal(0, params["variability"]))
        
        return contaminated
    
    def _apply_eeg_electrode_popping(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply EEG electrode popping artifacts."""
        n = len(data)
        contaminated = data.copy()
        
        # Assume 250 Hz sampling rate for EEG
        sampling_rate = 250.0
        dt = 1.0 / sampling_rate
        
        # Generate electrode pops
        pop_mask = np.random.random(n) < params["pop_probability"] * dt
        pop_indices = np.where(pop_mask)[0]
        
        for pop_idx in pop_indices:
            pop_duration = int(params["pop_duration"] * sampling_rate)
            pop_amplitude = params["pop_amplitude"] * np.random.uniform(0.5, 2.0)
            pop_sign = np.random.choice([-1, 1])
            
            # Create sharp pop artifact
            for i in range(min(pop_duration, n - pop_idx)):
                if pop_idx + i < n:
                    if i == 0:
                        contaminated[pop_idx + i] += pop_amplitude * pop_sign
                    else:
                        # Exponential decay
                        decay_factor = np.exp(-i / (pop_duration * 0.1))
                        contaminated[pop_idx + i] += pop_amplitude * pop_sign * decay_factor * 0.1
        
        return contaminated
    
    def _apply_eeg_electrode_drift(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply EEG electrode drift and impedance changes."""
        n = len(data)
        contaminated = data.copy()
        
        # Generate slow drift
        t = np.arange(n) / 250.0  # Assume 250 Hz sampling rate
        drift = params["drift_rate"] * t + np.random.normal(0, params["drift_variability"], n)
        
        # Add baseline shifts
        baseline_shifts = np.random.normal(0, params["baseline_shift"], n)
        drift += baseline_shifts * 0.01  # Slow baseline changes
        
        # Add impedance-related artifacts
        impedance_changes = np.random.normal(0, params["impedance_change"], n)
        impedance_effect = impedance_changes * np.random.normal(0, 0.1, n)
        
        contaminated += drift + impedance_effect
        return contaminated
    
    def _apply_eeg_60hz_noise(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply EEG 60Hz power line noise and harmonics."""
        n = len(data)
        contaminated = data.copy()
        
        # Assume 250 Hz sampling rate for EEG
        sampling_rate = 250.0
        t = np.arange(n) / sampling_rate
        
        # Generate 60Hz noise
        line_freq = params["line_frequency"] + np.random.normal(0, params["frequency_drift"])
        phase_noise = np.random.normal(0, params["phase_noise"], n)
        
        # Fundamental frequency
        line_noise = params["noise_amplitude"] * np.sin(2 * np.pi * line_freq * t + phase_noise)
        
        # Harmonics (120Hz, 180Hz)
        harmonic_noise = (params["harmonic_amplitude"] * 
                         (np.sin(2 * np.pi * 2 * line_freq * t + phase_noise) +
                          np.sin(2 * np.pi * 3 * line_freq * t + phase_noise)))
        
        contaminated += line_noise + harmonic_noise
        return contaminated
    
    def _apply_eeg_sweat_artifacts(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply EEG sweat artifacts and impedance changes."""
        n = len(data)
        contaminated = data.copy()
        
        # Assume 250 Hz sampling rate for EEG
        sampling_rate = 250.0
        dt = 1.0 / sampling_rate
        
        # Generate sweat events
        sweat_mask = np.random.random(n) < params["sweat_probability"] * dt
        sweat_indices = np.where(sweat_mask)[0]
        
        for sweat_idx in sweat_indices:
            sweat_duration = int(params["sweat_duration"] * sampling_rate)
            sweat_amplitude = params["sweat_amplitude"] * np.random.uniform(0.5, 1.5)
            
            # Create sweat artifact (slow drift + noise)
            for i in range(min(sweat_duration, n - sweat_idx)):
                if sweat_idx + i < n:
                    # Slow drift component
                    drift_component = params["slow_drift"] * i / sampling_rate
                    # Noise component
                    noise_component = np.random.normal(0, sweat_amplitude * 0.1)
                    contaminated[sweat_idx + i] += drift_component + noise_component
        
        return contaminated
    
    def _apply_eeg_movement_artifacts(self, data: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """Apply EEG head/body movement artifacts."""
        n = len(data)
        contaminated = data.copy()
        
        # Assume 250 Hz sampling rate for EEG
        sampling_rate = 250.0
        dt = 1.0 / sampling_rate
        
        # Generate movement events
        movement_mask = np.random.random(n) < params["movement_probability"] * dt
        movement_indices = np.where(movement_mask)[0]
        
        for movement_idx in movement_indices:
            movement_duration = int(params["movement_duration"] * sampling_rate)
            movement_amplitude = params["movement_amplitude"] * np.random.uniform(0.5, 1.5)
            
            # Create movement artifact (low-frequency oscillation)
            for i in range(min(movement_duration, n - movement_idx)):
                if movement_idx + i < n:
                    # Low-frequency movement
                    freq = np.random.uniform(params["frequency_min"], params["frequency_max"])
                    phase = 2 * np.pi * freq * i / sampling_rate
                    movement_signal = movement_amplitude * np.sin(phase) * np.random.uniform(0.5, 1.0)
                    contaminated[movement_idx + i] += movement_signal
        
        return contaminated
    
    def get_available_scenarios(self) -> List[ConfoundingScenario]:
        """Get list of available confounding scenarios."""
        return list(self.profiles.keys())
    
    def get_scenario_info(self, scenario: ConfoundingScenario) -> Dict[str, str]:
        """Get information about a specific scenario."""
        if scenario not in self.profiles:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        profile = self.profiles[scenario]
        return {
            "scenario": scenario.value,
            "description": profile.description,
            "default_intensity": str(profile.intensity),
            "parameters": str(profile.parameters)
        }
