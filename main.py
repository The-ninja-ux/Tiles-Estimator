import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MplPolygon
from shapely.geometry import Polygon as ShapelyPolygon, box
from math import floor, ceil
import numpy as np

st.set_page_config(layout="wide")
st.title("Polygon Tiling Web App")

st.markdown("""
**Instructions**:  
- Use the fields below to enter polygon vertices  
- Enter tile width and height  
- Click **Run Tiling** to see the grid and tile count
""")

# --- State for dynamic input ---
if "num_vertices" not in st.session_state:
    st.session_state.num_vertices = 3  # start with a triangle

# --- Input: tile dimensions ---
tile_w = st.number_input("Tile Width", min_value=1, value=200, key="tile_w")
tile_h = st.number_input("Tile Height", min_value=1, value=200, key="tile_h")

st.markdown("### Enter Polygon Vertices")

# --- Input: dynamic coordinate fields ---
cols = st.columns([1, 1, 0.5])
vertices = []

for i in range(st.session_state.num_vertices):
    with cols[0]:
        x = st.number_input(f"x{i+1}", key=f"x_{i}")
    with cols[1]:
        y = st.number_input(f"y{i+1}", key=f"y_{i}")
    vertices.append((x, y))

# --- Button to add a new vertex ---
with cols[2]:
    st.write("")  # spacer
    if st.button("+ Add Vertex"):
        st.session_state.num_vertices += 1
        st.rerun()

# --- RUN TILING LOGIC ---
if st.button("Run Tiling"):

    if len(vertices) < 3:
        st.error("Polygon must have at least 3 vertices.")
        st.stop()

    try:
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]

        x_min = floor(min(xs) / tile_w) * tile_w
        x_max = ceil(max(xs) / tile_w) * tile_w
        y_min = floor(min(ys) / tile_h) * tile_h
        y_max = ceil(max(ys) / tile_h) * tile_h

        n_cols = (x_max - x_min) // tile_w
        n_rows = (y_max - y_min) // tile_h

        grid_cells = []
        for i in range(n_cols):
            for j in range(n_rows):
                x0 = x_min + i * tile_w
                y0 = y_min + j * tile_h
                grid_cells.append(((x0, y0), (i, j)))

        poly = ShapelyPolygon(vertices)
        if not poly.is_valid:
            st.error("Invalid polygon geometry")
            st.stop()

        classified_tiles = []
        for (x0, y0), (i, j) in grid_cells:
            t = box(x0, y0, x0 + tile_w, y0 + tile_h)
            if poly.covers(t):
                status = "fully_inside"
            elif poly.intersects(t):
                status = "partially_inside"
            else:
                status = "outside"
            classified_tiles.append(((i, j), status))

        # --- Plot ---
        color_map = {"fully_inside": "green", "partially_inside": "orange", "outside": "none"}
        fig, ax = plt.subplots(figsize=(10, 10))
        polygon_patch = MplPolygon(vertices, closed=True, fill=True, edgecolor='black',
                                   facecolor='lightgray', linewidth=2, alpha=0.5)
        ax.add_patch(polygon_patch)

        for ((x0, y0), (i, j)), status in zip(grid_cells, [s for (_, s) in classified_tiles]):
            tile_color = color_map[status]
            tile = Rectangle((x0, y0), tile_w, tile_h,
                             edgecolor='blue' if status != "outside" else 'lightgray',
                             facecolor=tile_color,
                             linewidth=0.8,
                             alpha=0.6 if status != "outside" else 0.1)
            ax.add_patch(tile)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect('equal')
        ax.set_title("Tile Classification")
        ax.grid(True, which='both', color='gray', linewidth=0.25, linestyle='--')
        st.pyplot(fig)

        # --- Count tiles ---
        tile_area = tile_w * tile_h
        full_tile_count = 0
        partial_rollup_count = 0
        partial_fraction_pool = 0.0

        for ((x0, y0), (i, j)), status in zip(grid_cells, [s for (_, s) in classified_tiles]):
            t = box(x0, y0, x0 + tile_w, y0 + tile_h)
            if status == "fully_inside":
                full_tile_count += 1
            elif status == "partially_inside":
                overlap_area = poly.intersection(t).area
                fraction = overlap_area / tile_area
                if fraction >= 0.55:
                    full_tile_count += 1
                elif fraction:
                    partial_fraction_pool += fraction
                    if partial_fraction_pool + fraction >= 1:
                        partial_rollup_count += 1
                        partial_fraction_pool = 0

        total_tile_count = full_tile_count + partial_rollup_count + ceil(partial_fraction_pool)

        st.subheader("Results")
        st.write(f"✅ Full tiles: {full_tile_count}")
        st.write(f"🟧 Partial tiles converted to full: {partial_rollup_count}")
        st.write(f"🧮 Remaining fractional pool: {partial_fraction_pool:.2f}")
        st.success(f"🔢 Total tiles required: {total_tile_count}")

    except Exception as e:
        st.error(f"Error: {str(e)}")
