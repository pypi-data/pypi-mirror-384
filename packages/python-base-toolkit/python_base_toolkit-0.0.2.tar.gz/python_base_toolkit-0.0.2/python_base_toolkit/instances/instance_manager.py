from custom_python_logger.logger import get_logger


class InstanceManager:
    def __init__(self) -> None:
        self.logger = get_logger(__class__.__name__)
        self._instances = []

    def add(self, instance: object) -> None:
        self._instances.append(instance)

    def close_all(self) -> None:
        for instance in reversed(self._instances):
            _instance_name = instance.__class__.__name__
            try:
                if hasattr(instance, "close"):
                    instance.close()
                else:  # hasattr(instance, '__exit__'):
                    instance.__exit__(None, None, None)
                self.logger.info(f"Instance: {_instance_name} closed successfully.")
            except Exception as e:
                self.logger.info(f"Failed to close instance {instance}: {e}")

    def __enter__(self) -> "InstanceManager":
        return self

    def __exit__(self, exc_type: type, exc_value: Exception, traceback: object) -> None:
        self.close_all()


def main() -> None:
    class SomeInstance:
        def __init__(self, add_to_instance_manager: bool = False) -> None:
            self.logger = get_logger(__class__.__name__)

            if add_to_instance_manager:
                instance_manager.add(self)  # pylint: disable=E0601

        @property
        def class_name(self) -> str:
            return self.__class__.__name__

        def __enter__(self) -> "SomeInstance":
            self.logger.info(f"Entering {self.class_name}")
            return self

        def __exit__(self, exc_type: type, exc_value: Exception, traceback: object) -> bool:
            self.logger.info(f"Exiting {self.class_name}")
            # Handle any cleanup here
            if exc_type:
                self.logger.info(f"Exception: {exc_value}")
            return True

    SomeInstance(add_to_instance_manager=True)

    resource1 = open("file1.txt", "w")  # pylint: disable=R1732
    resource2 = open("file2.txt", "w")  # pylint: disable=R1732

    instance_manager.add(resource1)
    instance_manager.add(resource2)

    # do stuff...

    instance_manager.close_all()  # or, if inside `with manager:`, it will happen automatically


if __name__ == "__main__":
    instance_manager = InstanceManager()

    main()
