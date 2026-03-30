import streamlit as st
import streamlit.components.v1 as components
import heapq
import math
import time
import base64
import os
import matplotlib.pyplot as plt

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="Auto Park AI", layout="wide")

# ---------------------------
# IMAGE LOADING
# ---------------------------
def load_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_img = load_image("logo.jpeg")
banner_img = load_image("banner.jpeg")

# ---------------------------
# SIDEBAR MENU
# ---------------------------
menu = st.sidebar.selectbox("Menu", ["Home", "🚗 Simulation"])

# ===========================
# 🏠 HOME PAGE (YOUR DESIGN)
# ===========================
if menu == "Home":

    home_html = f"""
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: white;
        }}

        .container {{
            position: relative;
            height: 90vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }}

        .logo {{
            position: absolute;
            top: 20px;
            left: 30px;
            width: 70px;
            border-radius: 10px;
        }}

        .banner {{
            width: 380px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}

        .dept {{
            color: #ffd700;
            font-size: 26px;
            font-weight: bold;
            margin-bottom: 15px;
        }}

        .title {{
            font-size: 60px;
            font-weight: bold;
            margin-bottom: 30px;
        }}

        .credits {{
            font-size: 22px;
            margin-top: 20px;
            line-height: 1.8;
            font-weight: bold;
        }}
    </style>
    </head>

    <body>
        <div class="container">

            <img src="data:image/jpeg;base64,{logo_img}" class="logo">

            <img src="data:image/jpeg;base64,{banner_img}" class="banner">

            <div class="dept">ARTIFICIAL INTELLIGENCE & DATA SCIENCE</div>

            <div class="title">Auto-Park AI</div>

            <div class="credits">
                Designed by<br>
                Syed Afrin &nbsp; | &nbsp; P. Saranya &nbsp; | &nbsp; V. Priya
            </div>

        </div>
    </body>
    </html>
    """

    components.html(home_html, height=600, scrolling=False)

# ===========================
# 🚗 SIMULATION PAGE
# ===========================
if menu == "🚗 Simulation":

    st.title("🚗 Auto-Park AI (Sensor-Based A*)")

    def heuristic(a, b):
        return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

    def astar(start, goal, obstacles, grid_size):
        open_list = []
        heapq.heappush(open_list, (0, start))

        came_from = {}
        cost_so_far = {start: 0}

        directions = [(1,0), (-1,0), (0,1), (0,-1)]

        while open_list:
            _, current = heapq.heappop(open_list)

            if current == goal:
                break

            for dx, dy in directions:
                next_node = (current[0]+dx, current[1]+dy)

                if (0 <= next_node[0] < grid_size and
                    0 <= next_node[1] < grid_size and
                    next_node not in obstacles):

                    new_cost = cost_so_far[current] + 1

                    if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                        cost_so_far[next_node] = new_cost
                        priority = new_cost + heuristic(next_node, goal)
                        heapq.heappush(open_list, (priority, next_node))
                        came_from[next_node] = current

        return came_from

    def reconstruct_path(came_from, start, goal):
        current = goal
        path = []

        while current != start:
            path.append(current)
            if current not in came_from:
                return []
            current = came_from[current]

        path.append(start)
        path.reverse()
        return path

    def sensor_scan(real_obstacles, car_pos, radius=2):
        detected = set()
        for ox, oy in real_obstacles:
            if abs(ox - car_pos[0]) <= radius and abs(oy - car_pos[1]) <= radius:
                detected.add((ox, oy))
        return detected

    def plot_graph(path, real_obstacles, start, goal, current_pos=None):
        plt.figure(figsize=(6,6))

        # 🔴 Parking grid
        for i in range(10):
            for j in range(10):
                plt.scatter(i, j, color='red')

        # ⬛ Obstacles
        if real_obstacles:
            ox, oy = zip(*real_obstacles)
            plt.scatter(ox, oy, marker='s', s=120, color='black')

        # 🟢 Path
        if path:
            px, py = zip(*path)
            plt.plot(px, py, color='green', linewidth=3)

        # 🔵 Car
        if current_pos:
            plt.scatter(current_pos[0], current_pos[1], s=200, color='blue')

        # Start & Goal
        plt.scatter(start[0], start[1], s=150, color='yellow')
        plt.scatter(goal[0], goal[1], s=150, color='purple')

        plt.xlim(-1, 10)
        plt.ylim(-1, 10)
        plt.grid(True)

        return plt

    # ---------------------------
    # INPUTS (UNCHANGED)
    # ---------------------------
    grid_size = 10
    st.sidebar.header("⚙️ Controls")

    start_x = st.sidebar.number_input("Start X", 0, 9, 0)
    start_y = st.sidebar.number_input("Start Y", 0, 9, 0)

    goal_x = st.sidebar.number_input("Goal X", 0, 9, 9)
    goal_y = st.sidebar.number_input("Goal Y", 0, 9, 9)

    start = (start_x, start_y)
    goal = (goal_x, goal_y)

    # 10 Obstacles
    real_obstacles = {
        (2,2), (2,3), (2,4),
        (5,5), (5,6),
        (7,2), (7,3),
        (4,8), (6,8),
        (3,6)
    }

    # ---------------------------
    # RUN BUTTON
    # ---------------------------
    if st.button("Run Auto-Park 🚗"):

        if start in real_obstacles or goal in real_obstacles:
            st.error("❌ Start/Goal cannot be on obstacle!")
            st.stop()

        placeholder = st.empty()
        current_pos = start
        full_path = [start]

        while current_pos != goal:

            detected = sensor_scan(real_obstacles, current_pos)

            came_from = astar(current_pos, goal, detected, grid_size)
            path = reconstruct_path(came_from, current_pos, goal)

            if not path or len(path) < 2:
                st.error("❌ No path found!")
                break

            next_step = path[1]
            full_path.append(next_step)
            current_pos = next_step

            fig = plot_graph(full_path, real_obstacles, start, goal, current_pos)
            placeholder.pyplot(fig)
            plt.close()
            time.sleep(0.4)

        if current_pos == goal:
            st.success("🎯 Car reached destination!")

            st.subheader("📍 Path Traversed by Car")
            path_str = " ➝ ".join([str(p) for p in full_path])
            st.success(path_str)