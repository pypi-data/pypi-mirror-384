import webbrowser
import requests


LAUNCH_SERVER_MSG_TEMPLATE = """
The Visual Layer application was launched on your machine, you can find it on {} in your web browser.
Use Ctrl + C to stop the application server.

For more information, use help(fastdup) or check our documentation https://docs.visual-layer.com/docs/getting-started-with-fastdup."""


def wait_until_server_running(port: int) -> None:
    server_running = False
    while not server_running:
        try:
            ret = requests.get(f'http://localhost:{port}/api/v1/healthcheck')
            if ret.status_code == 200:
                server_running = True
        except requests.exceptions.ConnectionError:
            pass


def check_server_running_for_dataset_id(dataset_id: str, port: int) -> None:
    wait_until_server_running(port)
    start_address = f"http://localhost:{port}/dataset/{dataset_id}/data?page=1"
    print(LAUNCH_SERVER_MSG_TEMPLATE.format(start_address))
    webbrowser.open(start_address)
