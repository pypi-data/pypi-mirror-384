from typing import Any, List, Dict, Text, Optional, Tuple, Union, Awaitable

class ConsumerSettings():
    def __init__(self,
                 environment:str,
                 group_name:str,
                 stream_name:str,
                 consumer_name:str,
                 deleteAfterAck:bool=True,
                 claim_after_seconds:int=60*30,  # 30 minutes
                 count:int=10,
                 max_inflight:int=20
                ) -> None:
        self.group_name:str = f"{environment}:{group_name}"
        self.stream_name:str = f"{environment}:{stream_name}"
        self.consumer_name:str = consumer_name
        self.deleteAfterAck:bool = deleteAfterAck
        self.claim_after_seconds:int = claim_after_seconds
        self.count:int = count
        self.max_inflight:int = max_inflight