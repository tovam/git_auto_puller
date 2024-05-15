import subprocess, ssl
import http.server
import socketserver
import os
import time
import re
import sys

REPO_URL = sys.argv[1]
REPO_PATH = sys.argv[2]
BRANCH = sys.argv[3]

CHECK_INTERVAL = 60 * 1
PORT = 8001

def git_pull():
    try:
        # Change directory to the repository
        os.chdir(REPO_PATH)

        # Fetch the latest changes from the origin without applying them
        subprocess.run(['git', 'fetch'], check=True)

        # Check if there are updates to be applied
        status_result = subprocess.run(['git', 'status', '-uno'], capture_output=True, text=True)
        if 'Your branch is behind' in status_result.stdout:
            print("Updates found. Pulling new changes...")
            # Pull the latest changes
            subprocess.run(['git', 'pull'], check=True)
            print("Repository updated.")
        else:
            #print("No updates found.")
            pass
    except subprocess.CalledProcessError as e:
        print(f"Error updating the repository: {e}")

def run_server():
    class CustomHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            # Normalize the path
            path = super().translate_path(path)
            if path == REPO_PATH+"/":
                path = REPO_PATH+"/index.html"

            # Define allowed file and directory patterns
            allowed = [
                re.compile(rf'^{REPO_PATH}/img/[^/]*$'),
                re.compile(rf'^{REPO_PATH}/js/[^/]*$'),
                re.compile(rf'^{REPO_PATH}/.*\.html$'),
                re.compile(rf'^{REPO_PATH}/.*\.css$')
            ]
            # Check if the path is allowed
            if any(pat.match(path) for pat in allowed):
                return path
            else:
                # Path not allowed, return a non-existing path
                return os.path.join(REPO_PATH, 'does_not_exist')

    httpd = socketserver.TCPServer(("", PORT), CustomHttpRequestHandler)
#    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile="key.pem", certfile="cert.pem", server_side=True)
    print(f"Serving HTTP at port {PORT}")
    httpd.serve_forever()

def setup_repository(repo_path, repo_url, branch):
    if not os.path.exists(repo_path):
        print("Repository folder not found. Cloning repository...")
        try:
            # Attempt to clone the repository to the specified path
            subprocess.run(['git', 'clone', '--branch', branch, repo_url, repo_path], check=True)
            print("Repository successfully cloned.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning the repository: {e}")
            exit(1)
    else:
        print("Repository folder already exists.")

def main():
    # Ensure the repository is set up
    setup_repository(REPO_PATH, REPO_URL, BRANCH)

    # Run the HTTP server in a separate thread
    from threading import Thread
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    try:
        while True:
            #print("Checking for updates...")
            git_pull()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Script stopped by user.")

if __name__ == '__main__':
    main()
