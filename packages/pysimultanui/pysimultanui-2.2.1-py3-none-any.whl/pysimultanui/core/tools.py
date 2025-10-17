from nicegui import Client, app, ui, events


class ConfirmationDialog(ui.dialog):

    def __init__(self, question: str, *options: str, additional_content_fcn=None, **kwargs):
        super().__init__(value=True)
        self.props("persistent")
        with self, ui.card():
            ui.label(question).classes("text-lg")

            if additional_content_fcn:
                additional_content_fcn()

            with ui.row():
                for c_option in options:
                    ui.button(c_option, on_click=lambda e, option=c_option: self.submit(option))
