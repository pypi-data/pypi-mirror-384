import argparse

from softioc import asyncio_dispatcher, builder, softioc

# Create an asyncio dispatcher, the event loop is now running
dispatcher = asyncio_dispatcher.AsyncioDispatcher()

# Set the record prefix
builder.SetDeviceName("simulated")

# Create records
AA = builder.aOut("A", initial_value=1.0)
BB = builder.aOut("B", initial_value=2.0)
CC = builder.aOut("C", initial_value=3.0)
DD = builder.aOut("D", initial_value=4.0)
EE = builder.aOut("E", initial_value=5.0)
FF = builder.aOut("F", initial_value=6.0)
GG = builder.aOut("G", initial_value=7.0)
HH = builder.aOut("H", initial_value=8.0)
II = builder.aOut("I", initial_value=9.0)
JJ = builder.aOut("J", initial_value=10.0)


# Get the IOC started
builder.LoadDatabase()
softioc.iocInit(dispatcher)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simulated IOC for testing save-and-restore service",
    )

    parser.add_argument(
        "--no-shell",
        dest="no_shell",
        action="store_true",
        help="Start the IOC without interactive shell (for running as a background process)",
    )

    args = parser.parse_args()
    if args.no_shell:
        softioc.non_interactive_ioc()
    else:
        softioc.interactive_ioc(globals())
