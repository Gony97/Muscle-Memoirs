from pathlib import Path

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from app.core.db import init_db
from app.core.import_program import import_program
from app.core.services import WorkoutService

from app.ui.screens.home_screen import HomeScreen
from app.ui.screens.workout_screen import WorkoutScreen


class FWorkoutApp(App):
    def build(self):
        root = Path(__file__).resolve().parents[2]  # .../fworkout
        db_path = root / "data" / "fworkout.db"
        program_path = root / "program.json"

        init_db(db_path)
        import_program(db_path, program_path)

        service = WorkoutService(db_path)

        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home", service=service))
        sm.add_widget(WorkoutScreen(name="workout", service=service))
        return sm


if __name__ == "__main__":
    FWorkoutApp().run()