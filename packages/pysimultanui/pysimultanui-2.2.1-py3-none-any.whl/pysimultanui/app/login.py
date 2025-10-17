from nicegui import Client, app, ui
# from .theme import frame
# from ..router import router
from typing import Optional
from fastapi.responses import RedirectResponse

from .. import user_manager


def content() -> Optional[RedirectResponse]:
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        if user_manager.authenticate(username.value, password.value):
            app.storage.user.update({'username': username.value, 'authenticated': True})
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
            logger = user_manager.users[app.storage.user['username']].logger
            if logger is not None:
                user_manager.users[app.storage.user['username']].logger.info('Logged in')
        else:
            ui.notify('Wrong username or password', color='negative')

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    with ui.card().classes('h-full w-full').style('align-items: center;'):
        ui.label('PySimultan WebUI')
        with ui.card():
            username = ui.input('Username').on('keydown.enter', try_login)
            password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
            ui.button('Log in', on_click=try_login)
