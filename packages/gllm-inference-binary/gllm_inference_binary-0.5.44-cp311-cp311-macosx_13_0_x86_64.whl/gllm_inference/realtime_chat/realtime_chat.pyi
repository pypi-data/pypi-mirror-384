import abc
from abc import ABC, abstractmethod
from gllm_inference.realtime_chat.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer
from gllm_inference.realtime_chat.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer

class BaseRealtimeChat(ABC, metaclass=abc.ABCMeta):
    """[BETA] A base class for realtime chat modules.

    The `BaseRealtimeChat` class provides a framework for processing real-time conversations.
    """
    def __init__(self) -> None:
        """Initializes a new instance of the BaseRealtimeChat class."""
    @abstractmethod
    async def start(self, input_streamers: list[BaseInputStreamer] | None = None, output_streamers: list[BaseOutputStreamer] | None = None) -> None:
        """Starts the real-time conversation using the provided input and output streamers.

        This abstract method must be implemented by subclasses to define the logic
        for starting the real-time conversation.

        Args:
            input_streamers (list[BaseInputStreamer] | None, optional): The input streamers to use.
                Defaults to None.
            output_streamers (list[BaseOutputStreamer] | None, optional): The output streamers to use.
                Defaults to None.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
