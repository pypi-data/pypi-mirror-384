import sys
try:
    from auto_etp.jarvis import main_new_window

    main_new_window()
except ModuleNotFoundError as ex:
    print(ex)
    print(f'Please run "{sys.executable} -m pybenjarvis.install" before attempting to run jarvis again')
