import multiprocessing
import subprocess

def run_fastapi():
    subprocess.run(["python", "web_app.py"])

def run_streamlit():
    subprocess.run(["streamlit", "run", "streamlit_app.py"])

if __name__ == "__main__":
    fastapi_process = multiprocessing.Process(target=run_fastapi)
    streamlit_process = multiprocessing.Process(target=run_streamlit)

    fastapi_process.start()
    streamlit_process.start()

    fastapi_process.join()
    streamlit_process.join()