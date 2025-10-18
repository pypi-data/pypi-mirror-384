import argparse
from datetime import datetime
from time import time
import numpy as NP
from . import loader


def parse_arguments():
    parser = argparse.ArgumentParser(description="This command line interface is work in progess!\nTODO script description!")
    parser.add_argument(
        "-v", "--verbosity", 
        action="count", 
        default=False,
        help="Print more information to stdout"
    )


    parser.add_argument(
        "device",
        type=str,
        help="Keyword for selecting the device. TODO unused yet!"
    )
    parser.add_argument(
        "root_path",
        type=str,
        help="The path of the directory containing the data files. Recursive search."
    )
    parser.add_argument(
        "start",
        type=lambda x: datetime.fromisoformat(x),
        help="Start timestamp in ISO format (YYYY-MM-DDTHH:MM:SS)."
    )
    parser.add_argument(
        "end",
        type=lambda x: datetime.fromisoformat(x),
        help="End timestamp in ISO format (YYYY-MM-DDTHH:MM:SS)."
    )
    parser.add_argument(
        "time_step",
        type=int,
        help="Time step as an integer."
    )
    parser.add_argument(
        "channel_start",
        type=int,
        help="Channel start as an integer."
    )
    parser.add_argument(
        "channel_end",
        type=int,
        help="Channel end as an integer."
    )
    parser.add_argument(
        "channel_step",
        type=int,
        help="Channel step as an integer."
    )
    parser.add_argument(
        "output",
        type=str,
        help="The path where to store the numpy file containing the data \"default\" or \"stdout\". "
            + "If \"default\" is given, the file name will be the \"<startime>.npy\". "
            + "If \"stdout\" is given, the data is piped to stdout as binary."
            + "TODO: stdout not implemented yet!"
    )

    return parser.parse_args()

def main():
    args = parse_arguments()
    if args.verbosity: print("Args:", args)


    if args.output == "default":
        fname = args.start.strftime("%Y%m%dT%H%M%S") + ".npy"
    elif args.output == "stdout":
        raise RuntimeError("Not implemented yet")
    else:
        fname = output


    print("Load...")
    start = time()
    loaderinstance = loader(args.root_path, args.device, num_worker_threads=1)
    data = loaderinstance.load_array(args.start, args.end, args.time_step,
            args.channel_start, args.channel_end, args.channel_step)
    if args.verbosity:
        end = time()
        print("Duration", end-start)
        print("Data:", NP.array(data.shape).prod() * 2.0 * 1000 / 1.0e6, "mb")
        print("Rate:", NP.array(data.shape).prod() * 2.0 * 1000 / 1.0e6 / (end-start), "mb/s")
        print("Saving...", fname)
    NP.save(fname, data)



if __name__ == "__main__":
    main()

