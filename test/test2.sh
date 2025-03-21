for n in $(seq 1 16) ; do
  python ./test2.py &
done
wait
