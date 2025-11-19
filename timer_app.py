import tkinter as tk
from tkinter import messagebox

# Try to import plyer for cross-platform desktop notifications
try:
    from plyer import notification
except ImportError:
    notification = None


class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Desktop Timer")

        # Internal state
        self.remaining_seconds = 0
        self.timer_running = False
        self.timer_job = None

        # --- UI ---

        # Input label
        self.input_label = tk.Label(root, text="Time (MM:SS or minutes):")
        self.input_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Time entry
        self.time_entry = tk.Entry(root, width=10)
        self.time_entry.grid(row=0, column=1, padx=10, pady=10)
        self.time_entry.insert(0, "25")  # default 25 minutes

        # Display label
        self.display_label = tk.Label(
            root,
            text="00:00",
            font=("Helvetica", 36),
            padx=20,
            pady=10,
        )
        self.display_label.grid(row=1, column=0, columnspan=3)

        # Buttons
        self.start_button = tk.Button(root, text="Start", width=10, command=self.start_timer)
        self.start_button.grid(row=2, column=0, padx=5, pady=10)

        self.pause_button = tk.Button(root, text="Pause", width=10, command=self.pause_timer)
        self.pause_button.grid(row=2, column=1, padx=5, pady=10)

        self.reset_button = tk.Button(root, text="Reset", width=10, command=self.reset_timer)
        self.reset_button.grid(row=2, column=2, padx=5, pady=10)

        for i in range(3):
            root.grid_columnconfigure(i, weight=1)

    # --- Timer logic ---

    def parse_time_input(self) -> int:
        """
        Parse the time from the entry widget.
        - "MM:SS" -> total seconds
        - "M" or "MM" -> minutes -> total seconds
        """
        text = self.time_entry.get().strip()
        if not text:
            raise ValueError("Empty time input")

        if ":" in text:
            parts = text.split(":")
            if len(parts) != 2:
                raise ValueError("Invalid format, use MM:SS or minutes")
            minutes = int(parts[0])
            seconds = int(parts[1])
        else:
            minutes = int(text)
            seconds = 0

        if minutes < 0 or seconds < 0 or seconds >= 60:
            raise ValueError("Minutes must be >= 0 and seconds between 0–59")

        return minutes * 60 + seconds

    def start_timer(self):
        if self.timer_running:
            return

        if self.remaining_seconds <= 0:
            try:
                self.remaining_seconds = self.parse_time_input()
            except ValueError as e:
                messagebox.showerror("Invalid input", str(e))
                return

        if self.remaining_seconds <= 0:
            return

        self.timer_running = True
        self.update_display()
        self.schedule_tick()

    def schedule_tick(self):
        self.timer_job = self.root.after(1000, self.tick)

    def tick(self):
        if not self.timer_running:
            return

        self.remaining_seconds -= 1
        self.update_display()

        if self.remaining_seconds <= 0:
            self.timer_running = False
            self.remaining_seconds = 0
            self.update_display()
            self.notify_finished()
        else:
            self.schedule_tick()

    def update_display(self):
        minutes, seconds = divmod(max(self.remaining_seconds, 0), 60)
        self.display_label.config(text=f"{minutes:02d}:{seconds:02d}")

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            if self.timer_job is not None:
                self.root.after_cancel(self.timer_job)
                self.timer_job = None

    def reset_timer(self):
        self.pause_timer()
        self.remaining_seconds = 0
        self.update_display()

    def notify_finished(self):
        # Beep
        try:
            self.root.bell()
        except Exception:
            pass

        # OS desktop notification (if plyer is available)
        if notification is not None:
            try:
                notification.notify(
                    title="Timer finished",
                    message="Time's up!",
                    timeout=5,  # seconds (may be ignored by some OSes)
                )
            except Exception:
                # If notifications fail, just ignore and rely on messagebox
                pass

        # Fallback popup
        messagebox.showinfo("Timer finished", "Time's up!")

    def on_close(self):
        self.pause_timer()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
