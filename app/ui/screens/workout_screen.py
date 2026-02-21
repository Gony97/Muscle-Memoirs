from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.metrics import dp

from app.core.suggestions import suggest_weight


class WorkoutScreen(Screen):
    def __init__(self, service, **kwargs):
        super().__init__(**kwargs)
        self.service = service

        self.week = None
        self.day = None
        self.session_id = None

        self.root_layout = BoxLayout(orientation="vertical", padding=12, spacing=10)

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=8)
        self.title_lbl = Label(text="Workout", halign="left", valign="middle")
        self.title_lbl.bind(size=self._update_title_text_size)
        back_btn = Button(text="Back", size_hint_x=None, width=dp(90))
        back_btn.bind(on_release=self.go_back)
        header.add_widget(back_btn)
        header.add_widget(self.title_lbl)
        self.root_layout.add_widget(header)

        # Scrollable content
        self.scroll = ScrollView()
        self.content = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        self.root_layout.add_widget(self.scroll)

        # Footer
        footer = BoxLayout(size_hint_y=None, height=dp(52), spacing=8)
        self.save_btn = Button(text="Save all logs")
        self.save_btn.bind(on_release=self.save_all)
        footer.add_widget(self.save_btn)
        self.root_layout.add_widget(footer)

        self.add_widget(self.root_layout)

        # store widgets per exercise
        self.exercise_rows = []  # list[dict]

    def _update_title_text_size(self, instance, *_):
        instance.text_size = instance.size

    def go_back(self, *_):
        self.manager.current = "home"

    def load_workout(self, week: int, day: int):
        self.week = week
        self.day = day
        self.session_id = None
        self.title_lbl.text = f"Week {week} • Day {day}"

        self.content.clear_widgets()
        self.exercise_rows.clear()

        template = self.service.get_workout_template(week, day)

        if not template:
            self.content.add_widget(Label(text="No exercises found for this week/day. Check program.json import."))
            return

        for ex in template:
            self.content.add_widget(self._build_exercise_card(ex.name, ex.target_sets, ex.target_reps, ex.notes))

        # little spacer
        self.content.add_widget(Label(text="", size_hint_y=None, height=dp(20)))

    def open_history(self, exercise_name: str):
        history_screen = self.manager.get_screen("history")
        history_screen.show_exercise(exercise_name, return_to="workout")
        self.manager.current = "history"

    def _fmt_weight(self, w: float) -> str:
        return str(int(w)) if float(w).is_integer() else str(w)

    def _clear_set(self, rep_in: TextInput, wt_in: TextInput):
        rep_in.text = ""
        wt_in.text = ""

    def _build_exercise_card(self, exercise_name: str, target_sets, target_reps, notes: str):
        # Auto-sizing card
        card = GridLayout(cols=1, padding=10, spacing=8, size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))

        # Pull last session for this exercise (all sets)
        last_session = self.service.get_last_session_for_exercise(exercise_name)
        sug = suggest_weight(self.service, exercise_name)

        # Title row with History button (right side)
        title_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=8)

        title_lbl = Label(
            text=f"[b]{exercise_name}[/b]  ({target_sets}x{target_reps})",
            markup=True,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        title_lbl.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))

        history_btn = Button(
            text="H",
            size_hint_x=None,
            width=dp(40),
            font_size=dp(18),
            background_normal="",
            background_color=(0, 0, 0, 0),
        )
        history_btn.bind(on_release=lambda *_: self.open_history(exercise_name))

        title_row.add_widget(title_lbl)
        title_row.add_widget(history_btn)
        card.add_widget(title_row)

        # Notes
        if notes:
            n = Label(
                text=f"[i]{notes}[/i]",
                markup=True,
                size_hint_y=None,
                height=dp(24),
                halign="left",
                valign="middle",
            )
            n.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))
            card.add_widget(n)

        # Last time one-line: reps-weight, reps-weight, ...
        last_txt = "—"
        last_sets = []
        last_diff = "normal"

        if last_session and last_session.get("sets"):
            last_sets = last_session["sets"]
            last_diff = last_session.get("difficulty", "normal")

            parts = [f'{s["reps"]}-{self._fmt_weight(float(s["weight"]))}' for s in last_sets]
            last_txt = ", ".join(parts)

        sug_txt = "—" if sug is None else self._fmt_weight(float(sug))

        info = Label(
            text=f"Last time: {last_txt}\nSuggested: {sug_txt}",
            size_hint_y=None,
            height=dp(58),
            halign="left",
            valign="middle",
        )
        info.bind(size=lambda inst, *_: setattr(inst, "text_size", inst.size))
        card.add_widget(info)

        # Difficulty row
        diff_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=8)
        diff_row.add_widget(Label(text="Difficulty:", size_hint_x=None, width=dp(90)))
        diff_spinner = Spinner(text="normal", values=["easy", "normal", "hard"])
        diff_row.add_widget(diff_spinner)
        card.add_widget(diff_row)

        # Sets grid (auto-sizing)
        sets_n = int(target_sets) if target_sets else 3

        reps_default = ""
        if target_reps:
            reps_default = str(target_reps).split("-")[0].strip()

        # Smart bump: if last was easy and we have a suggestion, use suggested for all weights
        use_suggested_for_all_weights = (last_diff == "easy" and sug is not None)
        suggested_weight_str = "" if sug is None else self._fmt_weight(float(sug))

        sets_grid = GridLayout(cols=4, spacing=6, size_hint_y=None)
        sets_grid.bind(minimum_height=sets_grid.setter("height"))

        for header in ("Set", "Reps", "Weight", ""):
            sets_grid.add_widget(Label(text=header, size_hint_y=None, height=dp(30)))

        rep_inputs = []
        weight_inputs = []

        for i in range(1, sets_n + 1):
            sets_grid.add_widget(Label(text=str(i), size_hint_y=None, height=dp(30)))

            # Prefill reps/weight
            rep_text = reps_default
            weight_text = suggested_weight_str if suggested_weight_str else ""

            if i <= len(last_sets):
                rep_text = str(last_sets[i - 1]["reps"])
                if not use_suggested_for_all_weights:
                    weight_text = self._fmt_weight(float(last_sets[i - 1]["weight"]))

            # For extra sets beyond last time: keep reps_default, use suggestion if available
            if i > len(last_sets) and suggested_weight_str:
                weight_text = suggested_weight_str

            rep_in = TextInput(text=rep_text, multiline=False, input_filter="int", size_hint_y=None, height=dp(30))
            wt_in = TextInput(text=weight_text, multiline=False, input_filter="float", size_hint_y=None, height=dp(30))

            rep_inputs.append(rep_in)
            weight_inputs.append(wt_in)

            sets_grid.add_widget(rep_in)
            sets_grid.add_widget(wt_in)

            clr = Button(text="Clear", size_hint_y=None, height=dp(30))
            clr.bind(on_release=lambda _btn, r=rep_in, w=wt_in: self._clear_set(r, w))
            sets_grid.add_widget(clr)

        card.add_widget(sets_grid)

        self.exercise_rows.append(
            {
                "exercise_name": exercise_name,
                "difficulty_spinner": diff_spinner,
                "rep_inputs": rep_inputs,
                "weight_inputs": weight_inputs,
                "info_label": info,
            }
        )

        return card

    def save_all(self, *_):
        """
        Saves:
        - difficulty per exercise
        - overwrites sets per exercise (no duplicates)
        Creates a session ONLY if at least one valid set is filled.
        """
        # 1) First pass: gather all valid sets per exercise
        payload = []  # list of (exercise_name, difficulty, reps_list, weights_list)
        total_sets = 0

        for row in self.exercise_rows:
            ex = row["exercise_name"]
            diff = row["difficulty_spinner"].text
            rep_inputs = row["rep_inputs"]
            wt_inputs = row["weight_inputs"]

            reps_list = []
            weights_list = []

            for r_in, w_in in zip(rep_inputs, wt_inputs):
                r_txt = (r_in.text or "").strip()
                w_txt = (w_in.text or "").strip()
                if not r_txt or not w_txt:
                    continue
                try:
                    reps_list.append(int(r_txt))
                    weights_list.append(float(w_txt))
                except ValueError:
                    continue

            total_sets += len(reps_list)
            payload.append((ex, diff, reps_list, weights_list))

        # 2) If no sets were entered, don't create a session
        if total_sets == 0:
            self.title_lbl.text = f"Week {self.week} • Day {self.day} — nothing to save"
            return

        # 3) Create session only now (first save)
        if self.session_id is None:
            self.session_id = self.service.start_session(self.week, self.day)

        # 4) Save to DB
        saved_sets = 0
        saved_exercises = 0

        for ex, diff, reps_list, weights_list in payload:
            # Save difficulty always (per exercise)
            self.service.set_exercise_difficulty(self.session_id, ex, diff)
            saved_exercises += 1

            # Overwrite sets for this exercise (no duplicates)
            inserted = self.service.replace_sets_for_exercise(self.session_id, ex, reps_list, weights_list)
            saved_sets += inserted

        self.title_lbl.text = (
            f"Week {self.week} • Day {self.day} (session {self.session_id}) "
            f"✅ Saved {saved_sets} sets ({saved_exercises} exercises)"
        )