# data.py
import pandas as pd
import json
import os

DATA_DIR = "data"


# -------------------------------
# RAINFALL
# -------------------------------
def load_rainfall_excel(filename="rainfall.xlsx"):
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_excel(path)
    return df


def save_rainfall_excel(df, filename="rainfall.xlsx"):
    path = os.path.join(DATA_DIR, filename)
    df.to_excel(path, index=False)


# -------------------------------
# PROJECT SAVE / OPEN
# -------------------------------
def save_project(data: dict, filename="project.json"):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_project(filename="project.json"):
    path = os.path.join(DATA_DIR, filename)
    with open(path) as f:
        return json.load(f)
