import gradio as gr
from gradio_browser import Browser

with gr.Blocks(title="Browser Component Demo", fill_height=True) as demo:
    gr.Markdown("# 🌐 Custom Browser Component")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Controls")
            url_input = gr.Textbox(
                label="Enter URL",
                value="https://www.gradio.app/",
                placeholder="https://www.gradio.app/",
            )

            show_hostname = gr.Checkbox(
                label="Show full hostname in address bar", value=True
            )

            gr.Markdown(
                """
            ### Features:
            - ← → Navigation buttons with history
            - ↻ Refresh button  
            - ↗ Open in new tab button
            - Address bar supports both full URLs and paths
            - Enter key navigation
            """
            )

            gr.Markdown("### Try these URLs:")

            gr.Button("Gradio.com").click(
                lambda: "https://www.gradio.app/", outputs=[url_input]
            )
            gr.Button("Example.com").click(
                lambda: "https://example.com", outputs=[url_input]
            )

        with gr.Column(scale=3):
            browser = Browser(
                url="https://example.com",
                show_hostname=True,
                min_height="600px",
                scale=1,
            )

    # Update browser when URL changes
    url_input.change(lambda url: url, inputs=[url_input], outputs=[browser])

    # Update show_hostname setting (requires component rebuild)
    show_hostname.change(
        lambda show_host, url: Browser(value=url, show_hostname=show_host),
        inputs=[show_hostname, url_input],
        outputs=[browser],
    )


if __name__ == "__main__":
    demo.launch()
