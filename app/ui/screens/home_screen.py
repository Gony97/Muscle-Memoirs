from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.label import Label


class HomeScreen(Screen):
    def __init__(self, service, **kwargs):
        super().__init__(**kwargs)
        self.service = service

        self.selected_day = 1  # internal mapping from workout name -> day

        root = BoxLayout(orientation="vertical", padding=16, spacing=12)

        meta = self.service.get_program_meta()
        title = meta.get("program_name", "FWorkout")
        units = meta.get("units", "kg")
        root.add_widget(Label(text=f"[b]{title}[/b]\nUnits: {units}", markup=True, size_hint_y=None, height=80))

        # Week picker
        root.add_widget(Label(text="Week", size_hint_y=None, height=26))
        self.week_spinner = Spinner(
            text="1",
            values=[str(i) for i in range(1, 13)],
            size_hint_y=None,
            height=44,
        )
        self.week_spinner.bind(text=self.on_week_changed)
        root.add_widget(self.week_spinner)

        # Workout picker (by name)
        root.add_widget(Label(text="Workout", size_hint_y=None, height=26))
        self.workout_spinner = Spinner(
            text="(select workout)",
            values=[],
            size_hint_y=None,
            height=44,
        )
        self.workout_spinner.bind(text=self.on_workout_changed)
        root.add_widget(self.workout_spinner)

        # Buttons
        start_btn = Button(text="Start workout", size_hint_y=None, height=48)
        start_btn.bind(on_release=self.start_workout)
        root.add_widget(start_btn)

        self.add_widget(root)

        # initial load
        self.refresh_workouts_for_week(1)

    def refresh_workouts_for_week(self, week: int):
        workouts = self.service.list_workouts_for_week(week)  # [(day, name), ...]
        self._workouts = workouts

        names = [name for _day, name in workouts]
        self.workout_spinner.values = names

        if names:
            self.workout_spinner.text = names[0]
            self.selected_day = workouts[0][0]
        else:
            self.workout_spinner.text = "(no workouts found)"
            self.selected_day = 1

    def on_week_changed(self, _spinner, week_text: str):
        try:
            week = int(week_text)
        except ValueError:
            week = 1
        self.refresh_workouts_for_week(week)

    def on_workout_changed(self, _spinner, workout_name: str):
        # map selected name back to day
        for day, name in getattr(self, "_workouts", []):
            if name == workout_name:
                self.selected_day = day
                return

    def start_workout(self, *_):
        week = int(self.week_spinner.text)
        day = int(self.selected_day)

        workout_screen = self.manager.get_screen("workout")
        workout_screen.load_workout(week=week, day=day)
        self.manager.current = "workout"