import matplotlib
matplotlib.use('Agg')  # Set backend to non-GUI mode
import matplotlib.pyplot as plt
from skyfield.api import load, wgs84
import numpy as np
import os

def generate_trajectory(satellite_name):
    # Load TLE data
    satellites = load.tle("https://www.celestrak.com/NORAD/elements/tle-new.txt")
    if satellite_name not in satellites:
        return None

    # Get the satellite object
    satellite = satellites[satellite_name]

    # Generate trajectory data
    ts = load.timescale()
    t = ts.now()
    
    # Generate timestamps for the next 100 days
    days = np.linspace(0, 100, 100)  # 1000 points over 100 days
    times = ts.utc(t.utc.year, t.utc.month, t.utc.day, t.utc.hour, t.utc.minute, t.utc.second + days * 86400)  # Convert days to seconds

    # Compute positions
    geocentric = satellite.at(times)
    subpoint = wgs84.subpoint(geocentric)
    
    # Extract X, Y, Z coordinates
    x, y, z = geocentric.position.km

    # Plot the trajectory
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(x, y, z, label=f"Trajectory of {satellite_name}")
    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.set_zlabel("Z (km)")
    ax.set_title(f"100-Day Trajectory of {satellite_name}")
    ax.legend()

    # Save the plot to a file
    static_dir = os.path.join("static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    image_path = os.path.join(static_dir, f"{satellite_name}_trajectory.png")
    plt.savefig(image_path)
    plt.close(fig)

    return image_path
