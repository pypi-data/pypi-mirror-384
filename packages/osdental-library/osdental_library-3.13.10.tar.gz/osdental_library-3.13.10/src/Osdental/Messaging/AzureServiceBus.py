import json
import datetime
from typing import List, Dict, Any
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import AutoLockRenewer
from Osdental.Messaging import IMessageQueue
from Osdental.Shared.Logger import logger
from Osdental.Shared.Enums.Message import Message

class AzureServiceBusQueue(IMessageQueue):

    def __init__(self, conn_str:str, queue_name:str):
        self.conn_str = conn_str
        self.queue_name = queue_name

    async def enqueue(self, message: Dict[str, Any] | str) -> None:
        try:
            data = json.dumps(message) if isinstance(message, dict) else message
            async with ServiceBusClient.from_connection_string(self.conn_str) as servicebus_client:
                async with servicebus_client.get_queue_sender(queue_name=self.queue_name) as sender:
                    message = ServiceBusMessage(data)
                    await sender.send_messages(message)

        except Exception as e:
            logger.error(f'Unexpected Service Bus enqueue error: {str(e)}')
            raise ValueError(f'{Message.UNEXPECTED_ERROR_MSG}: {str(e)}')

    async def dequeue(self, max_messages: int = 1) -> List[Any]:
        results = []
        try:
            async with ServiceBusClient.from_connection_string(self.conn_str) as servicebus_client:
                async with servicebus_client.get_queue_receiver(queue_name=self.queue_name, max_wait_time=5) as receiver:
                    async with receiver, AutoLockRenewer() as renewer:
                        renewer.register(receiver, msg, max_lock_renewal_duration=datetime.timedelta(minutes=5))
                        received_msgs = await receiver.receive_messages(max_message_count=max_messages)
                        for msg in received_msgs:
                            body = str(msg)
                            try:
                                body = json.loads(body)
                            except json.JSONDecodeError:
                                pass
                            results.append(body)
                            await receiver.complete_message(msg)
        except Exception as e:
            logger.error(f'Unexpected Service Bus dequeue error: {str(e)}')
            raise ValueError(f'{Message.UNEXPECTED_ERROR_MSG}: {str(e)}')

        return results
    

    async def dequeue(self, max_messages: int = 1) -> List[Any]:
        results = []
        try:
            async with ServiceBusClient.from_connection_string(self.conn_str) as servicebus_client:
                async with servicebus_client.get_queue_receiver(queue_name=self.queue_name, max_wait_time=5) as receiver:
                    
                    received_msgs = await receiver.receive_messages(max_message_count=max_messages)
                    if not received_msgs:
                        return []

                    # Create AutoLockRenewer
                    async with AutoLockRenewer() as renewer:
                        for msg in received_msgs:
                            # Record each message received
                            renewer.register(receiver, msg, max_lock_renewal_duration=datetime.timedelta(minutes=5))

                        # Process each message
                        for msg in received_msgs:
                            body = str(msg)
                            try:
                                body = json.loads(body)
                            except json.JSONDecodeError:
                                pass
                            results.append(body)

                            # Mark the message as completed
                            await receiver.complete_message(msg)

        except Exception as e:
            logger.error(f'Unexpected Service Bus dequeue error: {str(e)}')
            raise ValueError(f'{Message.UNEXPECTED_ERROR_MSG}: {str(e)}')

        return results
