# run as mc_server!

tmux -S socket new-session -s termination-listener -d
tmux -S socket send-keys -t termination-listener "python3 termination_listener" ENTER
