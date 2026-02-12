# utils.py
import json
from datetime import datetime

HABIT_FILE = "habits.json"

def load_habits():
    try:
        with open(HABIT_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_habits(habits):
    with open(HABIT_FILE, "w") as f:
        json.dump(habits, f, indent=4)

def add_habit(user_id, habit_name, goal_minutes):
    habits = load_habits()
    if user_id not in habits:
        habits[user_id] = {}
    habits[user_id][habit_name] = {
        "goal": goal_minutes,
        "history": []
    }
    save_habits(habits)

def mark_done(user_id, habit_name, minutes_done):
    habits = load_habits()
    if user_id in habits and habit_name in habits[user_id]:
        today = datetime.now().strftime("%Y-%m-%d")
        habits[user_id][habit_name]["history"].append({
            "date": today,
            "minutes_done": minutes_done
        })
        save_habits(habits)

def delete_habit(user_id, habit_name):
    habits = load_habits()
    if user_id in habits and habit_name in habits[user_id]:
        del habits[user_id][habit_name]
        save_habits(habits)
