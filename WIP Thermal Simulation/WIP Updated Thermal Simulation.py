import pygame
import numpy as np
import pandas as pd
import time

# Initialize Pygame
pygame.init()

#import data from google drive
from google.colab import drive
drive.mount('/content/drive')
battery_data = pd.read_csv('/content/drive/MyDrive/BatteryProjectData/MyCleanedData/all_data_fixed.csv')

# Original Battery dimensions
original_radius = 18  # in mm
original_height = 65  # in mm
original_circumference = int(2 * np.pi * original_radius)

# Scale down the grid dimensions to 75%
scale_factor = 0.75
grid_width, grid_height = int(original_circumference * scale_factor), int(original_height * scale_factor)
cell_size = 5  # Size of each cell in pixels, adjust as needed

# Calculate window size to be larger than the grid
window_width = original_circumference * cell_size
window_height = original_height * cell_size
window = pygame.display.set_mode((window_width, window_height))

# Initialize simulation parameters
initial_temperature = 24  # Starting temperature, in degrees Celsius
current_temperature = initial_temperature

# Assuming actual_temperature_data is a list of actual temperature readings
actual_temperature_data = battery_data['Temperature_measured'].tolist()

# Determine min and max temperature for color mapping
min_temp = min(actual_temperature_data)
max_temp = max(actual_temperature_data)

# Function to map temperature to color
def temperature_to_color(temp):
    # Map the temperature value to a color
    # For simplicity, let's assume temp is a value between 0 (cool) and 1 (hot)
    blue = max(0, int(255 * (1 - temp)))
    red = max(0, int(255 * temp))
    return (red, 0, blue)

# Initialize a 2D grid for temperature distribution
temperature_grid = np.zeros((grid_width, grid_height))

# Function to update the temperature grid
def update_temperature_grid(grid, current_temperature, previous_temperature):
    # Determine whether we are in the heating or cooling phase
    is_heating = current_temperature > previous_temperature

    # Heating or Cooling Logic
    if is_heating:
        # Logic for spreading heat
        # For simplicity, increasing temperature in the center
        center_x, center_y = grid.shape[0] // 2, grid.shape[1] // 2
        radius = 5  # Radius of the heating area
        for x in range(center_x - radius, center_x + radius):
            for y in range(center_y - radius, center_y + radius):
                grid[x % grid.shape[0], y % grid.shape[1]] = min(grid[x, y] + 0.01, 1)  # Max at 1
    else:
        # Logic for cooling
        # Gradually decrease the temperature from the edges inward
        for x in range(grid.shape[0]):
            for y in range(grid.shape[1]):
                distance_to_edge = min(x, grid.shape[0] - x, y, grid.shape[1] - y)
                grid[x, y] = max(grid[x, y] - 0.01, 0)  # Min at 0

    return grid

# Function for drawing text on the simulation
def draw_text(surface, text, position, font_size=24, color=(255, 255, 255)):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)

# Main simulation loop
time_data = battery_data['Δt'].tolist()
current_temp = battery_data['Temperature_measured'].tolist()
previous_temp = initial_temperature
current_time_index = 0
running = True
scaling_factor = 1

while running:
    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    # Get the time step from the data
    time_step = time_data[current_time_index] / scaling_factor

    # Get the current temperature from the data
    current_temp_now = current_temp[current_time_index]

    # If enough time has passed for the next time step
    if elapsed_time >= time_step:
        # Reset the start time for the next time step
        start_time = time.time()

    # Update the temperature grid
    temperature_grid = update_temperature_grid(temperature_grid, current_temp_now, previous_temp)

    # Draw the grid
    for x in range(grid_width):
        for y in range(grid_height):
            temp = temperature_grid[x, y]
            color = temperature_to_color(temp)
            print(color)
            pygame.draw.rect(window, color, (x * cell_size, y * cell_size, cell_size, cell_size))

    # Display current time and temperature
    temperature_info = f"Time: {time_step:.2f}, Temperature: {current_temp_now}"
    previous_temp = current_temp_now

    # Calculate position for the text (centered horizontally, at the bottom)
    text_x = window_width // 2
    text_y = window_height - 30  # 30 pixels from the bottom, adjust as needed
    draw_text(window, temperature_info, (text_x, text_y))

    # Update the display
    pygame.display.flip()

    # Increment the time index and loop termination condition
    current_time_index += 1
    if current_time_index >= len(battery_data['Δt'].tolist()):
        running = False  # End the simulation if we've gone through all data

    # Pygame event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                scaling_factor *= 1.1  # Increase speed
            elif event.key == pygame.K_DOWN:
                scaling_factor /= 1.1  # Decrease speed
                scaling_factor = max(scaling_factor, 0.1)  # Prevent scaling factor from going below 0.1
            elif event.key == pygame.K_p:  # Press 'P' to pause/unpause
                paused = not paused
            elif event.key == pygame.K_s:  # Press 'S' to take a screenshot
                pygame.image.save(window, f'screenshot_{time.time()}.png')

# Shutdown Pygame
pygame.quit()
