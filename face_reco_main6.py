import sys
import os
import cv2
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import face_recognition
import csv
from datetime import datetime
from tkinter.simpledialog import askstring

# When running as a PyInstaller onefile executable, PyInstaller extracts
# bundled files to a temporary folder and sets sys._MEIPASS to that path.
# Add the extraction folder to sys.path so package-relative data lookups
# (face_recognition_models/models/...) can be resolved at runtime.
if getattr(sys, "frozen", False):
	meipass = getattr(sys, "_MEIPASS", None)
	if meipass and meipass not in sys.path:
		sys.path.insert(0, meipass)


# Ensure a default admin account exists on first run so installed users can log in.
def ensure_default_admin():
	try:
		save_dir = r"D:\code\Upwork Project\FRAS\Data\Admin_Data"
		os.makedirs(save_dir, exist_ok=True)
		csv_path = os.path.join(save_dir, "admin_signup_data.csv")
		if not os.path.exists(csv_path):
			with open(csv_path, "w", newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow(["First Name", "Last Name", "UserID", "Password", "Organization Name"])
				# default credentials (please change after first login)
				writer.writerow(["Default", "Admin", "admin", "admin123", "Organization"])
			print(f"Created default admin at: {csv_path} (UserID=admin Password=admin123)")
	except Exception as e:
		print(f"Could not create default admin data: {e}")

# Run the default admin check at module import time (ensures installer users can login)
ensure_default_admin()



def save_attendance_image(frame, student_name):

	save_dir = r"D:\code\Upwork Project\FRAS\Atten_Img"
	os.makedirs(save_dir, exist_ok=True)
	timestamp = time.strftime('%Y%m%d_%H%M%S')
	filename = f"{student_name}_{timestamp}.png"
	filepath = os.path.join(save_dir, filename)
	cv2.imwrite(filepath, frame)
	print(f"Attendance image saved: {filepath}")
	messagebox.showinfo("Saved", f"Attendance image saved:\n{filepath}")
	return filename, timestamp

def show_student_checklist(root):

	checklist_win = tk.Toplevel(root)
	checklist_win.title("Student Checklist")
	checklist_win.geometry("800x680")
	label = tk.Label(checklist_win, text="Student Checklist", font=("Arial", 16, "bold"))
	label.pack(pady=10)
	img_dir = r"D:\code\Upwork Project\FRAS\Atten_Img"
	if os.path.exists(img_dir):
		students = [f for f in os.listdir(img_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
		if students:
			for s in students:
				tk.Label(checklist_win, text=s, font=("Arial", 12)).pack(anchor="w", padx=20)
		else:
			tk.Label(checklist_win, text="No student images found.", font=("Arial", 12)).pack()
	else:
		tk.Label(checklist_win, text="No student images found.", font=("Arial", 12)).pack()



def open_camera_window():

	face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
	cap = cv2.VideoCapture(0)
	saved = False
	known_encodings = []

	# Load existing encodings to prevent duplicates
	img_dir = r"D:\code\Upwork Project\FRAS\Atten_Img"
	if os.path.exists(img_dir):
		for fname in os.listdir(img_dir):
			if fname.lower().endswith((".png", ".jpg", ".jpeg")):
				img_path = os.path.join(img_dir, fname)
				img = face_recognition.load_image_file(img_path)
				encodings = face_recognition.face_encodings(img)
				if encodings:
					known_encodings.append(encodings[0])

	data_dir = r"D:\code\Upwork Project\FRAS\data"
	os.makedirs(data_dir, exist_ok=True)
	csv_path = os.path.join(data_dir, "attendance.csv")
	window_name = 'Register Attendance'
	cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
	cv2.resizeWindow(window_name, 900, 600)
	while True:
		ret, frame = cap.read()
		if not ret:
			break
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(50, 50))
		for (x, y, w, h) in faces:
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
			cv2.putText(frame, 'Face Found', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
		cv2.putText(frame, 'Press SPACE to save, Q to quit', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
		cv2.imshow(window_name, frame)
		key = cv2.waitKey(1)
		if key & 0xFF == ord('q'):
			break
		elif key == 32:  # SPACE
			# Only save if a face is found
			if len(faces) == 0:
				messagebox.showwarning("No Face", "No face detected. Try again!")
				continue
			# Get the largest face
			(x, y, w, h) = max(faces, key=lambda rect: rect[2]*rect[3])
			face_img = frame[y:y+h, x:x+w]
			# Check for duplicate face
			rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
			encodings = face_recognition.face_encodings(rgb_face)
			if encodings:
				encoding = encodings[0]
				matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
				if True in matches:
					messagebox.showinfo("Duplicate", "This face is already registered.")
					continue
				# Prompt for student name
				student_name = askstring("Student Name", "Enter student name:")
				if not student_name:
					messagebox.showwarning("Input Error", "Student name is required!")
					continue
				# Save image and encoding
				filename, timestamp = save_attendance_image(face_img, student_name)
				known_encodings.append(encoding)
				# Save to CSV
				with open(csv_path, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					if f.tell() == 0:
						writer.writerow(["student_name", "filename", "timestamp"])
					writer.writerow([student_name, filename, timestamp])
				saved = True
			else:
				messagebox.showwarning("Encoding Error", "Could not encode face. Try again!")
	cap.release()
	cv2.destroyAllWindows()
	if not saved:
		print("No image saved.")



def open_web_live():

	# Load all known face encodings from Atten_Img
	known_encodings = []
	known_names = []
	student_names = []
	images_dir = r"D:\code\Upwork Project\FRAS\Atten_Img"
	if os.path.exists(images_dir):
		for fname in os.listdir(images_dir):
			if fname.lower().endswith((".png", ".jpg", ".jpeg")):
				img_path = os.path.join(images_dir, fname)
				img = face_recognition.load_image_file(img_path)
				encodings = face_recognition.face_encodings(img)
				if encodings:
					known_encodings.append(encodings[0])
					# Extract student name from filename (before first _)
					student_name = fname.split('_')[0]
					known_names.append(fname)
					student_names.append(student_name)
	else:
		messagebox.showinfo("No Images", "No attendance images found.")
		return

	# Prepare daily attendance folder and file
	today = datetime.now().strftime('%Y-%m-%d')
	daily_dir = os.path.join(r"D:\code\Upwork Project\FRAS\Data\Student_daily_basis_atten", today)
	os.makedirs(daily_dir, exist_ok=True)
	csv_path = os.path.join(daily_dir, "attendance.csv")
	present_students = set()

	cap = cv2.VideoCapture(0)
	window_name = 'CAP LIVE'
	cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
	cv2.resizeWindow(window_name, 900, 600)
	while True:
		ret, frame = cap.read()
		if not ret:
			break
		rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		face_locations = face_recognition.face_locations(rgb_frame)
		face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
		for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
			matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
			name = None
			if True in matches:
				match_index = matches.index(True)
				name = student_names[match_index]
				present_students.add(name)
				cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 3)
				cv2.putText(frame, 'Student Present in College', (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
			else:
				cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
				cv2.putText(frame, 'Unknown', (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
		cv2.putText(frame, 'Press Q to quit', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
		cv2.imshow(window_name, frame)
		key = cv2.waitKey(1)
		if key & 0xFF == ord('q'):
			break
	cap.release()
	cv2.destroyAllWindows()

	# Save daily attendance CSV

	all_students = set(student_names)
	absents = all_students - present_students
	with open(csv_path, 'w', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerow(["student_name", "status", "date"])
		for name in sorted(all_students):
			status = 'P' if name in present_students else 'A'
			writer.writerow([name, status, today])




def main():
	root = tk.Tk()
	root.title("FRAS")
	root.geometry("800x680")

	# --- Frame stacking system ---
	container = tk.Frame(root)
	container.pack(fill=tk.BOTH, expand=True)

	pages = {}

	def show_page(page_name):
		for name, frame in pages.items():
			frame.pack_forget()
		pages[page_name].pack(fill=tk.BOTH, expand=True)


	# --- Page 1: Register Attendance ---
	page1 = tk.Frame(container)
	pages['attendance'] = page1

	# --- Beautiful Heading with Background ---
	heading_frame = tk.Frame(page1, bg="#1976D2", height=60)
	heading_frame.pack(fill=tk.X, pady=(0, 8))
	heading_label = tk.Label(
		heading_frame,
		text="Let's Go Register Your Face",
		font=("Segoe UI", 22, "bold"),
		fg="white",
		bg="#A5971D",
		pady=10
	)
	heading_label.pack(fill=tk.BOTH, expand=True)

	# Image display for Register Attendance page
	att_img_path = r"D:\code\Upwork Project\FRAS\app_img\A student standing i.png"
	att_img_label = tk.Label(page1)
	att_img_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

	def update_att_img(event=None):
		w = page1.winfo_width()
		h = page1.winfo_height()
		h_img = max(int(h * 0.5), 200)
		w_img = max(w - 40, 200)
		try:
			pil_img = Image.open(att_img_path).convert("RGBA")
			pil_img = pil_img.resize((w_img, h_img), Image.LANCZOS)
			tk_img = ImageTk.PhotoImage(pil_img)
			att_img_label.configure(image=tk_img)
			att_img_label.image = tk_img
		except Exception as e:
			att_img_label.configure(text="Image not found", image="", font=("Arial", 16), fg="red")

	page1.bind('<Configure>', update_att_img)
	page1.after(100, update_att_img)

	# --- Button Style for Register Attendance page ---
	att_btn_style = {
		'font': ("Segoe UI", 14, "bold"),
		'bg': "#24B311",
		'fg': "white",
		'activebackground': "#9AB9A6",
		'activeforeground': "#FFF",
		'width': 22,
		'height': 2,
		'bd': 0,
		'relief': tk.FLAT,
		'cursor': "hand2"
	}

	btns_frame = tk.Frame(page1, bg="#E3F2FD")
	btns_frame.pack(pady=16)
	btn_back = tk.Button(btns_frame, text="Back to Home", command=lambda: show_page('home'), **att_btn_style)
	btn_back.pack(side=tk.LEFT, padx=16)
	btn_camera = tk.Button(btns_frame, text="Open Camera Window", command=open_camera_window, **att_btn_style)
	btn_camera.pack(side=tk.LEFT, padx=16)
	

	# --- Page 2: CAP LIVE ---
	page2 = tk.Frame(container)
	pages['caplive'] = page2

	# Beautiful Heading with Background
	cap_heading_frame = tk.Frame(page2, bg="#388E3C", height=60)
	cap_heading_frame.pack(fill=tk.X, pady=(0, 8))
	cap_heading_label = tk.Label(
		cap_heading_frame,
		text="CAP LIVE (Face Verification)",
		font=("Segoe UI", 22, "bold"),
		fg="white",
		bg="#388E3C",
		pady=10
	)
	cap_heading_label.pack(fill=tk.BOTH, expand=True)

	# Image display for CAP LIVE page
	cap_img_path = r"D:\code\Upwork Project\FRAS\app_img\verify face.webp"
	cap_img_label = tk.Label(page2)
	cap_img_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

	def update_cap_img(event=None):
		w = page2.winfo_width()
		h = page2.winfo_height()
		h_img = max(int(h * 0.5), 200)
		w_img = max(w - 40, 200)
		try:
			pil_img = Image.open(cap_img_path).convert("RGBA")
			pil_img = pil_img.resize((w_img, h_img), Image.LANCZOS)
			tk_img = ImageTk.PhotoImage(pil_img)
			cap_img_label.configure(image=tk_img)
			cap_img_label.image = tk_img
		except Exception as e:
			cap_img_label.configure(text="Image not found", image="", font=("Arial", 16), fg="red")

	page2.bind('<Configure>', update_cap_img)
	page2.after(100, update_cap_img)

	# Button Style for CAP LIVE page
	cap_btn_style = {
		'font': ("Segoe UI", 14, "bold"),
		'bg': "#388E3C",
		'fg': "white",
		'activebackground': "#2E7D32",
		'activeforeground': "#FFF",
		'width': 22,
		'height': 2,
		'bd': 0,
		'relief': tk.FLAT,
		'cursor': "hand2"
	}

	cap_btns_frame = tk.Frame(page2, bg="#E3F2FD")
	cap_btns_frame.pack(pady=16)
	cap_back = tk.Button(cap_btns_frame, text="Back to Home", command=lambda: show_page('home'), **cap_btn_style)
	cap_back.pack(side=tk.LEFT, padx=16)
	cap_live = tk.Button(cap_btns_frame, text="Start Face Verification", command=open_web_live, **cap_btn_style)
	cap_live.pack(side=tk.LEFT, padx=16)

	# --- Page 3: Student Checklist ---
	page3 = tk.Frame(container)
	pages['checklist'] = page3
	tk.Label(page3, text="Student Checklist", font=("Arial", 18, "bold")).pack(pady=30)
	tk.Button(page3, text="Back to Home", font=("Arial", 12), command=lambda: show_page('home')).pack(pady=10)
	# Show checklist in this frame
	checklist_text = tk.Text(page3, font=("Arial", 12), width=60, height=20)
	checklist_text.pack(pady=10)
	def update_checklist():
		checklist_text.delete(1.0, tk.END)
		img_dir = r"D:\code\Upwork Project\FRAS\Atten_Img"
		if os.path.exists(img_dir):
			students = [f for f in os.listdir(img_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
			if students:
				for s in students:
					checklist_text.insert(tk.END, s + "\n")
			else:
				checklist_text.insert(tk.END, "No student images found.\n")
		else:
			checklist_text.insert(tk.END, "No student images found.\n")

	# --- Home Page ---
	home = tk.Frame(container)
	pages['home'] = home
	img_path = r"D:\code\Upwork Project\FRAS\app_img\main_windows_img.webp"
	img_label = tk.Label(home)
	img_label.pack(fill=tk.BOTH, expand=True)

	def update_image(event=None):
		w = root.winfo_width()
		h = root.winfo_height()
		h_img = max(h - 180, 100)
		w_img = w
		pil_img = Image.open(img_path).convert("RGBA")
		pil_img = pil_img.resize((w_img, h_img), Image.LANCZOS)
		tk_img = ImageTk.PhotoImage(pil_img)
		img_label.configure(image=tk_img)
		img_label.image = tk_img

	root.bind('<Configure>', update_image)
	update_image()




	# --- Dynamic Heading ---
	heading_texts = ["FRAS", "Face Recognition Attendance System", "Gorilla Gang Technology"]
	heading_label = tk.Label(home, text="", font=("Segoe UI", 28, "bold"), fg="#0D47A1", bg="#E3F2FD")
	heading_label.place(relx=0.5, rely=0.08, anchor=tk.CENTER)

	def type_heading(idx=0, char_idx=0, deleting=False):
		text = heading_texts[idx]
		current = heading_label.cget("text")
		if not deleting:
			if char_idx <= len(text):
				heading_label.config(text=text[:char_idx])
				home.after(80, type_heading, idx, char_idx+1, False)
			else:
				# Pause, then start deleting
				home.after(1200, type_heading, idx, len(text), True)
		else:
			if char_idx >= 0:
				heading_label.config(text=text[:char_idx])
				home.after(40, type_heading, idx, char_idx-1, True)
			else:
				# Switch to next text
				next_idx = (idx+1) % len(heading_texts)
				home.after(400, type_heading, next_idx, 0, False)

	type_heading()

	# --- Consistent button style ---
	button_style = {
		'font': ("Segoe UI", 14, "bold"),
		'bg': "#1976D2",
		'fg': "white",
		'activebackground': "#1565C0",
		'activeforeground': "#FFF",
		'width': 30,
		'height': 2,
		'bd': 0,
		'relief': tk.FLAT,
		'cursor': "hand2"
	}

	# --- Help Window Function (must be defined before button uses it) ---
	def show_help():
		help_win = tk.Toplevel(root)
		help_win.title("Help & User Guide - FRAS")
		help_win.geometry("900x800")
		help_win.configure(bg="#181A20")
		help_win.resizable(False, False)

		# Heading
		heading = tk.Label(help_win, text="Help & User Guide", font=("Segoe UI", 28, "bold"), fg="#FFD600", bg="#181A20", pady=24)
		heading.pack()

		# Scrollable Frame for Help Content
		content_frame = tk.Frame(help_win, bg="#181A20")
		content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
		canvas = tk.Canvas(content_frame, bg="#181A20", highlightthickness=0)
		scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
		scrollable_frame = tk.Frame(canvas, bg="#181A20")

		scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(
				scrollregion=canvas.bbox("all")
			)
		)
		canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)
		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		# Help Content (step-by-step, common problems, solutions)
		def add_section(title, steps, color="#FFD600"):
			tk.Label(scrollable_frame, text=title, font=("Segoe UI", 20, "bold"), fg=color, bg="#181A20", pady=10).pack(anchor="w")
			for step in steps:
				tk.Label(scrollable_frame, text="• " + step, font=("Segoe UI", 14), fg="#FFF", bg="#181A20", wraplength=820, justify="left", anchor="w").pack(anchor="w", padx=18, pady=2)

		add_section("Getting Started", [
			"1. Register Attendance: Click 'Register Attendance' to add your face to the system. Follow on-screen instructions to capture your face and enter your name.",
			"2. CAP LIVE: Click 'CAP LIVE' to verify your face for daily attendance. The system will mark you present if your face is recognized.",
			"3. Student Checklist: View all registered students and their attendance images.",
			"4. Admin Login: For admin access, use your UserID and Password. Sign up if you are a new admin.",
			"5. Help: Access this help window anytime for guidance.",
			"6. Exit: Click 'Exit' to close the application safely."
		])

		add_section("Step-by-Step Usage", [
			"1. To register a new student, go to 'Register Attendance', open the camera, and follow prompts.",
			"2. For daily attendance, use 'CAP LIVE' and ensure your face is clearly visible to the camera.",
			"3. Admins can log in to view attendance records, images, and manage data.",
			"4. Use 'Student Checklist' to review all registered students and their images.",
			"5. For admin sign up, click 'Admin Login' > 'Sign Up' and fill all required fields."
		], color="#00E676")

		add_section("Common Problems & Solutions", [
			"• Camera Not Detected: Ensure your webcam is connected and not used by another application.",
			"• Face Not Detected: Make sure your face is well-lit and fully visible to the camera.",
			"• Duplicate Face Warning: The system prevents registering the same face twice. Try with a different person or angle.",
			"• Attendance Not Saved: Check if the data folder exists and you have write permissions.",
			"• Admin Login Failed: Double-check your UserID and Password. Use 'Sign Up' if you are a new admin.",
			"• Images Not Displaying: Ensure the image files exist in the correct folder and are not corrupted.",
			"• Application Not Starting: Make sure all required Python packages are installed (opencv-python, face_recognition, dlib, Pillow, etc.)."
		], color="#FF5252")

		add_section("Tips for Best Results", [
			"• Use a clear, front-facing photo for registration.",
			"• Avoid hats, sunglasses, or masks during face capture.",
			"• Register attendance in a well-lit environment.",
			"• Keep your data folders organized and do not delete important CSV/image files.",
			"• For any technical issues, contact your administrator or refer to the user manual."
		], color="#40C4FF")

		# Close Button
		close_btn = tk.Button(
			help_win, text="Close", font=("Segoe UI", 16, "bold"), bg="#FFD600", fg="#181A20",
			activebackground="#FFF176", activeforeground="#111", bd=0, relief=tk.FLAT, cursor="hand2",
			width=16, height=2, command=help_win.destroy
		)
		close_btn.pack(pady=24)

	# Use a frame to stack buttons vertically and center
	btn_frame = tk.Frame(home, bg="#E3F2FD")
	btn_frame.place(relx=0.2, rely=0.49, anchor=tk.CENTER)

	def admin_login():
		login_win = tk.Toplevel(root)
		login_win.title("Admin Login")
		login_win.geometry("400x420")
		login_win.configure(bg="#111111")
		login_win.resizable(False, False)

		# Heading
		heading = tk.Label(login_win, text="Admin Login", font=("Segoe UI", 22, "bold"), fg="#FFD600", bg="#111111", pady=18)
		heading.pack()

		# UserID
		user_label = tk.Label(login_win, text="User ID", font=("Segoe UI", 13, "bold"), fg="#FFF", bg="#111111")
		user_label.pack(pady=(18, 2))
		user_entry = tk.Entry(login_win, font=("Segoe UI", 13), bg="#222", fg="#FFD600", insertbackground="#FFD600", relief=tk.FLAT)
		user_entry.pack(ipady=7, ipadx=5, padx=40, fill=tk.X)

		# Password
		pass_label = tk.Label(login_win, text="Password", font=("Segoe UI", 13, "bold"), fg="#FFF", bg="#111111")
		pass_label.pack(pady=(18, 2))
		pass_entry = tk.Entry(login_win, font=("Segoe UI", 13), bg="#222", fg="#FFD600", insertbackground="#FFD600", relief=tk.FLAT, show="*")
		pass_entry.pack(ipady=7, ipadx=5, padx=40, fill=tk.X)

		# Login Button
		def validate_login():
			user_id = user_entry.get().strip()
			password = pass_entry.get().strip()
			csv_path = r"D:\code\Upwork Project\FRAS\Data\Admin_Data\admin_signup_data.csv"
			if not user_id or not password:
				messagebox.showwarning("Input Error", "Please enter both UserID and Password.", parent=login_win)
				return
			if not os.path.exists(csv_path):
				messagebox.showerror("Error", "No admin data found. Please sign up first.", parent=login_win)
				return
			found = False
			with open(csv_path, "r", encoding="utf-8") as f:
				reader = csv.DictReader(f)
				for row in reader:
					if row.get("UserID") == user_id and row.get("Password") == password:
						found = True
						break
			if found:
				login_win.destroy()
				show_admin_dashboard(user_id)
			else:
				messagebox.showerror("Login Failed", "Invalid UserID or Password.", parent=login_win)

		login_btn = tk.Button(
			login_win, text="Login", font=("Segoe UI", 14, "bold"), bg="#FFD600", fg="#111111",
			activebackground="#FFF176", activeforeground="#111", bd=0, relief=tk.FLAT, cursor="hand2",
			width=16, height=1, command=validate_login
		)
		login_btn.pack(pady=(28, 8))
		# Admin Dashboard after successful login
		def show_admin_dashboard(user_id):
			dash = tk.Toplevel(root)
			dash.title(f"Admin Dashboard - {user_id}")
			dash.geometry("900x800")
			dash.configure(bg="#181A20")
			dash.resizable(False, False)

			tk.Label(dash, text=f"Welcome, {user_id}", font=("Segoe UI", 22, "bold"), fg="#FFD600", bg="#181A20", pady=18).pack()

			btn_frame = tk.Frame(dash, bg="#181A20")
			btn_frame.pack(pady=40)

			def open_folder(path):
				try:
					os.startfile(path)
				except Exception as e:
					messagebox.showerror("Error", f"Could not open: {path}\n{e}", parent=dash)

			def open_file(path):
				try:
					os.startfile(path)
				except Exception as e:
					messagebox.showerror("Error", f"Could not open: {path}\n{e}", parent=dash)

			# Button style
			dash_btn_style = {
				'font': ("Segoe UI", 15, "bold"),
				'bg': "#FFD600",
				'fg': "#181A20",
				'activebackground': "#FFF176",
				'activeforeground': "#111",
				'bd': 0,
				'relief': tk.FLAT,
				'cursor': "hand2",
				'width': 32,
				'height': 2,
				'anchor': 'center',
				'justify': 'center',
				'highlightthickness': 0
			}

			# Student Daily Basis Attendance Folder
			tk.Button(
				btn_frame, text="Daily Basis Attendance",
				command=lambda: open_folder(r"D:\code\Upwork Project\FRAS\Data\Student_daily_basis_atten"),
				**dash_btn_style
			).pack(pady=16)

			# Attendance CSV
			tk.Button(
				btn_frame, text="ReG.. Attendance",
				command=lambda: open_file(r"D:\code\Upwork Project\FRAS\Data\attendance.csv"),
				**dash_btn_style
			).pack(pady=16)

			# Attendance Images Folder
			tk.Button(
				btn_frame, text="Attendance Images",
				command=lambda: open_folder(r"D:\code\Upwork Project\FRAS\Atten_Img"),
				**dash_btn_style
			).pack(pady=16)

			# Close button
			tk.Button(
				dash, text="Close", font=("Segoe UI", 13, "bold"), bg="#222", fg="#FFD600",
				activebackground="#FFD600", activeforeground="#111111", bd=0, relief=tk.FLAT, cursor="hand2",
				width=12, height=1, command=dash.destroy
			).pack(pady=18)

		# Forget Password and Sign Up
		link_frame = tk.Frame(login_win, bg="#111111")
		link_frame.pack(pady=(8, 0))
		def on_forget():
			messagebox.showinfo("Forgot Password", "Password recovery is not implemented yet.")
		def on_signup():
			# --- Sign Up Modal ---
			signup_win = tk.Toplevel(login_win)
			signup_win.title("Sign Up")
			signup_win.geometry("900x800")
			signup_win.configure(bg="#111111")
			signup_win.resizable(False, False)

			# Heading
			heading = tk.Label(signup_win, text="Admin Sign Up", font=("Segoe UI", 28, "bold"), fg="#FFD600", bg="#111111", pady=24)
			heading.pack()

			form_frame = tk.Frame(signup_win, bg="#111111")
			form_frame.pack(pady=20)

			# Field labels and entries
			fields = [
				("First Name", "first_name"),
				("Last Name", "last_name"),
				("User ID", "user_id"),
				("Set Password", "password"),
				("Confirm Password", "confirm_password"),
				("Organization Name", "org_name")
			]
			entries = {}
			for idx, (label, key) in enumerate(fields):
				lbl = tk.Label(form_frame, text=label, font=("Segoe UI", 16, "bold"), fg="#FFD600", bg="#111111")
				lbl.grid(row=idx, column=0, sticky="e", pady=18, padx=(40, 18))
				show = "*" if "password" in key else None
				ent = tk.Entry(form_frame, font=("Segoe UI", 16), bg="#222", fg="#FFD600", insertbackground="#FFD600", relief=tk.FLAT, width=32, show=show)
				ent.grid(row=idx, column=1, sticky="w", pady=18, padx=(0, 40))
				entries[key] = ent

			# Submit handler
			def submit_signup():
				data = {k: e.get().strip() for k, e in entries.items()}
				# Validation
				if not all(data.values()):
					messagebox.showwarning("Input Error", "All fields are required.", parent=signup_win)
					return
				if data["password"] != data["confirm_password"]:
					messagebox.showwarning("Password Error", "Passwords do not match.", parent=signup_win)
					return
				# Save to CSV
				save_dir = r"D:\code\Upwork Project\FRAS\Data\Admin_Data"
				os.makedirs(save_dir, exist_ok=True)
				csv_path = os.path.join(save_dir, "admin_signup_data.csv")
				file_exists = os.path.exists(csv_path)
				with open(csv_path, "a", newline='', encoding="utf-8") as f:
					writer = csv.writer(f)
					if not file_exists:
						writer.writerow(["First Name", "Last Name", "UserID", "Password", "Organization Name"])
					writer.writerow([
						data["first_name"],
						data["last_name"],
						data["user_id"],
						data["password"],
						data["org_name"]
					])
				messagebox.showinfo("Success", "Sign up successful!", parent=signup_win)
				signup_win.destroy()

			# Buttons
			btn_frame = tk.Frame(signup_win, bg="#111111")
			btn_frame.pack(pady=30)
			submit_btn = tk.Button(
				btn_frame, text="Submit", font=("Segoe UI", 16, "bold"), bg="#FFD600", fg="#111111",
				activebackground="#FFF176", activeforeground="#111", bd=0, relief=tk.FLAT, cursor="hand2",
				width=16, height=2, command=submit_signup
			)
			submit_btn.grid(row=0, column=0, padx=24)
			close_btn = tk.Button(
				btn_frame, text="Close", font=("Segoe UI", 16, "bold"), bg="#222", fg="#FFD600",
				activebackground="#FFD600", activeforeground="#111111", bd=0, relief=tk.FLAT, cursor="hand2",
				width=16, height=2, command=signup_win.destroy
			)
			close_btn.grid(row=0, column=1, padx=24)

		forget_btn = tk.Button(link_frame, text="Forgot Password?", font=("Segoe UI", 11, "underline"), fg="#FFD600", bg="#111111", bd=0, cursor="hand2", activebackground="#111111", activeforeground="#FFF176", command=on_forget)
		forget_btn.grid(row=0, column=0, padx=8)
		signup_btn = tk.Button(link_frame, text="Sign Up", font=("Segoe UI", 11, "underline"), fg="#FFD600", bg="#111111", bd=0, cursor="hand2", activebackground="#111111", activeforeground="#FFF176", command=on_signup)
		signup_btn.grid(row=0, column=1, padx=8)

		# Close Button
		close_btn = tk.Button(login_win, text="Close", font=("Segoe UI", 12, "bold"), bg="#222", fg="#FFD600", activebackground="#FFD600", activeforeground="#111111", bd=0, relief=tk.FLAT, cursor="hand2", width=10, command=login_win.destroy)
		close_btn.pack(pady=(30, 0))

		def show_help():
			help_win = tk.Toplevel(root)
			help_win.title("Help & User Guide - FRAS")
			help_win.geometry("900x800")
			help_win.configure(bg="#181A20")
			help_win.resizable(False, False)

			# Heading
			heading = tk.Label(help_win, text="Help & User Guide", font=("Segoe UI", 28, "bold"), fg="#FFD600", bg="#181A20", pady=24)
			heading.pack()

			# Scrollable Frame for Help Content
			content_frame = tk.Frame(help_win, bg="#181A20")
			content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
			canvas = tk.Canvas(content_frame, bg="#181A20", highlightthickness=0)
			scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
			scrollable_frame = tk.Frame(canvas, bg="#181A20")

			scrollable_frame.bind(
				"<Configure>",
				lambda e: canvas.configure(
					scrollregion=canvas.bbox("all")
				)
			)
			canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
			canvas.configure(yscrollcommand=scrollbar.set)
			canvas.pack(side="left", fill="both", expand=True)
			scrollbar.pack(side="right", fill="y")

			# Help Content (step-by-step, common problems, solutions)
			def add_section(title, steps, color="#FFD600"):
				tk.Label(scrollable_frame, text=title, font=("Segoe UI", 20, "bold"), fg=color, bg="#181A20", pady=10).pack(anchor="w")
				for step in steps:
					tk.Label(scrollable_frame, text="• " + step, font=("Segoe UI", 14), fg="#FFF", bg="#181A20", wraplength=820, justify="left", anchor="w").pack(anchor="w", padx=18, pady=2)

			add_section("Getting Started", [
				"1. Register Attendance: Click 'Register Attendance' to add your face to the system. Follow on-screen instructions to capture your face and enter your name.",
				"2. CAP LIVE: Click 'CAP LIVE' to verify your face for daily attendance. The system will mark you present if your face is recognized.",
				"3. Student Checklist: View all registered students and their attendance images.",
				"4. Admin Login: For admin access, use your UserID and Password. Sign up if you are a new admin.",
				"5. Help: Access this help window anytime for guidance.",
				"6. Exit: Click 'Exit' to close the application safely."
			])

			add_section("Step-by-Step Usage", [
				"1. To register a new student, go to 'Register Attendance', open the camera, and follow prompts.",
				"2. For daily attendance, use 'CAP LIVE' and ensure your face is clearly visible to the camera.",
				"3. Admins can log in to view attendance records, images, and manage data.",
				"4. Use 'Student Checklist' to review all registered students and their images.",
				"5. For admin sign up, click 'Admin Login' > 'Sign Up' and fill all required fields."
			], color="#00E676")

			add_section("Common Problems & Solutions", [
				"• Camera Not Detected: Ensure your webcam is connected and not used by another application.",
				"• Face Not Detected: Make sure your face is well-lit and fully visible to the camera.",
				"• Duplicate Face Warning: The system prevents registering the same face twice. Try with a different person or angle.",
				"• Attendance Not Saved: Check if the data folder exists and you have write permissions.",
				"• Admin Login Failed: Double-check your UserID and Password. Use 'Sign Up' if you are a new admin.",
				"• Images Not Displaying: Ensure the image files exist in the correct folder and are not corrupted.",
				"• Application Not Starting: Make sure all required Python packages are installed (opencv-python, face_recognition, dlib, Pillow, etc.)."
			], color="#FF5252")

			add_section("Tips for Best Results", [
				"• Use a clear, front-facing photo for registration.",
				"• Avoid hats, sunglasses, or masks during face capture.",
				"• Register attendance in a well-lit environment.",
				"• Keep your data folders organized and do not delete important CSV/image files.",
				"• For any technical issues, contact your administrator or refer to the user manual."
			], color="#40C4FF")

			# Close Button
			close_btn = tk.Button(
				help_win, text="Close", font=("Segoe UI", 16, "bold"), bg="#FFD600", fg="#181A20",
				activebackground="#FFF176", activeforeground="#111", bd=0, relief=tk.FLAT, cursor="hand2",
				width=16, height=2, command=help_win.destroy
			)
			close_btn.pack(pady=24)

	btn_attendance = tk.Button(btn_frame, text="Register Attendance", command=lambda: show_page('attendance'), **button_style)
	btn_attendance.pack(pady=8)
	btn_checklist = tk.Button(btn_frame, text="Student Checklist", command=lambda: [show_page('checklist'), update_checklist()], **button_style)
	btn_checklist.pack(pady=8)
	btn_web_live = tk.Button(btn_frame, text="CAP LIVE", command=lambda: show_page('caplive'), **button_style)
	btn_web_live.pack(pady=8)
	btn_admin = tk.Button(btn_frame, text="Admin Login", command=admin_login, **button_style)
	btn_admin.pack(pady=8)
	btn_help = tk.Button(btn_frame, text="Help", command=show_help, **button_style)
	btn_help.pack(pady=8)
	btn_exit = tk.Button(btn_frame, text="Exit", command=root.destroy, **button_style)
	btn_exit.pack(pady=8)

	# Set background for home page
	home.configure(bg="#2C80BD")

	# Show home page by default
	show_page('home')

	root.mainloop()

if __name__ == "__main__":
	main()
