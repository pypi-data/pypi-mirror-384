import os
import asyncio
from copy import deepcopy
from ..core import mapper
from logging import getLogger
from typing import Optional, Type
from datetime import datetime
from nicegui import app, ui, events
from PySimultan2.data_model import DataModel
from PySimultan2.object_mapper import PythonMapper

from .. import user_manager
from ..core.user import UserManager, User
from ..views.view_manager import ViewManager
from ..views.asset_view import AssetManager
from ..views.geometry_view import GeometryManager
from ..core.navigation import Navigation
# from ..views.geometry_view.geometry_file_manager import GeometryFileManager
# from ..views.asset_view.asset_manager import AssetManager

from ..app.project import content as project_content

import shutil


logger = getLogger('py_simultan_ui')


project_dir = os.environ.get('PROJECT_DIR', '/simultan_projects')
if not os.path.exists(project_dir):
    os.makedirs(project_dir)

app.add_static_files('/project', project_dir)


class NewProjectDialog(object):

    def __init__(self, *args, **kwargs):
        self.dialog = None
        self.parent = kwargs.get('parent', None)

    def validate_project_name(self, project_name):
        if not self.dialog.project_name_input.value.endswith('.simultan'):
            return "Project name must end with '.simultan'!"

    def ui_content(self):
        with ui.dialog() as dialog, ui.card():
            self.dialog = dialog
            with ui.row():
                project_name_input = ui.input('Project name',
                                              #validation=self.validate_project_name
                                              )
                ui.label('.simultan')

            user_name_input = ui.input('User name',
                                       value='admin',
                                       # validation=self.validate_project_name
                                       )
            password_input = ui.input('Password',
                                      value='admin',
                                      # validation=self.validate_project_name
                                      )

            dialog.project_name_input = project_name_input
            dialog.user_name_input = user_name_input
            dialog.password_input = password_input

            with ui.row():
                create_btn = ui.button('Create', on_click=self.new_project)
                ui.button('Cancel', on_click=dialog.close)

    def new_project(self, e: events.ClickEventArguments):
        self.dialog.close()

        project_path = f'{project_dir}/{self.dialog.project_name_input.value}.simultan'
        data_model = DataModel.create_new_project(project_path=project_path,
                                                  user_name=self.dialog.user_name_input.value,
                                                  password=self.dialog.password_input.value)
        data_model.save()
        data_model.cleanup()
        if isinstance(data_model, DataModel):
            ui.notify(f'Project {self.dialog.project_name_input.value} created!')
            self.parent.project_list.ui_content.refresh()
        else:
            ui.notify(f'Error creating project {self.dialog.project_name_input.value}!')


