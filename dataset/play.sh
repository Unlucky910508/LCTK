#!/usr/bin/env bash
set -e

# Trap Ctrl-C (SIGINT) and terminate the entire script and all child processes
trap 'echo "Caught Ctrl-C, terminating all processes..."; kill 0; exit 130' INT

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

source /opt/ros/humble/setup.bash

cd "$script_dir"
log_file="$script_dir/playback.log"

for d in *; do
    # Skip non-directory entries and the log file
    [[ -d "$d" ]] || continue

    echo "Playing $d..."
    ros2 bag play -r 0.5 "$d" >> "$log_file" 2>&1 &
    bag_pid=$!

    # Wait for the bag play to complete
    wait $bag_pid || exit $?

    # Sleep between bags
    echo "Sleep for 10 seconds..."
    sleep 5 &
    sleep_pid=$!
    wait $sleep_pid || exit $?
done

echo "Playback complete. Log saved to: $log_file"
