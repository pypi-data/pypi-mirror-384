import os
import sys
import asyncio
import uvicorn
from .fastapi_app import fastapi_app
from nicegui import app as ng_app, ui, Client
from . import user_manager
from .views.asset_view.asset_manager import AssetManager


from .app.theme import frame

from .app.auth import AuthMiddleware
from .app import login

unrestricted_page_routes = {'/login'}


# ui.add_head_html("<style>" + open(Path(__file__).parent / "static_files" / "styles.css").read() + "</style>")


@ui.page('/')
def index_page(client: Client) -> None:
    frame('Home')
    login.content()
    # with frame('Home'):
    #     home.content()


@ui.page('/login')
def index_page1() -> None:
    # frame('Home')
    # with frame('Home'):
    #     pass
    login.content()



@ui.page('/component/{global_id}/{local_id}')
def component_page(client: Client, global_id: str, local_id:str) -> None:
    username = ng_app.storage.user.get('username', None)
    if username is None:
        ui.navigate.to('/login')
        return

    with ui.element().classes('w-full h-full') as element:

        from .views.detail_views import show_detail_for_component_id
        show_detail_for_component_id(global_id,
                                     local_id,
                                     detail_view_space=element,)


@ui.page('/assets')
def assets_page(client: Client) -> None:
    username = ng_app.storage.user.get('username', None)
    if username is None:
        ui.navigate.to('/login')
        return

    user = user_manager.users[username]
    asset_manager = AssetManager(data_model=user.data_model)

    with ui.element().classes('w-full h-full') as element:

        with ui.splitter().classes('w-full h-full') as splitter:
            with splitter.after as right:
                element = ui.element().classes('w-full h-full')

                def show_detail(*args, **kwargs):
                    from .views.detail_views import show_detail
                    show_detail(detail_view_space=element,
                                value=asset_manager.selected_file_info,
                                )
            with splitter.before as left:
                asset_manager.ui_content(show_detail_fcn=show_detail)





@ui.page('/project')
def index_page2(client: Client) -> None:
    # frame('Home')
    # with frame('Home'):
    #     pass

    user = user_manager.users[ng_app.storage.user['username']]
    log_handler = user.ui_log.handler
    logger = user.logger

    def connected():
        # Add log event handler
        pass

    def disconnected():
        # Remove log event handler
        user.logger.removeHandler(log_handler)

    def clear_log():
        logger.debug(f'Client cleared local event log with id: {client.id}')
        user.ui_log.log.clear()

    client.on_connect(connected)
    client.on_disconnect(disconnected)

    frame('Project')

# def on_startup():
#
#
#
# ng_app.on_startup(on_startup)


# app.on_shutdown(handle_shutdown)
def run_ui(*args, **kwargs):
    ng_app.add_middleware(AuthMiddleware)
    storage_secret = kwargs.get('storage_secret', os.environ.get('STORAGE_SECRET', 'my_secret6849'))

    ui.run_with(
        app=fastapi_app,
        title = kwargs.get('title', 'Py Simultan'),
        mount_path = '/ui',
        dark = kwargs.get('dark', False),
        storage_secret = storage_secret,
        reconnect_timeout = 20,
        binding_refresh_interval = 0.2,
    )

    # set_storage_secret(storage_secret)
    # ui.run(storage_secret=storage_secret,
    #        title=kwargs.get('title', 'Py Simultan'),
    #        dark=kwargs.get('dark', False),
    #        reload=kwargs.get('reload', False),
    #        port=kwargs.get('port', 8080),
    #        uvicorn_logging_level=kwargs.get('uvicorn_logging_level', 'info'),
    #        )
    # set_storage_secret(storage_secret)

    from .core.patch_default_models import patch
    from . import user_manager
    patch(user_manager)

    if sys.platform in ('win32', 'cygwin', 'cli'):
        import winloop
        # winloop.install()
    else:
        # if we're on apple or linux do this instead
        from uvloop import run

    uvicorn.run(fastapi_app,
                host=kwargs.get('host', '0.0.0.0'),
                port=kwargs.get('port', os.environ.get('PORT', 8080)),
                reload=kwargs.get('reload', False),
                log_level=kwargs.get('uvicorn_logging_level', 'info'),
                )

    asyncio.get_event_loop()

    # loop = asyncio.get_event_loop()
    # config = uvicorn.Config(app=fastapi_app,
    #                         host=kwargs.get('host', '0.0.0.0'),
    #                         port=kwargs.get('port', os.environ.get('PORT', 8080)),
    #                         reload=kwargs.get('reload', False),
    #                         log_level=kwargs.get('uvicorn_logging_level', 'info'),
    #                         loop=loop)
    # server = uvicorn.Server(config)
    # asyncio.run(server.serve())



    print('done')

if __name__ in {"__main__", "__mp_main__"}:
    run_ui(reload=False)
