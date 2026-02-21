from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp


class HomeScreen(Screen):
    def __init__(self, service, **kwargs):
        super().__init__(**kwargs)
        self.service = service

        self.week = 1
        self._workouts = []  # [(day, name), ...]

        root = BoxLayout(orientation="vertical", padding=16, spacing=12)

        meta = self.service.get_program_meta()
        title = meta.get("program_name", "FWorkout")
        units = meta.get("units", "kg")
        root.add_widget(Label(text=f"[b]{title}[/b]\nUnits: {units}", markup=True, size_hint_y=None, height=80))

        # Week header row with Prev/Next
        week_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=8)

        prev_btn = Button(text="Prev", size_hint_x=None, width=dp(60))
        prev_btn.bind(on_release=lambda *_: self.change_week(-1))

        self.week_lbl = Label(text="Week 1", halign="left", valign="middle")
        self.week_lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))

        next_btn = Button(text="Next", size_hint_x=None, width=dp(60))
        next_btn.bind(on_release=lambda *_: self.change_week(+1))

        week_row.add_widget(prev_btn)
        week_row.add_widget(self.week_lbl)
        week_row.add_widget(next_btn)

        root.add_widget(week_row)

        # Workout buttons area (3 buttons stacked)
        root.add_widget(Label(text="Workouts", size_hint_y=None, height=dp(26)))

        self.workouts_box = BoxLayout(orientation="vertical", spacing=10)
        root.add_widget(self.workouts_box)

        # History button
        history_btn = Button(text="History", size_hint_y=None, height=dp(48))
        history_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "history"))
        root.add_widget(history_btn)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        # Every time you enter Home, refresh week based on latest session
        self.week = self.service.get_current_week()
        self.render_week()

    def change_week(self, delta: int):
        if delta > 0:
            # Only allow moving forward if CURRENT week is completed
            if not self.service.is_week_completed(self.week):
                # optional feedback in the label:
                self.week_lbl.text = f"Week {self.week} (finish all 3 workouts to unlock next)"
                return

        self.week = max(1, min(12, self.week + delta))
        self.render_week()

    def render_week(self):
        self.week_lbl.text = f"Week {self.week}"
        self._workouts = self.service.list_workouts_for_week(self.week)
        completed_days = self.service.get_completed_days_for_week(self.week)
        
        self.workouts_box.clear_widgets()

        if not self._workouts:
            self.workouts_box.add_widget(Label(text="No workouts found for this week."))
            return

        for day, name in self._workouts:
            btn = Button(text=name, size_hint_y=None, height=dp(56))
            btn.bind(on_release=lambda _btn, d=day: self.start_workout(d))

            if day in completed_days:
                btn.opacity = 0.35  # faded but still clickable
                # Optional: add a subtle marker
                # btn.text = f"{name}  ✓"

            self.workouts_box.add_widget(btn)

    def start_workout(self, day: int):
        workout_screen = self.manager.get_screen("workout")
        workout_screen.load_workout(week=self.week, day=day)
        self.manager.current = "workout"