#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path

# -----------------------------
# Base directory
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent

# -----------------------------
# Desired FinSecAI folder structure
# -----------------------------
structure = {
    "data": {
        "raw": [],
        "processed": [],
        "synthetic": [],
        "soc_feedback": []
    },
    "notebooks": {
        "1_data_ingestion.ipynb": [],
        "2_preprocessing.ipynb": [],
        "3_ml_models.ipynb": [],
        "4_event_correlation.ipynb": [],
        "5_mitre_mapping.ipynb": [],
        "6_nlp_narratives.ipynb": [],
        "7_feedback_learning.ipynb": [],
        "8_demo_dashboard.ipynb": []
    },
    "src": {
        "common": ["__init__.py", "alert_schema.py"],
        "data_ingestion": ["__init__.py", "ingestion.py", "log_parsers.py"],
        "preprocessing": ["__init__.py", "clean_logs.py"],
        "models": ["__init__.py", "fraud_detection.py", "anomaly_detection.py",
                   "insider_behavior.py", "risk_scoring.py", "model_registry.py",
                   "feature_engineering.py", "correlation_engine.py",
                   "retraining_dataset.py", "soc_intelligence.py", "soc_response.py",
                   "advanced_correlation_engine.py", "ambiguity.py"],
        "mitre": ["__init__.py", "tactic_mapper.py", "technique_mapper.py",
                  "mitre_rules.yaml", "mapping.py"],
        "nlp": ["__init__.py", "t5_narratives.py", "narration_templates.py",
                "loRA_update.py", "drift_detector.py", "feedback_handler.py",
                "narrative_generator.py", "narrative_quality.py"],
        "feedback_loop": ["__init__.py", "retraining.py", "drift_detection.py",
                          "soc_vote_processor.py"],
        "web3": ["__init__.py", "audit.py", "deploy.py", "log_event.py",
                 "contracts\\ThreatLogger.sol"],
        "dashboard": ["__init__.py", "app.py", "mitre_view.py", "soc_review.py"]
    },
    "scripts": ["run_pipeline.py", "simulate_feedback.py",
                "generate_synthetic_data.py", "retrain_models.py"],
    "requirements.txt": [],
    "README.md": [],
    "setup.py": []
}

# -----------------------------
# Folders to remove (unwanted / duplicates)
# -----------------------------
unwanted_folders = [
    "Phase 6 – Role-Based SOC Operations  Tier-1 vs Tier-2 analyst permissions  Incident escalation workflow  SLA timers",
    ".ipynb_checkpoints",
    "lora_incremental",
    "deployment",
    "offload_dir",
    "venv",
    ".qodo",
    ".venv"
]

# -----------------------------
# Remove unwanted folders
# -----------------------------
def remove_unwanted(base_dir, folders):
    for folder in folders:
        path = base_dir / folder
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            print(f"Removed folder: {path}")

# -----------------------------
# Create folders and files (nested paths safe)
# -----------------------------
def create_folders_and_files(base_path, struct):
    for name, value in struct.items():
        folder_path = base_path / name
        if isinstance(value, dict):
            folder_path.mkdir(parents=True, exist_ok=True)
            create_folders_and_files(folder_path, value)
        elif isinstance(value, list):
            folder_path.mkdir(parents=True, exist_ok=True)
            for file_name in value:
                file_path = folder_path / Path(file_name)
                file_path.parent.mkdir(parents=True, exist_ok=True)  # ensures nested dirs
                file_path.touch(exist_ok=True)

# -----------------------------
# Print folder tree
# -----------------------------
def print_tree(path, prefix=""):
    path = Path(path)
    print(f"{prefix}📂 {path.name}/")
    for item in sorted(path.iterdir()):
        if item.is_dir():
            print_tree(item, prefix + "    ")
        else:
            print(f"{prefix}    📄 {item.name}")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("Removing unwanted folders...")
    remove_unwanted(BASE_DIR, unwanted_folders)

    print("\nCreating folders and files...")
    create_folders_and_files(BASE_DIR, structure)

    print("\n✅ Updated FinSecAI Folder Structure:")
    print_tree(BASE_DIR)
