#!python
import random
import sys
import time

from ekfsm.lock import Locker


def use_shared_resource(myid: str):
    with open("shared_resource.txt", "w") as f:
        f.write(f"{myid}\n")
    time.sleep(random.random() * 1)  # Simulate some work with the shared resource
    # read the file
    with open("shared_resource.txt", "r") as f:
        data = f.read(len(myid))
        if data != myid:
            raise ValueError(f"file doesn't contain my id, but {data}")
        print("data ok")


def main():
    myid = sys.argv[1]
    print(f"myid is {myid}")

    lock = Locker("shared_resource.txt")

    for _ in range(5):
        with lock.lock():
            use_shared_resource(myid)
        time.sleep(0.5)

    sys.exit(0)


main()
