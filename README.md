# 🏋️ AI Personal Trainer

An intelligent virtual fitness coach that uses computer vision and machine learning to track exercises in real-time, provide form feedback, and analyze workout progress.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎥 Real-time Pose Detection | Uses MediaPipe to track 33 body landmarks |
| 🔢 Auto Rep Counting | Automatically counts push-ups and squats |
| ⚠️ Form Correction | Instant feedback on bad form |
| 🔥 Calorie Tracking | Personalized calculation based on weight |
| 📊 Analytics Dashboard | Progress charts and statistics |
| 💾 Data Persistence | SQLite database for workout history |

## 🛠️ Tech Stack

- Python 3.x
- OpenCV
- MediaPipe
- Tkinter
- Matplotlib
- SQLite3
- NumPy

## 📥 Installation

```bash
# Clone the repository
git clone https://github.com/MoAshraf149/AI-Personal-Trainer.git

# Install dependencies
pip install opencv-python mediapipe numpy matplotlib pillow

# Run the application
python gym_trainer.py
