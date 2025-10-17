from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel
import pyvisual as pv
from kivy.clock import Clock
import threading
import pyvisual as pv


class PvChatbot(Widget):
    def __init__(self, window, x=0, y=0, chatbot_width=750, chatbot_height=500, on_click=None,max_memory=10):
        super().__init__()
        self.window = window
        self.chatbot_width = chatbot_width
        self.chatbot_height = chatbot_height
        self.on_click = on_click
        self.max_memory = max_memory  # Maximum memory for chat history

        self.memory = {"user_prompts": [], "bot_responses": []}

        # Main chatbot container
        self.chatbot_container = pv.PvGroup(
            self.window, orientation="vertical", x=x, y=y, border_width=0, radius=20
        )

        # Chat container (scrollable)
        self.chat_container = pv.PvScroll(
            self.chatbot_container, orientation="vertical",
            width=self.chatbot_width, height=chatbot_height - 50, radius=0,
            padding=(20, 20, 0, 0), spacing=20, border_width=0
        )

        # Input prompt container
        self.prompt_container = pv.PvGroup(
            None, orientation="horizontal", border_width=0, spacing=30, padding=(0, 0, 0, 0)
        )
        self.input_text_prompt = pv.PvTextInput(
            None, width=self.chatbot_width - 200, border_style="top"
        )
        self.button = pv.PvButton(
            None, width=100, height=45, corner_radius=25,
            border_color=(0.7, 0.7, 0.7, 1), border_thickness=1.1,
            button_color=(1, 1, 1, 1), text="Ask",
            font_color=(0.7, 0.7, 0.7, 1), bold=True,
            on_click=lambda btn: (self.on_click(self) if self.on_click else None, self.ask_bot())
        )
        self.prompt_container.add_widget(self.input_text_prompt)
        self.prompt_container.add_widget(self.button)

        # Add the prompt container to the chatbot container
        self.chatbot_container.add_widget(self.prompt_container)

    def wrap_text(self, text, max_width):
        """
        Wrap the text into multiple lines based on the maximum width.

        Args:
            text (str): The text to wrap.
            max_width (int): The maximum width for a single line.

        Returns:
            str: A string with line breaks inserted where necessary.
        """
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if self.get_text_dimensions(test_line) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return "\n".join(lines)

    def add_user_prompt(self, text):
        max_width = self.chatbot_width - 100  # Available width for text
        wrapped_text = self.wrap_text(text, max_width)

        user_prompt_container = pv.PvGroup(
            self.chat_container, background_color=(0.9, 0.9, 0.9, 0.8),
            border_width=0, radius=20, orientation="horizontal",
            padding=(20, 10, 10, 10)
        )
        input_text_width = self.get_text_dimensions(wrapped_text) + 20
        pv.PvText(user_prompt_container, font_size=16, box_width=input_text_width, text=wrapped_text)
        self.memory["user_prompts"].append(text)

        # Add to memory and enforce max memory limit
        self.memory["user_prompts"].append(text)
        if len(self.memory["user_prompts"]) > self.max_memory:
            self.memory["user_prompts"].pop(0)

    def add_bot_prompt(self, text):
        max_width = self.chatbot_width - 150  # Available width for text
        wrapped_text = self.wrap_text(text, max_width)

        bot_prompt_container = pv.PvGroup(
            self.chat_container, background_color=(0.25, 0.878, 1, 0.8),
            border_width=0, radius=20, orientation="horizontal",
            padding=(20, 10, 10, 10)
        )
        bot_text_width = self.get_text_dimensions(wrapped_text) - 20
        pv.PvText(bot_prompt_container, font_size=16, box_width=bot_text_width, text=wrapped_text,multiline=True)
        self.memory["bot_responses"].append(text)

        # Add to memory and enforce max memory limit
        self.memory["bot_responses"].append(text)
        if len(self.memory["bot_responses"]) > self.max_memory:
            self.memory["bot_responses"].pop(0)

    def ask_bot(self):
        self.user_input = self.input_text_prompt.get_text()
        if self.user_input:
            # Add user input to the chat and memory
            self.add_user_prompt(self.user_input)

            # Clear the input field
            self.input_text_prompt.set_text("")
            self.show_typing_indicator()



    def show_typing_indicator(self):

        self.typing_indicator =pv.PvText(self.chat_container, font_size=16, text="  Bot is typing...",font_color=(0.7,0.7,0.7,0.8))
        # self.chat_container.add_widget(self.typing_indicator)

    def remove_typing_indicator(self):
        """Remove the typing indicator from the chat."""
        if self.typing_indicator:
            self.chat_container.remove_widget(self.typing_indicator)
            self.typing_indicator = None
    def schedule_default_function(self, func, delay=0):
        """
        Schedule a function to fetch data and display it as the bot's response.

        Args:
            func (callable): The function to fetch the response (should return a string).
            delay (float): Time in seconds after which the function should be executed.
        """

        def run_func(dt):
            try:
                # Remove typing indicator before adding the actual response
                self.remove_typing_indicator()
                response = func()
                self.add_bot_prompt(response)
            except Exception as e:
                self.add_bot_prompt(f"Error: {str(e)}")

            # Show typing indicator while waiting
        pv.PvTimer.schedule_once(run_func, delay)

    def get_memory_as_text(self):
        """
        Convert the chat memory into plain text format.

        Returns:
            str: The memory as plain text, alternating between user prompts and bot responses.
        """
        memory_text = []
        user_prompts = self.memory["user_prompts"]
        bot_responses = self.memory["bot_responses"]

        # Alternate between user prompts and bot responses
        for i in range(max(len(user_prompts), len(bot_responses))):
            if i < len(user_prompts):
                memory_text.append(f"User: {user_prompts[i]}")
            if i < len(bot_responses):
                memory_text.append(f"Bot: {bot_responses[i]}")

        return "\n".join(memory_text)
    def get_text_dimensions(self, text):
        label = CoreLabel(
            text=text,
            font_size=16,
            font_name="Roboto"
        )
        label.refresh()
        return label.texture.size[0]

    def get_chat_history(self):
        return self.memory


if __name__ == "__main__":
    import pyvisual as pv

    # Create the main window
    window = pv.PvWindow()

    # Initialize the chatbot
    chatbot = PvChatbot(window, x=50, y=50)

    print(chatbot.get_chat_history())

    # Show the window
    window.show()
