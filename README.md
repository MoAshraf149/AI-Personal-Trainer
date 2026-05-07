# 🏋️ AI Personal Trainer

An intelligent virtual fitness coach that uses computer vision and machine learning to track exercises in real-time, provide form feedback, and analyze workout progress.

---

## 🎮 How to Use

1️⃣ Enter your personal data 
 (name, age, weight, height) 
 
2️⃣ Select exercise
 (Push-ups or Squats) 
 
3️⃣ Press START and begin your workout

4️⃣ AI will count reps and provide feedback 
 
5️⃣ Check analytics to track your progress 


### Detailed Steps:

| Step | Action | What happens? |
|------|--------|----------------|
| **1** | Enter your personal data | Name, Age, Weight, Height → BMI & BMR calculated |
| **2** | Select exercise | Push-ups (20 reps) OR Squats (25 reps) |
| **3** | Press START | Camera activates, AI begins tracking |
| **4** | Perform exercise | AI detects movement and counts reps |
| **5** | Check feedback | "GOOD FORM!" or "⚠️ TOO LOW!" |
| **6** | Complete target | "🎉 CONGRATULATIONS!" message appears |
| **7** | View analytics | Progress charts and calorie statistics |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎥 Real-time Pose Detection | Uses MediaPipe to track 33 body landmarks |
| 🔢 Auto Rep Counting | Automatically counts push-ups and squats |
| ⚠️ Form Correction | Instant feedback on bad form |
| 🔥 Calorie Tracking | Personalized calculation based on weight |
| 📊 Analytics Dashboard | Progress charts and statistics |
| 💾 Data Persistence | SQLite database for workout history |

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.x |
| Computer Vision | OpenCV |
| Pose Detection | MediaPipe |
| GUI | Tkinter |
| Visualization | Matplotlib |
| Database | SQLite3 |
| Mathematics | NumPy |

---

## 📥 Installation

```bash
# Clone the repository
git clone https://github.com/MoAshraf149/AI-Personal-Trainer.git

# Go to project directory
cd AI-Personal-Trainer

# Install dependencies
pip install opencv-python mediapipe numpy matplotlib pillow

# Run the application
python gym_trainer.py
```

---

🎥 Demo Preview
