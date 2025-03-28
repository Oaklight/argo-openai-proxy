for n in $(seq 1 16) ; do
  python ./test.py &
done
wait
