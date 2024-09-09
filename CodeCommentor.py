import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk  # Import ttk for the progress bar
import google.generativeai as genai

# Configure the AI model
genai.configure(api_key="YOUR_API_KEY")

# Define the model generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the model instance
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Function to read the code from a local file
def read_code_file(filename):
    with open(filename, 'r') as file:
        code = file.read()
    return code

# Function to write the commented code to a file
def write_commented_code(filepath, content):
    with open(filepath, 'w') as file:
        file.write(content)

# Function to clean the output by removing unwanted Markdown formatting
def clean_output(output, language):
    if language == "Python":
        return output.replace("```python", "").replace("```", "").strip()
    elif language == "Java":
        # Assuming Java might use similar markdown, adjust if necessary
        return output.replace("```java", "").replace("```", "").strip()
    elif language == "C/C++":
        # Assuming C/C++ might use similar markdown, adjust if necessary
        return output.replace("```c", "").replace("```cpp", "").replace("```", "").strip()
    else:
        return output.strip()

# Function to handle the AI request and file operations
def comment_code():
    replace_original = action_choice.get() == "Replace"
    try:
        selected_files = [file for file, var in file_vars.items() if var['var'].get()]
        if not selected_files:
            messagebox.showwarning("No files selected", "Please select at least one file to proceed.")
            return

        # Reset progress bar
        progress_bar["maximum"] = len(selected_files)
        progress_bar["value"] = 0
        root.update_idletasks()  # Ensure the progress bar is updated immediately

        for file_path in selected_files:
            # Read the code from the selected file
            code_to_comment = read_code_file(file_path)

            # Determine language based on file extension
            file_extension = os.path.splitext(file_path)[1]
            if file_extension == '.py':
                language = "Python"
            elif file_extension == '.java':
                language = "Java"
            elif file_extension in ['.c', '.cpp']:
                language = "C/C++"
            else:
                language = "Unknown"

            # Create the prompt based on the language
            prompt = f"Add comments to the following {language} code. Please provide only the commented code, without any additional text or formatting:\n" + code_to_comment

            # Start a chat session with the AI model
            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [prompt],
                    },
                ]
            )

            # Send the code to the AI model and get the response
            response = chat_session.send_message(code_to_comment)

            # Extract the AI-generated commented code from the response
            commented_code = clean_output(response.text, language)

            # Get the output filename from the entry fields
            output_filename = output_name_vars[file_path].get()
            output_filepath = os.path.join(output_dir_path.get(), output_filename)

            if replace_original:
                # Replace the original file with commented code
                write_commented_code(file_path, commented_code)
                messagebox.showinfo("Success", f"Original file {file_path} has been replaced with the commented code.")
            else:
                # Write to the new file
                write_commented_code(output_filepath, commented_code)
                messagebox.showinfo("Success", f"Commented code has been saved to {output_filepath}")

            # Update the progress bar after each file is processed
            progress_bar["value"] += 1
            root.update_idletasks()  # Update the GUI to reflect the progress

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function to open directory dialog and list all supported files in the selected folder
def browse_folder():
    directory = filedialog.askdirectory(title="Select Folder Containing Code Files")
    if directory:
        input_folder_path.set(directory)
        list_files(directory)

# Function to list all supported files in the selected folder with checkboxes
def list_files(folder):
    # Define the extensions you want to support
    supported_extensions = ('.py', '.java', '.c', '.cpp')

    for widget in frame_files_content.winfo_children():
        widget.destroy()

    files = [f for f in os.listdir(folder) if f.endswith(supported_extensions)]
    if not files:
        messagebox.showinfo("No Files", "No supported files found in the selected folder.")
        return

    for file in files:
        file_path = os.path.join(folder, file)
        var = tk.BooleanVar()

        file_vars[file_path] = {'var': var}

        cb = tk.Checkbutton(frame_files_content, text=file, variable=var, command=update_output_settings)
        cb.pack(anchor="w")

# Function to open directory dialog for selecting the output directory
def browse_directory():
    directory = filedialog.askdirectory(title="Select Output Directory")
    output_dir_path.set(directory)

# Function to update the output settings in Step 2 dynamically
def update_output_settings():
    if action_choice.get() == "Replace":
        return  # Do nothing if "Replace Existing Files" is selected

    for widget in frame_output_content.winfo_children():
        widget.destroy()

    selected_files = [file for file, var in file_vars.items() if var['var'].get()]

    for file_path in selected_files:
        tk.Label(frame_output_content, text=f"Output name for {os.path.basename(file_path)}:").pack(anchor="w")
        output_name_var = tk.StringVar(value=os.path.basename(file_path))  # Default to original file name
        output_name_vars[file_path] = output_name_var
        tk.Entry(frame_output_content, textvariable=output_name_var).pack(anchor="w")

# Function to handle the radio button selection
def update_action_choice():
    if action_choice.get() == "New":
        frame_output_content.pack(fill="both", expand=True)
        button_comment.config(text="Comment to New File")
        update_output_settings()  # Update settings if "Save to New Files" is selected
    else:
        frame_output_content.pack_forget()  # Hide Step 2 elements
        button_comment.config(text="Replace Original File")

# Initialize the Tkinter window
root = tk.Tk()
root.title("Code Commenter")

# Variables to hold the selected folder path, file variables, output directory, and action choice
input_folder_path = tk.StringVar()
output_dir_path = tk.StringVar()
file_vars = {}
output_name_vars = {}
action_choice = tk.StringVar(value="New")

# Creating frames for better layout organization
frame_files = tk.LabelFrame(root, text="Step 1: Select Folder and Files", padx=10, pady=10)
frame_files.pack(padx=10, pady=10, fill="x")

frame_files_content = tk.Frame(frame_files)
frame_files_content.pack(padx=5, pady=5, fill="both", expand=True)

frame_output = tk.LabelFrame(root, text="Step 2: Output Settings", padx=10, pady=10)
frame_output.pack(padx=10, pady=10, fill="x")

frame_output_content = tk.Frame(frame_output)
frame_output_content.pack(padx=5, pady=5, fill="both", expand=True)

frame_actions = tk.LabelFrame(root, text="Step 3: Choose an Action", padx=10, pady=10)
frame_actions.pack(padx=10, pady=10, fill="x")

# Widgets for folder selection
tk.Label(frame_files, text="Select a Folder:").pack(anchor="w")
tk.Entry(frame_files, textvariable=input_folder_path, width=60).pack(pady=5)
tk.Button(frame_files, text="Browse Folder", command=browse_folder).pack()

# Widgets for output settings
tk.Label(frame_output, text="Select Output Directory:").pack(anchor="w")
tk.Entry(frame_output, textvariable=output_dir_path, width=50).pack(pady=5)
tk.Button(frame_output, text="Browse Directory", command=browse_directory).pack()

# Radio buttons for action choice
tk.Radiobutton(frame_actions, text="Save to New Files", variable=action_choice, value="New", command=update_action_choice).pack(anchor="w")
tk.Radiobutton(frame_actions, text="Replace Existing Files", variable=action_choice, value="Replace", command=update_action_choice).pack(anchor="w")

# Single button for commenting action
button_comment = tk.Button(frame_actions, text="Comment to New File", command=comment_code, width=30)
button_comment.pack(pady=5)

# Progress bar widget
progress_bar = ttk.Progressbar(frame_actions, orient="horizontal", mode="determinate")
progress_bar.pack(fill="x", pady=5)

# Start the Tkinter event loop
root.mainloop()
