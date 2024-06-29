import os
import shutil

from database.actions import add_session


async def import_sessions(session_folder: str, proxy_file: str) -> None:
    # Check if session folder exists
    if not os.path.exists(session_folder):
        print(f"Session folder '{session_folder}' does not exist.")
        return

    # Check if proxy file exists
    if not os.path.exists(proxy_file):
        print(f"Proxy file '{proxy_file}' does not exist.")
        return

    # Read proxies from file
    with open(proxy_file, 'r') as f:
        proxies = f.readlines()

    # Remove whitespace and empty lines from proxies list
    proxies = [proxy.strip() for proxy in proxies if proxy.strip()]


    for session_file in os.listdir(session_folder):
        if session_file.endswith('.session'):

            new_session_name = session_file.replace('_', '')  # убираем символ подчеркивания

            new_session_path = os.path.join('sessions', f"{new_session_name}")
            shutil.copyfile(os.path.join(session_folder, session_file), new_session_path)


            session_proxy = proxies.pop(0).strip() if proxies else None
            name, extension = os.path.splitext(new_session_name)
            await add_session(name, session_proxy)

            print(f"Session '{name}' imported with proxy '{session_proxy}'.")


            if session_proxy:
                with open(proxy_file, 'w') as f:
                    f.write('\n'.join(proxies))