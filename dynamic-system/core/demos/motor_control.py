import sys

sys.path.insert(0, '/dynamic-system/core')
import tkinter as tk
import requests
# Create the main window
window = tk.Tk()
window.title("Slider Application")

# Create a dictionary to store the slider values
ris_server = "http://127.0.0.1:5075"
slider_values = {"s1_base_angle": 75, "s2_base_angle": 60, "s3_base_angle": 90, "s4_base_angle": 90, "format": "servos"}


# Create a function to update the dictionary with the new slider values
def update_slider_values(slider_id, new_value):
    slider_values[slider_id] = new_value
    print(slider_values)
    requests.post(ris_server + "/ris", json=slider_values)


# Create four sliders, one for each value in the dictionary
s1_base_angle_slider = tk.Scale(window, from_=0, to=180, orient=tk.HORIZONTAL,
                                command=lambda value: update_slider_values("s1_base_angle", int(value)))
s1_base_angle_slider.set(
    slider_values["s1_base_angle"])  # Set the default value of the slider to the value in the dictionary
s1_base_angle_slider.pack()

s2_base_angle_slider = tk.Scale(window, from_=0, to=180, orient=tk.HORIZONTAL,
                                command=lambda value: update_slider_values("s2_base_angle", int(value)))
s2_base_angle_slider.set(
    slider_values["s2_base_angle"])  # Set the default value of the slider to the value in the dictionary
s2_base_angle_slider.pack()

s3_base_angle_slider = tk.Scale(window, from_=0, to=180, orient=tk.HORIZONTAL,
                                command=lambda value: update_slider_values("s3_base_angle", int(value)))
s3_base_angle_slider.set(
    slider_values["s3_base_angle"])  # Set the default value of the slider to the value in the dictionary
s3_base_angle_slider.pack()

s4_base_angle_slider = tk.Scale(window, from_=0, to=180, orient=tk.HORIZONTAL,
                                command=lambda value: update_slider_values("s4_base_angle", int(value)))
s4_base_angle_slider.set(
    slider_values["s4_base_angle"])  # Set the default value of the slider to the value in the dictionary
s4_base_angle_slider.pack()

# Run the main loop
window.mainloop()
