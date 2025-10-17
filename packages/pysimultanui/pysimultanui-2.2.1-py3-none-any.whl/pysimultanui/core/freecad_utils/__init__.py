import os
import sys
import subprocess
import platform

from logging import getLogger

logger = getLogger('py_simultan_ui')


def find_freecad_path_registry():

    import winreg

    try:
        # Open the registry key
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                try:
                    # Check for a display name entry in the subkey
                    name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                    # Check if it's FreeCAD
                    if "FreeCAD" in name:
                        # Get the installation path
                        path, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
                        return os.path.dirname(path)
                except FileNotFoundError:
                    pass
                finally:
                    subkey.Close()
                i += 1
            except WindowsError:
                break
    except Exception as e:
        return
    return


def find_freecad_path():
    try:
        logger.info('Searching for FreeCAD executable')

        # Use the 'where' command to find FreeCAD executable
        result = subprocess.run("where /R C:\ freecad.exe", capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            # Successful, extract the path
            paths = result.stdout.split('\n')
            # Usually the first result is the most relevant one
            return os.path.dirname(paths[0]) if paths else None
        else:
            return
    except Exception as e:
        logger.error(f'Could not find FreeCAD executable')
        return


if platform.system() == 'Windows':

    FREECADPATH = os.environ.get('FREECADPATH', None)
    if FREECADPATH is None:
        if os.path.isdir(r'C:\Program Files'):
            if 'FreeCAD' in os.listdir(r'C:\Program Files'):
                freecad_versions = os.listdir(r'C:\Program Files\FreeCAD')
                freecad_versions.sort(reverse=True)
                FREECADPATH = os.path.join(r'C:\Program Files\FreeCAD', freecad_versions[0], 'bin')
        if os.path.isdir(r'D:\Program Files'):
            if 'FreeCAD' in os.listdir(r'D:\Program Files'):
                freecad_versions = os.listdir(r'D:\Program Files\FreeCAD')
                freecad_versions.sort(reverse=True)
                FREECADPATH = os.path.join(r'D:\Program Files\FreeCAD', freecad_versions[0], 'bin')

                sys.path.append(os.path.join(r'D:\Program Files\FreeCAD', freecad_versions[0]))

    if FREECADPATH is None:
        FREECADPATH = find_freecad_path_registry()
    if FREECADPATH is None:
        FREECADPATH = find_freecad_path()

    if FREECADPATH is not None:
        sys.path.append(FREECADPATH)
