from contextlib import contextmanager
from nicegui import app, ui, context
from .. import user_manager

from ..__about__ import __version__
from . import home

from .. import core
from ..core.mappers import MapperExpansion


@contextmanager
def frame(navtitle: str):

    """Custom page frame to share the same styling and behavior across all pages"""
    # ui.colors(primary='#da291c', secondary='#941c13', accent='#941c13', positive='#53B689')
    with ui.header().classes('justify-between h-16 shadow-md') as header:

        username = app.storage.user.get('username', None)
        if username is None:
            ui.navigate.to('/login')
            return

        user = user_manager.users[username]

        # ui.image('web_ui/src/static_files/A1_Digital_identifier_pos_RGB.png').classes('w-32')

        with ui.column().classes('flex items-center'):
            with ui.row():
                ui.label('PySimultan').classes('font-bold text-xl')
                ui.label(f'Version {__version__}').classes('text-sm text-gray-500 justify-end items-center')

        with ui.column().classes('flex items-center'):
            with ui.row():

                ui.label(f'Hello {user.name}')
                ui.space()

        with ui.column():
            with ui.expansion() as expansion:
                tool_select = MapperExpansion(user=user_manager.users[app.storage.user['username']],
                                              expansion_object=expansion)
            # tool_select = MapperExpansion(user=user_manager.users[app.storage.user['username']]).classes('font-bold text-sm')
            # tool_select = MapperDropdown(user=user_manager.users[app.storage.user['username']]).classes('font-bold text-sm')
            user_manager.users[app.storage.user['username']].tool_select = tool_select

        with ui.column().classes('justify=end items=center'):
            with ui.row():

                with ui.tabs().classes('h-10') as tabs:
                    # ui.button('Mapped Classes', icon='checklist_rtl', on_click=lambda: left_drawer.toggle())
                    ui.tab('Home', icon='home').classes('h-10')
                    ui.tab('Project', icon='edit').classes('h-10')
                    ui.tab('Logs', icon='format_list_bulleted').classes('h-10')
                    ui.tab('Tasks', icon='work_history').classes('h-10')

                # mapper_select_dialog = core.mappers.MapperSelectDialog()
                user_settings_dialog = core.user.UserSettingsDialog()
                add_toolbox_dialog = core.mappers.AddPackageDialog()


                with ui.button(icon='menu'):
                    with ui.menu() as menu:

                        # def on_click_mappers():
                        #     setattr(mapper_select_dialog, 'user', user_manager.users[app.storage.user['username']])
                        #     mapper_select_dialog.open()
                        #
                        # ui.menu_item('Toolbox',
                        #              on_click=on_click_mappers
                        #              )

                        def on_click_user_settings():
                            setattr(user_settings_dialog, 'user', user_manager.users[app.storage.user['username']])
                            user_settings_dialog.open()

                        ui.menu_item('User Settings',
                                     on_click=on_click_user_settings
                                     )

                        def add_toolbox():
                            setattr(add_toolbox_dialog, 'user', user_manager.users[app.storage.user['username']])
                            add_toolbox_dialog.open()

                        ui.menu_item('Add Toolbox',
                                     on_click=add_toolbox
                                     )

                        ui.menu_item('Reload Project',
                                     on_click=lambda: user_manager.users[app.storage.user['username']].
                                     project_manager.open_data_model()
                                     )
                        ui.menu_item('Save Project',
                                     on_click=lambda: (user_manager.users[app.storage.user['username']].data_model.save(),
                                                       ui.notify('Project saved!'))
                                     )
                        ui.menu_item('Close Project',
                                     on_click=lambda: user_manager.users[app.storage.user['username']].
                                     project_manager.close_data_model()
                                     )
                        ui.menu_item('Logout',
                                     on_click=lambda: (user_manager.users[app.storage.user['username']].logout(),
                                                       app.storage.user.clear(),
                                                       ui.navigate.to('/login')))

                        ui.separator()
                        ui.menu_item('Close', menu.close)

    with ui.tab_panels(tabs, value='Home').classes('w-full h-full'):
        with ui.tab_panel('Project').classes('w-full h-full') as project_full_tab:
            with ui.splitter(value=60, limits=(10, 90)).classes('w-full h-full') as splitter:
                with splitter.before as project_tab:
                    context.client.content.classes('h-[92vh]')
                    user.project_tab = project_tab
                with splitter.after:
                    user.detail_view = ui.row().classes('w-full h-full')

        user.home_tab = ui.tab_panel('Home').classes('w-full h-full')

        with ui.tab_panel('Logs').classes('w-full h-full'):
            with ui.card().classes('w-full h-full') as logs_tab:
                user.log_tab = logs_tab

        with ui.tab_panel('Tasks').classes('w-full h-full') as tasks_tab:
            user.task_tab = tasks_tab
            user.task_manager.ui_content()

    with user.home_tab:
        home.content()
