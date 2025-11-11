from noton.Module import Module


class TextInput(Module):
    def __init__(self ) -> None:
        super().__init__()

    def forward(self, text:str) -> str:
        return text


# TODO: StreamlitTextInput



# more to do: check, option, value, files, images, videos