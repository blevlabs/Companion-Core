import sys
import tkinter as tk

sys.path.insert(0, '/home/blabs/Companion-Core/dynamic-system/core')
from aci import ACI

aci = ACI()

# Create the main window
window = tk.Tk()
window.title("Input Classifier")
window.geometry('500x500')

# Create a frame to hold the widgets
frame = tk.Frame(window)
frame.pack()

# Create a label for the text box
label = tk.Label(frame, text="Enter text to classify:")
label.pack()

# Create a text box
text_box = tk.Text(frame, height=10, width=50)
text_box.pack()


# Create a button to classify the text and display the result below the button
def classify():
    text = text_box.get("1.0", "end-1c")
    print("Processing: " + text)
    text = "Speaker 1: " + text
    result = aci.flan_classify(text)
    # Create a label to display the result
    result_label = tk.Label(frame, text=result, font=("Helvetica", 14))
    result_label.pack()


# Create a classify button
classify_button = tk.Button(frame, text="Classify", command=classify)
classify_button.pack()


# Create a clear button
def clear():
    text_box.delete("1.0", tk.END)
    for widget in frame.winfo_children():
        if widget.winfo_class() == 'Label':
            widget.destroy()


clear_button = tk.Button(frame, text="Clear", command=clear)
clear_button.pack()

# Start the GUI
window.mainloop()
