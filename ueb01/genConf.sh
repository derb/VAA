rm config
touch config

portRange=6000

for i in $(seq 1 1 $1)
  do
    port=$((portRange + i))
    echo "$i 127.0.0.1:$port" >> config 
  done   