class ProjectView(object):

    def __init__(self, *args, **kwargs):

        self._selected: bool = False

        self.parent: Optional[ProjectList] = kwargs.get('parent', None)
        self.project: Optional[str] = kwargs.get('project', None)
        self.project_manager: Optional[ProjectManager] = kwargs.get('project_manager', None)

        self.checkbox: Optional[ui.checkbox] = None
        self.card: Optional[ui.item] = None

        self.selected = kwargs.get('selected', False)

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        self._selected = value
        self.ui_content.refresh()

    @property
    def size(self):
        return os.path.getsize(f'{project_dir}/{self.project}')

    @property
    def last_modified(self):
        return datetime.fromtimestamp(os.path.getmtime(f'{project_dir}/{self.project}'))

    @property
    def path(self):
        return f'{project_dir}/{self.project}'

    @property
    def project_dict(self):
        return {'size': self.size,
                'last_modified': self.last_modified,
                'path': self.path,
                'project': self.project,
                }

    @ui.refreshable
    def ui_content(self):
        with ui.item() as self.card:
            with ui.item_section():
                ui.label(self.project).classes('text-xl')
            with ui.item_section():
                if self.size < 1024:
                    ui.label(f'Size: {self.size:.2f} B')
                elif self.size < 1024 ** 2:
                    ui.label(f'Size: {self.size / 1024:.2f} kB')
                else:
                    ui.label(f'Size: {self.size / 1024 ** 2:.2f} MB')
            with ui.item_section():
                ui.label(f'Last modified: {self.last_modified}')

            if self.project.endswith('.simultan') and not self.project.startswith('~'):
                if self.selected:
                    with ui.item_section():
                        self.card.classes('bg-blue-5')
                        sel_button = ui.button('Close',
                                               icon='close',
                                               on_click=self.parent.close_project).classes('q-ml-auto')
                        sel_button.project = self
                        sel_button.project_item = self.card
                    with ui.item_section():
                        save_button = ui.button('Save',
                                                icon='save',
                                                on_click=self.parent.save_project).classes('q-ml-auto')
                        save_button.project = self

                else:
                    with ui.item_section():
                        sel_button = ui.button('Open',
                                               icon='file_open',
                                               on_click=self.parent.select_project).classes('q-ml-auto')
                        sel_button.project = self
                        sel_button.project_item = self.card
                    with ui.item_section():
                        dl_button = ui.button(icon='download',
                                              on_click=self.parent.download_project).classes('q-ml-auto')
                        dl_button.project = self

                    with ui.item_section():
                        del_button = ui.button(icon='delete',
                                               on_click=self.parent.delete_project).classes('q-ml-auto')
                        del_button.project = self
            else:
                with ui.item_section():
                    pass
                with ui.item_section():
                    dl_button = ui.button(icon='download',
                                          on_click=self.download_project).classes('q-ml-auto')
                    dl_button.project = self.project_dict
                with ui.item_section():
                    del_button = ui.button(icon='delete',
                                           on_click=self.parent.delete_project).classes('q-ml-auto')
                    del_button.project = self

    def download_project(self, e: events.ClickEventArguments):
        ui.download(f'project/{self.project}')


class ProjectList(object):

    def __init__(self, *args, **kwargs):
        self._projects = None
        self.selected_project = kwargs.get('selected_project', None)
        self.project_manager = kwargs.get('project_manager', None)
        self.project_views = kwargs.get('project_views', {})

        self.file_list = None

    @property
    def projects(self):
        if self._projects is None:
            self.projects = self.refresh_projects()
        return self._projects

    @projects.setter
    def projects(self, value):

        old_set = set(self._projects) if self._projects is not None else set()
        new_set = set(value) if value is not None else set()
        self._projects = value

        common_projects = old_set.intersection(new_set)
        new_projects = new_set.difference(common_projects)
        removed_projects = old_set.difference(common_projects)

        for project in new_projects:
            self.add_project_to_view(project)

        for project in removed_projects:
            if project in self.project_views:
                self.project_views[project].card.parent_slot.parent.remove(self.project_views[project].card)

    def refresh_projects(self):
        return os.listdir(project_dir)

    @property
    def selected_project(self):
        return app.storage.user['selected_project']

    @selected_project.setter
    def selected_project(self, value):
        app.storage.user['selected_project'] = value

    @ui.refreshable
    def ui_content(self):
        self.project_views = {}
        ui.label('Files:').classes('text-2xl')
        with ui.list().classes('w-full h-full') as self.file_list:
            for project in os.listdir(project_dir):
                project_view = ProjectView(project=project,
                                           selected=project == self.selected_project,
                                           project_manager=self.project_manager,
                                           parent=self)
                self.project_views[project] = project_view
                project_view.ui_content()

    def add_project_to_view(self, project: str):
        if project not in self.project_views:
            project_view = ProjectView(project=project,
                                       selected=project == self.selected_project,
                                       project_manager=self.project_manager,
                                       parent=self)
            self.project_views[project] = project_view
            with self.file_list:
                project_view.ui_content()

    async def select_project(self, e: events.ClickEventArguments):
        self.selected_project = e.sender.project.project
        if self.project_manager is not None:
            await self.project_manager.open_project(e)
        self.projects = self.refresh_projects()

    def close_project(self, e: events.ClickEventArguments):
        self.selected_project = None
        self.project_manager.close_project(e)
        self.projects = self.refresh_projects()

    def delete_project(self, e: events.ClickEventArguments):
        if os.path.isfile(e.sender.project.path):
            file = e.sender.project.path
            os.remove(file)
            ui.notify(f"Project {e.sender.project.project} deleted!")
            self.ui_content.refresh()
        elif os.path.isdir(e.sender.project.path):
            shutil.rmtree(e.sender.project.path)
            ui.notify(f"Project {e.sender.project.project} deleted!")
            self.ui_content.refresh()

    def save_project(self, e: events.ClickEventArguments):
        if self.project_manager.data_model is not None:
            self.project_manager.data_model.save()
            ui.notify(f"Project {e.sender.project.project} saved!")
        else:
            ui.notify(f"Project {e.sender.project.project} not saved! No project loaded!")

    def download_project(self, e: events.ClickEventArguments):
        ui.download(f'project/{e.sender.project.project}')


