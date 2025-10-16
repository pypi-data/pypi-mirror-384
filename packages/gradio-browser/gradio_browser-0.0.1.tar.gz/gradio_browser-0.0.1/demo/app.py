import gradio as gr
from gradio_browser import Browser

with gr.Blocks() as demo:
    browser = Browser(value="https://example.com", show_hostname=True)
    browser.change(lambda x: x, browser, browser)


if __name__ == "__main__":
    demo.launch()
