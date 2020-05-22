# run as mc_server!

tmux -S tmux.sock new-session -s termination-listener -d
tmux -S tmux.sock send-keys -t termination-listener "python3 termination_listener.py" ENTER
