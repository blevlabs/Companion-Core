import tkinter as tk
import sys
import random

random_user_id = random.randint(1, 6)
print("ASSIGNED USER ID: " + str(random_user_id))
sys.path.insert(0, '/dynamic-system/core')
from aci import ACI

aci_instance = ACI()


def on_submit():
    message = user_input.get()
    if message == "quit":
        root.destroy()
    try:
        assert message != "", "You must enter a message."
    except AssertionError as e:
        print(e)
        return
    message = f"Speaker {random_user_id}: " + message
    message = message.strip()
    name = name_entry.get()
    observer_data = {"names": [name]}
    response = aci_instance.prompt_generation(message, observer_data)
    print(response["timestamps"])
    chat_log.configure(state='normal')
    chat_log.insert(tk.END, name + ": " + message + "\n")
    chat_log.insert(tk.END, "Companion Core: " + response["companionResponse"] + "\n")
    chat_log.configure(state='disabled')
    user_input.delete(0, tk.END)
    aci_instance.generate_speech(response["companionResponse"])
    aci_instance.run_speech()


root = tk.Tk()
root.title("Chat Interface")

name_label = tk.Label(root, text="What is your name? ")
name_label.pack()

name_entry = tk.Entry(root)
name_entry.pack()

chat_log = tk.Text(root, state='disabled')
chat_log.pack()

user_input = tk.Entry(root)
user_input.pack()

submit_button = tk.Button(root, text="Submit", command=on_submit)
submit_button.pack()

root.mainloop()
