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
        self.root.title("Desktop Timer & Stopwatch")

        # --- Internal state ---

        # Timer state (countdown)
        self.timer_seconds = 0
        self.timer_running = False
        self.timer_job = None

        # Stopwatch state (count up)
        self.stopwatch_seconds = 0
        self.stopwatch_running = False
        self.stopwatch_job = None

        # Current UI mode: "timer" or "stopwatch"
        self.mode = tk.StringVar(value="timer")

        # --- UI ---

        # Mode selection
        mode_label = tk.Label(root, text="Mode:")
        mode_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.timer_radio = tk.Radiobutton(
            root,
            text="Timer",
            variable=self.mode,
            value="timer",
            command=self.switch_mode,
        )
        self.timer_radio.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.stopwatch_radio = tk.Radiobutton(
            root,
            text="Stopwatch",
            variable=self.mode,
            value="stopwatch",
            command=self.switch_mode,
        )
        self.stopwatch_radio.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Input label + entry (used only in timer mode)
        self.input_label = tk.Label(root, text="Time (MM:SS or minutes, or HH:MM:SS):")
        self.input_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.time_entry = tk.Entry(root, width=10)
        self.time_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.time_entry.insert(0, "25")  # default 25 minutes

        # Big display label (shared)
        self.display_label = tk.Label(
            root,
            text="00:00:00",
            font=("Helvetica", 36),
            padx=20,
            pady=10,
        )
        self.display_label.grid(row=2, column=0, columnspan=3)

        # Buttons (act on current mode)
        self.start_button = tk.Button(root, text="Start", width=10, command=self.start)
        self.start_button.grid(row=3, column=0, padx=5, pady=10)

        self.pause_button = tk.Button(root, text="Pause", width=10, command=self.pause)
        self.pause_button.grid(row=3, column=1, padx=5, pady=10)

        self.reset_button = tk.Button(root, text="Reset", width=10, command=self.reset)
        self.reset_button.grid(row=3, column=2, padx=5, pady=10)

        for i in range(3):
            root.grid_columnconfigure(i, weight=1)

        # Initialize UI
        self.switch_mode()

    # --- Mode handling ---

    def switch_mode(self):
        """
        When the user switches between Timer and Stopwatch:
        - Do NOT reset or pause anything.
        - Only change labels / input state.
        - Refresh display to show the correct counter.
        """
        if self.mode.get() == "timer":
            self.input_label.config(text="Time (MM:SS or minutes, or HH:MM:SS):")
            self.time_entry.config(state="normal")
        else:
            self.input_label.config(text="Stopwatch (press Start to begin):")
            self.time_entry.config(state="disabled")

        # Update what is shown based on current mode
        self.update_display()

    # --- Parsing for timer mode ---

    def parse_time_input(self) -> int:
        """
        Parse the time from the entry widget.

        Allowed formats:
        - "M" or "MM" -> minutes
        - "MM:SS"
        - "HH:MM:SS"
        """
        text = self.time_entry.get().strip()
        if not text:
            raise ValueError("Empty time input")

        parts = text.split(":")

        if len(parts) == 1:
            # minutes only
            minutes = int(parts[0])
            if minutes < 0:
                raise ValueError("Minutes must be >= 0")
            return minutes * 60

        elif len(parts) == 2:
            # MM:SS
            minutes = int(parts[0])
            seconds = int(parts[1])
            if minutes < 0 or not (0 <= seconds < 60):
                raise ValueError("Minutes must be >= 0 and seconds between 0–59")
            return minutes * 60 + seconds

        elif len(parts) == 3:
            # HH:MM:SS
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            if hours < 0 or not (0 <= minutes < 60) or not (0 <= seconds < 60):
                raise ValueError("Hours must be >= 0; minutes, seconds between 0–59")
            return hours * 3600 + minutes * 60 + seconds

        else:
            raise ValueError("Invalid format; use M, MM:SS, or HH:MM:SS")

    # --- Public button actions (dispatch by mode) ---

    def start(self):
        if self.mode.get() == "timer":
            self.start_timer()
        else:
            self.start_stopwatch()

    def pause(self):
        if self.mode.get() == "timer":
            self.pause_timer()
        else:
            self.pause_stopwatch()

    def reset(self):
        if self.mode.get() == "timer":
            self.reset_timer()
        else:
            self.reset_stopwatch()

    # --- Timer (countdown) logic ---

    def start_timer(self):
        if self.timer_running:
            return

        if self.timer_seconds <= 0:
            try:
                self.timer_seconds = self.parse_time_input()
            except ValueError as e:
                messagebox.showerror("Invalid input", str(e))
                return

        if self.timer_seconds <= 0:
            return

        self.timer_running = True
        self.update_display()
        self.schedule_timer_tick()

    def schedule_timer_tick(self):
        self.timer_job = self.root.after(1000, self.tick_timer)

    def tick_timer(self):
        if not self.timer_running:
            return

        self.timer_seconds -= 1

        if self.timer_seconds <= 0:
            self.timer_seconds = 0
            self.timer_running = False
            self.update_display()
            self.notify_finished()
        else:
            self.update_display()
            self.schedule_timer_tick()

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            if self.timer_job is not None:
                try:
                    self.root.after_cancel(self.timer_job)
                except Exception:
                    pass
                self.timer_job = None

    def reset_timer(self):
        self.pause_timer()
        self.timer_seconds = 0
        # Update display only if timer mode is active
        if self.mode.get() == "timer":
            self.update_display()

    # --- Stopwatch (count up) logic ---

    def start_stopwatch(self):
        if self.stopwatch_running:
            return

        self.stopwatch_running = True
        self.update_display()
        self.schedule_stopwatch_tick()

    def schedule_stopwatch_tick(self):
        self.stopwatch_job = self.root.after(1000, self.tick_stopwatch)

    def tick_stopwatch(self):
        if not self.stopwatch_running:
            return

        self.stopwatch_seconds += 1
        self.update_display()
        self.schedule_stopwatch_tick()

    def pause_stopwatch(self):
        if self.stopwatch_running:
            self.stopwatch_running = False
            if self.stopwatch_job is not None:
                try:
                    self.root.after_cancel(self.stopwatch_job)
                except Exception:
                    pass
                self.stopwatch_job = None

    def reset_stopwatch(self):
        self.pause_stopwatch()
        self.stopwatch_seconds = 0
        # Update display only if stopwatch mode is active
        if self.mode.get() == "stopwatch":
            self.update_display()

    # --- Display ---

    def update_display(self):
        """
        Choose which counter to show based on current mode,
        then render as HH:MM:SS.
        """
        if self.mode.get() == "timer":
            total = self.timer_seconds
        else:
            total = self.stopwatch_seconds

        total = max(total, 0)
        hours, rem = divmod(total, 3600)
        minutes, seconds = divmod(rem, 60)
        self.display_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    # --- Notifications for TIMER mode ---

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
                pass

        # Fallback popup
        messagebox.showinfo("Timer finished", "Time's up!")

    # --- Window close handling ---

    def on_close(self):
        # Cancel both timers if needed
        self.pause_timer()
        self.pause_stopwatch()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
