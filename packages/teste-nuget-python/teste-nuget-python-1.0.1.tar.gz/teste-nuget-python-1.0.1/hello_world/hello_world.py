class HelloWorld:

    def __init__(self, message: str = "Hello, World!", greeting: str = "Hi there!"):
        self.message = message
        self.greeting = greeting

    def say_hello(self):
        return self.message
    
    def greet(self):
        return self.greeting
    