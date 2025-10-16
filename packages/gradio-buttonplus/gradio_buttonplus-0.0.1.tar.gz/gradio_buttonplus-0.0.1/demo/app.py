
import gradio as gr
from gradio_buttonplus import ButtonPlus


with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    gr.HTML("<h1><center>ButtonPlus Component Demo</center></h1>")
    with gr.Row():
        with gr.Column():
            btn = ButtonPlus("⚙️", help="This button triggers an action.")        
            btn_2 = ButtonPlus("Another Test", help="This is a demo test")
        


if __name__ == "__main__":
    demo.launch()
