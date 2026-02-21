from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp

from datetime import datetime


class HistoryScreen(Screen):
    def __init__(self, service, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.return_to = "home"
        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=8)
        back_btn = Button(text="Back", size_hint_x=None, width=dp(90))
        back_btn.bind(on_release=self.go_back)
        header.add_widget(back_btn)

        self.title_lbl = Label(text="History", halign="left", valign="middle")
        self.title_lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))
        header.add_widget(self.title_lbl)
        root.add_widget(header)

        # Exercise picker row
        picker = BoxLayout(size_hint_y=None, height=dp(44), spacing=8)
        picker.add_widget(Label(text="Exercise:", size_hint_x=None, width=dp(90)))
        self.exercise_spinner = Spinner(text="(select)", values=[])
        self.exercise_spinner.bind(text=self.on_exercise_selected)
        picker.add_widget(self.exercise_spinner)

        refresh_btn = Button(text="Refresh", size_hint_x=None, width=dp(110))
        refresh_btn.bind(on_release=lambda *_: self.refresh_exercise_list())
        picker.add_widget(refresh_btn)

        root.add_widget(picker)

        # Scrollable results
        self.scroll = ScrollView()
        self.results = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.results.bind(minimum_height=self.results.setter("height"))
        self.scroll.add_widget(self.results)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        # Called whenever we enter this screen
        self.refresh_exercise_list()

    def go_back(self, *_):
        self.manager.current = "home"

    def refresh_exercise_list(self):
        names = self.service.list_exercise_names()
        self.exercise_spinner.values = names
        if names and (self.exercise_spinner.text == "(select)" or self.exercise_spinner.text not in names):
            self.exercise_spinner.text = names[0]
        elif not names:
            self.exercise_spinner.text = "(no exercises found)"
            self.results.clear_widgets()
            self.results.add_widget(Label(text="No exercises in program/logs yet."))

    def on_exercise_selected(self, _spinner, exercise_name: str):
        if not exercise_name or exercise_name.startswith("("):
            return
        self.render_history(exercise_name)

    def render_history(self, exercise_name: str):
        self.title_lbl.text = f"History • {exercise_name}"
        self.results.clear_widgets()

        history = self.service.get_exercise_history(exercise_name, limit=200)
        if not history:
            self.results.add_widget(Label(text="No history yet for this exercise."))
            return

        # Group by started_at (session)
        grouped = {}
        for row in history:
            grouped.setdefault(row["started_at"], []).append(row)

        # Show newest sessions first
        for started_at in sorted(grouped.keys(), reverse=True):
            rows = grouped[started_at]

            # Take difficulty from first row (same session)
            difficulty = rows[0]["difficulty"]

            # Format: reps-weight, reps-weight, ...
            parts = [f'{r["reps"]} reps -{r["weight"]}kg' for r in rows]
            one_line = ", ".join(parts)

            card = BoxLayout(orientation="vertical", padding=10, spacing=6, size_hint_y=None)
            card.height = dp(90)

            try:
                dt = datetime.fromisoformat(started_at)
                date_only = dt.strftime("%d %b %Y")
            except Exception:
                date_only = started_at.split("T")[0]
            header = Label(
                text=f"[b]{date_only}[/b]   ({difficulty})",
                markup=True,
                size_hint_y=None,
                height=dp(26),
                halign="left",
                valign="middle",
            )
            header.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))
            card.add_widget(header)

            line = Label(
                text=one_line,
                size_hint_y=None,
                height=dp(52),
                halign="left",
                valign="top",
            )
            line.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))
            card.add_widget(line)

            self.results.add_widget(card)
            
    def show_exercise(self, exercise_name: str, return_to: str = "home"):
        self.return_to = return_to
        # Ensure list is loaded (in case screen wasn't entered yet)
        self.refresh_exercise_list()
        if exercise_name in self.exercise_spinner.values:
            self.exercise_spinner.text = exercise_name
            self.render_history(exercise_name)
        else:
            # If it's not in the spinner yet for some reason, still render
            self.exercise_spinner.text = exercise_name
            self.render_history(exercise_name)
    
    def go_back(self, *_):
        self.manager.current = getattr(self, "return_to", "home")   