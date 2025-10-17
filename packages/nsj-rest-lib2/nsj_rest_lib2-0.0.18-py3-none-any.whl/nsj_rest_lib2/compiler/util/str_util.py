class CompilerStrUtil:
    @staticmethod
    def to_camel_case(snake_str: str) -> str:
        """Converte uma string de snake_case para camelCase."""
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    @staticmethod
    def to_pascal_case(snake_str: str) -> str:
        """Converte uma string de snake_case para PascalCase."""
        components = snake_str.split("_")
        return "".join(x.title() for x in components)

    @staticmethod
    def to_snake_case(camel_str: str) -> str:
        """Converte uma string de camelCase ou PascalCase para snake_case."""
        snake_str = ""
        for i, char in enumerate(camel_str):
            if char.isupper() and i != 0:
                snake_str += "_"
            snake_str += char.lower()
        return snake_str
