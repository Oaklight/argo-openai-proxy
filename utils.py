def make_bar(message: str = "", bar_length=64) -> str:
    message = " " + message.strip() + " "
    dash_length = (bar_length - len(message)) // 2
    message = "-" * dash_length + message + "-" * dash_length
    return message
