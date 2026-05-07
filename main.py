"""
AI Personal Trainer - نسخة مستقرة مع تحليلات ومعلومات شخصية
"""

import cv2
import mediapipe as mp
import numpy as np
import sqlite3
import datetime
import time
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ============================================
# تهيئة MediaPipe
# ============================================
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# ============================================
# ألوان الجيم
# ============================================
COLORS = {
    'bg_dark': '#0a0a0a',
    'bg_card': '#1a1a2e',
    'primary': '#e63946',
    'secondary': '#f4a261',
    'success': '#2ecc71',
    'warning': '#f1c40f',
    'info': '#3498db',
    'text': '#ffffff',
    'text_muted': '#888888',
    'accent': '#00b4d8',
    'purple': '#9b59b6',
}

# ============================================
# متغيرات عامة لتخزين بيانات المستخدم
# ============================================
user_data = {
    'name': '',
    'age': 25,
    'weight': 70,
    'height': 170,
    'bmi': 0,
    'bmr': 0,
}

# ============================================
# قاعدة البيانات
# ============================================

def init_db():
    conn = sqlite3.connect('fitness_tracker.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        weight REAL,
        height REAL,
        bmi REAL,
        bmr REAL,
        created_date TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise TEXT,
        reps INTEGER,
        date TEXT,
        duration REAL,
        avg_angle REAL,
        weight REAL,
        calories_burned REAL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise TEXT,
        total_reps INTEGER,
        total_calories REAL,
        date TEXT
    )''')
    
    conn.commit()
    conn.close()

def save_user_profile(name, age, weight, height):
    conn = sqlite3.connect('fitness_tracker.db')
    c = conn.cursor()
    
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute('''INSERT INTO user_profile (name, age, weight, height, bmi, bmr, created_date) 
                 VALUES (?,?,?,?,?,?,?)''',
              (name, age, weight, height, bmi, bmr, today))
    
    conn.commit()
    conn.close()
    
    return bmi, bmr

def get_user_profile():
    conn = sqlite3.connect('fitness_tracker.db')
    c = conn.cursor()
    
    c.execute('''SELECT name, age, weight, height, bmi, bmr 
                 FROM user_profile 
                 ORDER BY id DESC LIMIT 1''')
    result = c.fetchone()
    
    conn.close()
    
    if result:
        return {
            'name': result[0],
            'age': result[1],
            'weight': result[2],
            'height': result[3],
            'bmi': result[4],
            'bmr': result[5]
        }
    return None

def calculate_calories(exercise, reps, weight, duration):
    if exercise == 'pushup':
        calories_per_rep_per_kg = 0.025
    else:
        calories_per_rep_per_kg = 0.032
    
    calories = reps * weight * calories_per_rep_per_kg
    if duration > 0:
        calories += (duration / 60) * (weight * 0.05)
    
    return round(calories, 1)

def save_workout(exercise, reps, duration, avg_angle, weight):
    conn = sqlite3.connect('fitness_tracker.db')
    c = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    calories = calculate_calories(exercise, reps, weight, duration)
    
    c.execute("""INSERT INTO workouts (exercise, reps, date, duration, avg_angle, weight, calories_burned) 
                 VALUES (?,?,?,?,?,?,?)""",
              (exercise, reps, today, duration, avg_angle, weight, calories))
    
    existing = c.execute("""SELECT total_reps, total_calories 
                            FROM daily_stats 
                            WHERE exercise=? AND date=?""", 
                        (exercise, today)).fetchone()
    
    if existing:
        c.execute("""UPDATE daily_stats 
                     SET total_reps=?, total_calories=? 
                     WHERE exercise=? AND date=?""", 
                 (existing[0] + reps, existing[1] + calories, exercise, today))
    else:
        c.execute("""INSERT INTO daily_stats (exercise, total_reps, total_calories, date) 
                     VALUES (?,?,?,?)""",
                 (exercise, reps, calories, today))
    
    conn.commit()
    conn.close()
    
    return calories

def get_advanced_stats(exercise=None):
    conn = sqlite3.connect('fitness_tracker.db')
    c = conn.cursor()
    
    stats = {}
    
    if exercise:
        c.execute("""SELECT SUM(reps), COUNT(*), AVG(avg_angle), SUM(calories_burned) 
                     FROM workouts WHERE exercise=?""", (exercise,))
        total_reps, sessions, avg_angle, total_calories = c.fetchone()
    else:
        c.execute("""SELECT SUM(reps), COUNT(*), AVG(avg_angle), SUM(calories_burned) 
                     FROM workouts""")
        total_reps, sessions, avg_angle, total_calories = c.fetchone()
    
    stats['total_reps'] = total_reps or 0
    stats['sessions'] = sessions or 0
    stats['avg_angle'] = int(avg_angle or 0)
    stats['total_calories'] = int(total_calories or 0)
    
    c.execute("""SELECT date, SUM(reps) as total 
                FROM workouts 
                GROUP BY date 
                ORDER BY total DESC LIMIT 1""")
    best_day = c.fetchone()
    stats['best_day'] = best_day if best_day else ('No data', 0)
    
    for ex in ['pushup', 'squat']:
        c.execute("SELECT MAX(reps) FROM workouts WHERE exercise=?", (ex,))
        stats[f'best_{ex}'] = c.fetchone()[0] or 0
    
    c.execute("""SELECT date, SUM(reps) as total, SUM(calories_burned) as calories
                FROM workouts 
                WHERE date >= date('now', '-7 days')
                GROUP BY date
                ORDER BY date""")
    stats['weekly_data'] = c.fetchall()
    
    conn.close()
    return stats

def get_comparison_stats():
    conn = sqlite3.connect('fitness_tracker.db')
    c = conn.cursor()
    
    comparison = {}
    for ex in ['pushup', 'squat']:
        c.execute("""SELECT SUM(reps), COUNT(*), AVG(avg_angle), SUM(calories_burned) 
                     FROM workouts WHERE exercise=?""", (ex,))
        total, sessions, avg_angle, calories = c.fetchone()
        comparison[ex] = {
            'total': total or 0,
            'sessions': sessions or 0,
            'avg_angle': int(avg_angle or 0),
            'calories': int(calories or 0)
        }
        c.execute("SELECT MAX(reps) FROM workouts WHERE exercise=?", (ex,))
        comparison[ex]['best_session'] = c.fetchone()[0] or 0
    
    conn.close()
    return comparison

def get_progress_data(days=30):
    conn = sqlite3.connect('fitness_tracker.db')
    c = conn.cursor()
    
    c.execute("""SELECT date, 
                SUM(CASE WHEN exercise='pushup' THEN reps ELSE 0 END) as pushups,
                SUM(CASE WHEN exercise='squat' THEN reps ELSE 0 END) as squats,
                SUM(CASE WHEN exercise='pushup' THEN calories_burned ELSE 0 END) as pushup_cals,
                SUM(CASE WHEN exercise='squat' THEN calories_burned ELSE 0 END) as squat_cals
                FROM workouts 
                WHERE date >= date('now', ?)
                GROUP BY date
                ORDER BY date""", (f'-{days} days',))
    
    data = c.fetchall()
    conn.close()
    return data

# ============================================
# تحليل التمارين
# ============================================

def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

class ExerciseAnalyzer:
    def __init__(self, exercise_type):
        self.exercise_type = exercise_type
        self.count = 0
        self.down = False
        self.angles = []
        self.feedback = "Ready!"
        
    def process(self, landmarks):
        try:
            if self.exercise_type == "pushup":
                shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
                wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
                angle = calculate_angle(shoulder, elbow, wrist)
                
                if angle < 90 and not self.down:
                    self.down = True
                    self.feedback = "⬇️ PUSH UP!"
                elif angle > 150 and self.down:
                    self.down = False
                    self.count += 1
                    self.feedback = f"🎉 REP {self.count}!"
                
                if angle < 70:
                    self.feedback = "⚠️ TOO LOW!"
                elif angle > 160 and self.down:
                    self.feedback = "⚠️ GO LOWER!"
                    
            else:
                hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
                knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
                ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
                angle = calculate_angle(hip, knee, ankle)
                
                if angle < 100 and not self.down:
                    self.down = True
                    self.feedback = "⬇️ SQUAT DOWN!"
                elif angle > 150 and self.down:
                    self.down = False
                    self.count += 1
                    self.feedback = f"🎉 REP {self.count}!"
                
                if angle < 70:
                    self.feedback = "⚠️ TOO DEEP!"
                elif angle > 160 and self.down:
                    self.feedback = "⚠️ GO DEEPER!"
            
            self.angles.append(angle)
            return self.count, angle, self.feedback
            
        except:
            return self.count, 0, "🚶 STEP INTO FRAME"

# ============================================
# نافذة إدخال البيانات الشخصية (مع زرار البدء)
# ============================================

class UserInfoWindow:
    def __init__(self, parent, on_complete_callback):
        self.parent = parent
        self.on_complete = on_complete_callback
        self.window = tk.Toplevel(parent)
        self.window.title("🏋️ Welcome to GYM AI Trainer")
        self.window.geometry("500x600")
        self.window.configure(bg=COLORS['bg_dark'])
        self.window.transient(parent)
        self.window.grab_set()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        
    def setup_ui(self):
        header = tk.Frame(self.window, bg=COLORS['primary'], height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🏋️ GYM AI TRAINER", 
                font=('Impact', 24), fg='white', bg=COLORS['primary']).pack(pady=30)
        
        content = tk.Frame(self.window, bg=COLORS['bg_dark'])
        content.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        tk.Label(content, text="👋", font=('Arial', 48), bg=COLORS['bg_dark'], fg=COLORS['secondary']).pack()
        tk.Label(content, text="Let's get to know you!", 
                font=('Arial', 16, 'bold'), bg=COLORS['bg_dark'], fg=COLORS['text']).pack(pady=(0, 20))
        
        # Full Name
        tk.Label(content, text="Full Name", font=('Arial', 11, 'bold'),
                bg=COLORS['bg_dark'], fg=COLORS['text_muted']).pack(anchor=tk.W)
        self.name_entry = tk.Entry(content, font=('Arial', 14), bg=COLORS['bg_card'], 
                                   fg=COLORS['text'], insertbackground=COLORS['text'],
                                   relief=tk.FLAT, bd=2)
        self.name_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Age
        tk.Label(content, text="Age", font=('Arial', 11, 'bold'),
                bg=COLORS['bg_dark'], fg=COLORS['text_muted']).pack(anchor=tk.W)
        self.age_entry = tk.Entry(content, font=('Arial', 14), bg=COLORS['bg_card'],
                                  fg=COLORS['text'], insertbackground=COLORS['text'],
                                  relief=tk.FLAT, bd=2)
        self.age_entry.pack(fill=tk.X, pady=(5, 15))
        self.age_entry.insert(0, "20")
        
        # Weight
        weight_frame = tk.Frame(content, bg=COLORS['bg_dark'])
        weight_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(weight_frame, text="Weight", font=('Arial', 11, 'bold'),
                bg=COLORS['bg_dark'], fg=COLORS['text_muted']).pack(anchor=tk.W)
        weight_input_frame = tk.Frame(weight_frame, bg=COLORS['bg_dark'])
        weight_input_frame.pack(fill=tk.X)
        self.weight_entry = tk.Entry(weight_input_frame, font=('Arial', 14), bg=COLORS['bg_card'],
                                     fg=COLORS['text'], insertbackground=COLORS['text'],
                                     relief=tk.FLAT, bd=2, width=15)
        self.weight_entry.pack(side=tk.LEFT)
        self.weight_entry.insert(0, "110")
        tk.Label(weight_input_frame, text="kg", font=('Arial', 12),
                bg=COLORS['bg_dark'], fg=COLORS['text_muted']).pack(side=tk.LEFT, padx=10)
        
        # Height
        height_frame = tk.Frame(content, bg=COLORS['bg_dark'])
        height_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(height_frame, text="Height", font=('Arial', 11, 'bold'),
                bg=COLORS['bg_dark'], fg=COLORS['text_muted']).pack(anchor=tk.W)
        height_input_frame = tk.Frame(height_frame, bg=COLORS['bg_dark'])
        height_input_frame.pack(fill=tk.X)
        self.height_entry = tk.Entry(height_input_frame, font=('Arial', 14), bg=COLORS['bg_card'],
                                     fg=COLORS['text'], insertbackground=COLORS['text'],
                                     relief=tk.FLAT, bd=2, width=15)
        self.height_entry.pack(side=tk.LEFT)
        self.height_entry.insert(0, "189")
        tk.Label(height_input_frame, text="cm", font=('Arial', 12),
                bg=COLORS['bg_dark'], fg=COLORS['text_muted']).pack(side=tk.LEFT, padx=10)
        
        # START TRAINING BUTTON - دا اللي كان ناقص!
        start_btn = tk.Button(content, text="🔥 START TRAINING 🔥", 
                              font=('Arial', 16, 'bold'),
                              bg=COLORS['success'], fg='white',
                              cursor='hand2', bd=0, pady=15,
                              command=self.save_and_proceed)
        start_btn.pack(fill=tk.X, pady=(20, 10))
        
        tk.Label(content, text="⚡ We'll use this data to calculate calories\n"
                              "   and provide personalized fitness analytics",
                font=('Arial', 9), bg=COLORS['bg_dark'], fg=COLORS['text_muted'],
                justify=tk.CENTER).pack(pady=10)
        
        # Load existing data
        self.load_existing_data()
        
    def load_existing_data(self):
        profile = get_user_profile()
        if profile:
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, profile['name'])
            self.age_entry.delete(0, tk.END)
            self.age_entry.insert(0, str(profile['age']))
            self.weight_entry.delete(0, tk.END)
            self.weight_entry.insert(0, str(profile['weight']))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(profile['height']))
    
    def save_and_proceed(self):
        name = self.name_entry.get().strip()
        age = self.age_entry.get().strip()
        weight = self.weight_entry.get().strip()
        height = self.height_entry.get().strip()
        
        if not name:
            messagebox.showwarning("⚠️ Missing Info", "Please enter your name!")
            return
        
        try:
            age_val = int(age)
            if age_val < 10 or age_val > 120:
                raise ValueError
        except:
            messagebox.showwarning("⚠️ Invalid Age", "Please enter a valid age (10-120)!")
            return
        
        try:
            weight_val = float(weight)
            if weight_val < 20 or weight_val > 300:
                raise ValueError
        except:
            messagebox.showwarning("⚠️ Invalid Weight", "Please enter a valid weight (20-300 kg)!")
            return
        
        try:
            height_val = float(height)
            if height_val < 80 or height_val > 250:
                raise ValueError
        except:
            messagebox.showwarning("⚠️ Invalid Height", "Please enter a valid height (80-250 cm)!")
            return
        
        bmi, bmr = save_user_profile(name, age_val, weight_val, height_val)
        
        global user_data
        user_data['name'] = name
        user_data['age'] = age_val
        user_data['weight'] = weight_val
        user_data['height'] = height_val
        user_data['bmi'] = bmi
        user_data['bmr'] = bmr
        
        self.window.destroy()
        
        messagebox.showinfo("🏆 Welcome Aboard!", 
                           f"Welcome {name}!\n\n"
                           f"📊 Your Stats:\n"
                           f"• Age: {age_val}\n"
                           f"• Weight: {weight_val} kg\n"
                           f"• Height: {height_val} cm\n"
                           f"• BMI: {bmi:.1f}\n\n"
                           f"🔥 Let's start training!")
        
        self.on_complete()
    
    def on_closing(self):
        messagebox.showwarning("⚠️ Required", "Please enter your information to continue!")


# ============================================
# نافذة التحليلات
# ============================================

class AnalyticsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("📊 Analytics | Gym AI Trainer")
        self.window.geometry("1200x700")
        self.window.configure(bg=COLORS['bg_dark'])
        self.window.transient(parent)
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        header = tk.Frame(self.window, bg=COLORS['bg_card'], height=60)
        header.pack(fill=tk.X, pady=(0, 20))
        header.pack_propagate(False)
        
        tk.Label(header, text="📊 FITNESS ANALYTICS DASHBOARD", 
                font=('Impact', 20), fg=COLORS['primary'], bg=COLORS['bg_card']).pack(pady=15)
        
        main_frame = tk.Frame(self.window, bg=COLORS['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        left_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'], width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_frame.pack_propagate(False)
        
        right_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        profile = get_user_profile()
        if profile:
            user_card = tk.Frame(left_frame, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
            user_card.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(user_card, text="👤 USER PROFILE", font=('Arial', 14, 'bold'),
                    fg=COLORS['secondary'], bg=COLORS['bg_card']).pack(pady=10)
            
            tk.Label(user_card, text=f"Name: {profile['name']}", 
                    font=('Arial', 12), fg=COLORS['text'], bg=COLORS['bg_card']).pack()
            tk.Label(user_card, text=f"Age: {profile['age']} years", 
                    font=('Arial', 10), fg=COLORS['text_muted'], bg=COLORS['bg_card']).pack()
            tk.Label(user_card, text=f"Weight: {profile['weight']} kg", 
                    font=('Arial', 10), fg=COLORS['info'], bg=COLORS['bg_card']).pack()
            tk.Label(user_card, text=f"Height: {profile['height']} cm", 
                    font=('Arial', 10), fg=COLORS['info'], bg=COLORS['bg_card']).pack()
            tk.Label(user_card, text=f"BMI: {profile['bmi']:.1f}", 
                    font=('Arial', 10), fg=COLORS['success'] if profile['bmi'] < 25 else COLORS['warning'], 
                    bg=COLORS['bg_card']).pack()
            tk.Label(user_card, text=f"BMR: {int(profile['bmr'])} cal/day", 
                    font=('Arial', 10), fg=COLORS['accent'], bg=COLORS['bg_card']).pack(pady=5)
        
        pushup_card = tk.Frame(left_frame, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
        pushup_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(pushup_card, text="💪 PUSH UPS", font=('Arial', 14, 'bold'),
                fg=COLORS['primary'], bg=COLORS['bg_card']).pack(pady=10)
        
        self.pushup_total_label = tk.Label(pushup_card, text="Total: 0", 
                                          font=('Arial', 12), fg=COLORS['text'], bg=COLORS['bg_card'])
        self.pushup_total_label.pack()
        
        self.pushup_calories_label = tk.Label(pushup_card, text="Calories: 0", 
                                             font=('Arial', 10), fg=COLORS['warning'], bg=COLORS['bg_card'])
        self.pushup_calories_label.pack()
        
        self.pushup_best_label = tk.Label(pushup_card, text="Best: 0", 
                                         font=('Arial', 10), fg=COLORS['success'], bg=COLORS['bg_card'])
        self.pushup_best_label.pack(pady=5)
        
        squat_card = tk.Frame(left_frame, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
        squat_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(squat_card, text="🦵 SQUATS", font=('Arial', 14, 'bold'),
                fg=COLORS['accent'], bg=COLORS['bg_card']).pack(pady=10)
        
        self.squat_total_label = tk.Label(squat_card, text="Total: 0", 
                                         font=('Arial', 12), fg=COLORS['text'], bg=COLORS['bg_card'])
        self.squat_total_label.pack()
        
        self.squat_calories_label = tk.Label(squat_card, text="Calories: 0", 
                                            font=('Arial', 10), fg=COLORS['warning'], bg=COLORS['bg_card'])
        self.squat_calories_label.pack()
        
        self.squat_best_label = tk.Label(squat_card, text="Best: 0", 
                                        font=('Arial', 10), fg=COLORS['success'], bg=COLORS['bg_card'])
        self.squat_best_label.pack(pady=5)
        
        total_card = tk.Frame(left_frame, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
        total_card.pack(fill=tk.X)
        
        tk.Label(total_card, text="🏆 TOTAL STATS", font=('Arial', 14, 'bold'),
                fg=COLORS['secondary'], bg=COLORS['bg_card']).pack(pady=10)
        
        self.total_reps_label = tk.Label(total_card, text="Total Reps: 0", 
                                        font=('Arial', 12), fg=COLORS['text'], bg=COLORS['bg_card'])
        self.total_reps_label.pack()
        
        self.total_calories_label = tk.Label(total_card, text="Total Calories: 0", 
                                            font=('Arial', 12), fg=COLORS['warning'], bg=COLORS['bg_card'])
        self.total_calories_label.pack()
        
        self.total_sessions_label = tk.Label(total_card, text="Total Sessions: 0", 
                                            font=('Arial', 12), fg=COLORS['text'], bg=COLORS['bg_card'])
        self.total_sessions_label.pack(pady=5)
        
        chart_frame1 = tk.Frame(right_frame, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
        chart_frame1.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        tk.Label(chart_frame1, text="📈 WEEKLY PROGRESS", font=('Arial', 12, 'bold'),
                fg=COLORS['secondary'], bg=COLORS['bg_card']).pack(pady=10)
        
        self.figure1 = Figure(figsize=(6, 4), facecolor=COLORS['bg_card'])
        self.canvas1 = FigureCanvasTkAgg(self.figure1, master=chart_frame1)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        chart_frame2 = tk.Frame(right_frame, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
        chart_frame2.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(chart_frame2, text="🔥 CALORIES BURNED", font=('Arial', 12, 'bold'),
                fg=COLORS['secondary'], bg=COLORS['bg_card']).pack(pady=10)
        
        self.figure2 = Figure(figsize=(6, 3), facecolor=COLORS['bg_card'])
        self.canvas2 = FigureCanvasTkAgg(self.figure2, master=chart_frame2)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def load_data(self):
        comparison = get_comparison_stats()
        
        self.pushup_total_label.config(text=f"Total: {comparison['pushup']['total']} reps")
        self.pushup_calories_label.config(text=f"Calories: {comparison['pushup']['calories']} cal")
        self.pushup_best_label.config(text=f"Best: {comparison['pushup']['best_session']} reps")
        
        self.squat_total_label.config(text=f"Total: {comparison['squat']['total']} reps")
        self.squat_calories_label.config(text=f"Calories: {comparison['squat']['calories']} cal")
        self.squat_best_label.config(text=f"Best: {comparison['squat']['best_session']} reps")
        
        total_reps = comparison['pushup']['total'] + comparison['squat']['total']
        total_calories = comparison['pushup']['calories'] + comparison['squat']['calories']
        total_sessions = comparison['pushup']['sessions'] + comparison['squat']['sessions']
        
        self.total_reps_label.config(text=f"Total Reps: {total_reps}")
        self.total_calories_label.config(text=f"Total Calories: {total_calories} cal")
        self.total_sessions_label.config(text=f"Total Sessions: {total_sessions}")
        
        self.plot_weekly_progress()
        self.plot_calories_chart()
        
    def plot_weekly_progress(self):
        self.figure1.clear()
        ax = self.figure1.add_subplot(111)
        
        data = get_progress_data(30)
        
        if data:
            dates = [d[0][5:] for d in data]
            pushups = [d[1] for d in data]
            squats = [d[2] for d in data]
            
            x = range(len(dates))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], pushups, width, label='Push-ups', color=COLORS['primary'])
            ax.bar([i + width/2 for i in x], squats, width, label='Squats', color=COLORS['accent'])
            
            ax.set_xlabel('Date', color=COLORS['text'])
            ax.set_ylabel('Reps', color=COLORS['text'])
            ax.set_title('Last 30 Days Progress', color=COLORS['secondary'])
            ax.set_xticks(x)
            ax.set_xticklabels(dates, rotation=45, color=COLORS['text'])
            ax.tick_params(colors=COLORS['text'])
            ax.legend(facecolor=COLORS['bg_card'], edgecolor=COLORS['primary'])
            ax.set_facecolor(COLORS['bg_card'])
        else:
            ax.text(0.5, 0.5, 'No data yet.\nComplete some workouts!', 
                   ha='center', va='center', transform=ax.transAxes, color=COLORS['text'])
            ax.set_facecolor(COLORS['bg_card'])
        
        self.figure1.tight_layout()
        self.canvas1.draw()
    
    def plot_calories_chart(self):
        self.figure2.clear()
        ax = self.figure2.add_subplot(111)
        
        comparison = get_comparison_stats()
        push_cals = comparison['pushup']['calories']
        squat_cals = comparison['squat']['calories']
        
        if push_cals + squat_cals > 0:
            labels = ['Push-ups', 'Squats']
            sizes = [push_cals, squat_cals]
            colors_pie = [COLORS['primary'], COLORS['accent']]
            
            ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%',
                   textprops={'color': COLORS['text']}, startangle=90)
            ax.set_title('Calories Burned by Exercise', color=COLORS['secondary'])
        else:
            ax.text(0.5, 0.5, 'No data yet', ha='center', va='center', color=COLORS['text'])
        
        ax.set_facecolor(COLORS['bg_card'])
        self.figure2.tight_layout()
        self.canvas2.draw()


# ============================================
# الواجهة الرئيسية
# ============================================

class GymTrainerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏋️ GYM AI TRAINER")
        self.root.geometry("1400x800")
        self.root.configure(bg=COLORS['bg_dark'])
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.camera_running = False
        self.cap = None
        self.analyzer = None
        self.current_exercise = None
        self.target_reps = 20
        self.start_time = None
        self.user_weight = 70
        
        init_db()
        
        profile = get_user_profile()
        if profile:
            global user_data
            user_data = profile
            self.user_weight = profile['weight']
            self.setup_ui()
        else:
            self.show_user_info_screen()
        
    def show_user_info_screen(self):
        welcome_frame = tk.Frame(self.root, bg=COLORS['bg_dark'])
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(welcome_frame, text="🏋️ GYM AI TRAINER", 
                font=('Impact', 36), fg=COLORS['primary'], bg=COLORS['bg_dark']).pack(expand=True)
        
        tk.Label(welcome_frame, text="Loading...", 
                font=('Arial', 14), fg=COLORS['text_muted'], bg=COLORS['bg_dark']).pack(pady=20)
        
        self.root.update()
        
        UserInfoWindow(self.root, self.on_user_info_complete)
        
        welcome_frame.destroy()
        
    def on_user_info_complete(self):
        profile = get_user_profile()
        if profile:
            global user_data
            user_data = profile
            self.user_weight = profile['weight']
        self.setup_ui()
        
    def setup_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        main_frame = tk.Frame(self.root, bg=COLORS['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header = tk.Frame(main_frame, bg=COLORS['bg_card'], height=70)
        header.pack(fill=tk.X, pady=(0, 20))
        header.pack_propagate(False)
        
        tk.Label(header, text="🏋️ GYM AI TRAINER", 
                font=('Impact', 26), fg=COLORS['primary'], bg=COLORS['bg_card']).pack(side=tk.LEFT, padx=30, pady=10)
        
        profile = get_user_profile()
        if profile:
            user_label = tk.Label(header, text=f"👤 {profile['name']}", 
                                 font=('Arial', 12, 'bold'), fg=COLORS['success'], bg=COLORS['bg_card'])
            user_label.pack(side=tk.LEFT, padx=20)
        
        analytics_btn = tk.Button(header, text="📊 ANALYTICS", 
                                  font=('Arial', 11, 'bold'),
                                  bg=COLORS['purple'], fg='white',
                                  cursor='hand2', bd=0, padx=20, pady=8,
                                  command=self.open_analytics)
        analytics_btn.pack(side=tk.RIGHT, padx=20)
        
        left_panel = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_panel = tk.Frame(main_frame, bg=COLORS['bg_dark'], width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        right_panel.pack_propagate(False)
        
        self.camera_frame = tk.Frame(left_panel, bg=COLORS['bg_card'], bd=3, relief=tk.RAISED)
        self.camera_frame.pack(fill=tk.BOTH, expand=True)
        
        self.video_label = tk.Label(self.camera_frame, bg=COLORS['bg_card'])
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        profile = get_user_profile()
        welcome_text = tk.Label(self.video_label, 
                                text=f"🤖 Welcome {profile['name'] if profile else 'Athlete'}!\n\nSelect exercise & press START", 
                                font=('Arial', 16), fg=COLORS['text_muted'], bg=COLORS['bg_card'])
        welcome_text.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        exercise_card = tk.Frame(right_panel, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
        exercise_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(exercise_card, text="💪 SELECT EXERCISE", 
                font=('Arial', 14, 'bold'), fg=COLORS['secondary'], bg=COLORS['bg_card']).pack(pady=15)
        
        btn_frame = tk.Frame(exercise_card, bg=COLORS['bg_card'])
        btn_frame.pack(pady=10)
        
        self.pushup_btn = tk.Button(btn_frame, text="🏋️ PUSH UPS", 
                                    font=('Arial', 12, 'bold'), bg=COLORS['primary'], fg='white',
                                    cursor='hand2', bd=0, padx=20, pady=10,
                                    command=lambda: self.select_exercise('pushup', 20))
        self.pushup_btn.pack(side=tk.LEFT, padx=5)
        
        self.squat_btn = tk.Button(btn_frame, text="🦵 SQUATS", 
                                   font=('Arial', 12, 'bold'), bg=COLORS['accent'], fg='white',
                                   cursor='hand2', bd=0, padx=20, pady=10,
                                   command=lambda: self.select_exercise('squat', 25))
        self.squat_btn.pack(side=tk.LEFT, padx=5)
        
        stats_card = tk.Frame(right_panel, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
        stats_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(stats_card, text="📊 LIVE STATS", 
                font=('Arial', 14, 'bold'), fg=COLORS['secondary'], bg=COLORS['bg_card']).pack(pady=15)
        
        self.reps_label = tk.Label(stats_card, text="0 / 20", 
                                   font=('Arial', 48, 'bold'), fg=COLORS['success'], bg=COLORS['bg_card'])
        self.reps_label.pack()
        
        self.angle_label = tk.Label(stats_card, text="Angle: 0°", 
                                    font=('Arial', 14), fg=COLORS['accent'], bg=COLORS['bg_card'])
        self.angle_label.pack(pady=5)
        
        self.feedback_label = tk.Label(stats_card, text="⚡ READY", 
                                       font=('Arial', 12, 'bold'), fg=COLORS['warning'], bg=COLORS['bg_card'])
        self.feedback_label.pack(pady=5)
        
        self.timer_label = tk.Label(stats_card, text="00:00", 
                                    font=('Arial', 24, 'bold'), fg=COLORS['text'], bg=COLORS['bg_card'])
        self.timer_label.pack(pady=10)
        
        control_card = tk.Frame(right_panel, bg=COLORS['bg_card'], relief=tk.RAISED, bd=2)
        control_card.pack(fill=tk.X)
        
        tk.Label(control_card, text="🎮 CONTROLS", 
                font=('Arial', 14, 'bold'), fg=COLORS['secondary'], bg=COLORS['bg_card']).pack(pady=15)
        
        self.start_btn = tk.Button(control_card, text="▶ START", 
                                   font=('Arial', 12, 'bold'), bg=COLORS['success'], fg='white',
                                   cursor='hand2', bd=0, pady=10,
                                   command=self.start_training)
        self.start_btn.pack(fill=tk.X, padx=20, pady=5)
        
        self.stop_btn = tk.Button(control_card, text="⏹ STOP", 
                                  font=('Arial', 12, 'bold'), bg=COLORS['primary'], fg='white',
                                  cursor='hand2', bd=0, pady=10,
                                  command=self.stop_training, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, padx=20, pady=5)
        
        self.reset_btn = tk.Button(control_card, text="🔄 RESET", 
                                   font=('Arial', 11), bg=COLORS['warning'], fg=COLORS['bg_dark'],
                                   cursor='hand2', bd=0, pady=8,
                                   command=self.reset_counter)
        self.reset_btn.pack(fill=tk.X, padx=20, pady=5)
        
    def open_analytics(self):
        AnalyticsWindow(self.root)
        
    def select_exercise(self, exercise, target):
        self.current_exercise = exercise
        self.target_reps = target
        self.reset_counter()
        
        if exercise == 'pushup':
            self.pushup_btn.config(bg=COLORS['primary'], relief=tk.SUNKEN)
            self.squat_btn.config(bg=COLORS['accent'], relief=tk.RAISED)
        else:
            self.squat_btn.config(bg=COLORS['primary'], relief=tk.SUNKEN)
            self.pushup_btn.config(bg=COLORS['accent'], relief=tk.RAISED)
            
    def reset_counter(self):
        if self.analyzer:
            self.analyzer.count = 0
            self.analyzer.down = False
            self.analyzer.angles = []
            self.reps_label.config(text=f"0 / {self.target_reps}")
            self.feedback_label.config(text="🔄 RESET")
            
    def start_training(self):
        if not self.current_exercise:
            messagebox.showwarning("⚠️ Error", "Select an exercise first!")
            return
            
        self.camera_running = True
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            messagebox.showerror("❌ Error", "Cannot open camera!")
            self.camera_running = False
            return
            
        self.analyzer = ExerciseAnalyzer(self.current_exercise)
        self.start_time = time.time()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.pushup_btn.config(state=tk.DISABLED)
        self.squat_btn.config(state=tk.DISABLED)
        
        self.update_camera()
        
    def update_camera(self):
        if not self.camera_running or self.cap is None:
            return
            
        ret, frame = self.cap.read()
        if not ret:
            return
            
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            results = pose.process(rgb)
            
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(46, 204, 113), thickness=2),
                    mp_drawing.DrawingSpec(color=(230, 57, 70), thickness=2)
                )
                
                reps, angle, feedback = self.analyzer.process(results.pose_landmarks.landmark)
                
                self.reps_label.config(text=f"{reps} / {self.target_reps}")
                self.angle_label.config(text=f"Angle: {int(angle)}°")
                self.feedback_label.config(text=feedback)
                
                if "🎉" in feedback:
                    self.feedback_label.config(fg=COLORS['success'])
                elif "⚠️" in feedback:
                    self.feedback_label.config(fg=COLORS['warning'])
                else:
                    self.feedback_label.config(fg=COLORS['accent'])
                
                if self.start_time:
                    elapsed = int(time.time() - self.start_time)
                    minutes = elapsed // 60
                    seconds = elapsed % 60
                    self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
                
                progress = min(1.0, reps / self.target_reps)
                cv2.rectangle(frame, (10, h-30), (int(progress * (w-20)), h-10), (46, 204, 113), -1)
                cv2.rectangle(frame, (10, h-30), (w-10, h-10), (50, 50, 50), 2)
                
                if reps >= self.target_reps:
                    cv2.rectangle(frame, (100, 200), (w-100, 300), (0, 0, 0), -1)
                    cv2.putText(frame, "🎉 CONGRATULATIONS! 🎉", (150, 260), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (46, 204, 113), 3)
                    self.stop_training(show_save_message=True)
                    return
        
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img = ImageTk.PhotoImage(img)
        
        self.video_label.config(image=img)
        self.video_label.image = img
        
        self.root.after(10, self.update_camera)
        
    def stop_training(self, show_save_message=False):
        if self.camera_running and self.analyzer and self.analyzer.count > 0:
            duration = time.time() - self.start_time if self.start_time else 0
            avg_angle = sum(self.analyzer.angles) / len(self.analyzer.angles) if self.analyzer.angles else 0
            
            calories = save_workout(self.current_exercise, self.analyzer.count, duration, avg_angle, self.user_weight)
            
            if show_save_message:
                messagebox.showinfo("✅ Workout Saved!", 
                                   f"Great job!\n\n"
                                   f"Exercise: {self.current_exercise.upper()}\n"
                                   f"Reps: {self.analyzer.count}\n"
                                   f"🔥 Calories Burned: {calories} cal\n"
                                   f"⏱️ Time: {int(duration//60)}m {int(duration%60)}s\n\n"
                                   f"Keep pushing! 💪")
            
        if self.cap:
            self.cap.release()
            
        self.camera_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pushup_btn.config(state=tk.NORMAL)
        self.squat_btn.config(state=tk.NORMAL)
        
        for widget in self.video_label.winfo_children():
            widget.destroy()
        
        profile = get_user_profile()    
        welcome_text = tk.Label(self.video_label, 
                                text=f"🤖 Welcome {profile['name'] if profile else 'Athlete'}!\n\nSelect exercise & press START", 
                                font=('Arial', 16), fg=COLORS['text_muted'], bg=COLORS['bg_card'])
        welcome_text.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
    def on_closing(self):
        if self.camera_running:
            self.stop_training(show_save_message=False)
        self.root.destroy()


# ============================================
# التشغيل
# ============================================

if __name__ == "__main__":
    if os.path.exists('fitness_tracker.db'):
        try:
            conn = sqlite3.connect('fitness_tracker.db')
            c = conn.cursor()
            c.execute("SELECT calories_burned FROM workouts LIMIT 1")
            conn.close()
        except:
            os.remove('fitness_tracker.db')
            print("✅ Old database removed. Creating new one...")
    
    root = tk.Tk()
    app = GymTrainerApp(root)
    root.mainloop()