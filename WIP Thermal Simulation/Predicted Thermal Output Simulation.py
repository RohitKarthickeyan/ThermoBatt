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

# from the battery dataset
def simulate_temperature_change(time_data, heat_generated, heat_flux, heat_loss_rate, convective_heat_transfer, initial_temperature):
    specific_heat_capacity = 900  # J/(kg*K) for lithium-ion battery
    battery_mass = 0.045  # kg for a typical 18650 battery

    # Initialize variables
    temperature = initial_temperature
    temperatures = [initial_temperature]  # List to store temperature at each time step

    # Iterate over each time step
    for i in range(1, len(time_data)):
        # Calculate time interval
        delta_t = time_data[i] - time_data[i-1]

        # Heat accumulation
        heat_in = heat_generated[i] * delta_t  # Assuming heat_generated is power in watts

        # Heat dissipation
        heat_out = (heat_flux[i] + heat_loss_rate[i] + convective_heat_transfer[i]) * delta_t

        # Net heat change
        net_heat = heat_in - heat_out

        # Temperature change
        delta_temp = net_heat / (specific_heat_capacity * battery_mass)
        temperature += delta_temp

        # Append new temperature to the list
        temperatures.append(temperature)

    return temperatures

# This function would be called with your actual data lists and an initial temperature:
temperatures_over_time = simulate_temperature_change(
    time_data=battery_data['Δt'].tolist(),
    heat_generated=battery_data['Heat_generated'].tolist(),
    heat_flux=battery_data['heat_flux'].tolist(),
    heat_loss_rate=battery_data['heat_loss_rate'].tolist(),
    convective_heat_transfer=battery_data['convective_heat_transfer'].tolist(),
    initial_temperature=initial_temperature
)

# Determine min and max temperature for color mapping
min_temp = np.percentile(temperatures_over_time, 5)
max_temp = np.percentile(temperatures_over_time, 95)

# Function to map temperature to color
def temperature_to_color(temp_change, min_temp, max_temp):
    # Adjust the range to increase color sensitivity
    range_center = (min_temp + max_temp) / 2
    adjusted_range = max(max_temp - range_center, range_center - min_temp)

    # Ensure adjusted_range is not zero to avoid division by zero
    if adjusted_range == 0:
        adjusted_range = 1  # Prevent division by zero

    # Normalize temperature change between 0 and 1 with increased sensitivity
    normalized_temp = (temp_change - range_center) / adjusted_range
    normalized_temp = min(max(normalized_temp, -1), 1)  # Clamp between -1 and 1

    # Handle NaN case for normalized_temp
    if np.isnan(normalized_temp):
        normalized_temp = 0  # Default value or choose an appropriate action

    # Convert to color (blue to red)
    blue = max(0, min(255, int(255 * (1 - normalized_temp))))
    red = max(0, min(255, int(255 * (1 + normalized_temp))))

    return (red, 0, blue)

# Initialize a 2D grid for temperature distribution
temperature_grid = np.zeros((grid_width, grid_height))

# Function to update the temperature grid
def update_temperature_grid(grid, current_temperature, previous_temperature):
    # Calculate the normalized temperature change
    normalized_temp_change = (current_temperature - previous_temperature) / max(abs(previous_temperature), 1e-5)
    normalized_temp_change = max(min(normalized_temp_change, 1), -1)  # Clamp between -1 and 1

    center_x, center_y = grid.shape[0] // 2, grid.shape[1] // 2

    # Determine heating or cooling based on the temperature change
    is_heating = current_temperature > previous_temperature

    if is_heating:
        # Heating: Spread heat from the center
        for x in range(grid.shape[0]):
            for y in range(grid.shape[1]):
                # Calculate distance from the center
                distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)

                # The closer to the center, the more the temperature increases
                grid[x, y] = min(grid[x, y] + normalized_temp_change * max(0, 1 - distance / center_x), 1)
    else:
        # Cooling: Decrease temperature from the edges inward
        for x in range(grid.shape[0]):
            for y in range(grid.shape[1]):
                # Calculate distance from the nearest edge
                distance_to_edge = min(x, grid.shape[0] - x - 1, y, grid.shape[1] - y - 1)

                # The closer to the edge, the more the temperature decreases
                grid[x, y] = max(grid[x, y] - normalized_temp_change * max(0, 1 - distance_to_edge / center_x), 0)

    return grid

# Function for drawing text on the simulation
def draw_text(surface, text, position, font_size=24, color=(255, 255, 255)):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)

# Start the simulation at the first data point
current_time_index = 0
previous_time = 0

print("Min temp:", min_temp, "Max temp:", max_temp)

# Main simulation loop
change_time = battery_data['Δt'].tolist()
previous_temperature = initial_temperature
scaling_factor = 5
start_time = time.time()
running = True
current_time_index = 0

while running:
    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    # Get the time step from the data
    time_step = change_time[current_time_index] / scaling_factor

    # If enough time has passed for the next time step
    if elapsed_time >= time_step:
        # Reset the start time for the next time step
        start_time = time.time()

        # Calculate the new temperature
        current_temperature = temperatures_over_time[current_time_index]

        print("Current temperature:", current_temperature)

        # Update the temperature grid
        temperature_grid = update_temperature_grid(temperature_grid, current_temperature, previous_temperature)

        # Draw the grid
        for x in range(grid_width):
            for y in range(grid_height):
                temp = temperature_grid[x, y]
                color = temperature_to_color(temp, min_temp, max_temp)
                print(color)
                pygame.draw.rect(window, color, (x * cell_size, y * cell_size, cell_size, cell_size))

        previous_temperature = current_temperature

        # Display current time and temperature
        temperature_info = f"Time: {time_step:.2f}, Temperature: {current_temperature}"

        # Calculate position for the text (centered horizontally, at the bottom)
        text_x = window_width // 2
        text_y = window_height - 30  # 30 pixels from the bottom, adjust as needed
        draw_text(window, temperature_info, (text_x, text_y))

        # Update the display
        pygame.display.flip()

        # Increment the time index
        current_time_index += 1
        if current_time_index >= len(battery_data['Δt']):
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