class ProjectManager(object):
    def __init__(self, *args, **kwargs):

        self.user_manager: UserManager = kwargs.get('user_manager', user_manager)
        self._projects = None
        self.project_list = None
        self.mapped_data = None

        if kwargs.get('data_model', None) is not None:
            self.data_model = kwargs.get('data_model', None)

    @property
    def mapper(self) -> PythonMapper:
        return self.user.mapper

    @mapper.setter
    def mapper(self, value: PythonMapper):
        self.user.mapper = value

    @property
    def grid_view(self):
        return self.user.grid_view

    @property
    def view_manager(self) -> ViewManager:
        return self.user.view_manager

    @property
    def task_manager(self):
        return self.user.task_manager

    @property
    def asset_manager(self) -> AssetManager:
        return self.user.asset_manager

    @property
    def geometry_manager(self) -> GeometryManager:
        return self.user.geometry_manager

    @property
    def array_manager(self):
        return self.user.array_manager

    @property
    def navigation(self) -> Navigation:
        return self.user.navigation

    @property
    def detail_view(self):
        return self.user.detail_view

    @property
    def home_tab(self):
        return self.user.home_tab

    @property
    def project_tab(self):
        return self.user.project_tab

    @property
    def user(self) -> User:
        return self.user_manager.users[app.storage.user['username']]

    @property
    def logger(self):
        return self.user.logger

    @property
    def data_model(self) -> Optional[DataModel]:
        return self.user.data_model

    @data_model.setter
    def data_model(self, value: Optional[DataModel]):
        logger.debug(f'Setting data model to {value}')
        self.user.data_model = value
        if self.user.data_model is not None:
            app.add_static_files('/assets', self.user.data_model.project.ProjectUnpackFolder.FullPath)

        for item in [self.view_manager,
                     self.asset_manager,
                     self.geometry_manager,
                     self.grid_view,
                     self.array_manager]:
            if item is not None:
                item.data_model = self.user.data_model

    @property
    def projects(self):
        # get list of files in project_dir
        self._projects = os.listdir(project_dir)
        return self._projects

    @property
    def selected_project(self):
        return self.project_list.selected_project

    def upload_project(self,
                       e: events.UploadEventArguments,
                       *args,
                       **kwargs):

        shutil.copyfileobj(e.content, open(f'{project_dir}/{e.name}', 'wb'))
        ui.notify(f'Project {e.name} uploaded!')
        self.project_list.ui_content.refresh()

    def refresh_all_items(self, *args, **kwargs):
        # self.view_manager.refresh_all_items()
        self.grid_view.ui_content.refresh()
        self.asset_manager.update_items_views()
        self.geometry_manager.update_items_views()
        # self.navigation.ui_content.refresh()

    def ui_content(self):

        self.user.add_ui_log()

        with self.project_tab:
            with ui.tabs() as tabs:
                ui.tab('Components', icon='category', label='')
                ui.tab('Assets', icon='description', label='')
                ui.tab('Geometry', icon='shape_line', label='')
                ui.tab('Arrays', icon='data_array', label='')

            with ui.tab_panels(tabs, value='Components').classes('w-full h-full').props('vertical'):
                with ui.tab_panel('Components').classes('w-full h-full'):
                    self.grid_view.ui_content()
                # self.view_manager.ui_content()
                with ui.tab_panel('Assets').classes('w-full h-full'):
                    self.asset_manager.ui_content()
                with ui.tab_panel('Geometry').classes('w-full h-full'):
                    self.geometry_manager.ui_content()

                with ui.tab_panel('Arrays').classes('w-full h-full'):
                    self.array_manager.ui_content()

            # self.navigation.ui_content()

        if self.data_model is None:
            selected = None
        else:
            selected = os.path.basename(self.data_model.project.ProjectFile.FullPath)

        self.project_list = ProjectList(project_manager=self,
                                        selected_project=selected
                                        )
        self.project_list.ui_content()

        new_project_dialog = NewProjectDialog(parent=self)
        new_project_dialog.ui_content()

        ui.button('New project', on_click=new_project_dialog.dialog.open).classes('max-w-full')

        ui.upload(label='Upload simultan project',
                  on_upload=self.upload_project).on(
            'finish', lambda: ui.notify('Finish!')
        ).classes('max-w-full')

    async def open_project(self, e: events.ClickEventArguments = None, *args, **kwargs):

        if e is not None:
            project = e.sender.project
        else:
            project = kwargs.get('project', None)

        # dialog to ask username and password and if to load all data
        with ui.dialog() as dialog, ui.card():

            ui.label(f'Open project: {project.project}')

            with ui.row():
                user_input = ui.input('User name', value='admin')
                pw_input = ui.input('Password', value='admin', password=True)

            open_all = ui.checkbox('Load all data', value=True)

            with ui.row():
                ui.button('OK', on_click=lambda: dialog.submit({'ok': True,
                                                                 'user': user_input.value,
                                                                 'pw': pw_input.value,
                                                                 'open_all': open_all.value}
                                                                )
                          )
                ui.button('Cancel', on_click=lambda: dialog.submit({'ok': False}))

        result = await dialog

        self.user.logger.info(f'Opening project {project.project}')

        if result is None or not result.get('ok', False):
            return

        self.mapper = self.user.mapper
        self.mapper.clear()

        logger.info(f'Opening project {project.project}')

        n = ui.notification(timeout=None)
        n.spinner = True
        n.message = f'Opening project {project.project}'

        project_dict = project.project_dict
        new_data_model = DataModel(project_path=project_dict['path'],
                                   user_name=result['user'],
                                   password=result['pw'])
        self.mapped_data = new_data_model.get_typed_data(self.mapper, create_all=True if result['open_all'] else False)
        self.data_model = new_data_model
        project.selected = True
        self.project_list.ui_content.refresh()
        n.message = f'Project {project.project} opened!'
        n.spinner = False
        n.dismiss()

    def open_data_model(self,
                        data_model: DataModel = None,
                        create_all: bool = True):
        self.mapper.clear()
        if data_model is None:
            data_model = self.data_model

        if data_model is not None:
            self.mapped_data = data_model.get_typed_data(self.mapper,
                                                         create_all=create_all)
        self.data_model = data_model

        ui.notify('Data model loaded!')

    def close_project(self, e):

        from ..views.detail_views import show_detail

        self.logger.info(f'Closing project {os.path.basename(self.data_model.project.ProjectFile.FullPath)}')

        if self.data_model is not None:
            self.data_model.cleanup()
        self.mapper.clear()
        self.mapped_data = []
        self.data_model = None
        ui.notify('Project closed!')
        self.project_list.ui_content.refresh()
        e.sender.project.selected = False
        self.project_list.ui_content.refresh()
        show_detail(None)

        # self.geometry_file_manager.geometry_models = []
        # project_content.refresh()
