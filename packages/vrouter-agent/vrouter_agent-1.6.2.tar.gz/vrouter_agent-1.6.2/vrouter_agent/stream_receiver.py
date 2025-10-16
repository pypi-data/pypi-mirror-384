
def stream_receiver(stream, txid, *args, **kwargs):
    """
    Receives data from a stream and processes it using the provided callback function.
    
    :param stream: The stream to read data from.
    :param callback: The function to call with the received data.
    :param args: Additional positional arguments to pass to the callback.
    :param kwargs: Additional keyword arguments to pass to the callback.
    """
    from vrouter_agent.stream_handler import StreamHandler

    handler = StreamHandler(stream, txid)
    handler.start()

    try:
        while True:
            data = handler.read_data()
            if data is None:
                break
            handler.process_data(data, *args, **kwargs)
    except Exception as e:
        handler.handle_error(e)
    finally:
        handler.cleanup()
#     logger.info("Stream receiver started")
    