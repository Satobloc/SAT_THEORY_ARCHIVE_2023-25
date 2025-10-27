
# 📌 BLOCK 3: Species Definitions and Traits (Expanded + Fixed)
import numpy as np
import pandas as pd
from collections import defaultdict
import random

# Local species list to support 'random' dyad logic
available_species = ["Human", "Pak", "Grog", "Chitter", "random"]

# Canonical vectors
species_vectors = {
    "Human": {
        "Interpretability": 3,
        "Deception Bias": 3,
        "Volatility": 7,
        "Resistance to Pressure": 2,
        "Cultural Rigidity": 0,
        "Assimilation Potential": 6,
        "Creative Divergence": 8,
        "Cooperation Bias": 5,
        "Conflict Bias": 5,
        "Hierarchy Enforcement": 3
    },
    "Pak": {
        "Interpretability": -5,
        "Deception Bias": 6,
        "Volatility": 4,
        "Resistance to Pressure": 9,
        "Cultural Rigidity": 9,
        "Assimilation Potential": -8,
        "Creative Divergence": -3,
        "Cooperation Bias": -5,
        "Conflict Bias": 9,
        "Hierarchy Enforcement": 8
    },
    "Grog": {
        "Interpretability": -2,
        "Deception Bias": -7,
        "Volatility": 1,
        "Resistance to Pressure": 10,
        "Cultural Rigidity": 8,
        "Assimilation Potential": -6,
        "Creative Divergence": -8,
        "Cooperation Bias": 7,
        "Conflict Bias": -3,
        "Hierarchy Enforcement": 4
    },
    "Chitter": {
        "Interpretability": -6,
        "Deception Bias": 7,
        "Volatility": 5,
        "Resistance to Pressure": -1,
        "Cultural Rigidity": 2,
        "Assimilation Potential": 3,
        "Creative Divergence": 4,
        "Cooperation Bias": -1,
        "Conflict Bias": 6,
        "Hierarchy Enforcement": 0
    }
}

# Traits by species
species_traits = {
    "Human": {
        "Tribal Empathy": ["Cooperation Bias", "Conflict Bias", "Assimilation Potential"],
        "Improvisational Intelligence": ["Creative Divergence", "Resistance to Pressure", "Volatility"],
        "Symbolic Saturation Tolerance": ["Interpretability", "Deception Bias", "Cultural Rigidity"],
        "Altruism Instability Reflex": ["Cooperation Bias", "Volatility", "Deception Bias"],
        "Strategic Transparency Tendency": ["Interpretability", "Deception Bias", "Resistance to Pressure"],
        "Violence Recursion Tolerance": ["Conflict Bias", "Cultural Rigidity", "Creative Divergence"],
        "Status Symbol Plasticity": ["Assimilation Potential", "Deception Bias", "Cultural Rigidity"],
        "Time Horizon Diversity": ["Volatility", "Resistance to Pressure", "Interpretability"]
    },
    "Pak": {
        "Gene-Anchor Drive": ["Cooperation Bias", "Conflict Bias", "Resistance to Pressure", "Cultural Rigidity"],
        "Optimization Psychosis": ["Creative Divergence", "Resistance to Pressure", "Volatility", "Deception Bias"],
        "Absolute Goal Lock": ["Interpretability", "Assimilation Potential", "Cultural Rigidity", "Cooperation Bias"],
        "Cognitive Asymmetry Tolerance": ["Interpretability", "Deception Bias", "Conflict Bias", "Hierarchy Enforcement"],
        "Preemptive Aggression Heuristic": ["Conflict Bias", "Volatility", "Resistance to Pressure", "Deception Bias"],
        "Tool Cognition Externalization": ["Assimilation Potential", "Cooperation Bias", "Creative Divergence", "Hierarchy Enforcement"]
    },
    "Grog": {
        "Sessile Survivalism": ["Resistance to Pressure", "Cultural Rigidity", "Volatility"],
        "Empathic Modulation": ["Cooperation Bias", "Conflict Bias", "Interpretability"],
        "Telepathic Dependence": ["Hierarchy Enforcement", "Deception Bias", "Assimilation Potential"]
    },
    "Chitter": {
        "Hypercultural Drift": ["Creative Divergence", "Interpretability", "Volatility"],
        "Myth-Encoded Camouflage": ["Deception Bias", "Cultural Rigidity", "Resistance to Pressure"],
        "Instinctual Narrative Masking": ["Conflict Bias", "Cooperation Bias", "Assimilation Potential"]
    }
}

# Trait-to-axis reverse mapping
def reverse_traits(trait_map):
    reverse = defaultdict(list)
    for trait, axes in trait_map.items():
        for axis in axes:
            reverse[axis].append(trait)
    return dict(reverse)

# Handle random selection
if species_a == "random":
    species_a = random.choice(available_species)
if species_b == "random":
    species_b = random.choice(available_species)

vector_a = species_vectors[species_a]
vector_b = species_vectors[species_b]
traits_a = reverse_traits(species_traits[species_a])
traits_b = reverse_traits(species_traits[species_b])
