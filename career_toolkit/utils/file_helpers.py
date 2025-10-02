"""File operation helpers for job tracking and asset management."""

import os
import json


def get_job_notes(job_folder_path: str) -> dict:
    """Read the notes.json file for a given job."""
    notes_path = os.path.join(job_folder_path, "notes.json")
    if os.path.exists(notes_path):
        with open(notes_path, 'r') as f:
            return json.load(f)
    return {}


def save_job_notes(job_folder_path: str, notes: dict):
    """Save the notes dictionary to notes.json."""
    notes_path = os.path.join(job_folder_path, "notes.json")
    with open(notes_path, 'w') as f:
        json.dump(notes, f, indent=2)
